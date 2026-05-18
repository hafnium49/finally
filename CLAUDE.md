# FinAlly Project — the Finance Ally

All project documentation lives in `planning/`. The full specification is `planning/PLAN.md` (included via `@` below).

## Current State

Only the **market data subsystem** is implemented. The remainder of the platform (FastAPI app wiring, SQLite, portfolio, chat, frontend, Docker) is still to be built — see `planning/PLAN.md` for the full vision.

### What exists today

| Component | Location | Notes |
|---|---|---|
| Market data simulator (GBM) | `backend/app/market/simulator.py` | Default when `MASSIVE_API_KEY` is unset |
| Massive (Polygon.io) client | `backend/app/market/massive_client.py` | Used when `MASSIVE_API_KEY` is set |
| In-memory price cache | `backend/app/market/cache.py` | Thread-safe, version-counter for change detection |
| SSE streaming router | `backend/app/market/stream.py` | Push-on-change + 15s keepalive (not yet mounted on an app) |
| Source factory | `backend/app/market/factory.py` | Env-var driven selection |
| **Rich terminal dashboard** | `backend/market_data_demo.py` | Live UI: header + timer, price table with sparklines, event log |
| Test suite | `backend/tests/market/` | 103 tests, ~98% coverage |

### Architecture in one paragraph

`MarketDataSource` (ABC) has two implementations (`SimulatorDataSource`, `MassiveDataSource`). Both are the **only** writers to `PriceCache`, which is the single fan-out point. Consumers (SSE generator, terminal demo, future portfolio code) only read from the cache and use its monotonic `version` counter to detect changes without polling each ticker. The `factory.create_market_data_source(cache)` helper selects the implementation from the `MASSIVE_API_KEY` env var.

### Terminal dashboard

`backend/market_data_demo.py` is a standalone Rich-based dashboard that wires the simulator → cache and renders three regions inside a `rich.live.Live` loop:

- **Header** with a running elapsed/remaining timer and ticker count
- **Live Prices table** with per-ticker price, change, percent, ▲/▼/─ arrow, and a 40-point unicode sparkline; colored green/red/dim by direction
- **Recent Events panel** logging notable moves (|Δ%| > 1.0) with timestamps

Run with `cd backend && uv run market_data_demo.py`. Duration defaults to 60s; Ctrl+C exits early. A session summary prints on exit.

## Documentation Map

- `planning/PLAN.md` — full project specification (source of truth, included below)
- `planning/MARKET_DATA_SUMMARY.md` — concise summary of what's been built (simulator + demo UI + tests)
- `planning/archive/` — older design docs, the original interface spec, the pre-fix review, and the previous Massive integration write-up. Consult only for historical context.

## Agent Notes

- The market data subsystem is feature-complete for now. Treat its public API (`PriceCache`, `PriceUpdate`, `MarketDataSource`, `create_market_data_source`, `create_stream_router`) as a stable contract for downstream work.
- The terminal demo is the canonical example of how to consume the cache directly. Future in-process consumers (e.g., a `price_ticks` persister) should follow the same pattern: read the cache, watch `version`, push when it advances.
- Backend-specific developer notes (commands, imports, tests) are in `backend/CLAUDE.md`.

@planning/PLAN.md
