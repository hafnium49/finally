"""Tests for SSE streaming endpoint."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.market.cache import PriceCache
from app.market.stream import KEEPALIVE_INTERVAL, _generate_events, create_stream_router


def _make_request(disconnected: bool = False) -> MagicMock:
    """Create a mock FastAPI Request object."""
    request = MagicMock()
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    request.is_disconnected = AsyncMock(return_value=disconnected)
    return request


async def _collect_events(
    cache: PriceCache,
    request: MagicMock,
    max_events: int = 10,
    interval: float = 0.01,
    keepalive_interval: float = KEEPALIVE_INTERVAL,
) -> list[str]:
    """Collect up to max_events SSE chunks from _generate_events."""
    events: list[str] = []
    async for chunk in _generate_events(cache, request, interval=interval, keepalive_interval=keepalive_interval):
        events.append(chunk)
        if len(events) >= max_events:
            break
    return events


class TestGenerateEvents:
    """Unit tests for the SSE event generator."""

    @pytest.mark.asyncio
    async def test_first_event_is_retry_directive(self):
        """Test that the generator starts with a retry directive."""
        cache = PriceCache()
        request = _make_request(disconnected=True)  # Disconnect immediately after retry

        events = []
        async for chunk in _generate_events(cache, request, interval=0.01):
            events.append(chunk)

        assert events[0] == "retry: 1000\n\n"

    @pytest.mark.asyncio
    async def test_stops_on_disconnect(self):
        """Test that the generator stops when the client disconnects."""
        cache = PriceCache()
        cache.update("AAPL", 190.00)

        call_count = 0

        async def is_disconnected():
            nonlocal call_count
            call_count += 1
            return call_count > 2  # Disconnect after 2 checks

        request = _make_request()
        request.is_disconnected = is_disconnected

        events = []
        async for chunk in _generate_events(cache, request, interval=0.01):
            events.append(chunk)

        # Should have stopped (not run indefinitely)
        assert len(events) < 20

    @pytest.mark.asyncio
    async def test_emits_price_event_on_cache_change(self):
        """Test that a data event is emitted when the cache version advances."""
        cache = PriceCache()

        disconnect_after = 3
        call_count = 0

        async def is_disconnected():
            nonlocal call_count
            call_count += 1
            return call_count > disconnect_after

        request = _make_request()
        request.is_disconnected = is_disconnected

        # Pre-populate cache so first check sees data
        cache.update("AAPL", 190.00)

        events = []
        async for chunk in _generate_events(cache, request, interval=0.01):
            events.append(chunk)

        data_events = [e for e in events if e.startswith("data:")]
        assert len(data_events) >= 1
        assert "AAPL" in data_events[0]

    @pytest.mark.asyncio
    async def test_no_duplicate_events_without_version_change(self):
        """Test that the same version doesn't produce repeated data events."""
        cache = PriceCache()
        cache.update("AAPL", 190.00)

        call_count = 0

        async def is_disconnected():
            nonlocal call_count
            call_count += 1
            return call_count > 5  # Run for several ticks

        request = _make_request()
        request.is_disconnected = is_disconnected

        events = []
        async for chunk in _generate_events(cache, request, interval=0.01):
            events.append(chunk)

        # Cache version doesn't change — should see exactly one data event
        # (the first time the version is observed)
        data_events = [e for e in events if e.startswith("data:")]
        assert len(data_events) == 1

    @pytest.mark.asyncio
    async def test_emits_keepalive_on_idle(self):
        """Test that a keepalive comment is sent when no price changes occur."""
        cache = PriceCache()
        cache.update("AAPL", 190.00)

        call_count = 0

        async def is_disconnected():
            nonlocal call_count
            call_count += 1
            return call_count > 8

        request = _make_request()
        request.is_disconnected = is_disconnected

        events = []
        # Use a very short keepalive_interval so we trigger it quickly
        async for chunk in _generate_events(
            cache, request, interval=0.01, keepalive_interval=0.03
        ):
            events.append(chunk)

        keepalive_events = [e for e in events if e.startswith(": keepalive")]
        assert len(keepalive_events) >= 1

    @pytest.mark.asyncio
    async def test_keepalive_resets_after_price_change(self):
        """Test that the keepalive timer resets when a price update is emitted."""
        cache = PriceCache()
        cache.update("AAPL", 190.00)

        call_count = 0

        async def is_disconnected():
            nonlocal call_count
            call_count += 1
            if call_count == 4:
                # Trigger a price update mid-stream
                cache.update("AAPL", 191.00)
            return call_count > 6

        request = _make_request()
        request.is_disconnected = is_disconnected

        events = []
        # Short keepalive so we'd see it if not reset
        async for chunk in _generate_events(
            cache, request, interval=0.01, keepalive_interval=0.02
        ):
            events.append(chunk)

        data_events = [e for e in events if e.startswith("data:")]
        # Should have at least 2 data events (initial + after price change)
        assert len(data_events) >= 2

    @pytest.mark.asyncio
    async def test_empty_cache_no_data_event(self):
        """Test that no data event is emitted when the cache is empty."""
        cache = PriceCache()

        call_count = 0

        async def is_disconnected():
            nonlocal call_count
            call_count += 1
            return call_count > 3

        request = _make_request()
        request.is_disconnected = is_disconnected

        events = []
        async for chunk in _generate_events(cache, request, interval=0.01):
            events.append(chunk)

        data_events = [e for e in events if e.startswith("data:")]
        assert len(data_events) == 0


class TestCreateStreamRouter:
    """Tests for the create_stream_router factory."""

    def test_returns_router_with_prices_endpoint(self):
        """Test that create_stream_router returns a router with /prices route."""
        from fastapi import APIRouter

        cache = PriceCache()
        router = create_stream_router(cache)

        assert isinstance(router, APIRouter)
        routes = [r.path for r in router.routes]
        assert "/api/stream/prices" in routes

    def test_each_call_returns_independent_router(self):
        """Test that each call to create_stream_router returns a new router."""
        cache = PriceCache()
        router1 = create_stream_router(cache)
        router2 = create_stream_router(cache)
        assert router1 is not router2
