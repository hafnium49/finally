#!/usr/bin/env bash
# Stop the FinAlly container (macOS / Linux).
# Idempotent: exits 0 whether or not the container was running.
# The ./db volume is intentionally NOT removed — data persists across stops.

set -euo pipefail

CONTAINER="finally"

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: docker is not installed or not on PATH." >&2
    exit 1
fi

if docker rm -f "${CONTAINER}" >/dev/null 2>&1; then
    echo "Stopped."
else
    echo "Not running."
fi
