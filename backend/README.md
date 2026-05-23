# FinAlly Backend

FastAPI backend for the FinAlly AI Trading Workstation. See [`CLAUDE.md`](CLAUDE.md) for the developer guide; this README is a quick map.

## Structure

```
backend/
├── app/
│   ├── market/              # GBM simulator + Massive client + PriceCache + SSE
│   │   ├── models.py        #   PriceUpdate dataclass
│   │   ├── cache.py         #   Thread-safe PriceCache + session anchors
│   │   ├── interface.py     #   MarketDataSource abstract base
│   │   ├── simulator.py     #   GBM in-process simulator
│   │   ├── massive_client.py#   Polygon.io REST client
│   │   ├── factory.py       #   create_market_data_source()
│   │   ├── stream.py        #   GET /api/stream/prices SSE
│   │   └── seed_prices.py   #   Default tickers + GBM params
│   ├── db/                  # SQLite lazy init + helpers
│   │   ├── schema.sql       #   8 CREATE TABLE statements + indexes
│   │   ├── init.py          #   init_database() — idempotent
│   │   ├── conn.py          #   get_connection() / connection() context mgr
│   │   └── seed.py          #   Default user + 10 watchlist tickers
│   ├── portfolio/           # Trade execution + portfolio math
│   │   ├── trade.py         #   execute_trade() with per-user asyncio.Lock
│   │   ├── positions.py     #   Position math + current_portfolio + get_portfolio_context
│   │   ├── snapshots.py     #   30s portfolio snapshot writer
│   │   └── tick_history.py  #   5s tick persister + 7-day pruner
│   ├── chat/                # LLM chat assistant
│   │   ├── client.py        #   LiteLLM -> OpenRouter (Cerebras) wrapper
│   │   ├── schemas.py       #   Pydantic v2 models (LLMResponse, ChatResponse, …)
│   │   ├── prompt.py        #   System-prompt assembly with SYSTEM_PROMPT_VOICE slot
│   │   ├── system_prompt.py #   User-authored voice block
│   │   ├── mock.py          #   LLM_MOCK=true deterministic responses
│   │   ├── executor.py      #   Applies LLM trades + watchlist changes
│   │   ├── summarizer.py    #   Rolling summary of older turns
│   │   └── handler.py       #   handle_message() top-level
│   ├── api/                 # FastAPI route modules
│   │   ├── market.py        #   SSE + price history
│   │   ├── watchlist.py     #   GET/POST/DELETE
│   │   ├── portfolio.py     #   GET / POST trade / GET history
│   │   ├── chat.py          #   POST /chat — delegates to app.chat.handle_message
│   │   └── system.py        #   GET /health
│   └── main.py              # FastAPI app + lifespan
├── tests/                   # 279 unit + integration tests
│   ├── market/
│   ├── db/
│   ├── portfolio/
│   ├── chat/
│   └── api/
├── pyproject.toml
├── uv.lock
└── market_data_demo.py      # Standalone terminal demo
```

## Running Tests

```bash
uv sync --extra dev                                    # install
env -u PYTHONPATH LLM_MOCK=true uv run pytest          # 279 tests
env -u PYTHONPATH LLM_MOCK=true uv run pytest --cov=app
uv run ruff check .                                     # lint
```

Why the env tweaks: see [`CLAUDE.md`](CLAUDE.md) "Project Setup".

## Environment Variables

| Variable | Required | Default | Effect |
|---|---|---|---|
| `OPENROUTER_API_KEY` | Yes (live LLM) | — | Validates at FastAPI startup unless `LLM_MOCK=true`. |
| `MASSIVE_API_KEY` | No | empty | Use Polygon.io REST if set, otherwise GBM simulator. |
| `LLM_MOCK` | No | `false` | `true` returns deterministic regex-matched mock chat responses. |
| `FINALLY_DB_PATH` | No | `/app/db/finally.db` | SQLite file location. |
| `FINALLY_STATIC_DIR` | No | `/app/static` | Frontend export directory to serve at `/`. Falls back to `<repo>/frontend/out` for dev. |

## Development

```bash
uv sync --extra dev
uv run uvicorn app.main:app --reload   # Local dev server on :8000
uv run ruff check .
uv run ruff format .
```

The Docker image builds this same `app.main:app` under `uvicorn` without reload; see `../Dockerfile`.
