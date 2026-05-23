"""Watchlist routes.

- ``GET /api/watchlist`` — list watched tickers hydrated with live price +
  session ``change_pct``.
- ``POST /api/watchlist`` — add a ticker (server-side uppercased, regex
  validated). Also calls ``market_source.add_ticker()`` so the simulator /
  Massive client starts producing ticks for it.
- ``DELETE /api/watchlist/{ticker}`` — remove a ticker.

Per API_CONTRACT.md §3 the ``change_pct`` field is computed server-side
from the ``PriceCache`` session anchor — never client-supplied.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Request, status
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import get_market_source, get_price_cache, normalize_ticker
from app.api.errors import APIError
from app.db import connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


class AddTickerBody(BaseModel):
    """Request body for ``POST /api/watchlist``.

    We do NOT enforce the 1-5 letter rule here at Pydantic level — the
    regex check in :func:`normalize_ticker` does, and it produces the
    contract-specified ``invalid_ticker`` error code (422). Pydantic-level
    length errors collapse to ``validation_error``, which is the wrong
    code for the ticker case.
    """

    model_config = ConfigDict(extra="forbid")
    ticker: str = Field(..., min_length=1)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_watchlist_item(ticker: str, price_cache) -> dict:
    """Build the response shape for a single watchlist row (API_CONTRACT §3.1)."""
    update = price_cache.get(ticker)
    price = update.price if update else None
    anchor = price_cache.get_session_anchor(ticker)
    if price is None or anchor is None:
        change_pct = None
    elif anchor == 0:
        change_pct = 0.0
    else:
        change_pct = round((price - anchor) / anchor * 100, 4)
    return {
        "ticker": ticker,
        "price": price,
        "session_anchor_price": anchor,
        "change_pct": change_pct,
    }


@router.get("")
async def list_watchlist(request: Request, user_id: str = "default") -> dict:
    """Return the user's watchlist with live pricing + change_pct."""
    cache = get_price_cache(request)
    with connection() as conn:
        rows = conn.execute(
            "SELECT ticker FROM watchlist WHERE user_id = ? "
            "ORDER BY added_at ASC, ticker ASC",
            (user_id,),
        ).fetchall()
    items = [_build_watchlist_item(row["ticker"], cache) for row in rows]
    return {"items": items}


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    body: AddTickerBody, request: Request, user_id: str = "default"
) -> dict:
    """Add ``body.ticker`` to the user's watchlist.

    409 ``ticker_already_in_watchlist`` if the row already exists.
    422 ``invalid_ticker`` if the structural regex fails.
    """
    ticker = normalize_ticker(body.ticker)

    with connection() as conn:
        existing = conn.execute(
            "SELECT 1 FROM watchlist WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        ).fetchone()
        if existing is not None:
            raise APIError(
                status_code=409,
                error="ticker_already_in_watchlist",
                error_message=f"{ticker} is already in your watchlist.",
            )
        conn.execute(
            "INSERT INTO watchlist (id, user_id, ticker, added_at) "
            "VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), user_id, ticker, _utc_now_iso()),
        )

    # Best-effort: ask the market source to start producing ticks. If this
    # fails (e.g., source not initialized in a test), we still return 201 —
    # the row exists in the DB and the next watchlist GET will reflect it.
    source = getattr(request.app.state, "market_source", None)
    if source is not None:
        try:
            await source.add_ticker(ticker)
        except Exception:
            logger.exception("market source add_ticker(%s) failed", ticker)

    cache = get_price_cache(request)
    return _build_watchlist_item(ticker, cache)


@router.delete("/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    ticker: str, request: Request, user_id: str = "default"
) -> Response:
    """Remove a ticker from the user's watchlist.

    404 ``unknown_ticker`` if the row does not exist.
    422 ``invalid_ticker`` if the regex fails.
    """
    ticker_u = normalize_ticker(ticker)

    with connection() as conn:
        cur = conn.execute(
            "DELETE FROM watchlist WHERE user_id = ? AND ticker = ?",
            (user_id, ticker_u),
        )
        deleted = cur.rowcount
    if not deleted:
        raise APIError(
            status_code=404,
            error="unknown_ticker",
            error_message=f"{ticker_u} is not in your watchlist.",
        )

    source = getattr(request.app.state, "market_source", None)
    if source is not None:
        try:
            await source.remove_ticker(ticker_u)
        except Exception:
            logger.exception("market source remove_ticker(%s) failed", ticker_u)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
