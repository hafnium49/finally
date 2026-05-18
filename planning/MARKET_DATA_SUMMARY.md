# Market Data — Implementation Summary

**Status:** Simulator, real-data client, in-memory cache, SSE streaming, and a live terminal dashboard are all complete and tested. 103 tests pass with ~98% coverage on the `app.market` package.

This document captures the shape of the market data subsystem and the terminal UI that visualizes it. For the original design rationale, retired pre-fix review notes, and earlier interface drafts, see `planning/archive/`.

## Scope

Two deliverables, one feature:

1. **Market data subsystem** — `backend/app/market/`. Streams mock or real prices through a single in-memory cache that fans out to all consumers.
2. **Rich terminal dashboard** — `backend/market_data_demo.py`. Live visualization of the simulator with a status header, color-coded price table, unicode sparklines, and an event log panel.

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                  Market Data Subsystem                         │
│                                                                │
│   MarketDataSource (ABC)                                       │
│   ├── SimulatorDataSource  ──► GBM with correlated moves       │
│   └── MassiveDataSource    ──► Polygon.io REST poller          │
│                       │                                        │
│                       ▼                                        │
│                  PriceCache (thread-safe, version-counter)     │
│                       │                                        │
│        ┌──────────────┼─────────────────┐                      │
│        ▼              ▼                 ▼                      │
│   SSE endpoint   Terminal Demo    Future portfolio /           │
│   (push-on-     (Rich Live      trade / chat consumers         │
│    change)      dashboard)                                     │
└────────────────────────────────────────────────────────────────┘
```

The `PriceCache` is the single point of fan-out. Producers (simulator or Massive poller) are the **only** writers. Consumers (SSE generator, terminal UI, future portfolio code) only read. The cache bumps a monotonic `version` counter on every change so consumers can detect "something moved" without polling individual tickers.

## Module Map

| File | Role |
|------|------|
| `app/market/models.py` | `PriceUpdate` — frozen dataclass with `ticker`, `price`, `previous_price`, `timestamp`, `change`, `change_percent`, `direction` |
| `app/market/interface.py` | `MarketDataSource` ABC — `start/stop/add_ticker/remove_ticker/get_tickers` |
| `app/market/cache.py` | `PriceCache` — thread-safe store, monotonic `version`, `update/get/get_price/get_all/remove` |
| `app/market/seed_prices.py` | Realistic seed prices, per-ticker GBM params, sector correlation groups |
| `app/market/simulator.py` | `GBMSimulator` (Geometric Brownian Motion, Cholesky-correlated moves, random shock events) + `SimulatorDataSource` |
| `app/market/massive_client.py` | `MassiveDataSource` — REST polling for Polygon.io via the `massive` SDK |
| `app/market/factory.py` | `create_market_data_source()` — picks simulator or Massive based on `MASSIVE_API_KEY` |
| `app/market/stream.py` | `create_stream_router()` — FastAPI SSE router with push-on-change + 15s keepalive |
| `backend/market_data_demo.py` | Standalone Rich terminal dashboard wiring `SimulatorDataSource` → `PriceCache` → live UI |

## Simulator Behavior

- **Geometric Brownian motion** per ticker, ~500 ms tick interval (configurable).
- **Correlated moves** via Cholesky decomposition of a sector correlation matrix (tech: 0.6, finance: 0.5, cross-sector: 0.3) — tech stocks tend to move together, financials track each other, everything has a mild market-wide correlation.
- **Random shock events** — small (~0.1% per tick per ticker) probability of a 2–5% jump for visual drama in the dashboard.
- **Unknown tickers** — adding a ticker not in `SEED_PRICES` auto-generates a plausible seed and default GBM params, so the watchlist can grow at runtime.

## Terminal Dashboard

The demo (`backend/market_data_demo.py`) renders three regions inside a `rich.live.Live` loop:

| Region | Contents |
|--------|----------|
| **Header** | "FinAlly Market Data Simulator" title, elapsed timer, remaining timer, ticker count, exit hint. Yellow border. |
| **Live Prices table** | Per-ticker row: symbol, price, absolute change, percent change, direction arrow (▲/▼/─), and a 40-point sparkline. Green for upticks, red for downticks, dim gray for flat. |
| **Recent Events log** | Notable moves (|change %| > 1.0) timestamped and color-coded. Newest at top, capped at 12 entries. Shows a placeholder when idle. |

### UI Building Blocks

- `rich.layout.Layout` with three vertical sections (header / body / footer of fixed sizes 3 / flex / 10) — the layout is rebuilt each frame from cache state to keep the rendering logic stateless.
- `rich.live.Live` with `refresh_per_second=4` and `screen=True` — alt-screen rendering avoids scroll spam.
- **Sparklines** use the 8-character ramp `▁▂▃▄▅▆▇█` normalized against the 40-point per-ticker history deque.
- **Change detection** is driven by the cache's `version` counter, not by polling each price. The render loop sleeps 250 ms, compares versions, and only redraws when something changed.
- **Session summary** prints after exit: a side-by-side table of seed price → final price → percent change, colored by direction.

### Running It

```bash
cd backend
uv run market_data_demo.py
```

Default duration is 60 s; exit early with Ctrl+C. The summary table prints either way.

## Streaming (SSE)

`create_stream_router(cache)` produces a FastAPI router with `GET /api/stream/prices`. The generator:

- Pushes a price event **only when the cache's version counter has advanced** for that ticker — no redundant frames at low poll cadences.
- Emits a `: keepalive` comment every 15 s so intermediaries don't close idle connections.
- Each event is `data: {ticker, price, previous_price, timestamp, change, change_percent, direction}`.

The endpoint is wired up by the FastAPI app once it exists. The terminal demo does not go through SSE — it reads the cache directly for simplicity.

## Tests

| Module | Tests | Notes |
|--------|-------|-------|
| `test_models.py` | 11 | `PriceUpdate` math, direction, serialization |
| `test_cache.py` | 19 | push-on-change, thread-safety hammer, `timestamp=0` preservation |
| `test_simulator.py` | 19 | GBM math, drift, correlated moves, shock probabilities |
| `test_simulator_source.py` | 10 | lifecycle integration (`start`/`stop`/`add`/`remove`) |
| `test_factory.py` | 7 | env-var-driven source selection |
| `test_massive.py` | 16 | poll loop, response parsing, case normalization, snapshot lists |
| `test_stream.py` | 10 | SSE push-on-change, keepalive, router identity |
| `test_interface_conformance.py` | 8 | parametrized ABC checks across both sources |

Run:

```bash
cd backend
uv run --extra dev pytest -q       # 103 passing
uv run --extra dev pytest --cov=app
```

## Usage from Downstream Code

```python
from app.market import PriceCache, create_market_data_source, create_stream_router

cache = PriceCache()
source = create_market_data_source(cache)        # simulator or Massive
await source.start(["AAPL", "GOOGL", "MSFT"])

# Read
update = cache.get("AAPL")           # PriceUpdate | None
price  = cache.get_price("AAPL")     # float | None
all_   = cache.get_all()             # dict[str, PriceUpdate]

# Dynamic watchlist
await source.add_ticker("TSLA")
await source.remove_ticker("GOOGL")

# Wire SSE into the FastAPI app
router = create_stream_router(cache)
app.include_router(router, prefix="/api")

# Shutdown
await source.stop()
```

## What's Next

The market data subsystem is feature-complete for the trading workstation. Downstream pieces that still need to be built (per `planning/PLAN.md`):

- FastAPI app composition (mount the SSE router, lifespan hook for the data source)
- SQLite schema + `price_ticks` persister task
- Portfolio module (trade execution, P&L, snapshots)
- Chat / LLM integration
- Next.js frontend

When the frontend lands, the same `PriceCache` will fan out to both the SSE endpoint and any in-process consumers (e.g., a tick-history persister), so nothing about the current contract should need to change.
