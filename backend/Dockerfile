# ============================================================
# NBA Enterprise AI Platform — Backend Dockerfile
# Multi-stage build: builder + production
# ============================================================

# ---- Stage 1: Builder ----
FROM python:3.11-slim AS builder

WORKDIR /build

# System deps for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ---- Stage 2: Production ----
FROM python:3.11-slim AS production

WORKDIR /app

# Runtime system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd -r nba && useradd -r -g nba -d /app -s /sbin/nologin nba

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY --chown=nba:nba . .

# Create required directories
RUN mkdir -p \
    /app/vector_db/faiss_index \
    /app/data/uploads \
    /app/data/generated_pdfs \
    /app/logs \
    && chown -R nba:nba /app

USER nba

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
