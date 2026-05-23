"""Tests for ``app.portfolio.trade.execute_trade``.

These cover both the happy path and every typed exception in the contract,
plus the **race-condition test** the orchestrator specifically calls out:
two concurrent ``await execute_trade`` calls for the same user must not
double-spend cash.
"""

from __future__ import annotations

import asyncio

import pytest

from app.db import connection
from app.portfolio.trade import (
    InsufficientCashError,
    InsufficientSharesError,
    InvalidQuantityError,
    UnknownTickerError,
    _user_locks,
    execute_trade,
)


@pytest.fixture(autouse=True)
def _clear_user_locks():
    """Each test gets a fresh per-user lock map.

    The module-level ``_user_locks`` dict survives between tests; flushing it
    here keeps a Lock created in one event loop from being reused in
    another, which would otherwise blow up.
    """
    _user_locks.clear()
    yield
    _user_locks.clear()


async def test_buy_records_trade_and_updates_cash(tmp_db_path, price_cache):
    price_cache.update("AAPL", 100.0)
    result = await execute_trade("AAPL", "buy", 5, price_cache)
    assert result.ticker == "AAPL"
    assert result.side == "buy"
    assert result.quantity == 5
    assert result.fill_price == 100.0
    assert result.cash_after == pytest.approx(10000.0 - 500.0)
    assert result.position_quantity == 5
    assert result.position_avg_cost == 100.0

    with connection() as conn:
        row = conn.execute("SELECT cash_balance FROM users_profile").fetchone()
        assert row["cash_balance"] == pytest.approx(9500.0)
        pos = conn.execute(
            "SELECT quantity, avg_cost FROM positions WHERE ticker='AAPL'"
        ).fetchone()
        assert pos is not None
        assert pos["quantity"] == 5
        trades = conn.execute(
            "SELECT side, quantity, price FROM trades WHERE ticker='AAPL'"
        ).fetchall()
        assert len(trades) == 1
        assert trades[0]["side"] == "buy"


async def test_buy_then_sell_full_position(tmp_db_path, price_cache):
    price_cache.update("AAPL", 100.0)
    await execute_trade("AAPL", "buy", 5, price_cache)
    price_cache.update("AAPL", 120.0)
    result = await execute_trade("AAPL", "sell", 5, price_cache)
    assert result.fill_price == 120.0
    assert result.cash_after == pytest.approx(10000.0 - 500.0 + 600.0)
    assert result.position_quantity == 0.0
    assert result.position_avg_cost == 0.0
    with connection() as conn:
        pos = conn.execute(
            "SELECT * FROM positions WHERE ticker='AAPL'"
        ).fetchone()
        assert pos is None  # Full sell deletes the row


async def test_buy_weighted_avg_cost(tmp_db_path, price_cache):
    price_cache.update("AAPL", 100.0)
    await execute_trade("AAPL", "buy", 5, price_cache)
    price_cache.update("AAPL", 200.0)
    result = await execute_trade("AAPL", "buy", 5, price_cache)
    # Avg cost should be 150 after the second buy
    assert result.position_quantity == 10
    assert result.position_avg_cost == pytest.approx(150.0)


async def test_partial_sell_keeps_avg_cost(tmp_db_path, price_cache):
    price_cache.update("AAPL", 100.0)
    await execute_trade("AAPL", "buy", 10, price_cache)
    price_cache.update("AAPL", 80.0)
    result = await execute_trade("AAPL", "sell", 4, price_cache)
    assert result.position_quantity == 6
    assert result.position_avg_cost == pytest.approx(100.0)


async def test_unknown_ticker_raises(tmp_db_path, price_cache):
    with pytest.raises(UnknownTickerError):
        await execute_trade("ZZZZZ", "buy", 1, price_cache)


async def test_insufficient_cash_raises(tmp_db_path, price_cache):
    price_cache.update("NVDA", 5000.0)
    with pytest.raises(InsufficientCashError) as exc_info:
        await execute_trade("NVDA", "buy", 3, price_cache)  # 15k > 10k
    assert exc_info.value.need == pytest.approx(15000.0)
    assert exc_info.value.have == pytest.approx(10000.0)


async def test_insufficient_shares_raises(tmp_db_path, price_cache):
    price_cache.update("AAPL", 100.0)
    with pytest.raises(InsufficientSharesError) as exc_info:
        await execute_trade("AAPL", "sell", 5, price_cache)
    assert exc_info.value.ticker == "AAPL"
    assert exc_info.value.want == 5


async def test_zero_quantity_raises(tmp_db_path, price_cache):
    price_cache.update("AAPL", 100.0)
    with pytest.raises(InvalidQuantityError):
        await execute_trade("AAPL", "buy", 0, price_cache)


async def test_negative_quantity_raises(tmp_db_path, price_cache):
    price_cache.update("AAPL", 100.0)
    with pytest.raises(InvalidQuantityError):
        await execute_trade("AAPL", "buy", -1, price_cache)


async def test_fill_uses_latest_cache_price_not_stale(tmp_db_path, price_cache):
    """Drift between caller context and execution time: the cache always wins."""
    price_cache.update("AAPL", 100.0)
    # Now the price jumps before execute_trade runs
    price_cache.update("AAPL", 999.99)
    result = await execute_trade("AAPL", "buy", 1, price_cache)
    assert result.fill_price == 999.99


async def test_ticker_normalized_to_uppercase(tmp_db_path, price_cache):
    price_cache.update("AAPL", 100.0)
    result = await execute_trade("aapl", "buy", 1, price_cache)
    assert result.ticker == "AAPL"


# ---------------------------------------------------------------------------
# THE race-condition test the orchestrator specifically asked for.
# Two concurrent buys for the same user must not double-spend cash.
# ---------------------------------------------------------------------------


async def test_concurrent_buys_serialize_via_per_user_lock(tmp_db_path, price_cache):
    """Two simultaneous buys for the same user must produce a consistent ledger.

    Without the per-user ``asyncio.Lock`` both trades would read the same
    ``cash_balance`` snapshot and both succeed even when only one fits,
    over-drawing cash. With the lock, exactly one trade succeeds (or both,
    if both fit), and the final cash balance equals
    ``initial - (sum of successful trade values)``.
    """
    # Each trade costs 6000; we only have 10000, so exactly ONE must succeed.
    price_cache.update("AAPL", 6000.0)

    results = await asyncio.gather(
        execute_trade("AAPL", "buy", 1, price_cache),
        execute_trade("AAPL", "buy", 1, price_cache),
        return_exceptions=True,
    )

    successes = [r for r in results if not isinstance(r, Exception)]
    failures = [r for r in results if isinstance(r, Exception)]

    # Exactly one must succeed; the other must hit insufficient_cash.
    assert len(successes) == 1, f"Expected 1 success, got results={results}"
    assert len(failures) == 1
    assert isinstance(failures[0], InsufficientCashError)

    # Ledger consistency: cash + position market value should equal the
    # original 10000 (price hasn't changed).
    with connection() as conn:
        cash = conn.execute(
            "SELECT cash_balance FROM users_profile"
        ).fetchone()["cash_balance"]
        positions = conn.execute(
            "SELECT quantity FROM positions WHERE ticker = 'AAPL'"
        ).fetchone()
        trades = conn.execute(
            "SELECT COUNT(*) AS c FROM trades WHERE ticker = 'AAPL'"
        ).fetchone()["c"]
    assert cash == pytest.approx(10000.0 - 6000.0)
    assert positions["quantity"] == 1
    assert trades == 1  # Only the successful trade is recorded


async def test_concurrent_buys_both_fit_both_succeed(tmp_db_path, price_cache):
    """Sanity: when both trades fit, both succeed and ledger sums correctly."""
    price_cache.update("AAPL", 1000.0)

    results = await asyncio.gather(
        execute_trade("AAPL", "buy", 1, price_cache),
        execute_trade("AAPL", "buy", 1, price_cache),
    )
    assert all(r.position_quantity in (1.0, 2.0) for r in results)

    with connection() as conn:
        cash = conn.execute(
            "SELECT cash_balance FROM users_profile"
        ).fetchone()["cash_balance"]
        quantity = conn.execute(
            "SELECT quantity FROM positions WHERE ticker='AAPL'"
        ).fetchone()["quantity"]
        trades = conn.execute(
            "SELECT COUNT(*) AS c FROM trades WHERE ticker='AAPL'"
        ).fetchone()["c"]
    assert cash == pytest.approx(10000.0 - 2 * 1000.0)
    assert quantity == 2
    assert trades == 2
