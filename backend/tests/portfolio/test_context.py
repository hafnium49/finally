"""Tests for ``app.portfolio.get_portfolio_context``.

Defect B017 regression: the chat handler needs a real portfolio + watchlist
snapshot to feed into the LLM prompt. Previously the symbol did not exist
and a defensive ``getattr`` silently produced an empty dict, so the model
answered "your portfolio is empty" even when positions existed.
"""

from __future__ import annotations

import asyncio
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.db import connection
from app.market import PriceCache
from app.portfolio import execute_trade, get_portfolio_context


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed_watchlist(db_path: Path, tickers: list[str]) -> None:
    """Insert a few watchlist rows so the context has something to render."""
    # tmp_db_path already seeds the default watchlist; we just append extras.
    with connection() as conn:
        existing = {row["ticker"] for row in conn.execute("SELECT ticker FROM watchlist")}
        for ticker in tickers:
            if ticker in existing:
                continue
            conn.execute(
                "INSERT INTO watchlist (id, user_id, ticker, added_at) "
                "VALUES (?, 'default', ?, ?)",
                (str(uuid.uuid4()), ticker, _utc_iso()),
            )


def test_get_portfolio_context_returns_full_snapshot(
    tmp_db_path: Path, price_cache: PriceCache
) -> None:
    """A user with a position + watchlist gets a fully-populated context dict."""
    # Seed prices so execute_trade has a fill price and the watchlist has live values.
    price_cache.update("AAPL", 190.00)
    price_cache.update("GOOGL", 175.00)
    price_cache.update("MSFT", 420.00)

    # Buy 5 AAPL via the real trade path so positions + cash are coherent.
    result = asyncio.run(execute_trade("AAPL", "buy", 5.0, price_cache))
    assert result.position_quantity == 5.0

    # Add an extra watchlist ticker beyond the seeded defaults.
    _seed_watchlist(tmp_db_path, ["PYPL"])
    price_cache.update("PYPL", 65.50)

    ctx = get_portfolio_context(price_cache)

    # Top-level keys present.
    assert set(ctx.keys()) == {
        "cash_balance",
        "total_value",
        "unrealized_pnl",
        "positions",
        "watchlist",
    }

    # Cash decreased by the fill cost; total_value approximately preserved.
    assert ctx["cash_balance"] == pytest.approx(10000.0 - 5 * 190.00)
    assert ctx["total_value"] == pytest.approx(10000.0, abs=1e-4)

    # The position is reflected with its current price + P&L fields.
    positions = ctx["positions"]
    assert len(positions) == 1
    aapl = positions[0]
    assert aapl["ticker"] == "AAPL"
    assert aapl["quantity"] == 5.0
    assert aapl["current_price"] == 190.00
    assert aapl["unrealized_pnl"] == pytest.approx(0.0)
    assert aapl["unrealized_pnl_pct"] == pytest.approx(0.0)

    # Watchlist contains AAPL (seeded default) + PYPL with live prices and change_pct.
    watch_by_ticker = {row["ticker"]: row for row in ctx["watchlist"]}
    assert "AAPL" in watch_by_ticker
    assert "PYPL" in watch_by_ticker
    assert watch_by_ticker["AAPL"]["price"] == 190.00
    assert watch_by_ticker["AAPL"]["change_pct"] == pytest.approx(0.0)
    assert watch_by_ticker["PYPL"]["price"] == 65.50
    assert watch_by_ticker["PYPL"]["change_pct"] == pytest.approx(0.0)


def test_get_portfolio_context_with_empty_db_still_returns_shape(
    tmp_db_path: Path, price_cache: PriceCache
) -> None:
    """Even with no positions and no live prices, the context dict has the right shape."""
    ctx = get_portfolio_context(price_cache)
    assert ctx["cash_balance"] == 10000.0
    assert ctx["total_value"] == 10000.0
    assert ctx["unrealized_pnl"] == 0.0
    assert ctx["positions"] == []
    # Default-seeded watchlist tickers are present but with price=None / change_pct=None
    # because the cache has never seen them.
    assert len(ctx["watchlist"]) == 10
    for row in ctx["watchlist"]:
        assert row["price"] is None
        assert row["change_pct"] is None


def test_get_portfolio_context_db_failure_returns_empty_dict(
    monkeypatch: pytest.MonkeyPatch, price_cache: PriceCache
) -> None:
    """If the DB can't be opened we return ``{}`` rather than crashing the chat path."""
    # Point at a path that doesn't exist (and don't init it) so the SELECT fails.
    monkeypatch.setenv("FINALLY_DB_PATH", "/tmp/does-not-exist-finally-test.db")

    def _broken_connect(*_args, **_kwargs) -> sqlite3.Connection:
        raise sqlite3.OperationalError("forced for test")

    monkeypatch.setattr("app.db.conn.sqlite3.connect", _broken_connect)

    ctx = get_portfolio_context(price_cache)
    assert ctx == {}
