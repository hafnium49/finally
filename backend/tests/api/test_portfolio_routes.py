"""Tests for the portfolio routes (API_CONTRACT.md §4)."""

from __future__ import annotations

import pytest


# ---------- GET /api/portfolio ----------


async def test_get_portfolio_default_is_cash_only(client):
    response = await client.get("/api/portfolio")
    assert response.status_code == 200
    body = response.json()
    assert body["cash_balance"] == 10000.0
    assert body["total_value"] == 10000.0
    assert body["unrealized_pnl"] == 0.0
    assert body["positions"] == []


async def test_get_portfolio_reflects_positions(client, price_cache):
    price_cache.update("AAPL", 100.0)
    # Buy 5 AAPL @ 100
    buy = await client.post(
        "/api/portfolio/trade",
        json={"ticker": "AAPL", "side": "buy", "quantity": 5},
    )
    assert buy.status_code == 201
    price_cache.update("AAPL", 110.0)  # Price moves up

    response = await client.get("/api/portfolio")
    body = response.json()
    assert body["cash_balance"] == 10000.0 - 500.0
    pos = body["positions"][0]
    assert pos["ticker"] == "AAPL"
    assert pos["quantity"] == 5
    assert pos["avg_cost"] == 100.0
    assert pos["current_price"] == 110.0
    assert pos["unrealized_pnl"] == 50.0  # (110 - 100) * 5
    assert pos["unrealized_pnl_pct"] == 10.0
    assert body["total_value"] == 9500.0 + 5 * 110.0
    assert body["unrealized_pnl"] == 50.0


async def test_get_portfolio_unpriced_position_has_null_pnl(client, price_cache):
    """A position whose ticker has no cached price gets null P&L fields."""
    price_cache.update("AAPL", 100.0)
    await client.post(
        "/api/portfolio/trade",
        json={"ticker": "AAPL", "side": "buy", "quantity": 1},
    )
    # Now drop the price from the cache (simulating restart / ticker removed)
    price_cache.remove("AAPL")

    response = await client.get("/api/portfolio")
    body = response.json()
    pos = body["positions"][0]
    assert pos["current_price"] is None
    assert pos["unrealized_pnl"] is None
    assert pos["unrealized_pnl_pct"] is None
    # The unpriced position contributes 0 to total_value, not None
    assert body["total_value"] == body["cash_balance"]


# ---------- POST /api/portfolio/trade ----------


async def test_post_trade_buy_success(client, price_cache):
    price_cache.update("AAPL", 192.34)
    response = await client.post(
        "/api/portfolio/trade",
        json={"ticker": "AAPL", "side": "buy", "quantity": 10},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["ticker"] == "AAPL"
    assert body["side"] == "buy"
    assert body["quantity"] == 10
    assert body["fill_price"] == 192.34
    assert body["cash_after"] == pytest.approx(10000.0 - 1923.4, rel=1e-6)
    assert body["position_after"]["quantity"] == 10
    assert body["position_after"]["avg_cost"] == 192.34
    assert "trade_id" in body


async def test_post_trade_sell_success(client, price_cache):
    """Sell after a buy — quantity & avg_cost go back to zero on full sell."""
    price_cache.update("AAPL", 100.0)
    await client.post(
        "/api/portfolio/trade",
        json={"ticker": "AAPL", "side": "buy", "quantity": 5},
    )
    price_cache.update("AAPL", 120.0)
    sell = await client.post(
        "/api/portfolio/trade",
        json={"ticker": "AAPL", "side": "sell", "quantity": 5},
    )
    assert sell.status_code == 201
    body = sell.json()
    assert body["fill_price"] == 120.0
    # Sold at 120 → cash up to 10000 - 500 + 600 = 10100
    assert body["cash_after"] == pytest.approx(10100.0, rel=1e-6)
    assert body["position_after"]["quantity"] == 0
    assert body["position_after"]["avg_cost"] == 0


async def test_post_trade_lowercase_ticker_normalized(client, price_cache):
    price_cache.update("AAPL", 50.0)
    response = await client.post(
        "/api/portfolio/trade",
        json={"ticker": "aapl", "side": "buy", "quantity": 1},
    )
    assert response.status_code == 201
    assert response.json()["ticker"] == "AAPL"


async def test_post_trade_unknown_ticker_returns_404(client):
    response = await client.post(
        "/api/portfolio/trade",
        json={"ticker": "ZZZZZ", "side": "buy", "quantity": 1},
    )
    assert response.status_code == 404
    assert response.json()["error"] == "unknown_ticker"


async def test_post_trade_insufficient_cash_returns_400(client, price_cache):
    price_cache.update("NVDA", 10000.0)
    response = await client.post(
        "/api/portfolio/trade",
        json={"ticker": "NVDA", "side": "buy", "quantity": 2},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "insufficient_cash"
    assert "$" in body["error_message"]


async def test_post_trade_insufficient_shares_returns_400(client, price_cache):
    price_cache.update("AAPL", 100.0)
    # Sell shares we don't own
    response = await client.post(
        "/api/portfolio/trade",
        json={"ticker": "AAPL", "side": "sell", "quantity": 5},
    )
    assert response.status_code == 400
    assert response.json()["error"] == "insufficient_shares"


async def test_post_trade_invalid_side_returns_422(client):
    response = await client.post(
        "/api/portfolio/trade",
        json={"ticker": "AAPL", "side": "hodl", "quantity": 1},
    )
    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


async def test_post_trade_zero_quantity_returns_422(client):
    response = await client.post(
        "/api/portfolio/trade",
        json={"ticker": "AAPL", "side": "buy", "quantity": 0},
    )
    assert response.status_code == 422


async def test_post_trade_invalid_ticker_returns_422(client):
    response = await client.post(
        "/api/portfolio/trade",
        json={"ticker": "TOOLONGGG", "side": "buy", "quantity": 1},
    )
    assert response.status_code == 422
    assert response.json()["error"] == "invalid_ticker"


async def test_post_trade_fractional_shares_allowed(client, price_cache):
    price_cache.update("AAPL", 100.0)
    response = await client.post(
        "/api/portfolio/trade",
        json={"ticker": "AAPL", "side": "buy", "quantity": 2.5},
    )
    assert response.status_code == 201
    assert response.json()["position_after"]["quantity"] == 2.5


# ---------- GET /api/portfolio/history ----------


async def test_get_history_empty_initially(client):
    response = await client.get("/api/portfolio/history")
    assert response.status_code == 200
    assert response.json()["range"] == "24h"
    assert response.json()["points"] == []


async def test_get_history_after_trade_has_points(client, price_cache):
    """Trading writes a snapshot; the history endpoint should return it."""
    price_cache.update("AAPL", 100.0)
    await client.post(
        "/api/portfolio/trade",
        json={"ticker": "AAPL", "side": "buy", "quantity": 1},
    )
    response = await client.get("/api/portfolio/history")
    body = response.json()
    assert body["range"] == "24h"
    assert len(body["points"]) >= 1
    point = body["points"][0]
    assert "ts" in point
    assert "total_value" in point


async def test_get_history_invalid_range_returns_422(client):
    response = await client.get("/api/portfolio/history?range=99h")
    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


async def test_get_history_accepts_all_valid_ranges(client):
    for r in ("1h", "6h", "24h", "7d"):
        response = await client.get(f"/api/portfolio/history?range={r}")
        assert response.status_code == 200, f"range={r} failed"
        assert response.json()["range"] == r
