"""Tests for ``app.db.init`` (schema application + seeding)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.db import (
    DEFAULT_CASH_BALANCE,
    DEFAULT_USER_ID,
    DEFAULT_WATCHLIST_TICKERS,
    get_connection,
    init_database,
    seed_default_data,
)

EXPECTED_TABLES = {
    "users_profile",
    "watchlist",
    "positions",
    "trades",
    "portfolio_snapshots",
    "price_ticks",
    "chat_messages",
    "chat_state",
}

EXPECTED_INDEXES = {
    "idx_price_ticks_recorded_at",
    "idx_portfolio_snapshots_user_recorded",
    "idx_chat_messages_user_created",
    "idx_trades_user_executed",
}


def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()
    return {row["name"] for row in rows}


def _index_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type = 'index' AND name NOT LIKE 'sqlite_autoindex_%'"
    ).fetchall()
    return {row["name"] for row in rows}


class TestInitDatabaseSchema:
    """Schema application: tables + indexes."""

    def test_creates_db_file(self, tmp_db_path: Path) -> None:
        assert not tmp_db_path.exists()
        init_database(tmp_db_path)
        assert tmp_db_path.exists()

    def test_creates_parent_directory(self, tmp_db_path: Path) -> None:
        assert not tmp_db_path.parent.exists()
        init_database(tmp_db_path)
        assert tmp_db_path.parent.is_dir()

    def test_returns_resolved_path(self, tmp_db_path: Path) -> None:
        resolved = init_database(tmp_db_path)
        assert resolved == tmp_db_path

    def test_all_expected_tables_exist(self, tmp_db_path: Path) -> None:
        init_database(tmp_db_path)
        conn = get_connection(tmp_db_path)
        try:
            assert EXPECTED_TABLES.issubset(_table_names(conn))
        finally:
            conn.close()

    def test_all_expected_indexes_exist(self, tmp_db_path: Path) -> None:
        init_database(tmp_db_path)
        conn = get_connection(tmp_db_path)
        try:
            assert EXPECTED_INDEXES.issubset(_index_names(conn))
        finally:
            conn.close()

    def test_init_is_idempotent(self, tmp_db_path: Path) -> None:
        """Reapplying the schema must not raise and must not duplicate rows."""
        init_database(tmp_db_path)
        init_database(tmp_db_path)
        init_database(tmp_db_path)

        conn = get_connection(tmp_db_path)
        try:
            assert EXPECTED_TABLES.issubset(_table_names(conn))
            assert EXPECTED_INDEXES.issubset(_index_names(conn))
            # Seed is still exactly the right size after three init runs.
            count = conn.execute(
                "SELECT COUNT(*) AS c FROM watchlist WHERE user_id = ?",
                (DEFAULT_USER_ID,),
            ).fetchone()["c"]
            assert count == len(DEFAULT_WATCHLIST_TICKERS)
        finally:
            conn.close()


class TestInitDatabaseSeed:
    """Default seed data: users_profile, chat_state, watchlist."""

    def test_seeds_default_user_profile(self, tmp_db_path: Path) -> None:
        init_database(tmp_db_path)
        conn = get_connection(tmp_db_path)
        try:
            row = conn.execute(
                "SELECT id, cash_balance, created_at FROM users_profile"
            ).fetchone()
        finally:
            conn.close()

        assert row is not None
        assert row["id"] == DEFAULT_USER_ID
        assert row["cash_balance"] == DEFAULT_CASH_BALANCE
        assert isinstance(row["created_at"], str) and row["created_at"]

    def test_seeds_chat_state_row(self, tmp_db_path: Path) -> None:
        init_database(tmp_db_path)
        conn = get_connection(tmp_db_path)
        try:
            row = conn.execute(
                "SELECT user_id, summary, updated_at FROM chat_state"
            ).fetchone()
        finally:
            conn.close()

        assert row is not None
        assert row["user_id"] == DEFAULT_USER_ID
        assert row["summary"] == ""
        assert row["updated_at"] is None

    def test_seeds_default_watchlist(self, tmp_db_path: Path) -> None:
        init_database(tmp_db_path)
        conn = get_connection(tmp_db_path)
        try:
            rows = conn.execute(
                "SELECT ticker FROM watchlist WHERE user_id = ? ORDER BY ticker",
                (DEFAULT_USER_ID,),
            ).fetchall()
        finally:
            conn.close()

        tickers = [row["ticker"] for row in rows]
        assert tickers == sorted(DEFAULT_WATCHLIST_TICKERS)

    def test_reseed_is_idempotent(self, tmp_db_path: Path) -> None:
        """Calling ``seed_default_data`` again must not duplicate rows."""
        init_database(tmp_db_path)
        conn = get_connection(tmp_db_path)
        try:
            seed_default_data(conn)
            conn.commit()
            user_count = conn.execute(
                "SELECT COUNT(*) AS c FROM users_profile"
            ).fetchone()["c"]
            chat_count = conn.execute(
                "SELECT COUNT(*) AS c FROM chat_state"
            ).fetchone()["c"]
            watchlist_count = conn.execute(
                "SELECT COUNT(*) AS c FROM watchlist"
            ).fetchone()["c"]
        finally:
            conn.close()

        assert user_count == 1
        assert chat_count == 1
        assert watchlist_count == len(DEFAULT_WATCHLIST_TICKERS)

    def test_empty_tables_start_empty(self, tmp_db_path: Path) -> None:
        """Tables that are not part of the seed must start empty."""
        init_database(tmp_db_path)
        conn = get_connection(tmp_db_path)
        try:
            for table in ("positions", "trades", "portfolio_snapshots",
                          "price_ticks", "chat_messages"):
                count = conn.execute(
                    f"SELECT COUNT(*) AS c FROM {table}"
                ).fetchone()["c"]
                assert count == 0, f"expected {table} to start empty"
        finally:
            conn.close()


class TestUniqueConstraints:
    """Unique constraints behave correctly under INSERT OR IGNORE."""

    def test_duplicate_watchlist_ticker_is_ignored(self, tmp_db_path: Path) -> None:
        """A second insert of the same (user_id, ticker) is silently ignored."""
        init_database(tmp_db_path)
        conn = get_connection(tmp_db_path)
        try:
            # AAPL is already seeded; attempting to re-add it must be ignored.
            conn.execute(
                "INSERT OR IGNORE INTO watchlist (id, user_id, ticker, added_at) "
                "VALUES (?, ?, ?, ?)",
                ("some-other-uuid", DEFAULT_USER_ID, "AAPL", "2026-01-01T00:00:00+00:00"),
            )
            conn.commit()
            count = conn.execute(
                "SELECT COUNT(*) AS c FROM watchlist WHERE ticker = 'AAPL'"
            ).fetchone()["c"]
        finally:
            conn.close()
        assert count == 1

    def test_duplicate_watchlist_ticker_without_ignore_raises(
        self, tmp_db_path: Path
    ) -> None:
        """Plain INSERT (no OR IGNORE) must surface the UNIQUE violation."""
        init_database(tmp_db_path)
        conn = get_connection(tmp_db_path)
        try:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO watchlist (id, user_id, ticker, added_at) "
                    "VALUES (?, ?, ?, ?)",
                    ("dup-uuid", DEFAULT_USER_ID, "AAPL", "2026-01-01T00:00:00+00:00"),
                )
        finally:
            conn.close()

    def test_trades_side_check_constraint(self, tmp_db_path: Path) -> None:
        """``side`` must be one of 'buy' or 'sell'."""
        init_database(tmp_db_path)
        conn = get_connection(tmp_db_path)
        try:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO trades (id, user_id, ticker, side, quantity, "
                    "price, executed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    ("trade-1", DEFAULT_USER_ID, "AAPL", "hold", 1.0, 100.0,
                     "2026-01-01T00:00:00+00:00"),
                )
        finally:
            conn.close()

    def test_chat_messages_role_check_constraint(self, tmp_db_path: Path) -> None:
        """``role`` must be one of 'user' or 'assistant'."""
        init_database(tmp_db_path)
        conn = get_connection(tmp_db_path)
        try:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO chat_messages (id, user_id, role, content, "
                    "actions, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    ("msg-1", DEFAULT_USER_ID, "system", "hi", None,
                     "2026-01-01T00:00:00+00:00"),
                )
        finally:
            conn.close()


class TestEnvironmentResolution:
    """The ``FINALLY_DB_PATH`` env var drives default resolution."""

    def test_env_var_is_honored(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        target = tmp_path / "from-env" / "finally.db"
        monkeypatch.setenv("FINALLY_DB_PATH", str(target))
        resolved = init_database()
        try:
            assert resolved == target
            assert target.exists()
        finally:
            monkeypatch.delenv("FINALLY_DB_PATH", raising=False)
