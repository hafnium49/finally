"""Persist tick history to ``price_ticks`` and prune old rows.

Two background tasks:

- :func:`tick_writer_loop` — every ``WRITE_INTERVAL_SECONDS`` (default ~5s),
  snapshot the current ``PriceCache`` and append a row per ticker.
- :func:`pruner_loop` — once a day, delete rows older than
  ``RETENTION_DAYS`` (default 7).

This module is the only persistence path for ``price_ticks``; the
``GET /api/prices/history/{ticker}`` route reads from the rows this writer
produces.
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from app.db import connection

if TYPE_CHECKING:
    from app.market import PriceCache

logger = logging.getLogger(__name__)

# PLAN.md §6 / §7: "every ~5 seconds per ticker"
WRITE_INTERVAL_SECONDS = 5.0

# PLAN.md §7: "Retention: last 7 days"
RETENTION_DAYS = 7

# Pruner cadence: once a day is plenty.
PRUNE_INTERVAL_SECONDS = 24 * 3600.0


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_tick_snapshot(price_cache: "PriceCache") -> int:
    """Append one row per ticker currently in the cache. Returns row count."""
    now = _utc_now_iso()
    rows = [
        (ticker, update.price, now)
        for ticker, update in price_cache.get_all().items()
    ]
    if not rows:
        return 0
    with connection() as conn:
        # INSERT OR IGNORE handles the (admittedly rare) collision on the
        # composite PRIMARY KEY (ticker, recorded_at) if the writer is
        # invoked twice within the same microsecond.
        conn.executemany(
            "INSERT OR IGNORE INTO price_ticks (ticker, price, recorded_at) "
            "VALUES (?, ?, ?)",
            rows,
        )
    return len(rows)


def prune_old_ticks(retention_days: int = RETENTION_DAYS) -> int:
    """Delete price_ticks rows older than ``retention_days``. Returns deleted count."""
    cutoff = (
        datetime.now(timezone.utc) - timedelta(days=retention_days)
    ).isoformat()
    with connection() as conn:
        cur = conn.execute(
            "DELETE FROM price_ticks WHERE recorded_at < ?", (cutoff,)
        )
        deleted = cur.rowcount
    return deleted if deleted is not None else 0


async def tick_writer_loop(
    price_cache: "PriceCache",
    interval: float = WRITE_INTERVAL_SECONDS,
) -> None:
    """Background task: write a tick snapshot every ``interval`` seconds."""
    logger.info("Tick writer loop started (interval=%.1fs)", interval)
    try:
        while True:
            await asyncio.sleep(interval)
            try:
                count = await asyncio.to_thread(write_tick_snapshot, price_cache)
                if count:
                    logger.debug("Wrote %d price_ticks rows", count)
            except Exception:
                logger.exception("Tick write failed; continuing")
    except asyncio.CancelledError:
        logger.info("Tick writer loop cancelled")
        raise


async def pruner_loop(
    interval: float = PRUNE_INTERVAL_SECONDS,
    retention_days: int = RETENTION_DAYS,
) -> None:
    """Background task: prune old ticks once a day."""
    logger.info(
        "Pruner loop started (interval=%.1fs, retention=%d days)",
        interval,
        retention_days,
    )
    try:
        while True:
            # Run once on startup as well (after a brief delay to let the
            # tick writer take precedence), then on each interval.
            await asyncio.sleep(interval)
            try:
                deleted = await asyncio.to_thread(prune_old_ticks, retention_days)
                logger.info("Pruner deleted %d old price_ticks rows", deleted)
            except Exception:
                logger.exception("Pruner failed; continuing")
    except asyncio.CancelledError:
        logger.info("Pruner loop cancelled")
        raise
