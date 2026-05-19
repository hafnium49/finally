"""Portfolio routes.

- ``GET /api/portfolio`` — current positions, cash balance, total value,
  unrealized P&L (API_CONTRACT.md §4.1).
- ``POST /api/portfolio/trade`` — execute a market order (API_CONTRACT.md
  §4.2). Always 201 on success; 400 / 404 / 422 envelope on failure.
- ``GET /api/portfolio/history`` — portfolio value snapshots over time
  (API_CONTRACT.md §4.3).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import get_price_cache, normalize_ticker
from app.api.errors import APIError
from app.db import connection
from app.portfolio import (
    InsufficientCashError,
    InsufficientSharesError,
    InvalidQuantityError,
    UnknownTickerError,
    current_portfolio,
    execute_trade,
    snapshot_now,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

RangeLiteral = Literal["1h", "6h", "24h", "7d"]
_RANGE_TO_DELTA: dict[str, timedelta] = {
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
}


class TradeBody(BaseModel):
    """Request body for ``POST /api/portfolio/trade``."""

    model_config = ConfigDict(extra="forbid")
    ticker: str = Field(..., min_length=1, max_length=8)
    side: Literal["buy", "sell"]
    quantity: float = Field(..., gt=0)


@router.get("")
async def get_portfolio(request: Request, user_id: str = "default") -> dict:
    """Return cash + positions + roll-up totals (API_CONTRACT.md §4.1)."""
    cache = get_price_cache(request)
    return current_portfolio(cache, user_id=user_id)


@router.post("/trade", status_code=status.HTTP_201_CREATED)
async def post_trade(
    body: TradeBody, request: Request, user_id: str = "default"
) -> dict:
    """Execute a market order at the latest cached price.

    All concrete error paths from ``portfolio.execute_trade`` are translated
    into the API_CONTRACT.md §1.2 envelope here.
    """
    ticker = normalize_ticker(body.ticker)
    cache = get_price_cache(request)

    try:
        result = await execute_trade(
            ticker=ticker,
            side=body.side,
            quantity=body.quantity,
            price_cache=cache,
            user_id=user_id,
        )
    except UnknownTickerError as e:
        raise APIError(
            status_code=404, error="unknown_ticker", error_message=str(e)
        ) from e
    except InsufficientCashError as e:
        raise APIError(
            status_code=400, error="insufficient_cash", error_message=str(e)
        ) from e
    except InsufficientSharesError as e:
        raise APIError(
            status_code=400, error="insufficient_shares", error_message=str(e)
        ) from e
    except InvalidQuantityError as e:
        raise APIError(
            status_code=422, error="invalid_quantity", error_message=str(e)
        ) from e

    # Fire a portfolio snapshot immediately after a successful trade
    # (PLAN.md §7: "immediately after each trade execution"). Best-effort —
    # don't fail the response if the snapshot write hiccups.
    try:
        import asyncio

        await asyncio.to_thread(snapshot_now, cache, user_id)
    except Exception:
        logger.exception("post-trade snapshot failed; trade itself succeeded")

    return {
        "trade_id": result.trade_id,
        "ticker": result.ticker,
        "side": result.side,
        "quantity": result.quantity,
        "fill_price": result.fill_price,
        "cash_after": round(result.cash_after, 4),
        "position_after": {
            "quantity": result.position_quantity,
            "avg_cost": round(result.position_avg_cost, 4),
        },
    }


@router.get("/history")
async def get_history(
    range: Annotated[RangeLiteral, Query()] = "24h",
    user_id: str = "default",
) -> dict:
    """Return ``portfolio_snapshots`` points within ``range`` (API_CONTRACT.md §4.3)."""
    delta = _RANGE_TO_DELTA[range]
    cutoff_iso = (datetime.now(timezone.utc) - delta).isoformat()
    with connection() as conn:
        rows = conn.execute(
            "SELECT recorded_at, total_value FROM portfolio_snapshots "
            "WHERE user_id = ? AND recorded_at >= ? "
            "ORDER BY recorded_at ASC",
            (user_id, cutoff_iso),
        ).fetchall()
    points = [
        {"ts": r["recorded_at"], "total_value": float(r["total_value"])}
        for r in rows
    ]
    return {"range": range, "points": points}
