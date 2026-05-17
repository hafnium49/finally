"""SSE streaming endpoint for live price updates."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from .cache import PriceCache

logger = logging.getLogger(__name__)

# PLAN.md §6: keep idle SSE connections open through proxies.
DEFAULT_KEEPALIVE_SECONDS = 15.0


def create_stream_router(price_cache: PriceCache) -> APIRouter:
    """Create an SSE streaming router bound to the given PriceCache.

    A fresh APIRouter is created on every call so multiple FastAPI apps
    (or tests) can each get their own routes with their own cache reference.
    """
    router = APIRouter(prefix="/api/stream", tags=["streaming"])

    @router.get("/prices")
    async def stream_prices(request: Request) -> StreamingResponse:
        """SSE endpoint for live price updates.

        Wakes every ~500 ms and yields the full price map if the cache
        version has advanced; otherwise emits a periodic keepalive comment
        so proxies don't close idle connections. Clients connect via
        EventSource and receive events in the format:

            data: {"AAPL": {"ticker": "AAPL", "price": 190.50, ...}, ...}
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
    keepalive_seconds: float = DEFAULT_KEEPALIVE_SECONDS,
) -> AsyncGenerator[str, None]:
    """Async generator that yields SSE-formatted price events.

    Pushes the full price map only when the cache version advances
    (push-on-change). After `keepalive_seconds` of idle, emits an SSE
    comment line so intermediaries (nginx, App Runner, Cloudflare) don't
    close the connection. Exits when the client disconnects.
    """
    # Tell the client to retry after 1 second if the connection drops
    yield "retry: 1000\n\n"

    last_version = -1
    last_yield_at = time.monotonic()
    client_ip = request.client.host if request.client else "unknown"
    logger.info("SSE client connected: %s", client_ip)

    try:
        while True:
            if await request.is_disconnected():
                logger.info("SSE client disconnected: %s", client_ip)
                break

            current_version = price_cache.version
            now = time.monotonic()

            if current_version != last_version:
                last_version = current_version
                prices = price_cache.get_all()
                if prices:
                    data = {ticker: update.to_dict() for ticker, update in prices.items()}
                    payload = json.dumps(data)
                    yield f"data: {payload}\n\n"
                    last_yield_at = now
            elif now - last_yield_at >= keepalive_seconds:
                yield ": keepalive\n\n"
                last_yield_at = now

            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logger.info("SSE stream cancelled for: %s", client_ip)
        raise
