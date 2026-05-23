"""Tests for pure position math (``app.portfolio.positions``)."""

from __future__ import annotations

import pytest

from app.market import PriceCache
from app.portfolio.positions import (
    compute_portfolio,
    position_unrealized,
    update_position_buy,
    update_position_sell,
)


class TestUpdatePositionBuy:
    def test_new_position_avg_cost_is_buy_price(self):
        qty, avg = update_position_buy(0.0, 0.0, 10.0, 100.0)
        assert qty == 10.0
        assert avg == 100.0

    def test_accumulating_position_weights_avg_cost(self):
        # Existing: 10 @ 100; buy 10 @ 200 → avg = (10*100 + 10*200) / 20 = 150
        qty, avg = update_position_buy(10.0, 100.0, 10.0, 200.0)
        assert qty == 20.0
        assert avg == pytest.approx(150.0)

    def test_fractional_shares(self):
        qty, avg = update_position_buy(2.5, 100.0, 2.5, 120.0)
        assert qty == 5.0
        assert avg == pytest.approx(110.0)


class TestUpdatePositionSell:
    def test_partial_sell_leaves_avg_cost_unchanged(self):
        qty, avg = update_position_sell(10.0, 100.0, 4.0)
        assert qty == 6.0
        assert avg == 100.0

    def test_full_sell_zeros_both(self):
        qty, avg = update_position_sell(10.0, 100.0, 10.0)
        assert qty == 0.0
        assert avg == 0.0

    def test_oversell_returns_zero_zero(self):
        # Trade-level validation guards against this; the math fn is defensive.
        qty, avg = update_position_sell(5.0, 100.0, 10.0)
        assert qty == 0.0
        assert avg == 0.0


class TestPositionUnrealized:
    def test_null_price_returns_none_pair(self):
        assert position_unrealized(10.0, 100.0, None) == (None, None)

    def test_profitable_position(self):
        pnl, pct = position_unrealized(10.0, 100.0, 110.0)
        assert pnl == pytest.approx(100.0)
        assert pct == pytest.approx(10.0)

    def test_losing_position(self):
        pnl, pct = position_unrealized(10.0, 100.0, 90.0)
        assert pnl == pytest.approx(-100.0)
        assert pct == pytest.approx(-10.0)

    def test_zero_avg_cost_yields_zero_pct(self):
        # Degenerate but defensive.
        pnl, pct = position_unrealized(1.0, 0.0, 5.0)
        assert pnl == pytest.approx(5.0)
        assert pct == 0.0


class TestComputePortfolio:
    def test_cash_only(self):
        cache = PriceCache()
        result = compute_portfolio(10000.0, [], cache)
        assert result["cash_balance"] == 10000.0
        assert result["total_value"] == 10000.0
        assert result["unrealized_pnl"] == 0.0
        assert result["positions"] == []

    def test_mixed_priced_and_unpriced(self):
        cache = PriceCache()
        cache.update("AAPL", 110.0)  # AAPL is priced
        # GOOGL is NOT in the cache → null price, contributes 0 to totals
        positions = [
            {"ticker": "AAPL", "quantity": 5, "avg_cost": 100.0},
            {"ticker": "GOOGL", "quantity": 2, "avg_cost": 50.0},
        ]
        result = compute_portfolio(1000.0, positions, cache)
        # AAPL P&L: (110 - 100) * 5 = 50
        assert result["unrealized_pnl"] == pytest.approx(50.0)
        # total_value = cash + AAPL position value (GOOGL contributes 0)
        assert result["total_value"] == pytest.approx(1000.0 + 5 * 110.0)

        aapl = next(p for p in result["positions"] if p["ticker"] == "AAPL")
        googl = next(p for p in result["positions"] if p["ticker"] == "GOOGL")
        assert aapl["current_price"] == 110.0
        assert aapl["unrealized_pnl"] == pytest.approx(50.0)
        assert googl["current_price"] is None
        assert googl["unrealized_pnl"] is None
        assert googl["unrealized_pnl_pct"] is None
