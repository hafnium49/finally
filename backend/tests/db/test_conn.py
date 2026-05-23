"""Tests for ``app.db.conn`` (connection helpers and PRAGMAs)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.db import (
    DEFAULT_DB_PATH,
    connection,
    get_connection,
    init_database,
    resolve_db_path,
)


class TestResolveDbPath:
    """Path resolution precedence: arg > env > default."""

    def test_explicit_arg_wins(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("FINALLY_DB_PATH", str(tmp_path / "env.db"))
        explicit = tmp_path / "explicit.db"
        assert resolve_db_path(explicit) == explicit

    def test_env_var_used_when_no_arg(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        target = tmp_path / "env.db"
        monkeypatch.setenv("FINALLY_DB_PATH", str(target))
        assert resolve_db_path() == target

    def test_default_when_no_arg_no_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("FINALLY_DB_PATH", raising=False)
        assert resolve_db_path() == DEFAULT_DB_PATH


class TestGetConnection:
    """``get_connection`` opens a configured SQLite connection."""

    def test_returns_sqlite_connection(self, tmp_db_path: Path) -> None:
        init_database(tmp_db_path)
        conn = get_connection(tmp_db_path)
        try:
            assert isinstance(conn, sqlite3.Connection)
        finally:
            conn.close()

    def test_row_factory_is_sqlite_row(self, tmp_db_path: Path) -> None:
        init_database(tmp_db_path)
        conn = get_connection(tmp_db_path)
        try:
            assert conn.row_factory is sqlite3.Row
            row = conn.execute("SELECT 1 AS one").fetchone()
            # Row supports both index and name access.
            assert row["one"] == 1
            assert row[0] == 1
        finally:
            conn.close()

    def test_journal_mode_is_wal(self, tmp_db_path: Path) -> None:
        init_database(tmp_db_path)
        conn = get_connection(tmp_db_path)
        try:
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            assert mode.lower() == "wal"
        finally:
            conn.close()

    def test_foreign_keys_pragma_enabled(self, tmp_db_path: Path) -> None:
        init_database(tmp_db_path)
        conn = get_connection(tmp_db_path)
        try:
            fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
            assert fk == 1
        finally:
            conn.close()


class TestConnectionContextManager:
    """``connection`` is a context-manager flavor of ``get_connection``."""

    def test_commits_on_clean_exit(self, tmp_db_path: Path) -> None:
        init_database(tmp_db_path)
        with connection(tmp_db_path) as conn:
            conn.execute(
                "INSERT INTO trades (id, user_id, ticker, side, quantity, "
                "price, executed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("t1", "default", "AAPL", "buy", 1.0, 190.0,
                 "2026-01-01T00:00:00+00:00"),
            )
        # Reopen and verify the row survived (proves commit happened).
        conn2 = get_connection(tmp_db_path)
        try:
            count = conn2.execute(
                "SELECT COUNT(*) AS c FROM trades WHERE id = 't1'"
            ).fetchone()["c"]
        finally:
            conn2.close()
        assert count == 1

    def test_rolls_back_on_exception(self, tmp_db_path: Path) -> None:
        init_database(tmp_db_path)

        class _BoomError(Exception):
            pass

        with pytest.raises(_BoomError):
            with connection(tmp_db_path) as conn:
                conn.execute(
                    "INSERT INTO trades (id, user_id, ticker, side, quantity, "
                    "price, executed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    ("t-bad", "default", "AAPL", "buy", 1.0, 190.0,
                     "2026-01-01T00:00:00+00:00"),
                )
                raise _BoomError()

        conn2 = get_connection(tmp_db_path)
        try:
            count = conn2.execute(
                "SELECT COUNT(*) AS c FROM trades WHERE id = 't-bad'"
            ).fetchone()["c"]
        finally:
            conn2.close()
        assert count == 0

    def test_closes_on_exit(self, tmp_db_path: Path) -> None:
        init_database(tmp_db_path)
        with connection(tmp_db_path) as conn:
            held = conn
        # After exit, the connection must be closed: any operation raises.
        with pytest.raises(sqlite3.ProgrammingError):
            held.execute("SELECT 1")
