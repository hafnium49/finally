# FinAlly — AI Trading Workstation

An AI-powered trading workstation that streams live market data, simulates portfolio trading on $10,000 of virtual cash, and lets an LLM chat assistant analyze positions and execute trades via natural language.

Built end-to-end by coordinated coding agents as a capstone project for an agentic AI coding course. The full vision and spec is in [`planning/PLAN.md`](planning/PLAN.md); the agent orchestration approach is in [`planning/AGENT_TEAM.md`](planning/AGENT_TEAM.md).

## Status

All v1 components specified in `PLAN.md` are now in the repository:

| Component | Status |
|---|---|
| Market data simulator (GBM) | Done |
| Massive (Polygon.io) client | Done |
| In-memory price cache | Done |
| SSE streaming module | Done |
| SSE ↔ FastAPI wiring | Done |
| FastAPI HTTP layer | Done |
| SQLite schema + persistence | Done |
| Portfolio / trade execution | Done |
| LLM chat integration | Done |
| Frontend (Next.js) | Done |
| Dockerfile / start scripts | Done |
| E2E Playwright suite | Done |

Test totals: **279/279 backend (pytest)**, **37/37 frontend (vitest)**, **10/10 E2E (Playwright)**. The golden-path live smoke (Docker + real OpenRouter + browser drive) is also documented in [`planning/SHIPPED.md`](planning/SHIPPED.md).

This is a simulated trading environment with no authentication. It is intended for **local use only** — see the warning in `planning/PLAN.md` §11 before exposing it on a network.

## Running the App

### Prerequisites

- Docker (Desktop on macOS/Windows, or Docker Engine on Linux)
- A `.env` file at the project root. Copy `.env.example` and fill in at minimum:
  ```bash
  OPENROUTER_API_KEY=sk-or-...   # required for live LLM chat
  ```

### Start (macOS / Linux)

```bash
bash scripts/start_mac.sh
```

### Start (Windows PowerShell)

```powershell
scripts\start_windows.ps1
```

Either script builds the Docker image (first run only), mounts `./db/` for SQLite persistence, loads `.env`, and exposes the app on port 8000. Visit:

```
http://localhost:8000
```

You'll land on the trading workstation with the default watchlist of 10 tickers streaming live, $10,000 cash, and the AI chat panel ready.

### Stop

```bash
bash scripts/stop_mac.sh           # macOS / Linux
scripts\stop_windows.ps1           # Windows
```

The SQLite database in `db/finally.db` persists across restarts. Delete that file to reset to a fresh seeded state.

### Tests

```bash
# Backend unit tests
cd backend && uv sync --dev && uv run pytest

# Frontend unit tests
cd frontend && npm install && npm test

# E2E (requires Docker; spins up app + Playwright via docker-compose.test.yml)
bash test/run-e2e.sh
```

## Environment Variables

| Variable | Required | Effect |
|---|---|---|
| `OPENROUTER_API_KEY` | Yes (for chat) | API key for OpenRouter; backend routes LLM calls through `openrouter/openai/gpt-oss-120b` with Cerebras inference. Without it, `/api/chat` will fail unless `LLM_MOCK=true`. |
| `MASSIVE_API_KEY` | No | If set, market data comes from the Massive (Polygon.io) REST client. If unset or empty, the in-process GBM simulator is used (recommended default). |
| `LLM_MOCK` | No | Set to `true` to return deterministic mock LLM responses (used by the E2E suite and for development without an API key). Defaults to `false`. |

See `.env.example` for the template.

## What's Inside

The codebase is organized around the agent-team layout in [`planning/AGENT_TEAM.md`](planning/AGENT_TEAM.md). Each module below was owned end-to-end by one agent role:

| Module | Owner role | Highlights |
|---|---|---|
| `backend/app/market/` | Market Data Engineer | GBM simulator, Massive REST client, shared `PriceCache` with version-counter change detection, SSE generator. |
| `backend/app/db/` | DB Engineer | `schema.sql` (8 tables incl. `chat_state` for conversation summary), lazy init from FastAPI lifespan, connection helpers, seed data. 26 unit tests. |
| `backend/app/portfolio/` | Portfolio Engineer | Per-user `asyncio.Lock` serializing trade execution, position math, 30s portfolio snapshots, 5s tick-history persister with 7-day pruning. Race-tested. |
| `backend/app/chat/` | LLM Engineer | LiteLLM → OpenRouter (Cerebras) client, structured-output schema, prompt assembly with rolling summary of older turns, action executor, deterministic mock mode. |
| `backend/app/api/` + `backend/app/main.py` | Backend API Engineer | FastAPI app with lifespan startup, REST + SSE routes per `PLAN.md` §8, error envelope. |
| `frontend/` | Frontend Engineer | Next.js (static export) — watchlist, sparklines, main chart, treemap heatmap, P&L chart, positions table, trade bar, AI chat panel. 37 unit tests (vitest + Testing Library). |
| `Dockerfile`, `docker-compose.yml`, `scripts/` | DevOps Engineer | Multi-stage Node→Python build; macOS/Linux + Windows start/stop scripts. |
| `test/playwright/` | Integration Tester | 10 Playwright scenarios covering watchlist, trade execution, chat (mocked), and SSE resilience. |

## Repository Layout

```
finally/
├── backend/                   # FastAPI uv project
│   ├── app/
│   │   ├── market/            # Simulator, Massive client, PriceCache, SSE
│   │   ├── db/                # schema.sql, init.py, conn.py, seed.py
│   │   ├── portfolio/         # trade.py, positions.py, snapshots.py, tick_history.py
│   │   ├── chat/              # client, schemas, prompt, executor, summarizer, mock
│   │   ├── api/               # market, watchlist, portfolio, chat, system routes
│   │   └── main.py            # FastAPI app + lifespan
│   ├── tests/                 # pytest suite
│   └── pyproject.toml
├── frontend/                  # Next.js (static export) TypeScript app
│   ├── app/                   # Pages, components, hooks, lib
│   └── __tests__/             # vitest unit tests
├── db/                        # Volume mount target — SQLite finally.db lives here at runtime
├── scripts/                   # start_mac.sh, stop_mac.sh, start_windows.ps1, stop_windows.ps1
├── test/                      # Playwright E2E suite + docker-compose.test.yml + run-e2e.sh
├── planning/                  # Specs, agent docs, archived design notes
│   ├── PLAN.md                # Project specification (source of truth)
│   ├── AGENT_TEAM.md          # Agent orchestration / team roles
│   └── MARKET_DATA_SUMMARY.md # Notes on the market data subsystem
├── Dockerfile                 # Multi-stage Node → Python build
├── docker-compose.yml         # Convenience wrapper for the app container
├── independent-reviewer/      # Plugin/tool for review automation
├── CLAUDE.md                  # Agent-facing project instructions
└── LICENSE
```

## Agent Hooks

`.claude/codex-review.sh` is a helper that runs `codex exec` against recent changes and writes a review file to `planning/`. It was originally wired up as a `Stop` hook in `.claude/settings.json` so a review ran after every Claude Code turn.

The hook is **currently disabled** — `.claude/settings.json` sets `"disableAllHooks": true` because the inline hook command had quoting issues that caused it to fail on certain change sets. The standalone `codex-review.sh` script is preserved and can be re-enabled by:

1. Fixing the command quoting in the `Stop` hook block, and
2. Removing `"disableAllHooks": true` from `.claude/settings.json`.

When re-enabled, expect `planning/review-<timestamp>.md` files to accumulate after each turn.

## License

See [LICENSE](LICENSE).
