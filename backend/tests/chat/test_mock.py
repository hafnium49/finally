"""Tests for the deterministic mock-mode response table.

Every regex pattern from LLM_CONTRACT.md §4.2 has its own scenario, plus
the byte-stability invariant the Integration Tester relies on.
"""

from __future__ import annotations

import pytest

from app.chat.mock import respond


class TestRegexTable:
    def test_buy_integer_quantity(self) -> None:
        resp = respond("Buy 10 AAPL")
        assert resp.message == "Buying 10 AAPL."
        assert len(resp.trades) == 1
        assert resp.trades[0].ticker == "AAPL"
        assert resp.trades[0].side == "buy"
        assert resp.trades[0].quantity == 10.0
        assert resp.watchlist_changes == []

    def test_buy_fractional_quantity(self) -> None:
        resp = respond("buy 2.5 nvda")
        assert resp.message == "Buying 2.5 NVDA."
        assert resp.trades[0].quantity == 2.5
        assert resp.trades[0].ticker == "NVDA"

    def test_sell_integer_quantity(self) -> None:
        resp = respond("Sell 3 META")
        assert resp.message == "Selling 3 META."
        assert resp.trades[0].side == "sell"
        assert resp.trades[0].quantity == 3.0

    def test_sell_fractional_quantity(self) -> None:
        resp = respond("sell 2.5 nvda")
        assert resp.message == "Selling 2.5 NVDA."
        assert resp.trades[0].quantity == 2.5

    def test_add_to_watchlist_short_form(self) -> None:
        resp = respond("Add PYPL to watchlist")
        assert resp.message == "Adding PYPL to your watchlist."
        assert resp.trades == []
        assert resp.watchlist_changes[0].ticker == "PYPL"
        assert resp.watchlist_changes[0].action == "add"

    def test_add_to_watchlist_long_form(self) -> None:
        resp = respond("Add PYPL to my watchlist")
        assert resp.message == "Adding PYPL to your watchlist."
        assert resp.watchlist_changes[0].action == "add"

    def test_remove_ticker(self) -> None:
        resp = respond("Remove META")
        assert resp.message == "Removing META from your watchlist."
        assert resp.watchlist_changes[0].action == "remove"

    def test_what_is_my_portfolio(self) -> None:
        resp = respond("What's my portfolio?")
        assert "Mock portfolio summary" in resp.message
        assert resp.trades == []
        assert resp.watchlist_changes == []

    def test_tell_me_about_my_portfolio(self) -> None:
        resp = respond("Tell me about my portfolio")
        assert "Mock portfolio summary" in resp.message

    def test_greeting_hello(self) -> None:
        resp = respond("hello")
        assert "FinAlly" in resp.message
        assert resp.trades == []

    def test_greeting_hi(self) -> None:
        resp = respond("Hi there")
        assert "FinAlly" in resp.message

    def test_default_fallback(self) -> None:
        resp = respond("explain technical analysis")
        assert "Mock mode" in resp.message
        assert resp.trades == []
        assert resp.watchlist_changes == []


class TestDeterminism:
    @pytest.mark.parametrize(
        "user_text",
        [
            "Buy 10 AAPL",
            "sell 2.5 nvda",
            "Add PYPL to watchlist",
            "Remove META",
            "What's my portfolio?",
            "hello",
            "explain technical analysis",
        ],
    )
    def test_byte_stable_across_calls(self, user_text: str) -> None:
        first = respond(user_text).model_dump_json()
        second = respond(user_text).model_dump_json()
        third = respond(user_text).model_dump_json()
        assert first == second == third

    def test_no_portfolio_side_effects(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The mock must not depend on any global state or env vars."""
        # Toggle env vars to make sure the mock doesn't sneak a read.
        monkeypatch.setenv("LLM_MOCK", "true")
        first = respond("Buy 1 AAPL").model_dump_json()
        monkeypatch.setenv("LLM_MOCK", "false")
        second = respond("Buy 1 AAPL").model_dump_json()
        assert first == second
