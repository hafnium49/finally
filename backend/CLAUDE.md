# Backend — Developer Guide

## Project Setup

```bash
cd backend
uv sync --extra dev   # Install all dependencies including test/lint tools
```

## Market Data API

The market data subsystem lives in `app/market/`. Use these imports:

```python
from app.market import PriceCache, PriceUpdate, MarketDataSource, create_market_data_source
```

### Core Types

- **`PriceUpdate`** — Immutable dataclass: `ticker`, `price`, `previous_price`, `timestamp`, plus properties `change`, `change_percent`, `direction` ("up"/"down"/"flat"), and `to_dict()` for JSON serialization.

- **`PriceCache`** — Thread-safe in-memory store. Key methods:
  - `update(ticker, price, timestamp=None) -> PriceUpdate`
  - `get(ticker) -> PriceUpdate | None`
  - `get_price(ticker) -> float | None`
  - `get_all() -> dict[str, PriceUpdate]`
  - `remove(ticker)`
  - `version` property — monotonic counter, increments on every update (for SSE change detection)

- **`MarketDataSource`** — Abstract interface implemented by `SimulatorDataSource` and `MassiveDataSource`. Lifecycle: `start(tickers)` -> `add_ticker()` / `remove_ticker()` -> `stop()`.

- **`create_market_data_source(cache)`** — Factory. Returns `MassiveDataSource` if `MASSIVE_API_KEY` is set, otherwise `SimulatorDataSource`.

### SSE Streaming

```python
from app.market import create_stream_router

router = create_stream_router(price_cache)  # Returns FastAPI APIRouter
# Endpoint: GET /api/stream/prices (text/event-stream)
```

### Seed Data

Default tickers: AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, JPM, V, NFLX. Seed prices and per-ticker volatility/drift params are in `app/market/seed_prices.py`.

## Running Tests

```bash
uv run --extra dev pytest -v              # All tests
uv run --extra dev pytest --cov=app       # With coverage
uv run --extra dev ruff check app/ tests/ # Lint
```

## Terminal Dashboard (`market_data_demo.py`)

A Rich-based live UI that wires `SimulatorDataSource` → `PriceCache` and renders:

- **Header** — title, elapsed/remaining timers, ticker count (yellow border)
- **Live Prices table** — per-ticker price, change, change %, ▲/▼/─ arrow, and a 40-point unicode sparkline; colored green/red/dim by direction
- **Recent Events panel** — timestamped notable moves (|Δ%| > 1.0), newest first, capped at 12 entries
- **Session summary** — printed on exit: seed price → final price → session % change

Implementation notes:
- Uses `rich.layout.Layout` (3 vertical sections: header/body/footer) + `rich.live.Live` with `refresh_per_second=4`, `screen=True`
- Each frame rebuilds the layout from cache state (stateless rendering)
- Render loop polls every 250 ms but only re-renders when `cache.version` advances
- Per-ticker price history kept in a `deque(maxlen=40)` for sparklines

```bash
uv run market_data_demo.py   # 60s by default, Ctrl+C to exit
```
