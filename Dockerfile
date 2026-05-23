# syntax=docker/dockerfile:1.7

# ---------------------------------------------------------------------------
# FinAlly — single-image build
#
# Stage 1 (frontend-build): build the Next.js static export (`output: 'export'`)
#                           producing frontend/out/, which the FastAPI app
#                           serves as static files at the same origin.
#
# Stage 2 (runtime):        Python 3.12 + uv, copies the backend, installs
#                           dependencies from the lockfile, drops the static
#                           export into /app/static, and runs uvicorn as the
#                           non-root `app` user on port 8000.
#
# See planning/PLAN.md §11 for the contract.
# ---------------------------------------------------------------------------

# =============================================================================
# Stage 1: frontend-build
# =============================================================================
FROM node:20-slim AS frontend-build

WORKDIR /build/frontend

# Copy manifest(s) first to maximise layer caching. The lockfile may not yet
# exist (frontend scaffolding lands in parallel) so guard the COPY.
COPY frontend/package*.json ./

# Use `npm ci` if a lockfile is present, fall back to `npm install` otherwise.
RUN if [ -f package-lock.json ]; then \
        npm ci; \
    else \
        npm install; \
    fi

# Copy the rest of the frontend source and build the static export.
# next.config.ts has `output: 'export'`, so `next build` writes to ./out/.
COPY frontend/ ./
RUN npm run build

# =============================================================================
# Stage 2: runtime
# =============================================================================
FROM python:3.12-slim AS runtime

# Faster, quieter, byte-code-free Python in container.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# curl is needed by the HEALTHCHECK below.
# ca-certificates is needed for outbound HTTPS (OpenRouter, Massive).
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Install uv (pinned). Using pip keeps this hermetic and avoids needing a
# shell-script installer.
RUN pip install --no-cache-dir "uv==0.5.11"

# Non-root user. We will chown /app to this user after files are copied.
RUN useradd --create-home --shell /bin/bash --uid 1000 app

WORKDIR /app

# Install Python deps from the lockfile first (best cache hit).
# We deliberately copy only the manifest + lockfile so dep installs are not
# invalidated by application code edits.
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Now copy the application source.
COPY backend/ ./

# Install the project itself into the venv (separate layer for fast rebuilds).
RUN uv sync --frozen --no-dev

# Bring in the static export from stage 1.
COPY --from=frontend-build /build/frontend/out /app/static

# Runtime DB directory (volume mount target). Must be writable by `app`.
RUN mkdir -p /app/db \
 && chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
