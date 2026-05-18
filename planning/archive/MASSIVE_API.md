# Massive API Reference

Reference documentation for the Massive (formerly Polygon.io) REST and WebSocket APIs as used in FinAlly. Verified against `massive.com/docs` (May 2026) and the shipped client at `backend/app/market/massive_client.py`.

> **Naming:** Polygon.io rebranded to **Massive** in early 2026. The PyPI package is `massive` (current as of May 2026: v2.7.0, published by massive.com), and `https://polygon.io` 301-redirects to `https://massive.com`. Legacy URLs and the old `polygon-api-client` package still work.

## Overview

| Property | Value |
|---|---|
| REST base URL | `https://api.massive.com` (legacy `https://api.polygon.io` still resolves) |
| WebSocket base URL | `wss://socket.massive.com/{stocks,options,forex,crypto}` |
| Python package | `massive` (install via `uv add massive` / `pip install -U massive`) |
| Min Python version | 3.9+ |
| Auth | API key via `MASSIVE_API_KEY` env var or `RESTClient(api_key=...)` |
| Auth header | `Authorization: Bearer <API_KEY>` (client handles automatically) |

FinAlly currently uses **REST polling of the snapshot endpoint**. WebSocket streaming and the historical aggregates endpoint are documented here so future work can adopt them without re-researching.

## Rate Limits

| Tier | Documented limit | FinAlly poll interval |
|------|------------------|----------------------|
| Free / Basic | 5 requests/min (historical Polygon limit, still assumed by FinAlly's default) | 15 s |
| Starter | Unlimited (advisory: stay under ~100 req/s) | 5 s |
| Developer / Advanced | Unlimited | 2 s |

The shipped `MassiveDataSource` defaults to `poll_interval=15.0` seconds — safe on the free tier and gives ~4 polls/min, well inside the limit. Override via constructor if you have a paid plan.

> ⚠️ **Tier limits change.** Massive periodically revises pricing-page numbers. Confirm against `https://massive.com/pricing` before relying on the free-tier limit for production scheduling.

## Client Initialization

```python
from massive import RESTClient

# Reads MASSIVE_API_KEY from environment automatically
client = RESTClient()

# Or pass explicitly
client = RESTClient(api_key="your_key_here")
```

`RESTClient` is **synchronous**. FinAlly wraps calls in `asyncio.to_thread(...)` so they don't block the event loop (see `massive_client.py:97`).

---

## REST Endpoints Used in FinAlly

### 1. Full Market Snapshot — Multiple Tickers (primary)

Returns current prices for many tickers in **a single API call** — the only endpoint we poll in production. Critical for staying within the free-tier rate limit.

**REST**: `GET /v2/snapshot/locale/us/markets/stocks/tickers?tickers=AAPL,GOOGL,MSFT`

**Query parameters**:

| Name | Type | Notes |
|------|------|-------|
| `tickers` | comma-separated string | Case-insensitive. Empty string = all tickers. |
| `include_otc` | bool | Include OTC securities. Default `false`. |

**Python client**:

```python
from massive import RESTClient
from massive.rest.models import SnapshotMarketType

client = RESTClient()
snapshots = client.get_snapshot_all(
    market_type=SnapshotMarketType.STOCKS,
    tickers=["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"],
)

for snap in snapshots:
    print(f"{snap.ticker}: ${snap.last_trade.price}")
    print(f"  Day change: {snap.day.change_percent}%")
    print(f"  Day OHLC: O={snap.day.open} H={snap.day.high} L={snap.day.low} C={snap.day.close}")
    print(f"  Volume: {snap.day.volume}")
```

**Raw JSON wire format** (one entry of the `tickers[]` array). The Python client unpacks these short keys into snake_case attributes — both layers are documented here because the project occasionally needs to debug raw responses:

```json
{
  "ticker": "AAPL",
  "todaysChangePerc": -3.50,
  "todaysChange": -4.54,
  "updated": 1675190399500,
  "day":       { "o": 129.61, "h": 130.15, "l": 125.07, "c": 125.07, "v": 111237700, "vw": 127.35 },
  "prevDay":   { "o": 127.0,  "h": 130.0,  "l": 126.5,  "c": 129.61, "v": 100000000 },
  "lastTrade": { "p": 125.07, "s": 100, "x": "XNYS", "t": 1675190399000, "i": "abc" },
  "lastQuote": { "P": 125.08, "p": 125.06, "S": 1000, "s": 500, "t": 1675190399500 }
}
```

| What we want | Raw JSON path | Python client attribute |
|---|---|---|
| Last trade price | `lastTrade.p` | `snap.last_trade.price` |
| Last trade timestamp (ms) | `lastTrade.t` | `snap.last_trade.timestamp` |
| Previous close | `prevDay.c` | `snap.day.previous_close` (note: maps via the client's `day` view) |
| Day change % | `todaysChangePerc` | `snap.day.change_percent` |
| Day OHLCV | `day.o/h/l/c/v` | `snap.day.open/high/low/close/volume` |

> The mapping from `prevDay.c` to `snap.day.previous_close` is a Python-client convenience — the raw JSON has no `day.previous_close` field. If you ever drop down to raw HTTP, look at `prevDay.c` instead.

**Timestamps**: all `t` / `updated` fields are **Unix milliseconds**. FinAlly converts to seconds in `massive_client.py:103`: `timestamp = snap.last_trade.timestamp / 1000.0`.

### 2. Single Ticker Snapshot

Heavier payload for one ticker (e.g., when the user clicks a ticker for the detail view). Currently unused by the frontend but available for the planned `/api/prices/history/{ticker}` route as a sanity-check fallback.

```python
snap = client.get_snapshot_ticker(
    market_type=SnapshotMarketType.STOCKS,
    ticker="AAPL",
)
print(f"Price: ${snap.last_trade.price}")
print(f"Bid/Ask: ${snap.last_quote.bid_price} / ${snap.last_quote.ask_price}")
```

### 3. Aggregates (Historical OHLCV Bars) — for the main chart

This is what `GET /api/prices/history/{ticker}?range=1h|6h|24h|7d` will be built on top of when the historical chart is wired up. The shipped backend writes to its own `price_ticks` table for tick history (per PLAN.md §7), but for production-grade history we'll pull official bars from this endpoint and merge.

**REST**: `GET /v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}`

| Path part | Allowed values | Notes |
|---|---|---|
| `multiplier` | positive integer | e.g. `1`, `5`, `15` |
| `timespan` | `second`, `minute`, `hour`, `day`, `week`, `month`, `quarter`, `year` | `second` typically requires a paid plan |
| `from`, `to` | `YYYY-MM-DD` or Unix-ms | Inclusive |

**Limits**: default page size **5,000 bars**, max **50,000** per request. Pagination via `next_url` in the response; the Python client's `list_aggs` follows `next_url` transparently.

**Python client**:

```python
from datetime import datetime, timedelta, timezone

end = datetime.now(timezone.utc)
start = end - timedelta(days=7)

aggs = list(client.list_aggs(
    ticker="AAPL",
    multiplier=5,             # 5-minute bars for a 7-day range
    timespan="minute",
    from_=int(start.timestamp() * 1000),
    to=int(end.timestamp() * 1000),
    limit=50000,
))

for a in aggs:
    print(f"t={a.timestamp}  O={a.open} H={a.high} L={a.low} C={a.close} V={a.volume}")
```

**Recommended `(multiplier, timespan)` for FinAlly chart ranges**:

| `range=` param | `multiplier` | `timespan` | Approx bars |
|---|---|---|---|
| `1h`  | 1 | `minute` | ~60   |
| `6h`  | 1 | `minute` | ~360  |
| `24h` | 5 | `minute` | ~288  |
| `7d`  | 15 | `minute` | ~1500 |

These all fit comfortably under the 5,000-bar default page size, so no pagination needed.

**Free / Basic tier restrictions**: Basic plan is **end-of-day only** with **2 years of history**. Real-time intraday data and full history back to 2003-09-10 require Advanced or Business. For demo use (the default) this means: on a free/Basic key, the `/api/prices/history` endpoint will return rows that are already 1+ day stale. The simulator therefore remains the better default for live charts.

**Raw response** (one bar):

```json
{ "o": 130.0, "h": 132.5, "l": 129.8, "c": 131.2, "v": 50000000, "t": 1672531200000, "vw": 130.9, "n": 12345 }
```

| Wire key | Meaning |
|---|---|
| `o`, `h`, `l`, `c` | OHLC |
| `v` | Volume (shares) |
| `vw` | Volume-weighted avg price |
| `n` | Number of trades in the bar |
| `t` | Bar start timestamp (Unix ms) |

### 4. Previous Close (single-day)

Useful for seeding starting prices when bootstrapping a brand-new watchlist ticker without polling the full snapshot endpoint.

```python
results = client.get_previous_close_agg(ticker="AAPL")
for agg in results:
    print(f"Previous close: ${agg.close}")
```

**REST**: `GET /v2/aggs/ticker/{ticker}/prev`

### 5. Last Trade / Last Quote (individual)

Rarely needed when the snapshot endpoint gives both for free, but available as point lookups:

```python
trade = client.get_last_trade(ticker="AAPL")
print(f"Last trade: ${trade.price} x {trade.size}")

quote = client.get_last_quote(ticker="AAPL")
print(f"Bid: ${quote.bid} x {quote.bid_size}")
print(f"Ask: ${quote.ask} x {quote.ask_size}")
```

---

## WebSocket Streaming (alternative to REST polling)

REST polling is what FinAlly uses today; WebSocket streaming would be the upgrade path on Developer/Advanced plans. Documented here for future work — **do not adopt this on the free tier; it is not entitled.**

### Endpoint

| Feed | URL |
|---|---|
| Real-time | `wss://socket.massive.com/stocks` |
| 15-min delayed (some tiers) | `wss://delayed.massive.com/stocks` |

### Connection flow

```
1. Open ws to wss://socket.massive.com/stocks
2. Server  → { "ev": "status", "status": "connected" }
3. Client → { "action": "auth",       "params": "<API_KEY>" }
4. Server  → { "ev": "status", "status": "auth_success" }
5. Client → { "action": "subscribe",  "params": "T.AAPL,T.MSFT" }
6. Server  → { "ev": "status", "status": "success", "message": "subscribed to: T.AAPL,T.MSFT" }
7. Server  → stream of trade events (see channel table)
```

### Channels

| Prefix | Payload | Frequency | FinAlly use case |
|---|---|---|---|
| `T.<sym>` | Tick trades (price, size, exchange, timestamp) | Per trade (hundreds per sec on liquid names) | Direct replacement for REST snapshot polling |
| `Q.<sym>` | NBBO quotes (bid/ask, sizes) | Per quote (very high volume) | Not needed |
| `A.<sym>` | Per-second OHLCV aggregate | 1/sec per ticker | Best fit for FinAlly — matches the 500 ms SSE cadence without the firehose of `T` |
| `AM.<sym>` | Per-minute OHLCV aggregate | 1/min per ticker | Backing for `/api/prices/history` realtime tail |
| `T.*`, `A.*` | All-tickers wildcard | Massive | Requires Business tier |

### Tier access (verified May 2026)

- `T.*` (trades): Stocks **Developer** or **Advanced** (individual), or any **Business** plan
- Real-time trade data: requires **Advanced** (individual) or **Business + Expansion**
- Other plans qualified for `T` receive **15-minute delayed** trades on the `delayed.massive.com` host
- Stocks **Basic** and **Starter** plans: REST snapshots only, no WebSocket access

### Trade event payload

```json
{ "ev": "T", "sym": "AAPL", "p": 192.34, "s": 100, "x": 11, "i": "abc", "z": 3, "t": 1675190399123, "pt": 1675190399118 }
```

| Field | Meaning |
|---|---|
| `ev` | Event type (always `"T"` here) |
| `sym` | Ticker symbol |
| `p` | Trade price |
| `s` | Trade size (shares) |
| `x` | Exchange ID |
| `i` | Trade ID |
| `z` | Tape (1=A, 2=B, 3=C) |
| `t` | SIP timestamp (Unix ms) |
| `pt` | Participant timestamp (Unix ms) |

### Python client (sketch)

```python
from massive import WebSocketClient

ws = WebSocketClient(
    api_key="...",
    market="stocks",
    subscriptions=["T.AAPL", "T.MSFT"],
)

def on_message(msgs):
    for m in msgs:
        if m.event_type == "T":
            price_cache.update(ticker=m.symbol, price=m.price, timestamp=m.timestamp / 1000.0)

ws.run(on_message)        # blocking
# or: AsyncWebSocketClient(...).connect()   # asyncio variant
```

If FinAlly ever adopts WebSocket, the right shape is a third `MarketDataSource` implementation (`MassiveWebSocketDataSource`) that writes into the same `PriceCache` — no other code needs to change.

---

## Error Handling & Retry Policy

The Massive `RESTClient` raises subclasses of `massive.exceptions.MassiveError` (formerly `polygon.exceptions.AuthError` etc.) for HTTP failures.

| HTTP | Meaning | FinAlly behavior (shipped) |
|---|---|---|
| `401` | Invalid or missing API key | Log `error`, skip the cycle, retry on next interval. **Will keep failing** until the key is fixed. |
| `403` | Endpoint not included in the current plan | Same as `401` — log and skip. |
| `429` | Rate limit exceeded | Same as `401` — log and skip. Next poll happens after `poll_interval`, which is what naturally backs us off. |
| `5xx` | Massive-side server error | Same as `401` — log and skip. RESTClient does its own internal retries first (see below). |
| Network errors (`ConnectionError`, `Timeout`) | Transient | Same — log and skip. |

The shipped `_poll_once` method wraps the entire fetch in a bare `try/except Exception` (see `massive_client.py:118`) and **does not re-raise**. This was an intentional decision: the poller loop must survive any single-request failure — a stale cache is better than a dead one.

### Built-in client retries

`RESTClient` ships with **3 automatic retries** with exponential backoff on 5xx and connection errors (configurable via `RESTClient(..., retries=N)`). This means a transient blip rarely propagates up to our `try/except` — by the time the exception fires, the client has already tried 4 times. **Do not add a second retry layer on top.** Doing so multiplies the wait time and burns rate-limit budget on the free tier.

### What's missing (intentional gaps)

- No `Retry-After` header parsing on 429 — Massive historically does not send this header, so honoring our own `poll_interval` is the safest backoff. If Massive starts sending one, the right fix is to read it inside the `except` clause and replace the next `asyncio.sleep` accordingly.
- No persistent-failure circuit breaker — if the key is bad, the poller will log "Massive poll failed" once per 15 s forever. Acceptable for a single-user demo; in a hosted multi-tenant version we'd want to surface this in the UI (connection-status dot turns red).
- No metrics emission — the loop logs at `DEBUG` (success) and `ERROR` (failure) but doesn't expose poll-success-rate as a metric. Add later if needed.

### Failure cascade & cache staleness

When polls fail, the `PriceCache` **retains its last known prices**. Two downstream consequences:

1. **SSE clients stop receiving updates.** The SSE generator pushes on version-counter change, and the version only advances on cache writes. If the poller is silent, SSE goes silent — the client's connection-status dot turning yellow/red is the only signal. The keepalive comment fires every 15 s to prevent intermediaries from closing the SSE connection.
2. **Trades and portfolio valuations use stale prices.** This is bad in real money but acceptable in a $10K-of-fake-money simulator. If we ever ship this for real, add a "data freshness" check that refuses trades when `now - cache.get(ticker).timestamp > N` seconds.

---

## How FinAlly Currently Uses the API

The shipped poller is in `backend/app/market/massive_client.py`:

```python
async def _poll_once(self) -> None:
    if not self._tickers or not self._client:
        return
    try:
        # RESTClient is synchronous — run in a thread so we don't block the event loop
        snapshots = await asyncio.to_thread(self._fetch_snapshots)
        for snap in snapshots:
            try:
                price = snap.last_trade.price
                timestamp = snap.last_trade.timestamp / 1000.0  # ms → s
                self._cache.update(ticker=snap.ticker, price=price, timestamp=timestamp)
            except (AttributeError, TypeError) as e:
                logger.warning("Skipping snapshot for %s: %s", getattr(snap, "ticker", "???"), e)
    except Exception as e:
        logger.error("Massive poll failed: %s", e)
        # Don't re-raise — the loop will retry next interval.
        # Common failures: 401 (bad key), 429 (rate limit), network errors.

def _fetch_snapshots(self) -> list:
    return self._client.get_snapshot_all(
        market_type=SnapshotMarketType.STOCKS,
        tickers=self._tickers,
    )
```

Key details:

1. **One call per cycle.** `get_snapshot_all` returns every watched ticker in one HTTP round-trip — this is the only way to stay under 5 req/min on the free tier with a 10-ticker watchlist.
2. **`asyncio.to_thread` wrapping.** The Massive SDK is sync; the FastAPI app is async. Running the call in a thread keeps the event loop responsive.
3. **Per-snapshot try/except.** If one ticker's snapshot is malformed (no `last_trade`, e.g., halted stock), we log and continue rather than discard the whole batch.
4. **`add_ticker` is lazy.** It just appends to `self._tickers`; the next `_poll_once` picks up the new symbol. No immediate single-ticker fetch — keeps the request rate predictable.

---

## Related Documents

- `MARKET_INTERFACE.md` — the `MarketDataSource` ABC that `MassiveDataSource` implements, plus the `PriceCache` it writes to
- `MARKET_SIMULATOR.md` — the GBM-based fallback used when `MASSIVE_API_KEY` is not set
- `PLAN.md` §6 — product-level requirements for the market-data subsystem
