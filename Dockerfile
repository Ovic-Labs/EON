# OVIC EON — Emotion Recognition System (ERS) CPU-First Production Container
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=4 \
    ORT_DISABLE_ALL_ACCELERATORS=0

WORKDIR /app

# Create unprivileged runtime user
RUN groupadd --system ersgroup && useradd --system --gid ersgroup --create-home ersuser

# Upgrade pip and setuptools first to eliminate known packaging vulnerabilities
RUN python -m pip install --no-cache-dir --upgrade pip "setuptools>=84.1.0"

COPY pyproject.toml LICENSE README.md ./
COPY packages/ers/ ./packages/ers/

RUN pip install --no-cache-dir "./packages/ers[ml,live]" && \
    chown -R ersuser:ersgroup /app

USER ersuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()"

CMD ["uvicorn", "eon_ers.live.server:create_live_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
