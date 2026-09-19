FROM ghcr.io/astral-sh/uv:debian

WORKDIR /app

COPY main.py .
COPY pyproject.toml .
COPY uv.lock .
COPY config.yml .
COPY update_config_from_environ.py .
COPY run_docker.sh .

RUN uv sync
RUN chmod +x run_docker.sh

EXPOSE 8080

CMD ["./run_docker.sh"]