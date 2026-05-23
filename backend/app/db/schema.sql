-- FinAlly database schema (canonical, see planning/SCHEMA.md §1 + §2).
-- Every statement uses IF NOT EXISTS so init_database() is idempotent.

-- 1.1 users_profile
CREATE TABLE IF NOT EXISTS users_profile (
    id           TEXT PRIMARY KEY DEFAULT 'default',
    cash_balance REAL NOT NULL DEFAULT 10000.0,
    created_at   TEXT NOT NULL
);

-- 1.2 watchlist
CREATE TABLE IF NOT EXISTS watchlist (
    id       TEXT PRIMARY KEY,
    user_id  TEXT NOT NULL DEFAULT 'default',
    ticker   TEXT NOT NULL,
    added_at TEXT NOT NULL,
    UNIQUE (user_id, ticker)
);

-- 1.3 positions
CREATE TABLE IF NOT EXISTS positions (
    id         TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL DEFAULT 'default',
    ticker     TEXT NOT NULL,
    quantity   REAL NOT NULL,
    avg_cost   REAL NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (user_id, ticker)
);

-- 1.4 trades
CREATE TABLE IF NOT EXISTS trades (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL DEFAULT 'default',
    ticker      TEXT NOT NULL,
    side        TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
    quantity    REAL NOT NULL,
    price       REAL NOT NULL,
    executed_at TEXT NOT NULL
);

-- 1.5 portfolio_snapshots
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL DEFAULT 'default',
    total_value REAL NOT NULL,
    recorded_at TEXT NOT NULL
);

-- 1.6 price_ticks
CREATE TABLE IF NOT EXISTS price_ticks (
    ticker      TEXT NOT NULL,
    price       REAL NOT NULL,
    recorded_at TEXT NOT NULL,
    PRIMARY KEY (ticker, recorded_at)
);

-- 1.7 chat_messages
CREATE TABLE IF NOT EXISTS chat_messages (
    id         TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL DEFAULT 'default',
    role       TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content    TEXT NOT NULL,
    actions    TEXT,
    created_at TEXT NOT NULL
);

-- 1.8 chat_state
CREATE TABLE IF NOT EXISTS chat_state (
    user_id    TEXT PRIMARY KEY DEFAULT 'default',
    summary    TEXT NOT NULL DEFAULT '',
    updated_at TEXT
);

-- 2. Indexes
CREATE INDEX IF NOT EXISTS idx_price_ticks_recorded_at
    ON price_ticks(recorded_at);

CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_user_recorded
    ON portfolio_snapshots(user_id, recorded_at);

CREATE INDEX IF NOT EXISTS idx_chat_messages_user_created
    ON chat_messages(user_id, created_at);

CREATE INDEX IF NOT EXISTS idx_trades_user_executed
    ON trades(user_id, executed_at);
