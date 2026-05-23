#!/usr/bin/env bash
# run-e2e.sh — One-shot wrapper for the FinAlly Phase 3 Playwright suite.
#
# Why this script exists (planning/BUGS.md B003):
#   The docker-compose.test.yml uses a named volume `finally_test_db` so each
#   suite run starts from a clean SQLite database. A plain `docker compose down`
#   leaves that volume in place, so re-running the suite without `-v` carries
#   over $10k → e.g. $9,431.06 cash plus leftover positions from prior runs,
#   and test 01 / 03 / 05 then fail their "starts from $10,000.00" assertions.
#
#   This wrapper ALWAYS passes `-v` on teardown — and runs teardown both BEFORE
#   start-up (to guarantee a clean slate even if a prior crashed run left a
#   volume around) and AFTER the suite (regardless of pass/fail). The volume
#   delete is intentional; do not remove the `-v` flags without re-reading
#   BUGS.md B003.
#
# Usage:
#   test/run-e2e.sh                       # full rebuild + run
#   test/run-e2e.sh --no-build            # skip docker build (image already up to date)
#   test/run-e2e.sh -- <playwright args>  # forward args (e.g. `-- 03-buy-shares`)

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$REPO_ROOT/test/docker-compose.test.yml"
PLAYWRIGHT_DIR="$REPO_ROOT/test/playwright"

BUILD=1
PW_ARGS=()
while (( "$#" )); do
  case "$1" in
    --no-build) BUILD=0; shift ;;
    --) shift; PW_ARGS+=("$@"); break ;;
    *) PW_ARGS+=("$1"); shift ;;
  esac
done

cleanup() {
  echo "[run-e2e] tearing down stack with volume removal (-v)..."
  docker compose -f "$COMPOSE_FILE" down -v >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "[run-e2e] pre-flight: removing any pre-existing volume..."
cleanup

if [ "$BUILD" = 1 ]; then
  echo "[run-e2e] building finally:test..."
  docker build -t finally:test "$REPO_ROOT"
fi

echo "[run-e2e] starting stack..."
docker compose -f "$COMPOSE_FILE" up -d

echo "[run-e2e] waiting for /api/health (up to 60s)..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
    echo "[run-e2e] healthy after ${i} polls"
    break
  fi
  sleep 2
done

if ! curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
  echo "[run-e2e] FATAL: /api/health never returned 200"
  docker logs finally-test 2>&1 | tail -30
  exit 1
fi

echo "[run-e2e] running Playwright..."
cd "$PLAYWRIGHT_DIR"
npx playwright test --reporter=list "${PW_ARGS[@]}"
EXIT_CODE=$?

echo "[run-e2e] Playwright exit: $EXIT_CODE"
exit $EXIT_CODE
