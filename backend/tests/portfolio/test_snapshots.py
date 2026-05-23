"""Tests for ``app.portfolio.snapshots`` and ``app.portfolio.tick_history``."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.db import connection
from app.portfolio.snapshots import snapshot_now
from app.portfolio.tick_history import prune_old_ticks, write_tick_snapshot


# ---------- snapshots ----------


def test_snapshot_now_writes_a_row(tmp_db_path, price_cache):
    price_cache.update("AAPL", 100.0)
    total = snapshot_now(price_cache)
    assert total == pytest.approx(10000.0)  # default cash, no positions
    with connection() as conn:
        rows = conn.execute(
            "SELECT total_value FROM portfolio_snapshots WHERE user_id='default'"
        ).fetchall()
    assert len(rows) == 1
    assert rows[0]["total_value"] == pytest.approx(10000.0)


def test_snapshot_now_includes_position_market_value(tmp_db_path, price_cache):
    """Snapshot total_value should reflect current price, not avg_cost."""
    price_cache.update("AAPL", 100.0)
    # Manually insert a position so we don't have to call execute_trade
    import uuid
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    with connection() as conn:
        conn.execute(
            "INSERT INTO positions (id, user_id, ticker, quantity, avg_cost, updated_at) "
            "VALUES (?, 'default', 'AAPL', 5, 90.0, ?)",
            (str(uuid.uuid4()), now),
        )
    price_cache.update("AAPL", 120.0)  # Price moves up after the position was created
    total = snapshot_now(price_cache)
    # Total = 10000 (cash) + 5 * 120 (current AAPL value) = 10600
    assert total == pytest.approx(10600.0)


# ---------- tick_history ----------


def test_write_tick_snapshot_inserts_one_row_per_cached_ticker(
    tmp_db_path, price_cache
):
    price_cache.update("AAPL", 100.0)
    price_cache.update("GOOGL", 175.0)
    count = write_tick_snapshot(price_cache)
    assert count == 2
    with connection() as conn:
        rows = conn.execute(
            "SELECT ticker, price FROM price_ticks ORDER BY ticker"
        ).fetchall()
    assert {r["ticker"] for r in rows} == {"AAPL", "GOOGL"}


def test_write_tick_snapshot_empty_cache_is_no_op(tmp_db_path, price_cache):
    count = write_tick_snapshot(price_cache)
    assert count == 0


def test_prune_old_ticks_deletes_only_old_rows(tmp_db_path, price_cache):
    old_ts = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    new_ts = datetime.now(timezone.utc).isoformat()
    with connection() as conn:
        conn.executemany(
            "INSERT INTO price_ticks (ticker, price, recorded_at) VALUES (?, ?, ?)",
            [
                ("AAPL", 100.0, old_ts),
                ("AAPL", 101.0, new_ts),
            ],
        )
    deleted = prune_old_ticks(retention_days=7)
    assert deleted == 1
    with connection() as conn:
        remaining = conn.execute(
            "SELECT recorded_at FROM price_ticks"
        ).fetchall()
    assert len(remaining) == 1
    assert remaining[0]["recorded_at"] == new_ts
