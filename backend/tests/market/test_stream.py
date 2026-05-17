"""Tests for SSE streaming router and event generator."""

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI

from app.market.cache import PriceCache
from app.market.stream import _generate_events, create_stream_router

NEVER_DISCONNECT = 9999


def _make_request(disconnect_after: int = NEVER_DISCONNECT) -> MagicMock:
    """Build a fake FastAPI Request that disconnects after N calls to is_disconnected()."""
    calls = {"n": 0}

    async def is_disconnected() -> bool:
        calls["n"] += 1
        return calls["n"] > disconnect_after

    request = MagicMock()
    request.is_disconnected = is_disconnected
    request.client = MagicMock()
    request.client.host = "test-client"
    return request


async def _collect(
    gen: AsyncGenerator[str, None], max_items: int, timeout: float = 1.0
) -> list[str]:
    """Drain an async generator until it terminates or yields max_items."""
    out: list[str] = []
    for _ in range(max_items):
        try:
            chunk = await asyncio.wait_for(gen.__anext__(), timeout=timeout)
        except (StopAsyncIteration, asyncio.TimeoutError):
            break
        out.append(chunk)
    return out


class TestCreateStreamRouter:
    """Tests for the router factory itself."""

    def test_each_call_returns_independent_router(self):
        """B1: Two calls must return distinct routers bound to their own cache."""
        cache_a = PriceCache()
        cache_b = PriceCache()

        router_a = create_stream_router(cache_a)
        router_b = create_stream_router(cache_b)

        assert router_a is not router_b
        # Each router should have exactly one /prices route, not two from a singleton.
        paths_a = [r.path for r in router_a.routes]
        paths_b = [r.path for r in router_b.routes]
        assert paths_a == ["/api/stream/prices"]
        assert paths_b == ["/api/stream/prices"]

    def test_router_can_be_included_in_fastapi_app(self):
        """The router can be mounted on a FastAPI app without conflict."""
        cache = PriceCache()
        app = FastAPI()
        app.include_router(create_stream_router(cache))

        # The mounted app should have exactly one route at /api/stream/prices.
        sse_routes = [r for r in app.routes if getattr(r, "path", None) == "/api/stream/prices"]
        assert len(sse_routes) == 1

    def test_two_routers_can_be_mounted_independently(self):
        """B1 regression: distinct routers don't double-register or share state."""
        cache_a = PriceCache()
        cache_b = PriceCache()
        app_a = FastAPI()
        app_b = FastAPI()
        app_a.include_router(create_stream_router(cache_a))
        app_b.include_router(create_stream_router(cache_b))

        routes_a = [r for r in app_a.routes if getattr(r, "path", None) == "/api/stream/prices"]
        routes_b = [r for r in app_b.routes if getattr(r, "path", None) == "/api/stream/prices"]
        assert len(routes_a) == 1
        assert len(routes_b) == 1


@pytest.mark.asyncio
class TestGenerateEvents:
    """Tests for the SSE event generator."""

    async def test_emits_retry_directive_first(self):
        cache = PriceCache()
        request = _make_request(disconnect_after=0)  # disconnects on first check
        gen = _generate_events(cache, request, interval=0.01)

        chunks = await _collect(gen, max_items=5)
        assert chunks[0] == "retry: 1000\n\n"

    async def test_yields_data_when_version_advances(self):
        cache = PriceCache()
        cache.update("AAPL", 190.00)  # cache version is now 1
        request = _make_request(disconnect_after=2)
        gen = _generate_events(cache, request, interval=0.01)

        chunks = await _collect(gen, max_items=10)
        data_chunks = [c for c in chunks if c.startswith("data: ")]
        assert data_chunks, "expected at least one data frame"
        assert "AAPL" in data_chunks[0]

    async def test_does_not_yield_when_version_unchanged(self):
        """If the cache version never advances, no data frames are emitted."""
        cache = PriceCache()
        cache.update("AAPL", 190.00)
        request = _make_request(disconnect_after=5)
        gen = _generate_events(cache, request, interval=0.01, keepalive_seconds=60.0)

        chunks = await _collect(gen, max_items=20)
        data_chunks = [c for c in chunks if c.startswith("data: ")]
        # Exactly one data frame for the single version advance, then quiet.
        assert len(data_chunks) == 1

    async def test_emits_keepalive_after_idle(self):
        """PLAN.md §6: emit ': keepalive\\n\\n' after the configured idle window."""
        cache = PriceCache()
        cache.update("AAPL", 190.00)
        request = _make_request(disconnect_after=50)
        # 10 ms tick, 30 ms keepalive — keepalive should fire after ~3 idle ticks.
        gen = _generate_events(cache, request, interval=0.01, keepalive_seconds=0.03)

        chunks = await _collect(gen, max_items=30, timeout=2.0)
        keepalives = [c for c in chunks if c == ": keepalive\n\n"]
        assert keepalives, "expected at least one keepalive comment"

    async def test_exits_on_client_disconnect(self):
        cache = PriceCache()
        cache.update("AAPL", 190.00)
        request = _make_request(disconnect_after=1)
        gen = _generate_events(cache, request, interval=0.01)

        chunks = await _collect(gen, max_items=20)
        # The generator should terminate (collect stops early when StopAsyncIteration fires).
        # We can also verify by attempting another anext().
        with pytest.raises(StopAsyncIteration):
            await asyncio.wait_for(gen.__anext__(), timeout=0.5)
        # Sanity: at least the retry directive came through.
        assert chunks[0] == "retry: 1000\n\n"

    async def test_skips_data_frame_when_cache_empty(self):
        """No data frame is emitted while the cache is empty, but retry directive still fires."""
        cache = PriceCache()
        request = _make_request(disconnect_after=3)
        gen = _generate_events(cache, request, interval=0.01, keepalive_seconds=60.0)

        chunks = await _collect(gen, max_items=10)
        assert chunks[0] == "retry: 1000\n\n"
        data_chunks = [c for c in chunks if c.startswith("data: ")]
        assert data_chunks == []

    async def test_anonymous_client_logged_as_unknown(self):
        """When request.client is None, the generator still works."""
        cache = PriceCache()
        cache.update("AAPL", 190.00)

        calls = {"n": 0}

        async def is_disconnected() -> bool:
            calls["n"] += 1
            return calls["n"] > 1

        request = MagicMock()
        request.is_disconnected = is_disconnected
        request.client = None

        gen = _generate_events(cache, request, interval=0.01)
        chunks = await _collect(gen, max_items=5)
        assert chunks[0] == "retry: 1000\n\n"
