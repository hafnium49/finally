# FinAlly — AI Trading Workstation

An AI-powered trading workstation that will stream live market data, simulate portfolio trading, and let an LLM chat assistant analyze positions and execute trades via natural language.

Built incrementally by coding agents as a capstone project for an agentic AI coding course. The full vision is in [`planning/PLAN.md`](planning/PLAN.md); this README describes what you can actually run today.

## Status

This repo is mid-build. Only the **market data subsystem** is implemented:

| Component | Status |
|---|---|
| Market data simulator (GBM) | Done |
| Massive (Polygon.io) client | Done |
| In-memory price cache | Done |
| SSE streaming module | Done (not yet wired to an HTTP server) |
| FastAPI HTTP layer | Not built |
| SQLite schema + persistence | Not built |
| Portfolio / trade execution | Not built |
| LLM chat integration | Not built |
| Frontend (Next.js) | Not built |
| Dockerfile / start scripts | Not built |

If you came here expecting a runnable trading app, **come back later**. If you're here to inspect the market data work or run its tests, read on.

See [`planning/MARKET_DATA_SUMMARY.md`](planning/MARKET_DATA_SUMMARY.md) for the completed component's design notes.

## Running What Exists

Everything live today is under `backend/`. You'll need [`uv`](https://docs.astral.sh/uv/) and Python 3.12+.

```bash
cd backend
uv sync --dev          # install dependencies
uv run pytest          # run the market data test suite
uv run python market_data_demo.py    # watch the simulator stream prices
```

The demo prints live price ticks from the GBM simulator to stdout — handy for sanity-checking that the cache and update loop behave as documented in `planning/PLAN.md` §6.

## Environment Variables

Only one variable is read by the code that currently exists:

| Variable | Required | Effect |
|---|---|---|
| `MASSIVE_API_KEY` | No | If set, the market data factory uses the Massive (Polygon.io) client. If unset or empty, it uses the built-in GBM simulator. |

The full env-var surface (`OPENROUTER_API_KEY`, `LLM_MOCK`, etc.) is described in `planning/PLAN.md` §5 but those variables are not yet consumed.

There is no `.env.example` yet. Export `MASSIVE_API_KEY` in your shell or omit it.

## Repository Layout

```
finally/
├── backend/                   # uv project — only live code lives here
│   ├── app/market/            # Implemented: simulator, cache, SSE, Massive client
│   ├── tests/                 # pytest suite for the market subsystem
│   ├── market_data_demo.py    # Standalone demo: prints streaming prices
│   └── README.md              # Backend-specific dev notes
├── planning/                  # Specs and agent-generated review files
│   ├── PLAN.md                # Full project specification (source of truth)
│   ├── MARKET_DATA_SUMMARY.md # Notes on the completed component
│   ├── archive/               # Earlier design docs
│   └── review-*.md            # Auto-generated reviews (see "Agent Hooks" below)
├── independent-reviewer/      # Plugin/tool for review automation
├── CLAUDE.md                  # Agent-facing project instructions
└── LICENSE
```

Directories mentioned in `PLAN.md` but **not yet present**: `frontend/`, `db/`, `scripts/`, `test/` (E2E), and the root `Dockerfile`.

## Agent Hooks

A `Stop` hook in `.claude/settings.json` runs `codex exec` after each Claude Code turn and writes a review of recent changes to `planning/review-<timestamp>.md`. If you're running Claude Code locally against this repo, expect `planning/` to accumulate these files. They're committed git-ignored only if you choose — by default they will appear in `git status`.

To disable, remove the `Stop` block from `.claude/settings.json`.

## License

See [LICENSE](LICENSE).
