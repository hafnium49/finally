"""Seed default data into a freshly initialized database.

Every insert uses ``INSERT OR IGNORE`` so reseeding is a safe no-op once the
rows exist (see ``planning/SCHEMA.md`` §4).
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone

DEFAULT_USER_ID = "default"
"""Single-user mode: every row defaults to this user id."""

DEFAULT_CASH_BALANCE = 10000.0
"""Starting paper-trading cash balance (planning/PLAN.md §7)."""

DEFAULT_WATCHLIST_TICKERS: tuple[str, ...] = (
    "AAPL",
    "GOOGL",
    "MSFT",
    "AMZN",
    "TSLA",
    "NVDA",
    "META",
    "JPM",
    "V",
    "NFLX",
)
"""The 10 default watchlist tickers from planning/PLAN.md §7."""


def _utc_now_iso() -> str:
    """Return an ISO 8601 UTC timestamp (matches the rest of the codebase)."""
    return datetime.now(timezone.utc).isoformat()


def seed_default_data(conn: sqlite3.Connection) -> None:
    """Insert the default user, chat state, and watchlist rows.

    Idempotent: re-running against an already-seeded database is a no-op
    because every insert uses ``INSERT OR IGNORE`` and the natural unique
    keys (``users_profile.id``, ``chat_state.user_id``,
    ``watchlist.(user_id, ticker)``) already constrain duplicates.

    The caller owns the transaction; this function does not commit.
    """
    now = _utc_now_iso()

    # 4.1 Default user profile.
    conn.execute(
        "INSERT OR IGNORE INTO users_profile (id, cash_balance, created_at) "
        "VALUES (?, ?, ?)",
        (DEFAULT_USER_ID, DEFAULT_CASH_BALANCE, now),
    )

    # 4.2 Default chat state (empty rolling summary).
    conn.execute(
        "INSERT OR IGNORE INTO chat_state (user_id, summary, updated_at) "
        "VALUES (?, ?, ?)",
        (DEFAULT_USER_ID, "", None),
    )

    # 4.3 Default watchlist. UUIDs are fresh per insert; the
    # UNIQUE(user_id, ticker) constraint guarantees idempotency.
    conn.executemany(
        "INSERT OR IGNORE INTO watchlist (id, user_id, ticker, added_at) "
        "VALUES (?, ?, ?, ?)",
        [
            (uuid.uuid4().hex, DEFAULT_USER_ID, ticker, now)
            for ticker in DEFAULT_WATCHLIST_TICKERS
        ],
    )
