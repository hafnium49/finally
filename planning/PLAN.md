# FinAlly — AI Trading Workstation

## Project Specification

## 1. Vision

FinAlly (Finance Ally) is a visually stunning AI-powered trading workstation that streams live market data, lets users trade a simulated portfolio, and integrates an LLM chat assistant that can analyze positions and execute trades on the user's behalf. It looks and feels like a modern Bloomberg terminal with an AI copilot.

This is the capstone project for an agentic AI coding course. It is built entirely by Coding Agents demonstrating how orchestrated AI agents can produce a production-quality full-stack application. Agents interact through files in `planning/`.

## 2. User Experience

### First Launch

The user runs a single Docker command (or a provided start script). A browser opens to `http://localhost:8000`. No login, no signup. They immediately see:

- A watchlist of 10 default tickers with live-updating prices in a grid
- $10,000 in virtual cash
- A dark, data-rich trading terminal aesthetic
- An AI chat panel ready to assist

### What the User Can Do

- **Watch prices stream** — prices flash green (uptick) or red (downtick) with subtle CSS animations that fade
- **View sparkline mini-charts** — price action beside each ticker in the watchlist, accumulated on the frontend from the SSE stream since page load (sparklines fill in progressively)
- **Click a ticker** to see a larger detailed chart in the main chart area
- **Buy and sell shares** — market orders only, instant fill at current price, no fees, no confirmation dialog
- **Monitor their portfolio** — a heatmap (treemap) showing positions sized by weight and colored by P&L, plus a P&L chart tracking total portfolio value over time
- **View a positions table** — ticker, quantity, average cost, current price, unrealized P&L, % change
- **Chat with the AI assistant** — ask about their portfolio, get analysis, and have the AI execute trades and manage the watchlist through natural language
- **Manage the watchlist** — add/remove tickers manually or via the AI chat

### Visual Design

- **Dark theme**: backgrounds around `#0d1117` or `#1a1a2e`, muted gray borders, no pure black
- **Price flash animations**: brief green/red background highlight on price change, fading over ~500ms via CSS transitions
- **Connection status indicator**: a small colored dot (green = connected, yellow = reconnecting, red = disconnected) visible in the header
- **Professional, data-dense layout**: inspired by Bloomberg/trading terminals — every pixel earns its place
- **Responsive but desktop-first**: optimized for wide screens, functional on tablet

### Color Scheme
- **Accent Yellow** `#ecad0a` — chart highlights, selected-state indicators, key callouts
- **Blue Primary** `#209dd7` — links, secondary actions, informational headers, focus rings
- **Purple Secondary** `#753991` — primary action buttons (Buy, Sell, Send chat)

Price flash colors (uptick green / downtick red) are separate from the brand palette and not configurable.

## 3. Architecture Overview

### Single Container, Single Port

```
┌─────────────────────────────────────────────────┐
│  Docker Container (port 8000)                   │
│                                                 │
│  FastAPI (Python/uv)                            │
│  ├── /api/*          REST endpoints             │
│  ├── /api/stream/*   SSE streaming              │
│  └── /*              Static file serving         │
│                      (Next.js export)            │
│                                                 │
│  SQLite database (volume-mounted)               │
│  Background task: market data polling/sim        │
└─────────────────────────────────────────────────┘
```

- **Frontend**: Next.js with TypeScript, built as a static export (`output: 'export'`), served by FastAPI as static files
- **Backend**: FastAPI (Python), managed as a `uv` project
- **Database**: SQLite, single file at `db/finally.db`, volume-mounted for persistence
- **Real-time data**: Server-Sent Events (SSE) — simpler than WebSockets, one-way server→client push, works everywhere
- **AI integration**: LiteLLM → OpenRouter (Cerebras for fast inference), with structured outputs for trade execution
- **Market data**: Environment-variable driven — simulator by default, real data via Massive API if key provided

### Why These Choices

| Decision | Rationale |
|---|---|
| SSE over WebSockets | One-way push is all we need; simpler, no bidirectional complexity, universal browser support |
| Static Next.js export | Single origin, no CORS issues, one port, one container, simple deployment |
| SQLite over Postgres | No auth = no multi-user = no need for a database server; self-contained, zero config |
| Single Docker container | Students run one command; no docker-compose for production, no service orchestration |
| uv for Python | Fast, modern Python project management; reproducible lockfile; what students should learn |
| Market orders only | Eliminates order book, limit order logic, partial fills — dramatically simpler portfolio math |

---

## 4. Directory Structure

```
finally/
├── frontend/                 # Next.js TypeScript project (static export)
├── backend/                  # FastAPI uv project (Python)
│   ├── pyproject.toml
│   ├── app/                  # Application package
│   │   ├── __init__.py
│   │   ├── market/           # Market data: simulator, Massive client, price cache, SSE
│   │   ├── db/               # Schema SQL, seed data, lazy-init logic, connection helpers
│   │   ├── portfolio/        # Trade execution, position math, P&L, snapshots
│   │   ├── chat/             # LLM client, prompt assembly, structured-output parsing
│   │   └── api/              # FastAPI route modules wiring the above
│   └── tests/                # pytest suite (mirrors app/ subpackage layout)
├── planning/                 # Project-wide documentation for agents
│   ├── PLAN.md               # This document
│   └── ...                   # Additional agent reference docs
├── scripts/
│   ├── start_mac.sh          # Launch Docker container (macOS/Linux)
│   ├── stop_mac.sh           # Stop Docker container (macOS/Linux)
│   ├── start_windows.ps1     # Launch Docker container (Windows PowerShell)
│   └── stop_windows.ps1      # Stop Docker container (Windows PowerShell)
├── test/                     # Playwright E2E tests + docker-compose.test.yml
├── db/                       # Volume mount target (SQLite file lives here at runtime)
│   └── .gitkeep              # Directory exists in repo; finally.db is gitignored
├── Dockerfile                # Multi-stage build (Node → Python)
├── docker-compose.yml        # Optional convenience wrapper
├── .env                      # Environment variables (gitignored, .env.example committed)
└── .gitignore
```

Note on the two `db` paths: **`backend/app/db/`** holds Python code (schema SQL, seed data, init logic). **`db/`** at the project root is the host directory mounted into the container as `/app/db`, where the SQLite file `finally.db` actually lives at runtime. The names overlap but the paths don't — one is source, the other is data.

### Key Boundaries

- **`frontend/`** is a self-contained Next.js project. It knows nothing about Python. It talks to the backend via `/api/*` endpoints and `/api/stream/*` SSE endpoints. Internal structure is up to the Frontend Engineer agent.
- **`backend/`** is a self-contained uv project with its own `pyproject.toml`. It owns all server logic — database initialization, schema, seed data, API routes, SSE streaming, market data, LLM integration. Code lives under `backend/app/` and is organized into feature subpackages (`market/`, `db/`, `portfolio/`, `chat/`, `api/`). New subpackages may be added by feature owners as needed.
- **`backend/app/db/`** contains schema SQL definitions, seed logic, and connection helpers. The backend initializes the database in a FastAPI lifespan startup hook — creating tables and seeding default data if the SQLite file doesn't exist or is empty.
- **`db/`** at the project root is the runtime volume mount point. The SQLite file (`db/finally.db`) is created here by the backend and persists across container restarts via Docker volume.
- **`planning/`** contains project-wide documentation, including this plan. All agents reference files here as the shared contract.
- **`test/`** contains Playwright E2E tests and supporting infrastructure (e.g., `docker-compose.test.yml`). Unit tests live within `frontend/` and `backend/` respectively, following each framework's conventions.
- **`scripts/`** contains start/stop scripts that wrap Docker commands.

---

## 5. Environment Variables

```bash
# Required: OpenRouter API key for LLM chat functionality
OPENROUTER_API_KEY=your-openrouter-api-key-here

# Optional: Massive (Polygon.io) API key for real market data
# If not set, the built-in market simulator is used (recommended for most users)
MASSIVE_API_KEY=

# Optional: Set to "true" for deterministic mock LLM responses (testing)
LLM_MOCK=false
```

### Behavior

- If `MASSIVE_API_KEY` is set and non-empty → backend uses Massive REST API for market data
- If `MASSIVE_API_KEY` is absent or empty → backend uses the built-in market simulator
- If `LLM_MOCK=true` → backend returns deterministic mock LLM responses (for E2E tests)
- The backend reads `.env` from the project root (mounted into the container or read via docker `--env-file`)

---

## 6. Market Data

### Two Implementations, One Interface

Both the simulator and the Massive client implement the same abstract interface. The backend selects which to use based on the environment variable. All downstream code (SSE streaming, price cache, frontend) is agnostic to the source.

### Simulator (Default)

- Generates prices using geometric Brownian motion (GBM) with configurable drift and volatility per ticker
- Updates at ~500ms intervals
- Correlated moves across tickers (e.g., tech stocks move together)
- Occasional random "events" — sudden 2-5% moves on a ticker for drama
- Starts from realistic seed prices for the 10 default tickers (e.g., AAPL ~$190, GOOGL ~$175)
- **Unknown tickers**: When a ticker not in the seed list is added to the watchlist (by the user or LLM), the simulator auto-generates a plausible seed price (random in a sensible range, e.g., $20–$400) and default GBM parameters (moderate drift and volatility). The new ticker is treated like any other from that point on, including correlation behavior at the cross-sector level.
- Runs as an in-process background task — no external dependencies

### Massive API (Optional)

- REST API polling (not WebSocket) — simpler, works on all tiers
- Polls for the union of all watched tickers on a configurable interval
- Free tier (5 calls/min): poll every 15 seconds
- Paid tiers: poll every 2-15 seconds depending on tier
- Parses REST response into the same format as the simulator

### Shared Price Cache

- A single background task (simulator or Massive poller) writes to an in-memory price cache
- The cache holds the latest price, previous price, and timestamp for each ticker
- SSE streams read from this cache and push updates to connected clients
- This architecture supports future multi-user scenarios without changes to the data layer

### SSE Streaming

- Endpoint: `GET /api/stream/prices`
- Long-lived SSE connection; client uses native `EventSource` API
- **Push-on-change, not push-on-tick.** The `PriceCache` uses a version counter; the SSE generator only emits an event when a ticker's cached price has actually changed. This avoids redundant frames when the upstream source polls slowly (e.g., Massive free tier at 15s) and keeps client-side flash logic from firing on no-op updates.
- A periodic SSE comment (`: keepalive\n\n`) is sent every ~15s to prevent intermediaries from closing idle connections.
- Each SSE event contains ticker, price, previous price, timestamp, and change direction
- Client handles reconnection automatically (EventSource has built-in retry)

---

## 7. Database

### SQLite with Lazy Initialization

The backend initializes the database once in a FastAPI lifespan startup hook. If the SQLite file doesn't exist or required tables are missing, it creates the schema and seeds default data. This means:

- No separate migration step
- No manual database setup
- Fresh Docker volumes start with a clean, seeded database automatically
- No cold-start penalty on the first request — init has already completed by the time the server accepts connections

### Concurrent Trade Safety

Both UI clicks and LLM auto-trades hit the same trade-execution path, and read-modify-write cycles on `cash_balance` / `positions` can interleave under `asyncio`. All trade execution must go through a single `asyncio.Lock` keyed on `user_id` (a `dict[str, asyncio.Lock]`, lazily populated). This serializes trades per user without blocking unrelated requests, and avoids dropping into SQLite-level transaction tricks.

### Schema

All tables include a `user_id` column defaulting to `"default"`. This is hardcoded for now (single-user) but enables future multi-user support without schema migration.

**users_profile** — User state (cash balance)
- `id` TEXT PRIMARY KEY (default: `"default"`)
- `cash_balance` REAL (default: `10000.0`)
- `created_at` TEXT (ISO timestamp)

**watchlist** — Tickers the user is watching
- `id` TEXT PRIMARY KEY (UUID)
- `user_id` TEXT (default: `"default"`)
- `ticker` TEXT
- `added_at` TEXT (ISO timestamp)
- UNIQUE constraint on `(user_id, ticker)`

**positions** — Current holdings (one row per ticker per user)
- `id` TEXT PRIMARY KEY (UUID)
- `user_id` TEXT (default: `"default"`)
- `ticker` TEXT
- `quantity` REAL (fractional shares supported)
- `avg_cost` REAL
- `updated_at` TEXT (ISO timestamp)
- UNIQUE constraint on `(user_id, ticker)`

**trades** — Trade history (append-only log)
- `id` TEXT PRIMARY KEY (UUID)
- `user_id` TEXT (default: `"default"`)
- `ticker` TEXT
- `side` TEXT (`"buy"` or `"sell"`)
- `quantity` REAL (fractional shares supported)
- `price` REAL
- `executed_at` TEXT (ISO timestamp)

**portfolio_snapshots** — Portfolio value over time (for P&L chart). Recorded every 30 seconds by a background task, and immediately after each trade execution. No retention policy in v1; if growth becomes a concern, downsample to 5-minute aggregates beyond 24h of history.
- `id` TEXT PRIMARY KEY (UUID)
- `user_id` TEXT (default: `"default"`)
- `total_value` REAL
- `recorded_at` TEXT (ISO timestamp)

**price_ticks** — Persisted price history for the main chart. Written by a background task at a fixed cadence (~5 seconds per ticker, independent of SSE push cadence) for every ticker currently in any watchlist. Retention: last 7 days; older rows pruned by a daily background task.
- `ticker` TEXT
- `price` REAL
- `recorded_at` TEXT (ISO timestamp)
- PRIMARY KEY (`ticker`, `recorded_at`)
- INDEX on `recorded_at` for pruning

Note: tick history is global (not per-user) because price data is the same for all users; this keeps the table small and makes pruning trivial.

**chat_messages** — Conversation history with LLM
- `id` TEXT PRIMARY KEY (UUID)
- `user_id` TEXT (default: `"default"`)
- `role` TEXT (`"user"` or `"assistant"`)
- `content` TEXT
- `actions` TEXT (JSON — trades executed, watchlist changes made; null for user messages)
- `created_at` TEXT (ISO timestamp)

### Default Seed Data

- One user profile: `id="default"`, `cash_balance=10000.0`
- Ten watchlist entries: AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, JPM, V, NFLX

---

## 8. API Endpoints

### Market Data
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/stream/prices` | SSE stream of live price updates (push-on-change) |
| GET | `/api/prices/history/{ticker}?range=1h\|6h\|24h\|7d` | Historical price ticks for the main chart, served from the `price_ticks` table |

### Portfolio
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/portfolio` | Current positions, cash balance, total value, unrealized P&L |
| POST | `/api/portfolio/trade` | Execute a trade: `{ticker, quantity, side}` |
| GET | `/api/portfolio/history` | Portfolio value snapshots over time (for P&L chart) |

### Watchlist
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/watchlist` | Current watchlist tickers with latest prices |
| POST | `/api/watchlist` | Add a ticker: `{ticker}` |
| DELETE | `/api/watchlist/{ticker}` | Remove a ticker |

### Chat
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat` | Send a message, receive complete JSON response (message + executed actions) |

### System
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check (for Docker/deployment) |

---

## 9. LLM Integration

When writing code to make calls to LLMs, use cerebras-inference skill to use LiteLLM via OpenRouter to the `openrouter/openai/gpt-oss-120b` model with Cerebras as the inference provider. Structured Outputs should be used to interpret the results.

There is an OPENROUTER_API_KEY in the .env file in the project root.

### How It Works

When the user sends a chat message, the backend:

1. Loads the user's current portfolio context (cash, positions with P&L, watchlist with live prices, total portfolio value)
2. Loads recent conversation history from the `chat_messages` table (see **Conversation Context Window** below)
3. Constructs a prompt with a system message, portfolio context, conversation history, and the user's new message
4. Calls the LLM via LiteLLM → OpenRouter, requesting structured output, using the cerebras-inference skill
5. Parses the complete structured JSON response
6. Auto-executes any trades or watchlist changes specified in the response (see **Trade Execution & Validation** below)
7. Stores the message and the resolved `actions` array in `chat_messages`
8. Returns the complete JSON response to the frontend (no token-by-token streaming — Cerebras inference is fast enough that a loading indicator is sufficient)

### Conversation Context Window

To bound token cost while preserving continuity:
- The most recent **10 messages** (user + assistant turns combined) are included verbatim
- All messages older than the last 10 are represented by a single rolling **summary** maintained by a lightweight LLM call (or simple truncation if no summary exists yet)
- The summary is regenerated when the verbatim window overflows: take the oldest message about to be evicted, prepend it to the existing summary, and ask the LLM to rewrite it as a concise paragraph
- The summary is stored separately (e.g., a `summary` row in a small `chat_state` table or as JSON in the `users_profile` row) so it survives across requests

This keeps prompts O(1) in size regardless of session length, at the cost of one extra LLM call per ~10 turns.

### Trade Execution & Validation

When the parsed response contains `trades`, each trade is executed sequentially through the same trade path used by `POST /api/portfolio/trade`:

- **Fill price** = the latest price in the `PriceCache` *at execution time*, not the price the LLM saw in its context. (Price may drift between LLM generation and execution; the cache value is always authoritative.)
- Each trade acquires the per-user `asyncio.Lock` before reading cash/positions and writing the trade.
- Validation errors (insufficient cash, insufficient shares, unknown ticker) do not raise — they are captured as `error` fields in the corresponding `actions` entry. The LLM's `message` text won't acknowledge these failures because the failure happens *after* generation; the chat UI surfaces them inline so the user sees what actually executed vs. what was attempted.

### Structured Output Schema

The LLM is instructed to respond with JSON matching this schema:

```json
{
  "message": "Your conversational response to the user",
  "trades": [
    {"ticker": "AAPL", "side": "buy", "quantity": 10}
  ],
  "watchlist_changes": [
    {"ticker": "PYPL", "action": "add"}
  ]
}
```

- `message` (required): The conversational text shown to the user
- `trades` (optional): Array of trades to auto-execute. Each trade goes through the same validation as manual trades (sufficient cash for buys, sufficient shares for sells)
- `watchlist_changes` (optional): Array of watchlist modifications

### Backend Response & `actions` Shape

The backend's response to the frontend wraps the LLM message with a resolved `actions` array describing what actually happened:

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

- `kind`: `"trade"` or `"watchlist"`
- `status`: `"ok"` or `"error"`
- Trade entries always include `ticker`, `side`, `quantity`; on success also `fill_price` and `cash_after`; on failure also `error` (machine code) and `error_message` (human text)
- The same `actions` array is persisted in `chat_messages.actions` so the chat panel can re-render history accurately on reload

### Auto-Execution

Trades specified by the LLM execute automatically — no confirmation dialog. This is a deliberate design choice:
- It's a simulated environment with fake money, so the stakes are zero
- It creates an impressive, fluid demo experience
- It demonstrates agentic AI capabilities — the core theme of the course

If a trade fails validation (e.g., insufficient cash), the error is included in the chat response so the LLM can inform the user.

### System Prompt Guidance

The LLM should be prompted as "FinAlly, an AI trading assistant" with instructions to:
- Analyze portfolio composition, risk concentration, and P&L
- Suggest trades with reasoning
- Execute trades when the user asks or agrees
- Manage the watchlist proactively
- Be concise and data-driven in responses
- Always respond with valid structured JSON

### LLM Mock Mode

When `LLM_MOCK=true`, the backend returns deterministic mock responses instead of calling OpenRouter. This enables:
- Fast, free, reproducible E2E tests
- Development without an API key
- CI/CD pipelines

---

## 10. Frontend Design

### Layout

The frontend is a single-page application with a dense, terminal-inspired layout. The specific component architecture and layout system is up to the Frontend Engineer, but the UI should include these elements:

- **Watchlist panel** — grid/table of watched tickers with: ticker symbol, current price (flashing green/red on change), daily change %, and a sparkline mini-chart (accumulated from SSE since page load). **Daily change %** uses a session anchor: the baseline is the first price the backend observed for that ticker at process start (the cache's initial value). The anchor resets whenever the backend restarts. This is honest about the absence of a real market open/close in the simulator and avoids a scheduled-reset job.
- **Main chart area** — larger chart for the currently selected ticker, showing price over time. On selection, the frontend fetches `GET /api/prices/history/{ticker}?range=1h` (default) to populate history from the `price_ticks` table, then appends live ticks from the SSE stream. The user can switch the range to 6h / 24h / 7d. Clicking a ticker in the watchlist selects it here.
- **Portfolio heatmap** — treemap visualization where each rectangle is a position, sized by portfolio weight, colored by P&L (green = profit, red = loss)
- **P&L chart** — line chart showing total portfolio value over time, using data from `portfolio_snapshots`
- **Positions table** — tabular view of all positions: ticker, quantity, avg cost, current price, unrealized P&L, % change
- **Trade bar** — simple input area: ticker field, quantity field, buy button, sell button. Market orders, instant fill.
- **AI chat panel** — docked/collapsible sidebar. Message input, scrolling conversation history, loading indicator while waiting for LLM response. Trade executions and watchlist changes shown inline as confirmations.
- **Header** — portfolio total value (updating live), connection status indicator, cash balance

### Technical Notes

- Use `EventSource` for SSE connection to `/api/stream/prices`
- Canvas-based charting library preferred (Lightweight Charts or Recharts) for performance
- Price flash effect: on receiving a new price, briefly apply a CSS class with background color transition, then remove it
- All API calls go to the same origin (`/api/*`) — no CORS configuration needed
- Tailwind CSS for styling with a custom dark theme

---

## 11. Docker & Deployment

### Multi-Stage Dockerfile

```
Stage 1: Node 20 slim
  - Copy frontend/
  - npm install && npm run build (produces static export)

Stage 2: Python 3.12 slim
  - Install uv
  - Copy backend/
  - uv sync (install Python dependencies from lockfile)
  - Copy frontend build output into a static/ directory
  - Expose port 8000
  - CMD: uvicorn serving FastAPI app
```

FastAPI serves the static frontend files and all API routes on port 8000.

### Docker Volume

The SQLite database persists via a named Docker volume:

```bash
docker run -v finally-data:/app/db -p 8000:8000 --env-file .env finally
```

The `db/` directory in the project root maps to `/app/db` in the container. The backend writes `finally.db` to this path.

### Start/Stop Scripts

**`scripts/start_mac.sh`** (macOS/Linux):
- Builds the Docker image if not already built (or if `--build` flag passed)
- Runs the container with the volume mount, port mapping, and `.env` file
- Prints the URL to access the app
- Optionally opens the browser

**`scripts/stop_mac.sh`** (macOS/Linux):
- Stops and removes the running container
- Does NOT remove the volume (data persists)

**`scripts/start_windows.ps1`** / **`scripts/stop_windows.ps1`**: PowerShell equivalents for Windows.

All scripts should be idempotent — safe to run multiple times.

### Optional Cloud Deployment

The container is designed to deploy to AWS App Runner, Render, or any container platform. A Terraform configuration for App Runner may be provided in a `deploy/` directory as a stretch goal, but is not part of the core build.

---

## 12. Testing Strategy

### Unit Tests (within `frontend/` and `backend/`)

**Backend (pytest)**:
- Market data: simulator generates valid prices, GBM math is correct, Massive API response parsing works, both implementations conform to the abstract interface
- Portfolio: trade execution logic, P&L calculations, edge cases (selling more than owned, buying with insufficient cash, selling at a loss)
- LLM: structured output parsing handles all valid schemas, graceful handling of malformed responses, trade validation within chat flow
- API routes: correct status codes, response shapes, error handling

**Frontend (React Testing Library or similar)**:
- Component rendering with mock data
- Price flash animation triggers correctly on price changes
- Watchlist CRUD operations
- Portfolio display calculations
- Chat message rendering and loading state

### E2E Tests (in `test/`)

**Infrastructure**: A separate `docker-compose.test.yml` in `test/` that spins up the app container plus a Playwright container. This keeps browser dependencies out of the production image.

**Environment**: Tests run with `LLM_MOCK=true` by default for speed and determinism.

**Key Scenarios**:
- Fresh start: default watchlist appears, $10k balance shown, prices are streaming
- Add and remove a ticker from the watchlist
- Buy shares: cash decreases, position appears, portfolio updates
- Sell shares: cash increases, position updates or disappears
- Portfolio visualization: heatmap renders with correct colors, P&L chart has data points
- AI chat (mocked): send a message, receive a response, trade execution appears inline
- SSE resilience: disconnect and verify reconnection

---

## 13. Review Notes — Open Questions, Gaps, and Simplifications

This section captures questions, ambiguities, and simplification opportunities surfaced during a documentation review. It is a working list — items should be triaged (answered, deferred, or rejected) before the next agent picks up implementation.

### 13.1 Open Questions (need a decision before implementation)

1. **LLM conversation context window.** Section 9 says "loads recent conversation history" but never bounds it. Unbounded history grows token cost on every call. Specify a policy: last N messages (e.g., 20), last N tokens (e.g., 4k), or a summarization scheme.

2. **Price used for LLM-initiated trades.** When the LLM returns `trades: [{ticker, side, quantity}]`, what price fills the order? The latest in the price cache *at execution time*? The price snapshot loaded into the LLM's context? These can differ by several seconds. Recommendation: fill at latest-cache price, and include the actual fill price in the response so the chat panel can show it.

3. **Trade validation timing.** Section 9 says invalid trades cause an error "included in the chat response so the LLM can inform the user." But the LLM has already finished responding — there is no second pass. Clarify: the failed trade is appended to the `actions` array with an `error` field, and the chat UI surfaces it inline. The LLM's text won't mention the failure (it didn't know).

4. **Arbitrary watchlist tickers under the simulator.** Section 6 lists 10 seeded tickers with GBM params. If a user (or the LLM) adds `PYPL` via `POST /api/watchlist`, what does the simulator do? Options: (a) reject unknown tickers when in simulator mode, (b) auto-generate a seed price and default GBM params, (c) require a fixed allowlist. Pick one and document.

5. **Main chart history source.** The "Main chart area" (Section 10) shows "price over time" for the selected ticker. There is no DB table for tick history. Is this chart also accumulated from SSE since page load (like sparklines)? If so, it will be empty/short on a fresh load — state that explicitly. If not, specify the source.

6. **Database init point.** Section 7 says "on startup (or first request)" — pick one. FastAPI lifespan startup is reliable and runs once; first-request init forces a check in every handler and adds a cold-start penalty. Recommendation: lifespan startup only.

7. **Concurrent trade safety.** Single-user, but the UI's Buy button and an LLM auto-trade can fire near-simultaneously. Two read-modify-write paths on `cash_balance` and `positions` can race in Python before SQLite sees them. Specify: trades go through a single `asyncio.Lock` (or per-user lock keyed on `user_id`).

8. **Daily change % anchor.** Watchlist shows "daily change %" — what's the baseline? Simulator has no concept of "previous close." Options: (a) use the first price observed at process start, (b) reset at UTC midnight, (c) drop the column and rely on the sparkline + flash for movement signaling. (c) is the honest simplification.

9. **`quantity` as REAL in positions/trades.** Is fractional share trading intended? If only whole shares are supported, INTEGER would be more appropriate and avoids floating-point rounding issues in P&L calculations. If REAL is intentional, the trade validation section should mention whether fractional quantities are accepted.
   - **ANSWER:** Yes, fractional shares SHOULD be supported.

### 13.2 Inconsistencies & Gaps

1. **Directory structure is out of date with the implemented backend.** Section 4 describes `backend/db/` for schemas, but the actual layout (`backend/app/market/`) follows an `app/` package convention. Update the tree to reflect `backend/app/{market,db,api,llm}/...` (or whatever the agreed layout becomes) so future agents don't re-invent it.

2. **Cloud-deployment auth gap.** Section 11 mentions AWS App Runner / Render as stretch goals. With zero auth, any URL discovery = full trading access + LLM token spend on your key. Either call this out as "local-only — do not expose publicly" or specify a minimal auth shim (basic auth, a shared secret header) before any cloud target.

3. **`backend/db/` vs `db/` collision.** Section 4 has both — one is "schema definitions," the other is the runtime SQLite mount. Easy to confuse. Rename one (e.g., `backend/app/db/` for code; `data/` at root for the volume mount).

4. **Color scheme is decorative-only.** Section 2 lists Yellow/Blue/Purple but never says where they appear (buttons? accents? charts?). Either map each color to a UI role or drop the list.

5. **SSE cadence vs. Massive poll cadence.** Section 6 says SSE pushes "at a regular cadence (~500ms)" while Massive polls every 15s on the free tier. Pushing unchanged prices 30× per real update wastes bandwidth and forces redundant flash logic on the client. The implemented `PriceCache` already uses version-based change detection — surface this in the plan: **SSE pushes only when a price changes** (with a periodic keepalive comment for connection liveness).

6. **`actions` field semantics.** `chat_messages.actions` is described as "trades executed, watchlist changes made." Define the JSON shape: success vs. error per item, fill price, resulting cash balance, etc. Otherwise different agents will invent different shapes.

7. **`portfolio_snapshots` retention.** Recording every 30s for an always-on container = ~1M rows/year. Not catastrophic on SQLite but worth a sentence: "no retention policy in v1; if needed, downsample to 5-minute aggregates beyond 24h."

### 13.3 Simplification Opportunities

**IMPORTANT: Simplify LLM response flow: don't stream, just return.** The structured output requirement already means waiting for the full response. Instead of the complexity of streaming tokens while also parsing JSON, just return the complete response as a single JSON payload. The LLM call takes 1-3 seconds on Cerebras — fast enough that streaming adds complexity without meaningful UX improvement. Show a loading indicator instead.

`★ Insight ─────────────────────────────────────`
- The plan's biggest source of ambiguity is the **chat → trade execution boundary**: pricing, validation timing, error surfacing, and the `actions` JSON shape are all underspecified, and they're the contract between the LLM, the backend, and the chat UI. Nail that shape down before anyone writes the chat endpoint.
- Several "future-proofing" choices (UUID PKs on uniquely-keyed tables, `user_id` everywhere) cost very little but pay off only if multi-user actually ships. Worth being honest about which of these are genuine extensibility and which are speculative.
- SSE-on-change (not SSE-on-tick) is already how the market subsystem works, but the plan still describes the older "push every 500ms" model. Documenting the actual behavior closes a gap that would otherwise show up as redundant client-side animation logic.
`─────────────────────────────────────────────────`
