"""Tests for the market routes (API_CONTRACT.md §2)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.db import connection


# ---------- GET /api/prices/history/{ticker} ----------


async def test_prices_history_unknown_ticker_returns_404(client):
    """A ticker with no cache entry and no rows in price_ticks returns 404."""
    response = await client.get("/api/prices/history/ZZZZZ")
    assert response.status_code == 404
    assert response.json()["error"] == "unknown_ticker"


async def test_prices_history_invalid_ticker_returns_422(client):
    response = await client.get("/api/prices/history/TOOLONGTICKER")
    assert response.status_code == 422
    assert response.json()["error"] == "invalid_ticker"


async def test_prices_history_invalid_range_returns_422(client):
    response = await client.get("/api/prices/history/AAPL?range=99h")
    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


async def test_prices_history_empty_for_freshly_cached_ticker(client, price_cache):
    """Ticker is in the cache but no rows in price_ticks → empty points list."""
    price_cache.update("AAPL", 100.0)
    response = await client.get("/api/prices/history/AAPL")
    assert response.status_code == 200
    body = response.json()
    assert body["ticker"] == "AAPL"
    assert body["range"] == "1h"
    assert body["points"] == []


async def test_prices_history_returns_persisted_rows(client, price_cache):
    """Rows in price_ticks within the range should be returned chronologically."""
    price_cache.update("AAPL", 100.0)
    now = datetime.now(timezone.utc).isoformat()
    earlier = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    with connection() as conn:
        conn.executemany(
            "INSERT INTO price_ticks (ticker, price, recorded_at) VALUES (?, ?, ?)",
            [
                ("AAPL", 100.0, earlier),
                ("AAPL", 101.0, now),
            ],
        )
    response = await client.get("/api/prices/history/AAPL")
    body = response.json()
    assert len(body["points"]) == 2
    assert body["points"][0]["price"] == 100.0
    assert body["points"][1]["price"] == 101.0
    # Chronological order
    assert body["points"][0]["ts"] <= body["points"][1]["ts"]


async def test_prices_history_ticker_uppercased(client, price_cache):
    price_cache.update("AAPL", 100.0)
    response = await client.get("/api/prices/history/aapl")
    assert response.status_code == 200
    assert response.json()["ticker"] == "AAPL"


# ---------- GET /api/stream/prices ----------


async def test_stream_prices_returns_event_stream_content_type(app, price_cache):
    """SSE endpoint should respond with text/event-stream and the retry hint.

    httpx's ``ASGITransport`` buffers streaming responses end-to-end (it
    waits for the generator to complete before returning anything), so we
    can't drive an infinite SSE stream through it. Instead, drive the ASGI
    app directly: open the lifespan, send an HTTP scope, capture the first
    ``http.response.body`` event, then send a disconnect so the generator
    exits cleanly.
    """
    import asyncio as _asyncio

    price_cache.update("AAPL", 192.34)

    # Drive lifespan + request manually so we can read partial streamed output.
    lifespan_recv: _asyncio.Queue = _asyncio.Queue()
    lifespan_send: _asyncio.Queue = _asyncio.Queue()

    async def _lifespan_task() -> None:
        async def _recv():
            return await lifespan_recv.get()

        async def _send(msg):
            await lifespan_send.put(msg)

        await app({"type": "lifespan"}, _recv, _send)

    lt = _asyncio.create_task(_lifespan_task())
    await lifespan_recv.put({"type": "lifespan.startup"})
    msg = await lifespan_send.get()
    assert msg["type"] == "lifespan.startup.complete"

    request_recv: _asyncio.Queue = _asyncio.Queue()
    request_send: _asyncio.Queue = _asyncio.Queue()
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/api/stream/prices",
        "raw_path": b"/api/stream/prices",
        "query_string": b"",
        "headers": [(b"host", b"test")],
        "client": ("127.0.0.1", 12345),
        "server": ("test", 80),
        "root_path": "",
    }

    async def _drive_request():
        async def _recv():
            return await request_recv.get()

        async def _send(msg):
            await request_send.put(msg)

        try:
            await app(scope, _recv, _send)
        except _asyncio.CancelledError:
            pass

    rt = _asyncio.create_task(_drive_request())

    try:
        # Capture response start.
        start = await _asyncio.wait_for(request_send.get(), timeout=5.0)
        assert start["type"] == "http.response.start"
        assert start["status"] == 200
        headers = {k.decode(): v.decode() for k, v in start["headers"]}
        assert headers.get("content-type", "").startswith("text/event-stream")
        assert headers.get("cache-control") == "no-cache"
        assert headers.get("x-accel-buffering") == "no"

        # Capture first body chunk.
        body = await _asyncio.wait_for(request_send.get(), timeout=5.0)
        assert body["type"] == "http.response.body"
        assert b"retry:" in body["body"]
    finally:
        await request_recv.put({"type": "http.disconnect"})
        try:
            await _asyncio.wait_for(rt, timeout=2.0)
        except _asyncio.TimeoutError:
            rt.cancel()
            try:
                await rt
            except BaseException:
                pass
        # Tear down lifespan.
        await lifespan_recv.put({"type": "lifespan.shutdown"})
        try:
            await _asyncio.wait_for(lifespan_send.get(), timeout=2.0)
        except _asyncio.TimeoutError:
            pass
        if not lt.done():
            lt.cancel()
            try:
                await lt
            except BaseException:
                pass
