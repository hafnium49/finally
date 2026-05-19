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


async def test_stream_prices_returns_event_stream_content_type(client, price_cache):
    """SSE endpoint should respond with text/event-stream and the retry hint.

    We make a streaming request and immediately close after the first chunk so
    we don't block on the generator's sleep loop.
    """
    price_cache.update("AAPL", 192.34)
    async with client.stream("GET", "/api/stream/prices") as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert response.headers.get("cache-control") == "no-cache"
        assert response.headers.get("x-accel-buffering") == "no"

        # Read one chunk to verify the retry hint shows up first
        chunk_iter = response.aiter_text()
        first = await chunk_iter.__anext__()
        # The retry hint plus the initial data frame may arrive together
        assert "retry:" in first or "retry:" in first[:64]
