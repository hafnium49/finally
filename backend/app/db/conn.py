"""SQLite connection helpers.

The database lives at a path resolved from the ``FINALLY_DB_PATH`` environment
variable (default ``/app/db/finally.db``). Both a plain function and a
contextmanager flavor are exposed so request handlers and background tasks can
pick whichever style they prefer.
"""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

DEFAULT_DB_PATH = Path("/app/db/finally.db")
"""Production default path; mounted as a Docker volume in production."""


def resolve_db_path(db_path: Path | None = None) -> Path:
    """Resolve which SQLite file to open.

    Precedence:
        1. Explicit ``db_path`` argument (caller knows best, e.g. tests).
        2. ``FINALLY_DB_PATH`` environment variable.
        3. :data:`DEFAULT_DB_PATH` (``/app/db/finally.db``).
    """
    if db_path is not None:
        return Path(db_path)
    env_path = os.environ.get("FINALLY_DB_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_DB_PATH


def _configure(conn: sqlite3.Connection) -> sqlite3.Connection:
    """Apply standard PRAGMAs and row factory to a fresh connection."""
    conn.row_factory = sqlite3.Row
    # Future-proof: we don't currently declare FKs but turning enforcement
    # on now means a later schema change can rely on it.
    conn.execute("PRAGMA foreign_keys = ON")
    # WAL improves concurrency between readers (SSE/portfolio snapshot writer)
    # and the writer (trade execution). Safe to re-set on every connection.
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Open a new SQLite connection with the project's standard settings.

    Callers are responsible for closing the connection (or using
    :func:`connection` for automatic cleanup).
    """
    path = resolve_db_path(db_path)
    conn = sqlite3.connect(str(path))
    return _configure(conn)


@contextmanager
def connection(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Context-manager flavor of :func:`get_connection`.

    Commits on clean exit, rolls back on exception, always closes.
    """
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
