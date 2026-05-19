"""Shared FastAPI dependencies + app-state accessors.

The market data subsystem lives at app-startup scope: one ``PriceCache`` and
one ``MarketDataSource`` per process. Routes pull them out of ``app.state``
via these dependency helpers so we don't sprinkle module-level globals
through the codebase.

Tests use these same accessors with a fixture-built FastAPI app.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from fastapi import Request

from app.api.errors import APIError

if TYPE_CHECKING:
    from app.market import MarketDataSource, PriceCache


# API_CONTRACT.md §1.4: tickers are 1-5 letters (case-insensitive in request,
# uppercase server-side). Punctuation, digits, and length > 5 are rejected.
TICKER_REGEX = re.compile(r"^[A-Za-z]{1,5}$")


def normalize_ticker(ticker: str) -> str:
    """Validate ticker against the regex and return its uppercased form.

    Raises :class:`APIError` (422 ``invalid_ticker``) on malformed input.
    """
    if not isinstance(ticker, str) or not TICKER_REGEX.match(ticker):
        raise APIError(
            status_code=422,
            error="invalid_ticker",
            error_message=f"{ticker!r} is not a valid ticker symbol.",
        )
    return ticker.upper()


def get_price_cache(request: Request) -> "PriceCache":
    """Return the process-wide ``PriceCache`` from app state."""
    cache = getattr(request.app.state, "price_cache", None)
    if cache is None:
        # Lifespan should always set this — if missing, fail loud rather
        # than silently returning None.
        raise APIError(
            status_code=500,
            error="internal_error",
            error_message="Price cache not initialized.",
        )
    return cache


def get_market_source(request: Request) -> "MarketDataSource":
    """Return the process-wide ``MarketDataSource`` from app state."""
    source = getattr(request.app.state, "market_source", None)
    if source is None:
        raise APIError(
            status_code=500,
            error="internal_error",
            error_message="Market source not initialized.",
        )
    return source
