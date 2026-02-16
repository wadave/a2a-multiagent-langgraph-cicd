FROM python:3.12-slim
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY . /app
ENV PATH="/app/.venv/bin:$PATH"
RUN uv sync
ENTRYPOINT ["uv", "run", "fastmcp", "run", "weather_server.py"]
