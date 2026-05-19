"""Portfolio snapshot writer.

Writes a row to ``portfolio_snapshots`` every 30 seconds (background task)
and immediately after each successful trade. Reads from the in-memory
``PriceCache`` plus the ``positions`` / ``users_profile`` tables.
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.db import connection
from app.portfolio.positions import compute_portfolio

if TYPE_CHECKING:
    from app.market import PriceCache

logger = logging.getLogger(__name__)

# Cadence per PLAN.md §7: "Recorded every 30 seconds by a background task".
SNAPSHOT_INTERVAL_SECONDS = 30.0


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def snapshot_now(price_cache: "PriceCache", user_id: str = "default") -> float:
    """Write a single portfolio_snapshots row and return the total_value.

    Pure write — no lock required. Concurrent writes may interleave but the
    schema is append-only and there are no per-row contention points.
    """
    with connection() as conn:
        cash_row = conn.execute(
            "SELECT cash_balance FROM users_profile WHERE id = ?",
            (user_id,),
        ).fetchone()
        cash = float(cash_row["cash_balance"]) if cash_row else 0.0
        pos_rows = conn.execute(
            "SELECT ticker, quantity, avg_cost FROM positions WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        positions = [dict(r) for r in pos_rows]
        portfolio = compute_portfolio(cash, positions, price_cache)
        total_value = portfolio["total_value"]
        conn.execute(
            "INSERT INTO portfolio_snapshots (id, user_id, total_value, recorded_at) "
            "VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), user_id, total_value, _utc_now_iso()),
        )
    return total_value


async def snapshot_loop(
    price_cache: "PriceCache",
    user_id: str = "default",
    interval: float = SNAPSHOT_INTERVAL_SECONDS,
) -> None:
    """Background task: sleep, then write a snapshot, forever.

    Cancellable; on ``CancelledError`` it exits cleanly so the FastAPI
    lifespan can tear it down on shutdown.
    """
    logger.info("Snapshot loop started (interval=%.1fs)", interval)
    try:
        while True:
            await asyncio.sleep(interval)
            try:
                await asyncio.to_thread(snapshot_now, price_cache, user_id)
            except Exception:
                logger.exception("Snapshot write failed; continuing")
    except asyncio.CancelledError:
        logger.info("Snapshot loop cancelled")
        raise
