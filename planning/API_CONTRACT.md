# API_CONTRACT.md — FinAlly HTTP & SSE wire format (Phase 1 contract)

This document is the canonical wire-format contract for every FastAPI endpoint and the SSE stream that FinAlly exposes. It is owned by the **Backend API Engineer** and consumed read-only by the **Frontend Engineer** (for fetch shapes and EventSource parsing) and the **LLM Engineer** (so the chat layer surfaces results consistently with the rest of the API).

Sources of truth: `planning/PLAN.md` §6 (market data interface), §7 (schema), §8 (endpoints), §9 (chat response shape), §10 (frontend needs); `planning/SCHEMA.md` (canonical table shapes and the `actions` JSON); the existing `backend/app/market/` subsystem (frozen). Where these are silent, this file picks the conservative interpretation and flags it inline.

---

## 1. Conventions

### 1.1 Base URL and content types

- **Base URL.** All endpoints are same-origin under `/api/*`. The frontend is served from the same FastAPI process as a static export, so there is no CORS configuration and no separate API hostname.
- **Request bodies.** JSON (`Content-Type: application/json`). Endpoints with no body (`GET`, `DELETE`) take no request payload.
- **Response bodies.** JSON (`Content-Type: application/json`), with one exception: the SSE stream uses `text/event-stream` and is documented in §2.1.
- **Encoding.** UTF-8 throughout.
- **Timestamps.** Unless noted otherwise, timestamps in responses are ISO 8601 UTC strings (`"2026-05-20T10:15:30.123456+00:00"`), matching what `SCHEMA.md` stores. The single exception is the SSE `ts` field, which is a Unix float (seconds), because that is what `PriceUpdate.timestamp` already produces and the market subsystem is frozen.
- **Casing.** All JSON keys are `snake_case` to match the Pydantic / SQLite columns. Tickers are uppercased server-side; clients may send any case.

### 1.2 Error envelope

Every non-2xx response body is the following envelope (no nesting under `detail`, no FastAPI default validation shape — the API layer wraps Pydantic's `RequestValidationError` and its own exceptions into this single format):

```json
{
  "error": "<machine_code>",
  "error_message": "<human readable sentence>"
}
```

- `error` (string, required) is one of the codes in §1.4.
- `error_message` (string, required) is a one-sentence human-readable explanation, safe to render directly in the UI.

The same field names (`error`, `error_message`) appear inside the chat `actions[]` array on failed entries (see §5 and SCHEMA.md §3) so the frontend can use one renderer for both shapes.

### 1.3 HTTP status code mapping

| Status | Meaning in FinAlly | Used by |
|---|---|---|
| 200 | OK — request succeeded, response body is a resource representation | `GET /api/portfolio`, `GET /api/portfolio/history`, `GET /api/watchlist`, `GET /api/prices/history/{ticker}`, `GET /api/health`, `POST /api/chat` |
| 201 | Created — a new resource was created and returned in the body | `POST /api/watchlist`, `POST /api/portfolio/trade` |
| 204 | No Content — request succeeded, no body returned | `DELETE /api/watchlist/{ticker}` |
| 400 | Bad Request — business-rule rejection (e.g. trade fails due to insufficient cash/shares). Body is the error envelope. | `POST /api/portfolio/trade` |
| 404 | Not Found — resource does not exist on this server. Body is the error envelope. | `DELETE /api/watchlist/{ticker}`, `GET /api/prices/history/{ticker}`, `POST /api/portfolio/trade` (unknown ticker) |
| 409 | Conflict — request collides with current resource state. Body is the error envelope. | `POST /api/watchlist` (ticker already present) |
| 422 | Unprocessable Entity — input fails structural / regex validation (e.g. malformed ticker, negative quantity). Body is the error envelope. | `POST /api/watchlist`, `POST /api/portfolio/trade`, `POST /api/chat`, `GET /api/prices/history/{ticker}` (bad `range`) |
| 500 | Internal Server Error — unhandled exception. Body is the error envelope with `error: "internal_error"`. | Any endpoint as a last resort |

`POST /api/chat` is **always 200** as long as the request body parses; per-trade and per-watchlist failures induced by the LLM are reported inside the `actions[]` array, not as HTTP errors (see §5).

The SSE endpoint (`GET /api/stream/prices`) is **always 200** while the connection is open; transport-level failures (client disconnect, server shutdown) close the stream without an HTTP error body.

### 1.4 Error code enum

The full set of `error` machine codes that may appear in any error envelope or in a failed `actions[]` entry:

| Code | Meaning | HTTP status when surfaced as an envelope |
|---|---|---|
| `insufficient_cash` | Buy would overdraw the cash balance. | 400 |
| `insufficient_shares` | Sell exceeds current position quantity. | 400 |
| `unknown_ticker` | Ticker not recognized by the active market data source / not in the watchlist for routes that require it. | 404 |
| `invalid_ticker` | Ticker symbol fails the structural regex `^[A-Z]{1,5}$` (after uppercasing). | 422 |
| `validation_error` | Request body fails Pydantic / structural validation (negative quantity, missing field, bad `side`, bad `range`, etc.). | 422 |
| `ticker_already_in_watchlist` | `POST /api/watchlist` with a ticker already present. | 409 |
| `internal_error` | Unhandled server-side exception. | 500 |

Inside `actions[]` (chat responses), only `insufficient_cash`, `insufficient_shares`, and `unknown_ticker` appear in `error` (per PLAN.md §9). `validation_error` cannot occur there because the LLM Engineer validates the LLM-generated trade payload before invoking the trade path; structurally malformed LLM output is collapsed into a human-readable `error_message` on a synthetic action entry.

---

## 2. Market endpoints

### 2.1 `GET /api/stream/prices` — Live price stream (SSE)

Server-Sent Events stream of live price updates. The client connects with the native `EventSource` API and lets the browser reconnect automatically on transient failures.

- **Method / path.** `GET /api/stream/prices`
- **Query / body.** None.
- **Response status.** 200 (open). The stream stays open until the client disconnects or the server shuts down.
- **Response media type.** `text/event-stream; charset=utf-8`.
- **Response headers.** `Cache-Control: no-cache`, `Connection: keep-alive`, `X-Accel-Buffering: no` (disables nginx buffering when proxied).

#### Event shape

The first frame on every connection is an SSE retry hint:

```
retry: 1000

```

After that, the server emits one of two frame kinds:

**1. Price-update frame** — emitted only when the `PriceCache.version` counter has advanced since the previous emit (push-on-change). The `data:` payload is a JSON **object keyed by ticker symbol**; each value is the full per-ticker `PriceUpdate`:

```
data: {"AAPL": {"ticker": "AAPL", "price": 192.34, "previous_price": 191.88, "timestamp": 1747741234.812, "change": 0.46, "change_percent": 0.2397, "direction": "up"}, "GOOGL": {"ticker": "GOOGL", "price": 175.20, "previous_price": 175.20, "timestamp": 1747741234.811, "change": 0.0, "change_percent": 0.0, "direction": "flat"}}

```

Per-ticker fields (all required, none nullable):

| Field | Type | Notes |
|---|---|---|
| `ticker` | string | Uppercase symbol, matches the outer key. |
| `price` | number | Current price, rounded to 2 decimal places. |
| `previous_price` | number | Previous cached price; equals `price` on the very first observation for a ticker. |
| `timestamp` | number | Unix time in seconds (float), wall-clock at the source's tick. |
| `change` | number | `price - previous_price`, rounded to 4 decimal places. |
| `change_percent` | number | `(price - previous_price) / previous_price * 100`, rounded to 4 dp; `0.0` if `previous_price == 0`. |
| `direction` | `"up" \| "down" \| "flat"` | Sign of `change`. `"flat"` on the first observation. |

> Implementation note for downstream agents: the orchestrator prompt described a per-event `{ticker, price, prev_price, ts, direction}` shape. The actual shipping market subsystem emits a full ticker map per frame with the field names listed above (the market subsystem is frozen). The Frontend Engineer should subscribe and iterate the keys of the parsed JSON; the LLM Engineer does not consume this stream directly.

**2. Keepalive comment** — emitted after `~15s` of cache idleness so proxies (nginx, App Runner, Cloudflare) don't drop the connection. SSE comments are ignored by `EventSource`:

```
: keepalive

```

#### Behavior guarantees

- **Push-on-change.** A frame is only emitted when `PriceCache.version` has advanced since the last emit. The version counter only increments when a ticker's rounded price actually changes (or when a ticker is first seen). Identical successive prices do not produce frames; this is what keeps client-side flash animations from firing on no-op updates.
- **Reconnection.** The leading `retry: 1000` hints `EventSource` to reconnect after 1s on a dropped connection. No application-layer auth, cookies, or query params are required to resume.
- **Disconnection.** When `Request.is_disconnected()` returns true, the generator exits cleanly. Server shutdown closes all open streams.

### 2.2 `GET /api/prices/history/{ticker}` — Historical price ticks

Returns persisted price history for the main chart, served from the `price_ticks` table (SCHEMA.md §1.6). The frontend calls this on ticker selection to populate the main chart, then appends live ticks from §2.1.

- **Method / path.** `GET /api/prices/history/{ticker}`
- **Path params.** `ticker` — alphabetic 1-5 chars, uppercased server-side. Must match `^[A-Z]{1,5}$` after uppercasing.
- **Query params.**

  | Name | Type | Default | Allowed values |
  |---|---|---|---|
  | `range` | string | `"1h"` | `"1h"`, `"6h"`, `"24h"`, `"7d"` |

- **Response status.** 200 OK on success; 404 with `unknown_ticker` if the ticker is structurally valid but not present in any watchlist / not known to the active market source and therefore has no history bucket; 422 with `invalid_ticker` if the ticker fails the regex; 422 with `validation_error` if `range` is not one of the allowed values.
- **Response body.**

  ```json
  {
    "ticker": "AAPL",
    "range": "1h",
    "points": [
      {"ts": "2026-05-20T10:15:30.123456+00:00", "price": 192.34},
      {"ts": "2026-05-20T10:15:35.124001+00:00", "price": 192.40}
    ]
  }
  ```

  | Field | Type | Notes |
  |---|---|---|
  | `ticker` | string | Echoed uppercase ticker. |
  | `range` | string | Echoed `range` value. |
  | `points` | array of objects | May be empty (e.g., immediately after a fresh ticker is added — the tick persister has not yet written a row). |
  | `points[].ts` | string | ISO 8601 UTC, matches `price_ticks.recorded_at`. |
  | `points[].price` | number | Price at that tick. |

  Points are returned in **chronological order** (oldest first), filtered to the window `[now − range, now]`. No downsampling in v1.

---

## 3. Watchlist endpoints

### 3.1 `GET /api/watchlist` — List watched tickers with live pricing

Returns the user's current watchlist, each row hydrated with the latest cached price and the session change percent computed server-side.

- **Method / path.** `GET /api/watchlist`
- **Query / body.** None.
- **Response status.** 200 OK.
- **Response body.**

  ```json
  {
    "items": [
      {
        "ticker": "AAPL",
        "price": 192.34,
        "session_anchor_price": 191.50,
        "change_pct": 0.4386
      },
      {
        "ticker": "PYPL",
        "price": null,
        "session_anchor_price": null,
        "change_pct": null
      }
    ]
  }
  ```

  Field shapes (per item):

  | Field | Type | Nullable | Notes |
  |---|---|---|---|
  | `ticker` | string | no | Uppercase. |
  | `price` | number | **yes** | Latest cached price. `null` when the row was just added and the market source has not produced a tick yet. |
  | `session_anchor_price` | number | **yes** | The first price the backend observed for this ticker since the current process started. Resets on backend restart — there is no concept of a real market open in the simulator. `null` when no tick has been observed yet. Read from `PriceCache.get_session_anchor(ticker)`. |
  | `change_pct` | number | **yes** | Signed percent change: `(price − session_anchor_price) / session_anchor_price * 100`, rounded to 4 decimal places. Computed server-side so all clients agree. `null` when either `price` or `session_anchor_price` is `null`. Returns `0.0` (not `null`) in the degenerate case of `session_anchor_price == 0`. |

  Items are returned in `watchlist.added_at` ascending order so the seed watchlist is rendered in the order PLAN.md §7 lists.

### 3.2 `POST /api/watchlist` — Add a ticker

Adds a ticker to the user's watchlist and asks the active market data source to begin producing ticks for it. The simulator auto-generates a seed price and GBM parameters for unknown tickers; the Massive client accepts any valid Polygon symbol (PLAN.md §6).

- **Method / path.** `POST /api/watchlist`
- **Request body.**

  ```json
  {"ticker": "PYPL"}
  ```

  | Field | Type | Required | Notes |
  |---|---|---|---|
  | `ticker` | string | yes | Validated against `^[A-Za-z]{1,5}$`, then uppercased server-side before storage. |

- **Response status.**
  - 201 Created on success.
  - 409 Conflict with `ticker_already_in_watchlist` if `(user_id, ticker)` already exists.
  - 422 Unprocessable Entity with `invalid_ticker` if the regex fails, or `validation_error` if the body is structurally invalid (e.g. missing `ticker`).

- **Response body (201).** The shape matches a single item in `GET /api/watchlist`, with `price` / `session_anchor_price` / `change_pct` likely `null` because the source has not produced a tick yet:

  ```json
  {
    "ticker": "PYPL",
    "price": null,
    "session_anchor_price": null,
    "change_pct": null
  }
  ```

### 3.3 `DELETE /api/watchlist/{ticker}` — Remove a ticker

Removes the ticker from the watchlist and asks the market source to stop tracking it (which also clears its cache entry and session anchor — see `PriceCache.remove()`).

- **Method / path.** `DELETE /api/watchlist/{ticker}`
- **Path params.** `ticker` — same regex / uppercasing as §3.2.
- **Response status.**
  - 204 No Content on success.
  - 404 Not Found with `unknown_ticker` if the row does not exist.
  - 422 Unprocessable Entity with `invalid_ticker` if the regex fails.

- **Response body.** None on 204; error envelope on 404 / 422.

---

## 4. Portfolio endpoints

### 4.1 `GET /api/portfolio` — Current portfolio snapshot

Returns the user's current cash balance, all positions hydrated with live pricing and P&L, and the rolled-up total value and unrealized P&L.

- **Method / path.** `GET /api/portfolio`
- **Query / body.** None.
- **Response status.** 200 OK.
- **Response body.**

  ```json
  {
    "cash_balance": 8076.60,
    "total_value": 10044.00,
    "unrealized_pnl": 44.00,
    "positions": [
      {
        "ticker": "AAPL",
        "quantity": 10,
        "avg_cost": 192.34,
        "current_price": 196.74,
        "unrealized_pnl": 44.00,
        "unrealized_pnl_pct": 2.2876
      },
      {
        "ticker": "TSLA",
        "quantity": 5,
        "avg_cost": 220.00,
        "current_price": null,
        "unrealized_pnl": null,
        "unrealized_pnl_pct": null
      }
    ]
  }
  ```

  Top-level fields:

  | Field | Type | Nullable | Notes |
  |---|---|---|---|
  | `cash_balance` | number | no | From `users_profile.cash_balance`. |
  | `total_value` | number | no | `cash_balance + Σ(quantity × current_price)` across positions **where `current_price` is not null**. Positions with `current_price == null` contribute zero to `total_value` rather than collapsing the whole sum to `null`. |
  | `unrealized_pnl` | number | no | `Σ((current_price − avg_cost) × quantity)` across positions where `current_price` is not null. Zero when all positions are unpriced. |
  | `positions` | array | no | Empty array if the user holds nothing. |

  Per-position fields:

  | Field | Type | Nullable | Notes |
  |---|---|---|---|
  | `ticker` | string | no | Uppercase. |
  | `quantity` | number | no | Fractional shares allowed (SCHEMA.md §1.3 stores REAL). |
  | `avg_cost` | number | no | Weighted average cost basis maintained by `portfolio.positions`. |
  | `current_price` | number | **yes** | From `PriceCache`. `null` when no tick has been observed yet for the ticker (e.g., a position that exists in DB but the source has not yet produced a tick after restart). |
  | `unrealized_pnl` | number | **yes** | `(current_price − avg_cost) × quantity`. `null` iff `current_price` is `null`. |
  | `unrealized_pnl_pct` | number | **yes** | `(current_price − avg_cost) / avg_cost * 100`, rounded to 4 dp. `null` iff `current_price` is `null`. Returns `0.0` in the degenerate case of `avg_cost == 0` (which shouldn't occur for real trades). |

  Positions are returned in `positions.updated_at` descending (most recently touched first), which keeps newly-bought tickers visually prominent.

### 4.2 `POST /api/portfolio/trade` — Execute a trade

Executes a market order at the latest cached price. This is the **single trade path** in the system: both this endpoint and the LLM auto-trade flow (`backend/app/chat`) call into `portfolio.execute_trade()`, which acquires a per-user `asyncio.Lock` keyed in a `dict[str, asyncio.Lock]` so concurrent UI clicks and LLM-initiated trades cannot race on `cash_balance` / `positions`.

- **Method / path.** `POST /api/portfolio/trade`
- **Request body.**

  ```json
  {"ticker": "AAPL", "side": "buy", "quantity": 10}
  ```

  | Field | Type | Required | Notes |
  |---|---|---|---|
  | `ticker` | string | yes | Same regex / uppercasing as §3.2. Must be present in the user's watchlist or otherwise be known to the market source; unknown tickers are rejected with 404 `unknown_ticker`. |
  | `side` | `"buy" \| "sell"` | yes | Anything else → 422 `validation_error`. |
  | `quantity` | number | yes | Must be `> 0`. Fractional shares allowed. Non-numeric, zero, or negative → 422 `validation_error`. |

- **Response status.**
  - 201 Created on success.
  - 400 Bad Request with `insufficient_cash` (buy) or `insufficient_shares` (sell).
  - 404 Not Found with `unknown_ticker` if the ticker is unknown to the market source.
  - 422 Unprocessable Entity with `validation_error` (bad shape) or `invalid_ticker` (bad regex).
  - 500 Internal Server Error with `internal_error` as a last resort.

- **Response body (201).**

  ```json
  {
    "trade_id": "9f0e34ed-7b3e-4a76-bd16-7c1a8aa3a98f",
    "ticker": "AAPL",
    "side": "buy",
    "quantity": 10,
    "fill_price": 192.34,
    "cash_after": 8076.60,
    "position_after": {"quantity": 10, "avg_cost": 192.34}
  }
  ```

  | Field | Type | Notes |
  |---|---|---|
  | `trade_id` | string | UUID; matches the `trades.id` row just inserted. |
  | `ticker` | string | Echoed uppercase ticker. |
  | `side` | `"buy" \| "sell"` | Echoed side. |
  | `quantity` | number | Echoed quantity. |
  | `fill_price` | number | The price used to fill — **the latest value in `PriceCache` at execution time, not the price the client showed**. Price may drift between the client rendering the watchlist and the server processing the trade; the cache value is always authoritative (PLAN.md §9 "Trade Execution & Validation"). |
  | `cash_after` | number | `users_profile.cash_balance` after the trade is applied. |
  | `position_after.quantity` | number | Resulting position size. **Will be `0` after a full-sell**; the position row is removed when this happens but the response still echoes the realized state. |
  | `position_after.avg_cost` | number | Weighted average cost after the trade. `0` after a full-sell. |

- **Error response (400).** The error envelope:

  ```json
  {
    "error": "insufficient_cash",
    "error_message": "Need $12,400.00 but only $8,076.60 available."
  }
  ```

  The `error_message` is the same human-readable string the chat layer puts into `actions[].error_message`, so the two surfaces stay aligned.

### 4.3 `GET /api/portfolio/history` — Portfolio value over time

Returns time-series points from `portfolio_snapshots` for the P&L chart (PLAN.md §10 "P&L chart"). Snapshots are written every 30s by a background task and immediately after each trade.

- **Method / path.** `GET /api/portfolio/history`
- **Query params.**

  | Name | Type | Default | Allowed values |
  |---|---|---|---|
  | `range` | string | `"24h"` | `"1h"`, `"6h"`, `"24h"`, `"7d"` |

- **Response status.** 200 OK on success; 422 with `validation_error` if `range` is invalid.
- **Response body.**

  ```json
  {
    "range": "24h",
    "points": [
      {"ts": "2026-05-19T10:15:30.000000+00:00", "total_value": 10000.00},
      {"ts": "2026-05-19T10:16:00.000000+00:00", "total_value": 10003.21}
    ]
  }
  ```

  | Field | Type | Notes |
  |---|---|---|
  | `range` | string | Echoed `range`. |
  | `points` | array of objects | Chronological order, oldest first. Empty array on a brand-new install before the first snapshot has been written. |
  | `points[].ts` | string | ISO 8601 UTC, matches `portfolio_snapshots.recorded_at`. |
  | `points[].total_value` | number | Snapshot value (cash + position market value at the time of the snapshot). |

---

## 5. Chat endpoint

### 5.1 `POST /api/chat` — Send a message to FinAlly

Sends a user message to the LLM-powered assistant and returns a single complete response. **This is not a streaming endpoint** — Cerebras inference is fast enough that the frontend simply shows a loading indicator and awaits the full JSON. Any trades or watchlist changes the LLM emits are auto-executed by the backend and surfaced inside the `actions[]` array; the response body is the **same shape** as what is persisted in `chat_messages.actions` (see SCHEMA.md §3) modulo wrapping the message text alongside.

- **Method / path.** `POST /api/chat`
- **Request body.**

  ```json
  {"message": "Buy 10 shares of AAPL and add PYPL to my watchlist."}
  ```

  | Field | Type | Required | Notes |
  |---|---|---|---|
  | `message` | string | yes | Non-empty, max 4000 chars (rejected with 422 `validation_error` otherwise). |

- **Response status.** Always 200 OK as long as the request body parses. LLM-initiated trades or watchlist changes that fail validation are reported inside `actions[]` as `status: "error"` entries — they do **not** turn the HTTP response into a 4xx. The only non-200 responses are 422 `validation_error` (malformed body) and 500 `internal_error` (unhandled exception in the chat pipeline).

- **Response body.** The full `ChatResponse` shape — copied verbatim from PLAN.md §9 "Backend Response & `actions` Shape" and matching SCHEMA.md §3:

  ```json
  {
    "message": "I've added 10 shares of AAPL and put PYPL on the watchlist.",
    "actions": [
      {
        "kind": "trade",
        "status": "ok",
        "ticker": "AAPL",
        "side": "buy",
        "quantity": 10,
        "fill_price": 192.34,
        "cash_after": 8076.60
      },
      {
        "kind": "trade",
        "status": "error",
        "ticker": "TSLA",
        "side": "buy",
        "quantity": 50,
        "error": "insufficient_cash",
        "error_message": "Need $12,400 but only $8,076.60 available."
      },
      {
        "kind": "watchlist",
        "status": "ok",
        "ticker": "PYPL",
        "action": "add"
      }
    ]
  }
  ```

  Top-level fields:

  | Field | Type | Nullable | Notes |
  |---|---|---|---|
  | `message` | string | no | The LLM's conversational text shown to the user. Never empty in a successful response. |
  | `actions` | array | **no — always present** | The resolved list of trades and watchlist changes that were actually executed. **The API always returns `[]` (an empty array, never `null`)** for messages where the LLM made no changes — even though SCHEMA.md §1.7 / §3 permit either `NULL` or `[]` in the underlying `chat_messages.actions` storage column. The serialization layer in `backend/app/chat` normalizes a stored `NULL` to `[]` on read. **Decision for this contract: the wire format is always `[]`, never `null`, so the Frontend Engineer can map without a null-check and the LLM Engineer must mirror this on assistant rows that performed no actions.** |

  Per-action fields (full reference; see SCHEMA.md §3 for the canonical examples):

  | Field | Required when | Type | Notes |
  |---|---|---|---|
  | `kind` | always | `"trade" \| "watchlist"` | |
  | `status` | always | `"ok" \| "error"` | |
  | `ticker` | always | string | Uppercase. |
  | `side` | `kind == "trade"` | `"buy" \| "sell"` | |
  | `quantity` | `kind == "trade"` | number | Echo of the executed (or attempted) quantity. Fractional allowed. |
  | `fill_price` | `kind == "trade" && status == "ok"` | number | Latest `PriceCache` value at execution time. |
  | `cash_after` | `kind == "trade" && status == "ok"` | number | `users_profile.cash_balance` after the trade. |
  | `action` | `kind == "watchlist"` | `"add" \| "remove"` | |
  | `error` | `status == "error"` | string | One of `insufficient_cash`, `insufficient_shares`, `unknown_ticker` (PLAN.md §9). |
  | `error_message` | `status == "error"` | string | Human-readable sentence; identical formatting to the 400 envelope from §4.2 so the frontend can use one renderer. |

  Order: the `actions[]` array preserves the order the LLM emitted in its structured output (trades first, then watchlist changes — see LLM_CONTRACT.md when published).

---

## 6. System

### 6.1 `GET /api/health` — Health check

Cheap liveness / readiness probe for the Docker container (PLAN.md §11). Touches the database to verify it has been initialized and reports which market data source is active.

- **Method / path.** `GET /api/health`
- **Query / body.** None.
- **Response status.** Always 200 OK; `db` and `market` fields communicate sub-system status.
- **Response body.**

  ```json
  {"status": "ok", "db": "ok", "market": "simulator"}
  ```

  | Field | Type | Allowed values | Notes |
  |---|---|---|---|
  | `status` | string | `"ok"` | Always `"ok"` in v1 (we do not return degraded states yet). |
  | `db` | string | `"ok" \| "missing"` | `"ok"` if the database file exists and the bootstrap queries succeed; `"missing"` if the file or tables are absent (should not occur in normal operation because lifespan startup initializes the DB first). |
  | `market` | string | `"simulator" \| "massive"` | Which `MarketDataSource` implementation is active (decided by `create_market_data_source()` based on `MASSIVE_API_KEY`). |

---

## 7. Internal request-handling notes (informative — not part of the wire contract)

This section is informative for builder agents; the Frontend Engineer can skip it.

- **Single trade path.** `POST /api/portfolio/trade` and the LLM auto-trade flow both call into `portfolio.execute_trade()` (lives in `backend/app/portfolio/trade.py`). That function acquires a per-user `asyncio.Lock` from a module-level `dict[str, asyncio.Lock]` (lazily populated on first access), reads cash and positions, validates, computes the fill at the latest `PriceCache` value, writes the `trades` row and the position update, snapshots `portfolio_snapshots`, and releases the lock. This serializes trades per user without blocking unrelated requests and avoids dropping into SQLite-level transaction tricks (PLAN.md §7 "Concurrent Trade Safety").
- **Watchlist session anchors.** `session_anchor_price` and `change_pct` are not stored in SQL — they are derived from the in-memory `PriceCache`. The anchor is captured by `PriceCache.update()` the first time it sees a ticker since process start and cleared by `PriceCache.remove()` when the ticker is dropped. There is no scheduled reset; the anchor is honest about the absence of a real market open in the simulator (PLAN.md §10 "Watchlist panel").
- **Fill-price authority.** The `fill_price` in trade responses and `actions[]` entries is the value the cache returned at the moment `execute_trade()` ran — not whatever price the client / LLM had in its context. Clients should display this fill price (which the backend returns explicitly) rather than the watchlist price they had cached.
- **`actions` storage vs. wire.** Storage in `chat_messages.actions` may be `NULL` (assistant row with no actions, per SCHEMA.md §1.7 / §3); the wire response always returns `[]` in that case (this contract, §5).
- **Background tasks.** Three lifespan-managed `asyncio.Task`s — the tick-history persister (`price_ticks`), the snapshot writer (`portfolio_snapshots`), and the daily pruner — run alongside the market data source and the FastAPI app. They are started in the lifespan startup hook after `init_database()` and cancelled cleanly on shutdown.

---

## 8. Open ambiguities / flags for the orchestrator

These are items where this contract chose conservatively but the orchestrator may want to re-affirm before Phase 2 dispatch:

1. **SSE event shape diverges from the orchestrator prompt.** The prompt described `{ticker, price, prev_price, ts, direction}` per event; the frozen market subsystem actually emits a full ticker map (`{TICKER: PriceUpdate.to_dict(), ...}`) on each frame, with the field names `previous_price`, `timestamp`, `change`, `change_percent`, `direction`. This contract documents the actual behavior because `backend/app/market/` is read-only for the Backend API Engineer. Confirm with the Frontend Engineer that the dict-map shape is acceptable.
2. **`POST /api/watchlist` regex.** This contract enforces `^[A-Za-z]{1,5}$` (1-5 letters, no digits or punctuation) and uppercases server-side. PLAN.md §8 only says "rejects non-alphabetic input." Confirm the 1-5 length bound matches what the Massive client / simulator can actually accept.
3. **`actions` wire shape is always `[]`, never `null`.** SCHEMA.md §3 explicitly defers this choice to the LLM Engineer. This contract pins the **wire** form to `[]` so the frontend has a single shape; the storage form may still be `NULL` and the API layer normalizes on read. The LLM Engineer must align by either storing `[]` on actionless assistant rows or by relying on the API normalizer.
4. **`current_price == null` does not collapse `total_value`.** Positions with no cached price contribute zero to `total_value` and `unrealized_pnl` instead of making the whole sum `null`. This is friendlier to the frontend's P&L renderer; flag this if the integration tester prefers an all-or-nothing total.
5. **Trade endpoint 404 vs 400.** This contract returns 404 `unknown_ticker` for unrecognized tickers on `POST /api/portfolio/trade` (because the ticker is the missing resource). Some teams would return 400 here; PLAN.md §9 lists `unknown_ticker` as an error code but doesn't pin a status. Confirm 404 is the desired mapping.
