# Backend — Developer Guide

FastAPI app, owned by 4 agent roles (market, db, portfolio, chat) plus the Backend API Engineer who wires them together. All Python under `backend/app/`. Tests under `backend/tests/`.

## Project Setup

```bash
cd backend
uv sync --extra dev        # Install runtime + test/lint deps
source .venv/bin/activate  # Optional; uv run handles this for you
```

Test the full suite (279 tests as of HEAD):

```bash
env -u PYTHONPATH LLM_MOCK=true uv run --extra dev pytest -v
```

Why `env -u PYTHONPATH`: on systems with a ROS overlay or other global Python path leak, pytest can pull in foreign plugins. Stripping `PYTHONPATH` makes the run reproducible.

Why `LLM_MOCK=true`: chat tests use deterministic mock responses; live mode requires `OPENROUTER_API_KEY` and would slow the suite.

## Module map

```
backend/app/
├── market/      # GBM simulator + Massive client + PriceCache + SSE
├── db/          # SQLite lazy init + connection helpers + seed
├── portfolio/   # Trade execution + position math + snapshot/tick persisters
├── chat/        # LiteLLM client + prompt assembly + mock mode + executor
├── api/         # FastAPI routes (market, watchlist, portfolio, chat, system)
└── main.py      # FastAPI app + lifespan (init DB, start background tasks)
```

### `app.market` — Market data

```python
from app.market import (
    PriceCache, PriceUpdate, MarketDataSource, create_market_data_source,
    create_stream_router,
)
```

- **`PriceUpdate`** — immutable dataclass: `ticker`, `price`, `previous_price`, `timestamp`, plus `change`, `change_percent`, `direction`, `to_dict()`.
- **`PriceCache`** — thread-safe in-memory store. `update`, `get`, `get_price`, `get_all`, `remove`, `version` (monotonic counter for SSE change detection), `get_session_anchor(ticker)` (first observed price; powers `change_pct`).
- **`MarketDataSource`** abstract — implemented by `SimulatorDataSource` and `MassiveDataSource`. Lifecycle: `start(tickers)` → `add_ticker()` / `remove_ticker()` → `stop()`.
- **`create_market_data_source(cache)`** — factory; returns Massive if `MASSIVE_API_KEY` is set, simulator otherwise.
- **`create_stream_router(price_cache)`** — returns the `APIRouter` exposing `GET /api/stream/prices` (per-frame ticker-map JSON, push-on-change, 15s keepalive comments).
- Default tickers + GBM params: `app/market/seed_prices.py`. Unknown tickers added to the watchlist get auto-seeded with plausible price/vol params.

### `app.db` — SQLite persistence

```python
from app.db import init_database, get_connection, connection, DEFAULT_USER_ID
```

- **`init_database(db_path=None)`** — idempotent: creates schema + seeds default user + 10 watchlist rows. Called once from the FastAPI lifespan startup. Resolves path from `FINALLY_DB_PATH` (default `/app/db/finally.db`).
- **`get_connection()`** — returns `sqlite3.Connection` with `row_factory = sqlite3.Row`, WAL journal, FK pragmas on.
- **`connection()`** — context-manager wrapper that auto-commits/rolls-back/closes; preferred for route handlers.
- 8 tables: `users_profile`, `watchlist`, `positions`, `trades`, `portfolio_snapshots`, `price_ticks`, `chat_messages`, `chat_state`. Schema is in `app/db/schema.sql` and frozen by `planning/SCHEMA.md`.

### `app.portfolio` — Trade execution + portfolio math

```python
from app.portfolio import (
    execute_trade, current_portfolio, snapshot_now, get_portfolio_context,
    InsufficientCashError, InsufficientSharesError, UnknownTickerError, InvalidQuantityError,
)
```

- **`execute_trade(*, ticker, side, quantity, price_cache, user_id="default")`** — async. The single trade path used by both the UI's `POST /api/portfolio/trade` and the chat executor. Acquires a per-user `asyncio.Lock` from a module-level dict, reads the live cache for the fill price (NOT a caller-supplied snapshot), writes the trade + updates positions + triggers an immediate portfolio snapshot. Raises the typed exceptions on validation failures.
- **`current_portfolio(price_cache, user_id="default")`** — returns the dict shape that `GET /api/portfolio` serializes.
- **`get_portfolio_context(price_cache, user_id="default")`** — same as `current_portfolio` plus the live watchlist with prices. Consumed by `app.chat.handler` to populate the LLM's prompt context.
- **`snapshot_now(...)`** — writes one `portfolio_snapshots` row. Also runs on a 30s background task.
- Background tasks (started from `main.py` lifespan): tick-history persister (5s cadence), snapshot writer (30s), daily pruner (deletes `price_ticks` > 7 days).

### `app.chat` — LLM chat

```python
from app.chat import handle_message  # async -> ChatResponse
```

- **`handle_message(user_text, *, price_cache)`** — orchestrates the full chat turn:
  1. Loads `portfolio_context` via `app.portfolio.get_portfolio_context`.
  2. Loads conversation history (last 10) + rolling summary from `chat_state`.
  3. Builds the prompt via `app.chat.prompt.build_system_prompt`.
  4. Calls the LLM via `app.chat.client.complete` (or `app.chat.mock.respond` when `LLM_MOCK=true`).
  5. Parses the structured `LLMResponse` (Pydantic v2).
  6. Applies trades + watchlist changes via `app.chat.executor.apply` → returns `actions[]`.
  7. Persists user + assistant messages to `chat_messages`. If verbatim window > 10, folds the oldest into `chat_state.summary`.
- **`SYSTEM_PROMPT_VOICE`** in `app/chat/system_prompt.py` is the user-authored voice block. It is concatenated into the prompt; the rest of the prompt skeleton is mechanical.
- Live LLM uses LiteLLM → OpenRouter `openrouter/openai/gpt-oss-120b` with Cerebras provider (set up via the `cerebras-inference` skill). Structured output via `response_format=LLMResponse`.

### `app.api` — FastAPI routes

All routes live under `/api/*`. Mounted from `main.py` via `api_router = APIRouter(prefix="/api")`. Wire shapes are frozen in `planning/API_CONTRACT.md`.

- `market.py` — `GET /stream/prices` (SSE), `GET /prices/history/{ticker}?range=...`
- `watchlist.py` — `GET/POST/DELETE /watchlist[/{ticker}]`; uppercases + regex-validates tickers; computes `change_pct` from session anchor.
- `portfolio.py` — `GET /portfolio`, `POST /portfolio/trade`, `GET /portfolio/history?range=...`
- `chat.py` — `POST /chat`. Thin wrapper that resolves the price cache from app state and delegates to `app.chat.handle_message`.
- `system.py` — `GET /health` returning `{status, db, market}`.

### `main.py` — App lifespan

The FastAPI lifespan does these things in order on startup and reverses them on shutdown:

1. `init_database()` — creates schema + seeds if needed.
2. `app.market.factory.create_market_data_source(cache)` — picks simulator vs. Massive based on env.
3. `app.chat.client.validate_config()` — raises if `OPENROUTER_API_KEY` is missing AND `LLM_MOCK != "true"`. Fails fast at startup, not lazily on first request.
4. Starts background tasks: tick-history persister, portfolio snapshot writer, daily pruner.
5. Mounts `/api/*` routes, then a static-files catch-all at `/` pointing to `frontend/out/` (or `/app/static` inside Docker).

On shutdown: cancels background tasks, stops the data source, closes the DB.

## Running Tests

```bash
# Full suite (default — mock LLM, no real network)
env -u PYTHONPATH LLM_MOCK=true uv run --extra dev pytest -v

# Single module
env -u PYTHONPATH LLM_MOCK=true uv run pytest tests/chat/ -v

# Coverage
env -u PYTHONPATH LLM_MOCK=true uv run --extra dev pytest --cov=app

# Lint
uv run --extra dev ruff check app/ tests/
```

Notable test suites:

- `tests/portfolio/test_trade.py::test_concurrent_buys_serialize_via_per_user_lock` — race-condition regression. Proves the per-user `asyncio.Lock` prevents double-spend.
- `tests/portfolio/test_context.py` — regression for **B017** (chat handler must see real portfolio context).
- `tests/chat/test_handler.py::test_handler_passes_real_portfolio_context_to_prompt` — captures the prompt and asserts position data reached it.
- `tests/api/test_chat_route.py` — `/api/chat` happy + error paths; requires `LLM_MOCK=true`.

## Demos

```bash
uv run market_data_demo.py   # Terminal dashboard streaming simulated prices
```

## Conventions

- All timestamps are ISO 8601 strings via `datetime.now(timezone.utc).isoformat()`.
- All IDs are UUIDv4 strings (`uuid.uuid4().hex`). `price_ticks` is the exception (composite PK `(ticker, recorded_at)`).
- Quantity columns are `REAL` — fractional shares are first-class.
- Trade fills always use the live `PriceCache` value at execution time, not the caller's snapshot. This is enforced by `execute_trade`'s signature.
- Errors at the API boundary use the envelope `{error: "<machine_code>", error_message: "<human>"}` — codes enumerated in `planning/API_CONTRACT.md` §1.4.
