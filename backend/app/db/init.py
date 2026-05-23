"""Lazy database initialization.

Called once from the FastAPI lifespan startup hook (see planning/PLAN.md §7
"SQLite with Lazy Initialization"). Creates the schema and seeds default
data if missing. Idempotent — re-running against an existing database is a
cheap no-op because every DDL uses ``CREATE ... IF NOT EXISTS`` and every
seed uses ``INSERT OR IGNORE``.
"""

from __future__ import annotations

from pathlib import Path

from .conn import get_connection, resolve_db_path
from .seed import seed_default_data

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def _load_schema_sql() -> str:
    """Read the bundled ``schema.sql`` from disk."""
    return _SCHEMA_PATH.read_text(encoding="utf-8")


def init_database(db_path: Path | None = None) -> Path:
    """Initialize the SQLite database at ``db_path``.

    Resolution order for the path: explicit argument > ``FINALLY_DB_PATH`` env
    var > ``/app/db/finally.db``. The parent directory is created if missing.

    Steps:
        1. Ensure the parent directory exists.
        2. Open a connection and apply every statement from ``schema.sql``.
        3. Run :func:`seed_default_data` against the same connection.
        4. Commit and close the bootstrap connection.

    Returns the resolved database path so callers can log or assert on it.
    """
    resolved = resolve_db_path(db_path)
    resolved.parent.mkdir(parents=True, exist_ok=True)

    schema_sql = _load_schema_sql()
    conn = get_connection(resolved)
    try:
        conn.executescript(schema_sql)
        seed_default_data(conn)
        conn.commit()
    finally:
        conn.close()
    return resolved
