# Market Data Interface Design

Unified Python interface for market data in FinAlly. Two implementations (simulator and Massive REST poller) sit behind one abstract interface and write to a shared cache. All downstream code — SSE streaming, history endpoint, portfolio valuation, trade execution — is source-agnostic.

This document reflects the **shipped layout in `backend/app/market/`**. The archived version had `PriceCache` co-located with the ABC; the implementation split them.

## File Layout

```
backend/app/market/
  ├── __init__.py          # Public re-exports (PriceCache, PriceUpdate, MarketDataSource,
  │                          create_market_data_source, create_stream_router)
  ├── models.py            # PriceUpdate dataclass
  ├── interface.py         # MarketDataSource ABC (no implementations, no cache)
  ├── cache.py             # PriceCache class
  ├── factory.py           # create_market_data_source()
  ├── simulator.py         # SimulatorDataSource + GBMSimulator
  ├── massive_client.py    # MassiveDataSource (Polygon/Massive REST poller)
  ├── seed_prices.py       # Constants for the simulator (see MARKET_SIMULATOR.md)
  └── stream.py            # FastAPI SSE router factory
```

The 1:1 module-to-concept split is intentional. The ABC has no concrete dependencies, so it can be imported and subclassed in tests without booting NumPy or hitting the network.

## Public Imports

```python
from app.market import (
    PriceUpdate,                  # the data record
    PriceCache,                   # the shared store
    MarketDataSource,             # the ABC
    create_market_data_source,    # the factory
    create_stream_router,         # SSE FastAPI router factory
)
```

## Core Data Model: `PriceUpdate`

```python
@dataclass(frozen=True, slots=True)
class PriceUpdate:
    ticker: str
    price: float
    previous_price: float
    timestamp: float = field(default_factory=time.time)  # Unix seconds

    @property
    def change(self) -> float:           # round(price - previous_price, 4)
        ...
    @property
    def change_percent(self) -> float:   # 0.0 if previous_price == 0
        ...
    @property
    def direction(self) -> str:          # "up" | "down" | "flat"
        ...

    def to_dict(self) -> dict:           # for JSON / SSE serialization
        ...
```

Design choices worth knowing:

- **`frozen=True, slots=True`** — immutable and memory-compact. Every cache update produces a new instance rather than mutating in place; downstream readers can hand the same `PriceUpdate` to multiple consumers without defensive copying.
- **`timestamp` defaults to `time.time()` via `default_factory`** — callers can pass an explicit timestamp (e.g., the Massive client passes `snap.last_trade.timestamp / 1000.0` to preserve the exchange-side time of the trade).
- **`change` / `change_percent` / `direction` are computed properties, not stored fields** — derives them from `price` and `previous_price` so they can't disagree.
- **Unit:** `timestamp` is Unix **seconds** (float). The Massive client converts from the wire format's milliseconds; the simulator uses `time.time()` directly.

## Abstract Interface: `MarketDataSource`

```python
class MarketDataSource(ABC):
    @abstractmethod
    async def start(self, tickers: list[str]) -> None:
        """Begin producing price updates. Call exactly once."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop background task. Safe to call multiple times."""

    @abstractmethod
    async def add_ticker(self, ticker: str) -> None:
        """Add to the active set. No-op if already present."""

    @abstractmethod
    async def remove_ticker(self, ticker: str) -> None:
        """Remove from the active set and from the cache. No-op if absent."""

    @abstractmethod
    def get_tickers(self) -> list[str]:
        """Snapshot of currently tracked tickers."""
```

**The interface does not return prices.** Implementations push into a shared `PriceCache` on their own schedule; consumers read from the cache. This is the strategy pattern: any future data source (WebSocket, replay-from-file for tests) plugs in here without touching the consumer side.

### Lifecycle (FastAPI lifespan)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.market import PriceCache, create_market_data_source, create_stream_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    cache = PriceCache()
    source = create_market_data_source(cache)
    await source.start(initial_tickers=["AAPL", "GOOGL", ...])

    app.state.price_cache = cache
    app.state.market_source = source

    yield

    await source.stop()

app = FastAPI(lifespan=lifespan)
app.include_router(create_stream_router(cache))
```

### Dynamic watchlist

When the user (or LLM) adds/removes a ticker:

```python
await app.state.market_source.add_ticker("PYPL")
await app.state.market_source.remove_ticker("GOOGL")
```

- The **simulator** picks up `add_ticker` on the next 500 ms tick (and seeds the cache immediately so the new ticker has a price right away — see `SimulatorDataSource.add_ticker`).
- The **Massive poller** picks up `add_ticker` lazily on the next poll (15 s by default). The new ticker won't have a price until then.

## `PriceCache`

```python
class PriceCache:
    def __init__(self) -> None:
        self._prices: dict[str, PriceUpdate] = {}
        self._lock = Lock()                  # threading.Lock — not asyncio.Lock
        self._version: int = 0               # monotonically increasing

    def update(self, ticker, price, timestamp=None) -> PriceUpdate: ...
    def get(self, ticker) -> PriceUpdate | None: ...
    def get_price(self, ticker) -> float | None: ...   # convenience: just the price float
    def get_all(self) -> dict[str, PriceUpdate]: ...   # shallow copy
    def remove(self, ticker) -> None: ...

    @property
    def version(self) -> int: ...

    def __len__(self) -> int: ...
    def __contains__(self, ticker: str) -> bool: ...
```

### Why `threading.Lock` and not `asyncio.Lock`

The Massive poller runs its synchronous `RESTClient` call inside `asyncio.to_thread(...)`. That means a write can be in flight from a **non-event-loop thread** while an SSE generator reads from the event loop. A `threading.Lock` correctly serializes those; `asyncio.Lock` would not. The lock is held only for the dict mutation (microseconds), so contention is invisible in practice.

### The `version` counter — what it's for

`update()` and `remove()` bump `version` by 1. The SSE generator caches the last version it sent and only emits a new event when `cache.version` advances. This means:

- Slow upstream sources (Massive on free tier: one update every 15 s) don't cause 30 redundant SSE pushes between real updates.
- Client-side flash animations only fire on actual price changes, not on no-op heartbeats.
- The cost is one integer compare per SSE loop iteration — effectively free.

### Update semantics

- First update for a ticker: `previous_price == price`, so `change == 0` and `direction == "flat"`.
- Prices are rounded to 2 decimals on insert (`round(price, 2)`). Downstream consumers don't need to round again.
- `remove(ticker)` doesn't bump `version` (silent removal). If we ever needed SSE clients to see explicit "ticker removed" events, we'd add a new method or a sentinel `PriceUpdate(price=NaN)`.

## Factory: `create_market_data_source`

```python
def create_market_data_source(price_cache: PriceCache) -> MarketDataSource:
    api_key = os.environ.get("MASSIVE_API_KEY", "").strip()
    if api_key:
        return MassiveDataSource(api_key=api_key, price_cache=price_cache)
    else:
        return SimulatorDataSource(price_cache=price_cache)
```

The `.strip()` matters — environments occasionally end up with `MASSIVE_API_KEY="  "` from misformatted `.env` files. Treating whitespace-only as unset routes users to the simulator instead of giving them a confusing `401` from Massive.

Returns an **unstarted** source. The caller must `await source.start(initial_tickers)` to kick off the background task.

## SSE Streaming: `create_stream_router`

```python
router = create_stream_router(price_cache)
# Endpoint: GET /api/stream/prices, media_type text/event-stream
```

Inside `stream.py`:

```python
async def _generate_events(price_cache, request, interval=0.5):
    yield "retry: 1000\n\n"                  # browser auto-reconnect hint
    last_version = -1
    try:
        while True:
            if await request.is_disconnected():
                break
            current = price_cache.version
            if current != last_version:
                last_version = current
                prices = price_cache.get_all()
                if prices:
                    data = {t: u.to_dict() for t, u in prices.items()}
                    yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        ...
```

Wire format on the client (`EventSource`):

```js
const es = new EventSource("/api/stream/prices");
es.onmessage = (event) => {
  const prices = JSON.parse(event.data);
  for (const [ticker, update] of Object.entries(prices)) {
    // update = { ticker, price, previous_price, timestamp, change, change_percent, direction }
    flash(ticker, update.direction);
  }
};
```

### Response headers

- `Cache-Control: no-cache` — proxies must not cache
- `Connection: keep-alive` — long-lived
- `X-Accel-Buffering: no` — disables nginx response buffering (would otherwise hold events for several seconds before forwarding)

### Push-on-change, not push-on-tick

Even though `_generate_events` wakes every 500 ms, **it only yields when `cache.version` has advanced**. With the Massive free tier (15 s polls), the client receives one event per 15 s, not 30 redundant frames in the gap. The cache itself only bumps `version` when the rounded price differs from the previous, so a Massive poll that returns an identical `last_trade.price` does not cause a redundant SSE frame either.

### Keepalive comments

After `keepalive_seconds` (default 15 s) of idle — no version change — `_generate_events` emits a single `: keepalive\n\n` SSE comment line. SSE comments are silently ignored by `EventSource` clients but keep the connection alive through intermediaries (nginx, App Runner, Cloudflare) that close idle TCP connections. The keepalive cadence is independent of the wake interval.

## Historical-Price Endpoint Backing

PLAN.md §8 introduces `GET /api/prices/history/{ticker}?range=1h|6h|24h|7d`. This is **not** served from `PriceCache` (which only holds the latest tick per ticker) — it's served from the `price_ticks` SQLite table written to by a separate background task (PLAN.md §7).

The market layer's contribution to that flow is:

1. Provide a stable read interface (`PriceCache.get(ticker).price`) for the tick-history writer to sample every ~5 seconds per ticker.
2. Optionally, on **first connect** for a ticker not yet in the table, backfill from the Massive aggregates endpoint (`MASSIVE_API.md` §3) so the chart isn't blank for new symbols. If Massive isn't configured, the chart simply shows the live tail from SSE.

Sketch of the planned `prices/history` handler:

```python
@router.get("/api/prices/history/{ticker}")
async def price_history(ticker: str, range: str = "1h"):
    since = {"1h": 3600, "6h": 21600, "24h": 86400, "7d": 604800}[range]
    rows = await fetch_ticks(ticker, since)            # from SQLite price_ticks
    return [{"t": r.recorded_at, "p": r.price} for r in rows]
```

The frontend pre-loads this for the selected ticker, then appends live ticks from SSE — the cache and the table converge on the same data within a few seconds.

## Error Handling & Retry Contract

Different layers handle different failures. The contract:

| Layer | Failure mode | Behavior |
|---|---|---|
| `MarketDataSource` background task | Network / API error in one cycle | Log, do **not** re-raise. Loop continues on next interval. Cache retains last known prices. |
| `MarketDataSource` background task | Malformed single-ticker response | Log a warning for that ticker, continue processing the rest of the batch. |
| `MassiveDataSource._client` (Massive SDK) | 5xx, connection errors | SDK does **3 internal retries with exponential backoff** before raising. Do not wrap with a second retry layer. |
| `PriceCache.update` | Unknown ticker | No-op rejection logic — any string is a valid ticker key. Validation happens upstream (watchlist endpoint). |
| SSE generator | Client disconnects | `request.is_disconnected()` checked each loop; breaks cleanly. |
| SSE generator | `asyncio.CancelledError` (app shutdown) | Caught, logged, generator exits. |
| Lifespan `stop()` | Task already cancelled | Safe — caught `CancelledError` swallowed. |

### What's deliberately not handled

- **Persistent 401/403.** If the API key is bad or unentitled, the poller logs one error per interval forever. There's no surface area on the frontend connection-status dot today; add when needed.
- **Cache staleness gating.** Trade execution reads the cache without checking the age of the price. For a fake-money demo this is fine; for real money, add `if now - update.timestamp > threshold: reject_trade()`.
- **WebSocket fallback.** No automatic upgrade from REST to WebSocket on Developer-tier keys — would require a new `MassiveWebSocketDataSource` and a smarter factory.

## Adding a Third Data Source

The intended extension path:

```python
class MyDataSource(MarketDataSource):
    def __init__(self, price_cache: PriceCache, ...): ...
    async def start(self, tickers): ...
    async def stop(self): ...
    async def add_ticker(self, ticker): ...
    async def remove_ticker(self, ticker): ...
    def get_tickers(self): ...
```

Then update `factory.py` to route to it based on whatever env var or config key makes sense (e.g., `DATA_SOURCE=mock_replay` for replaying a recorded session in tests).

Concrete near-term candidates:

- `MockReplayDataSource` — read price ticks from a CSV or JSONL, play them back at configurable speed. Useful for deterministic E2E tests and demos that need a known price path.
- `MassiveWebSocketDataSource` — drop-in upgrade for Developer-plan users. Same `PriceCache`, same `MarketDataSource` contract; only the producer changes.

## Testing

Coverage matrix (mirrors `backend/tests/market/`):

| Module | Test file | What it pins |
|---|---|---|
| `models.py` | `test_models.py` | Property correctness (direction, change_percent, to_dict round-trip) |
| `cache.py` | `test_cache.py` | Threadsafe `update` (multi-thread hammer), version bumps only on rounded-price change, `timestamp=0.0` preserved, `get_all` returns a copy |
| `simulator.py` | `test_simulator.py`, `test_simulator_source.py` | GBM math, Cholesky rebuild, lifecycle, cache seeding on start, unknown-ticker price range matches PLAN.md ($20–$400) |
| `massive_client.py` | `test_massive.py` | Snapshot parsing, malformed-response skip, async loop survives exceptions, ticker case-normalization in `start`/`add`/`remove`, poll loop fires repeatedly, `_poll_once` snapshots `_tickers` before the worker thread call |
| `factory.py` | `test_factory.py` | Routes on `MASSIVE_API_KEY`, treats whitespace as empty |
| `stream.py` | `test_stream.py` | Each `create_stream_router` call returns an independent router (no module-level singleton), push-on-change behavior, keepalive comment after idle, disconnect cleanup, empty-cache short-circuit |
| ABC contract | `test_interface_conformance.py` | Both implementations honor the `MarketDataSource` interface (lifecycle, `get_tickers`, async signatures) |

## Related Documents

- `MARKET_SIMULATOR.md` — internals of the GBM simulator behind `SimulatorDataSource`
- `MASSIVE_API.md` — the Massive REST/WebSocket surface that `MassiveDataSource` polls (and the future-WebSocket alternative)
- `PLAN.md` §6, §7, §8 — product-level requirements for streaming, cache behavior, historical endpoints
