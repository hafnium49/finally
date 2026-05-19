"""Tests for the watchlist routes (API_CONTRACT.md §3)."""

from __future__ import annotations

import pytest


# ---------- GET /api/watchlist ----------


async def test_get_watchlist_returns_seeded_tickers(client):
    response = await client.get("/api/watchlist")
    assert response.status_code == 200
    body = response.json()
    tickers = [item["ticker"] for item in body["items"]]
    # Seeded by app.db.seed.DEFAULT_WATCHLIST_TICKERS
    assert "AAPL" in tickers
    assert "GOOGL" in tickers
    assert len(tickers) == 10


async def test_get_watchlist_unpriced_items_have_null_price(client):
    """A ticker with no cache entry returns null price/anchor/change_pct."""
    response = await client.get("/api/watchlist")
    body = response.json()
    # No prices pushed into the cache in this test → everything null
    for item in body["items"]:
        assert item["price"] is None
        assert item["session_anchor_price"] is None
        assert item["change_pct"] is None


async def test_get_watchlist_priced_item_computes_change_pct(client, price_cache):
    """When the cache has a price, change_pct is derived from the anchor."""
    price_cache.update("AAPL", 100.0)  # First update sets anchor=100
    price_cache.update("AAPL", 110.0)  # Now price=110, anchor=100
    response = await client.get("/api/watchlist")
    items = {item["ticker"]: item for item in response.json()["items"]}
    aapl = items["AAPL"]
    assert aapl["price"] == 110.0
    assert aapl["session_anchor_price"] == 100.0
    assert aapl["change_pct"] == 10.0


# ---------- POST /api/watchlist ----------


async def test_post_watchlist_creates_and_returns_item(client, stub_market_source):
    response = await client.post("/api/watchlist", json={"ticker": "pypl"})
    assert response.status_code == 201
    body = response.json()
    assert body["ticker"] == "PYPL"  # Uppercased server-side
    assert body["price"] is None
    assert "PYPL" in stub_market_source.added


async def test_post_watchlist_invalid_ticker_returns_422(client):
    response = await client.post("/api/watchlist", json={"ticker": "TOOLONGGG"})
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "invalid_ticker"
    assert "error_message" in body


async def test_post_watchlist_digit_in_ticker_rejected(client):
    response = await client.post("/api/watchlist", json={"ticker": "AB1"})
    assert response.status_code == 422
    assert response.json()["error"] == "invalid_ticker"


async def test_post_watchlist_missing_body_returns_422(client):
    response = await client.post("/api/watchlist", json={})
    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


async def test_post_watchlist_duplicate_returns_409(client):
    # AAPL is in the seeded watchlist already
    response = await client.post("/api/watchlist", json={"ticker": "AAPL"})
    assert response.status_code == 409
    assert response.json()["error"] == "ticker_already_in_watchlist"


# ---------- DELETE /api/watchlist/{ticker} ----------


async def test_delete_watchlist_removes_ticker(client, stub_market_source):
    response = await client.delete("/api/watchlist/AAPL")
    assert response.status_code == 204
    assert response.content == b""
    assert "AAPL" in stub_market_source.removed
    # Confirm it's gone from the list
    follow_up = await client.get("/api/watchlist")
    tickers = [item["ticker"] for item in follow_up.json()["items"]]
    assert "AAPL" not in tickers


async def test_delete_watchlist_unknown_ticker_returns_404(client):
    response = await client.delete("/api/watchlist/PYPL")
    assert response.status_code == 404
    assert response.json()["error"] == "unknown_ticker"


async def test_delete_watchlist_invalid_ticker_returns_422(client):
    response = await client.delete("/api/watchlist/TOOLONGTICKER")
    assert response.status_code == 422
    assert response.json()["error"] == "invalid_ticker"
