"""SQLite persistence layer for FinAlly.

Public API:
    init_database     - Lazy schema + seed initializer (call from lifespan startup)
    get_connection    - Open a configured ``sqlite3.Connection`` (caller closes)
    connection        - Context-manager flavor of ``get_connection``
    resolve_db_path   - Resolve the DB path from env/arg/default
    seed_default_data - Insert default rows into an open connection
"""

from .conn import DEFAULT_DB_PATH, connection, get_connection, resolve_db_path
from .init import init_database
from .seed import (
    DEFAULT_CASH_BALANCE,
    DEFAULT_USER_ID,
    DEFAULT_WATCHLIST_TICKERS,
    seed_default_data,
)

__all__ = [
    "DEFAULT_CASH_BALANCE",
    "DEFAULT_DB_PATH",
    "DEFAULT_USER_ID",
    "DEFAULT_WATCHLIST_TICKERS",
    "connection",
    "get_connection",
    "init_database",
    "resolve_db_path",
    "seed_default_data",
]
