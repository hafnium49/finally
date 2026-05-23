#!/usr/bin/env bash
# Stop-hook helper: runs codex to review changes since the last commit.
# Lives in its own file so the hook doesn't have to wrestle with multi-layer
# JSON-then-shell quote escaping for the codex prompt argument.

set -u
mkdir -p /tmp/claude
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
PROMPT="Review changes since last commit and write results to a file named planning/review-${TIMESTAMP}.md"
exec codex exec "${PROMPT}" </dev/null >>/tmp/claude/codex-stop.log 2>&1
