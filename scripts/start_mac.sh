#!/usr/bin/env bash
# Start the FinAlly container (macOS / Linux).
# Usage:
#   scripts/start_mac.sh            # build only if image missing
#   scripts/start_mac.sh --build    # force rebuild
#
# Idempotent: safe to run repeatedly. Any existing `finally` container is
# removed before a new one is started.

set -euo pipefail

IMAGE="finally:latest"
CONTAINER="finally"
PORT=8000

# Move to the project root (parent of scripts/) so relative paths resolve
# regardless of where the user invokes the script from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

# Parse flags.
FORCE_BUILD=0
for arg in "$@"; do
    case "${arg}" in
        --build) FORCE_BUILD=1 ;;
        -h|--help)
            cat <<EOF
Usage: $(basename "$0") [--build]

  --build   Force-rebuild the Docker image even if it already exists.

The container is named "${CONTAINER}" and listens on port ${PORT}.
The SQLite database is persisted to ./db on the host.
EOF
            exit 0
            ;;
        *)
            echo "Unknown argument: ${arg}" >&2
            exit 2
            ;;
    esac
done

# Sanity check: docker must be on PATH.
if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: docker is not installed or not on PATH." >&2
    exit 1
fi

# Warn (don't fail) if .env is missing — the container will still come up but
# the LLM chat won't work without OPENROUTER_API_KEY.
if [ ! -f .env ]; then
    echo "WARNING: .env not found. Copy .env.example to .env and fill in keys." >&2
    echo "         Continuing without it; LLM chat will be unavailable." >&2
    ENV_FILE_ARG=()
else
    ENV_FILE_ARG=(--env-file .env)
fi

# Ensure the bind-mount target exists on the host.
mkdir -p db

# Build the image if missing, or if --build was requested.
if [ "${FORCE_BUILD}" -eq 1 ] || ! docker image inspect "${IMAGE}" >/dev/null 2>&1; then
    echo "Building ${IMAGE}..."
    docker build -t "${IMAGE}" .
else
    echo "Reusing existing image ${IMAGE} (pass --build to force rebuild)."
fi

# Remove any prior container with the same name (idempotency).
docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true

# Launch.
docker run -d \
    --name "${CONTAINER}" \
    -p "${PORT}:${PORT}" \
    "${ENV_FILE_ARG[@]}" \
    -v "$(pwd)/db:/app/db" \
    --restart unless-stopped \
    "${IMAGE}" >/dev/null

echo "FinAlly is starting at http://localhost:${PORT} — tail logs with: docker logs -f ${CONTAINER}"
