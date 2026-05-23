"""Market data routes.

- ``GET /api/stream/prices`` — SSE price stream. The actual generator lives
  in :mod:`app.market.stream` (frozen subsystem). API_CONTRACT.md §2.1 notes
  this emits a full ticker map per frame, not per-event objects — that
  divergence is intentional and matches the existing market subsystem.

- ``GET /api/prices/history/{ticker}`` — historical price ticks for the main
  chart, served from the ``price_ticks`` table written by the tick
  persister background task.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse

from app.api.deps import get_price_cache, normalize_ticker
from app.api.errors import APIError
from app.db import connection
from app.market.stream import _generate_events

router = APIRouter(tags=["market"])

# Allowed `range` values for /api/prices/history (API_CONTRACT.md §2.2)
RangeLiteral = Literal["1h", "6h", "24h", "7d"]
_RANGE_TO_DELTA: dict[str, timedelta] = {
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
}


@router.get("/stream/prices")
async def stream_prices(request: Request) -> StreamingResponse:
    """SSE stream of live price updates (push-on-change, with keepalives).

    Returns frames whose ``data:`` payload is a JSON object keyed by ticker
    symbol (each value is the full ``PriceUpdate.to_dict()`` — see
    API_CONTRACT.md §2.1).
    """
    price_cache = get_price_cache(request)
    return StreamingResponse(
        _generate_events(price_cache, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/prices/history/{ticker}")
async def prices_history(
    ticker: str,
    request: Request,
    range: Annotated[RangeLiteral, Query()] = "1h",
) -> dict:
    """Return persisted price ticks for ``ticker`` within ``range``.

    API_CONTRACT.md §2.2:
      - 404 ``unknown_ticker`` if the ticker is structurally valid but has no
        cached price (i.e. not produced by the active market source).
      - 422 ``invalid_ticker`` if the regex fails.
      - 422 ``validation_error`` if ``range`` is not one of the allowed values
        (FastAPI/Pydantic handles this automatically via the Literal type).
    """
    ticker_u = normalize_ticker(ticker)
    cache = get_price_cache(request)
    # 404 only when the ticker has no presence in the cache and no rows in
    # the table — otherwise an empty array is the correct response (a brand
    # new ticker that just hasn't been written to price_ticks yet).
    if cache.get(ticker_u) is None:
        # Still allow read-through when there ARE persisted rows — the
        # cache might have been cleared but historical data remains.
        with connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM price_ticks WHERE ticker = ? LIMIT 1", (ticker_u,)
            ).fetchone()
        if row is None:
            raise APIError(
                status_code=404,
                error="unknown_ticker",
                error_message=f"{ticker_u} is not currently tracked.",
            )

    delta = _RANGE_TO_DELTA[range]
    cutoff_iso = (datetime.now(timezone.utc) - delta).isoformat()
    with connection() as conn:
        rows = conn.execute(
            "SELECT recorded_at, price FROM price_ticks "
            "WHERE ticker = ? AND recorded_at >= ? "
            "ORDER BY recorded_at ASC",
            (ticker_u, cutoff_iso),
        ).fetchall()
    points = [{"ts": r["recorded_at"], "price": float(r["price"])} for r in rows]
    return {"ticker": ticker_u, "range": range, "points": points}
