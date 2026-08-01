# syntax=docker/dockerfile:1.7
#
# HypoKiln — multi-stage image.
#
# Stage 1: build the Next.js dashboard.
# Stage 2: slim Python runtime with the orchestrator + control plane.
#          The dashboard is served by its own `web` service in docker-compose;
#          this image only carries the Python side. Keeps the image small and
#          lets the API run standalone (`docker run -p 8765:8765 ...`).

# ── 1. web build stage ─────────────────────────
FROM node:25-alpine AS web-builder
WORKDIR /web
COPY web/package.json web/package-lock.json* ./
RUN npm ci --no-audit --no-fund
COPY web/ .
RUN npm run build

# ── 2. python runtime ──────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HYPOKILN_STATE_DIR=/data/state \
    HYPOKILN_SKIP_SKILLS=1

# Build deps for any wheels that need compilation, plus git so `kiln` can
# `git clone` skill packs at runtime if configured.
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only what's needed to install first — keeps layers cacheable.
COPY pyproject.toml README.md ./
COPY hypokiln/ ./hypokiln/
COPY agents/ ./agents/
COPY control/ ./control/
COPY skills/ ./skills/
COPY factory/ ./factory/
COPY scripts/ ./scripts/

RUN pip install --upgrade pip \
 && pip install ".[control]"

# Carry the prebuilt web bundle for users who want to serve static assets
# from the same image (e.g. behind a reverse proxy). Mount or symlink as
# needed; `make dev` in compose still runs Next.js as its own service.
COPY --from=web-builder /web/.next /app/web/.next
COPY --from=web-builder /web/public /app/web/public

# State volume — runs persist outside the image.
RUN mkdir -p /data/state /data/products
VOLUME ["/data"]

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://localhost:8765/healthz || exit 1

# Default: run the FastAPI control plane. Override with `kiln build ...` to
# use the CLI inside the container.
CMD ["uvicorn", "control.main:app", "--host", "0.0.0.0", "--port", "8765"]
