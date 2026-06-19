FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_ENV=production \
    DEMO_MODE=true \
    STORAGE_PATH=/data/specpilot.sqlite3

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY specpilot_ai ./specpilot_ai

RUN pip install --upgrade pip \
    && pip install .

RUN useradd --create-home --shell /bin/bash specpilot \
    && mkdir -p /data \
    && chown -R specpilot:specpilot /data /app

USER specpilot

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/ready || exit 1

CMD ["uvicorn", "specpilot_ai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
