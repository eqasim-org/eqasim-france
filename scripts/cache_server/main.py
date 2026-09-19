import asyncio
import hashlib
import ipaddress
import os
import socket
import time
from pathlib import Path
from urllib.parse import urlparse
import yaml
import re

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CONFIG_FILE = os.getenv("CONFIG_FILE", "config.yaml")

def parse_size(value) -> int:
    """
    Convert sizes such as:
        500MB
        50GB
        1TB
        1000000
    into bytes.
    """
    if isinstance(value, int):
        return value
    value = str(value).strip().upper()

    match = re.fullmatch(
        r"([0-9]+(?:\.[0-9]+)?)\s*(B|KB|MB|GB|TB)?",
        value,
    )

    if not match:
        raise ValueError(f"Invalid size: {value}")

    number = float(match.group(1))
    unit = match.group(2) or "B"

    multipliers = {
        "B": 1,
        "KB": 1024,
        "MB": 1024**2,
        "GB": 1024**3,
        "TB": 1024**4,
    }

    return int(number * multipliers[unit])


def load_config() -> dict:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    server = config.setdefault("server", {})
    cache = config.setdefault("cache", {})
    origin = config.setdefault("origin", {})
    security = config.setdefault("security", {})

    server.setdefault("host", "0.0.0.0")
    server.setdefault("port", 8080)

    cache.setdefault("directory", "./cache")
    cache.setdefault("ttl", 3600)
    cache.setdefault("max_size", "50GB")

    origin.setdefault("connect_timeout", 10)
    origin.setdefault("read_timeout", 60)
    origin.setdefault(
        "user_agent",
        "PythonCachedFileProxy/1.0",
    )

    security.setdefault("allow_http", True)
    security.setdefault("allow_private_addresses", False)

    cache["max_size"] = parse_size(cache["max_size"])

    return config


CONFIG = load_config()

HOST = CONFIG["server"]["host"]
PORT = int(CONFIG["server"]["port"])

CACHE_DIR = Path(CONFIG["cache"]["directory"])
CACHE_TTL = int(CONFIG["cache"]["ttl"]) * 3600
MAX_CACHE_SIZE = CONFIG["cache"]["max_size"]

CONNECT_TIMEOUT = float(CONFIG["origin"]["connect_timeout"])
READ_TIMEOUT = float(CONFIG["origin"]["read_timeout"])
USER_AGENT = CONFIG["origin"]["user_agent"]

CACHE_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Cached File Proxy")

# Prevent multiple clients requesting the same uncached URL from downloading
# it from the origin simultaneously.
_download_locks: dict[str, asyncio.Lock] = {}
_download_locks_guard = asyncio.Lock()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def cache_key(url: str) -> str:
    """Create a filesystem-safe cache key."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def cache_path(url: str) -> Path:
    return CACHE_DIR / cache_key(url)


def meta_path(url: str) -> Path:
    return CACHE_DIR / f"{cache_key(url)}.meta"


def cache_is_valid(path: Path) -> bool:
    if not path.exists():
        return False

    age = time.time() - path.stat().st_mtime
    return age < CACHE_TTL


def validate_url(url: str) -> None:
    """
    Basic SSRF protection.

    Only HTTP/HTTPS URLs are allowed. Hostnames resolving to private,
    loopback, link-local, multicast, or unspecified addresses are rejected.
    """

    try:
        parsed = urlparse(url)
    except Exception:
        raise HTTPException(400, "Invalid URL")

    if parsed.scheme not in ("http", "https"):
        raise HTTPException(400, "Only http:// and https:// URLs are allowed")

    if not parsed.hostname:
        raise HTTPException(400, "URL has no hostname")

    hostname = parsed.hostname

    # Reject obvious local hostnames.
    if hostname.lower() in {
        "localhost",
        "localhost.localdomain",
        "ip6-localhost",
    }:
        raise HTTPException(403, "Access to local addresses is not allowed")

    try:
        addresses = socket.getaddrinfo(
            hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror:
        raise HTTPException(502, "Could not resolve origin hostname")

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])

        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_unspecified
            or ip.is_reserved
        ):
            raise HTTPException(
                403,
                "Access to private or local addresses is not allowed",
            )


async def get_download_lock(url: str) -> asyncio.Lock:
    async with _download_locks_guard:
        lock = _download_locks.get(url)

        if lock is None:
            lock = asyncio.Lock()
            _download_locks[url] = lock

        return lock


def read_metadata(url: str) -> dict:
    path = meta_path(url)

    if not path.exists():
        return {}

    result = {}

    try:
        for line in path.read_text().splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                result[key] = value
    except OSError:
        pass

    return result


def write_metadata(url: str, metadata: dict) -> None:
    path = meta_path(url)
    tmp = path.with_suffix(".tmp")

    content = "\n".join(
        f"{key}={value}"
        for key, value in metadata.items()
    )

    tmp.write_text(content)
    os.replace(tmp, path)


def current_cache_size() -> int:
    total = 0

    try:
        for path in CACHE_DIR.iterdir():
            if path.is_file() and not path.name.endswith(".meta"):
                total += path.stat().st_size
    except OSError:
        pass

    return total


def enforce_cache_size() -> None:
    """
    Simple LRU-ish cleanup based on file modification time.
    Oldest cache entries are deleted first.
    """

    try:
        files = [
            p
            for p in CACHE_DIR.iterdir()
            if p.is_file() and not p.name.endswith(".meta")
        ]

        total = sum(p.stat().st_size for p in files)

        if total <= MAX_CACHE_SIZE:
            return

        files.sort(key=lambda p: p.stat().st_mtime)

        for path in files:
            if total <= MAX_CACHE_SIZE:
                break

            try:
                size = path.stat().st_size
                path.unlink(missing_ok=True)

                metadata = path.with_name(path.name + ".meta")
                metadata.unlink(missing_ok=True)

                total -= size
            except OSError:
                pass

    except OSError:
        pass


async def download_to_cache(url: str) -> tuple[Path, dict]:
    """
    Download the origin into a temporary file and atomically move it into
    the cache once the download succeeds.
    """

    destination = cache_path(url)
    temporary = destination.with_name(destination.name + ".downloading")

    timeout = httpx.Timeout(
        connect=CONNECT_TIMEOUT,
        read=READ_TIMEOUT,
        write=READ_TIMEOUT,
        pool=CONNECT_TIMEOUT,
    )

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
    }

    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
    ) as client:

        # Revalidate the final redirected URL as well.
        async with client.stream(
            "GET",
            url,
            headers=headers,
        ) as response:

            if response.status_code >= 400:
                raise HTTPException(
                    502,
                    f"Origin returned HTTP {response.status_code}",
                )

            # Important: redirects can lead somewhere different from the
            # original hostname. Check the final URL too.
            validate_url(str(response.url))

            content_type = response.headers.get(
                "content-type",
                "application/octet-stream",
            )

            content_length = response.headers.get("content-length")

            metadata = {
                "content_type": content_type,
                "origin_url": url,
            }

            if content_length:
                metadata["content_length"] = content_length

            try:
                with temporary.open("wb") as f:
                    async for chunk in response.aiter_bytes(1024 * 1024):
                        f.write(chunk)

                os.replace(temporary, destination)
                write_metadata(url, metadata)

            except Exception:
                temporary.unlink(missing_ok=True)
                raise

    enforce_cache_size()

    return destination, metadata


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def proxy(request: Request, url: str):
    if not url:
        raise HTTPException(400, "Missing ?url= parameter")

    validate_url(url)

    destination = cache_path(url)

    # -----------------------------------------------------------------------
    # Cache hit
    # -----------------------------------------------------------------------

    if cache_is_valid(destination):
        metadata = read_metadata(url)

        content_type = metadata.get(
            "content_type",
            "application/octet-stream",
        )

        headers = {
            "X-Cache": "HIT",
            "Cache-Control": "public",
        }

        content_length = metadata.get("content_length")

        if content_length:
            headers["Content-Length"] = content_length

        async def cached_stream():
            with destination.open("rb") as f:
                while True:
                    chunk = f.read(1024 * 1024)

                    if not chunk:
                        break

                    yield chunk

        return StreamingResponse(
            cached_stream(),
            media_type=content_type,
            headers=headers,
        )

    # -----------------------------------------------------------------------
    # Cache miss
    # -----------------------------------------------------------------------

    lock = await get_download_lock(url)

    async with lock:
        # Another request may have populated the cache while we waited.
        if cache_is_valid(destination):
            metadata = read_metadata(url)

        else:
            destination, metadata = await download_to_cache(url)

    content_type = metadata.get(
        "content_type",
        "application/octet-stream",
    )

    content_length = metadata.get("content_length")

    headers = {
        "X-Cache": "MISS",
        "Cache-Control": "public",
    }

    if content_length:
        headers["Content-Length"] = content_length

    async def cached_stream():
        with destination.open("rb") as f:
            while True:
                chunk = f.read(1024 * 1024)

                if not chunk:
                    break

                yield chunk

    return StreamingResponse(
        cached_stream(),
        media_type=content_type,
        headers=headers,
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "cache_size": current_cache_size(),
        "cache_ttl": CACHE_TTL,
        "max_cache_size": MAX_CACHE_SIZE,
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
    )
