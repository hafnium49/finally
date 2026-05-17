"""SSE streaming endpoint for live price updates."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from .cache import PriceCache

logger = logging.getLogger(__name__)

KEEPALIVE_INTERVAL = 15.0  # seconds between keepalive comments when no price changes


def create_stream_router(price_cache: PriceCache) -> APIRouter:
    """Create the SSE streaming router with a reference to the price cache.

    This factory pattern lets us inject the PriceCache without globals.
    Returns a new APIRouter each call so the function is safe to call once.
    """
    router = APIRouter(prefix="/api/stream", tags=["streaming"])

    @router.get("/prices")
    async def stream_prices(request: Request) -> StreamingResponse:
        """SSE endpoint for live price updates.

        Pushes price data only when the PriceCache version advances (push-on-change,
        not push-on-tick). A keepalive comment is sent every ~15s on idle connections
        to prevent proxies and load balancers from closing the connection.

        Client connects with EventSource; receives events in the format:

            data: {"AAPL": {"ticker": "AAPL", "price": 190.50, ...}, ...}

        Includes a retry directive so the browser auto-reconnects on disconnection.
        """
        return StreamingResponse(
            _generate_events(price_cache, request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering if proxied
            },
        )

    return router


async def _generate_events(
    price_cache: PriceCache,
    request: Request,
    interval: float = 0.5,
    keepalive_interval: float = KEEPALIVE_INTERVAL,
) -> AsyncGenerator[str, None]:
    """Async generator that yields SSE-formatted price events.

    Push-on-change: emits a data event only when the cache version advances.
    Keepalive: emits an SSE comment every ~keepalive_interval seconds when
    no price changes occur, preventing proxies from closing idle connections.
    Stops when the client disconnects (detected via request.is_disconnected()).
    """
    # Tell the client to retry after 1 second if the connection drops
    yield "retry: 1000\n\n"

    last_version = -1
    last_keepalive = asyncio.get_running_loop().time()
    client_ip = request.client.host if request.client else "unknown"
    logger.info("SSE client connected: %s", client_ip)

    try:
        while True:
            # Check for client disconnect
            if await request.is_disconnected():
                logger.info("SSE client disconnected: %s", client_ip)
                break

            current_version = price_cache.version
            now = asyncio.get_running_loop().time()

            if current_version != last_version:
                last_version = current_version
                last_keepalive = now
                prices = price_cache.get_all()

                if prices:
                    data = {ticker: update.to_dict() for ticker, update in prices.items()}
                    payload = json.dumps(data)
                    yield f"data: {payload}\n\n"
            elif now - last_keepalive >= keepalive_interval:
                # No price changes; send a keepalive comment to prevent proxy timeouts
                last_keepalive = now
                yield ": keepalive\n\n"

            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logger.info("SSE stream cancelled for: %s", client_ip)
