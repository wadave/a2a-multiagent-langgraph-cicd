FROM python:3.12-slim
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libffi-dev gcc zlib1g-dev libjpeg-dev libgeos-dev && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY . /app
ENV PATH="/app/.venv/bin:$PATH"
RUN uv sync --no-install-project --index-url https://pypi.org/simple
ENTRYPOINT ["python", "main.py"]
