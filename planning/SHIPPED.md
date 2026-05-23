# SHIPPED — What's actually in the repo

This document is the source of truth for *what's built*. It complements `PLAN.md` (which describes *what the app does*) and `AGENT_TEAM.md` (which describes *how the team built it*). When in doubt about whether a feature exists or how to find it, look here first.

## TL;DR

FinAlly is a full-stack AI trading workstation. It ships as a single Docker container that serves a Next.js SPA at `http://localhost:8000`, backed by a FastAPI server with SQLite persistence, an SSE-driven market data feed, and an LLM chat assistant on OpenRouter (Cerebras provider).

| | Result |
|---|---|
| Backend unit tests | 279 / 279 |
| Frontend unit tests | 37 / 37 |
| Mocked E2E (Playwright) | 10 / 10 |
| Live smoke (real OpenRouter) | golden path verified |
| Open bugs | 1 (B019, favicon 404, cosmetic) |
| Container image | builds + healthchecks in <10s on a warm cache |

## How to run it

Local-only. See `PLAN.md` §11 — no auth, do not expose publicly.

```bash
# Prereqs: Docker, .env with OPENROUTER_API_KEY=sk-or-...
bash scripts/start_mac.sh        # macOS / Linux
scripts\start_windows.ps1        # Windows PowerShell
# Visit http://localhost:8000
bash scripts/stop_mac.sh         # to stop
```

`./db/finally.db` persists across restarts (bind mount). Delete it to reset to a fresh seeded portfolio.

## Module map

| Path | Purpose | Built by |
|---|---|---|
| `backend/app/market/` | GBM simulator, Massive REST client, `PriceCache`, SSE generator | Market Data Engineer (pre-existing) |
| `backend/app/db/` | SQLite schema (8 tables), lazy init, connection helpers, seed | DB Engineer |
| `backend/app/portfolio/` | `execute_trade` with per-user `asyncio.Lock`, position math, snapshot writer, tick-history persister | Backend API Engineer |
| `backend/app/chat/` | LiteLLM → OpenRouter (Cerebras) client, prompt assembly, mock mode, executor, rolling summarizer | LLM Engineer |
| `backend/app/api/` + `main.py` | FastAPI app, lifespan startup, 11 REST/SSE routes, static-file mount | Backend API Engineer |
| `frontend/` | Next.js static-export SPA (watchlist, charts, heatmap, P&L, positions, trade bar, chat panel) | Frontend Engineer |
| `Dockerfile`, `docker-compose.yml`, `scripts/` | Multi-stage Node→Python build, idempotent start/stop scripts for macOS/Linux + Windows | DevOps Engineer |
| `test/playwright/` | 10 Playwright scenarios + `docker-compose.test.yml` + `run-e2e.sh` | Integration Tester |
| `backend/app/chat/system_prompt.py` | LLM voice block — "terse desk trader" | **User** (1-slot human contribution) |

Repository tree is mirrored in `README.md`.

## How it was built

A 6-agent team coordinated by an orchestrator (the main Claude Code session). See `AGENT_TEAM.md` for the team plan and the Appendix A post-mortem for execution details.

### Phases

1. **Contracts** — DB Engineer wrote `SCHEMA.md`, Backend API wrote `API_CONTRACT.md`, LLM Engineer wrote `LLM_CONTRACT.md`. Three frozen docs that the builders consumed read-only.
2. **Parallel build** — 5 builders dispatched simultaneously, each owning a disjoint subtree. Zero merge conflicts.
3. **Mocked integration loop** — Integration Tester ran Playwright E2E under `LLM_MOCK=true`. Bugs routed to owning agents. Looped until 10/10 green.
4. **Live smoke** — Real OpenRouter LLM exercised against the running stack via browser drive. Caught two majors the mocked suite missed.

### Bug ledger (full chronology in `planning/BUGS.md`)

| ID | Owner | Severity | Iter | Status |
|---|---|---|---:|---|
| B001 | frontend | blocker | 1 | Fixed `5385833` — single mount; Tailwind `order-*` for responsive |
| B002 | tester | minor | 1 | Fixed `5385833` — SSE test: `route.abort` instead of `fulfill(503)` |
| B003 | tester | minor | 1 | Fixed `5385833` — `down -v` wrapper in `test/run-e2e.sh` |
| B004 | tester | minor | 1 | Fixed `5385833` — test ordering + delta assertions |
| B005 | orchestrator | minor | — | Sandbox config note (no code) |
| B006 | llm | major | 2 | Fixed `496a6cb` — `price_cache` threaded through chat path |
| B017 | llm | major | 3 | Fixed `4082ce8` — `get_portfolio_context` now reaches LLM prompt |
| B018 | devops | major | 3 | Fixed `6f54251` — `chmod 0777 db/` in start scripts |
| B019 | frontend | minor | — | Deferred — favicon 404, cosmetic only |

## Lessons learned

### 1. Mock fidelity matters more than test count

A 10/10 green mocked E2E suite hid two majors. The regex-keyed chat mock ignored prompt content entirely → couldn't catch the empty-context bug (B017). The test stack's Docker-named volume bypassed bind-mount perms → couldn't catch the uid mismatch (B018).

**Takeaway**: mocks that strip the very signal you're testing give false confidence. Pair mocked E2E with at least one live smoke before declaring shipped. For mock-mode chat tests specifically, capture the assembled prompt and assert that the context reached it — don't just assert on the response shape.

### 2. Disjoint subtree ownership beats code review

Five agents wrote ~5,000 LOC in parallel. The only thing keeping them from clobbering each other was a contract that said "you own these directories and only these directories." No agent ever needed to read another agent's code; they only read each other's frozen contract docs in `planning/`.

**Takeaway**: for parallel agent work, ownership is the dominant variable. Code review can catch conflicts after the fact; ownership prevents them entirely.

### 3. Contracts before code

Phase 1 (contract docs) caught the SSE per-frame-map vs. per-event shape mismatch *before* anyone built against the wrong assumption. Without it, the frontend would have iterated event-by-event and the backend per-frame, and integration would have surfaced the mismatch a day later.

**Takeaway**: when interfaces are non-trivial, freezing the contract in a doc and getting the orchestrator's review costs minutes and saves iterations.

### 4. Reserve one high-leverage slot for human authorship

`SYSTEM_PROMPT_VOICE` is six lines. Everything else in the chat subsystem is mechanical (assembly, parsing, executing). Those six lines determine the entire feel of the assistant.

**Takeaway**: in an otherwise agent-built feature, identify the one place where a human voice has the highest leverage and reserve it explicitly. Don't let the agents fill it with a generic default.

### 5. Bug routing beats bug triage

Each bug in `BUGS.md` has an `owner` field. The orchestrator's job at every iteration was to send each bug to its owner with ONLY the relevant context, not the whole file. This kept each fix tight (no scope creep) and parallelizable (B017 and B018 fixed simultaneously by different agents).

**Takeaway**: structured bug reports with explicit ownership turn into routing work, not triage work. The integration tester's discipline ("file bugs, don't fix them") makes this possible.

## Where to look next

- `PLAN.md` — the spec. What the app should do.
- `AGENT_TEAM.md` — the team plan + Appendix A (post-mortem).
- `BUGS.md` — full bug chronology with reproducible cases.
- `SCHEMA.md`, `API_CONTRACT.md`, `LLM_CONTRACT.md` — frozen contracts.
- `backend/CLAUDE.md` — backend developer guide (module-by-module).
- `frontend/README.md` — frontend stack notes and wire-contract assumptions.
- `.claude/agents/*.md` — persona files for the six builder roles.
- `smoke/` — screenshots from the live smoke test (5 images covering the golden path).
