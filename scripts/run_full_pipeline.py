from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    code_dir = Path(__file__).resolve().parent.parent
    default_config = code_dir / "config.yml"
    prompt = f"Path to synpp config file [{default_config}]: "
    raw_value = input(prompt).strip()

    config_path = Path(raw_value) if raw_value else default_config
    if not config_path.is_absolute():
        candidate = code_dir / config_path
        if candidate.is_file():
            config_path = candidate

    if not config_path.is_file():
        print(f"Error: config file not found: {config_path}", file=sys.stderr)
        return 1

    command = [sys.executable, "-m", "synpp", str(config_path)]
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, cwd = code_dir)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
