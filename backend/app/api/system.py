"""System routes (health check)."""

from __future__ import annotations

import logging
import os
import sqlite3

from fastapi import APIRouter

from app.db import connection

logger = logging.getLogger(__name__)

router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict:
    """Liveness / readiness probe (API_CONTRACT.md §6.1).

    - ``db``: ``"ok"`` if the DB file responds to a trivial query;
      ``"missing"`` otherwise.
    - ``market``: ``"massive"`` if ``MASSIVE_API_KEY`` is set, else
      ``"simulator"``.
    """
    db_status = "ok"
    try:
        with connection() as conn:
            conn.execute("SELECT 1 FROM users_profile LIMIT 1").fetchone()
    except sqlite3.DatabaseError:
        db_status = "missing"
    except Exception:
        logger.exception("Unexpected error in /api/health DB check")
        db_status = "missing"

    market = "massive" if os.environ.get("MASSIVE_API_KEY", "").strip() else "simulator"
    return {"status": "ok", "db": db_status, "market": market}
