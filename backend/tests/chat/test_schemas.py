"""Round-trip tests for the chat Pydantic models."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from app.chat.schemas import (
    ChatResponse,
    LLMResponse,
    LLMTrade,
    LLMWatchlistChange,
    TradeActionError,
    TradeActionOk,
    WatchlistActionError,
    WatchlistActionOk,
)


class TestLLMResponse:
    def test_minimal_message_only(self) -> None:
        resp = LLMResponse(message="hello")
        dumped = json.loads(resp.model_dump_json())
        assert dumped == {
            "message": "hello",
            "trades": [],
            "watchlist_changes": [],
        }

    def test_trades_and_watchlist(self) -> None:
        resp = LLMResponse(
            message="ok",
            trades=[LLMTrade(ticker="aapl", side="buy", quantity=10)],
            watchlist_changes=[LLMWatchlistChange(ticker="pypl", action="add")],
        )
        # ticker fields auto-uppercase
        assert resp.trades[0].ticker == "AAPL"
        assert resp.watchlist_changes[0].ticker == "PYPL"

        # round-trip via JSON
        again = LLMResponse.model_validate_json(resp.model_dump_json())
        assert again == resp

    def test_quantity_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            LLMTrade(ticker="AAPL", side="buy", quantity=0)
        with pytest.raises(ValidationError):
            LLMTrade(ticker="AAPL", side="buy", quantity=-1)

    def test_extra_keys_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            LLMResponse.model_validate({"message": "x", "bogus": True})

    def test_message_must_be_nonempty(self) -> None:
        with pytest.raises(ValidationError):
            LLMResponse(message="")

    def test_invalid_side_rejected(self) -> None:
        with pytest.raises(ValidationError):
            LLMTrade(ticker="AAPL", side="long", quantity=1)  # type: ignore[arg-type]


class TestChatActions:
    def test_trade_ok_round_trip(self) -> None:
        action = TradeActionOk(
            ticker="AAPL",
            side="buy",
            quantity=10,
            fill_price=192.34,
            cash_after=8076.60,
        )
        dumped = action.model_dump()
        assert dumped["kind"] == "trade"
        assert dumped["status"] == "ok"
        assert dumped["fill_price"] == 192.34
        assert dumped["cash_after"] == 8076.60

    def test_trade_error_round_trip(self) -> None:
        action = TradeActionError(
            ticker="TSLA",
            side="buy",
            quantity=50,
            error="insufficient_cash",
            error_message="Need $12,400.00 but only $8,076.60 available.",
        )
        dumped = action.model_dump()
        assert dumped["kind"] == "trade"
        assert dumped["status"] == "error"
        assert dumped["error"] == "insufficient_cash"

    def test_watchlist_ok_round_trip(self) -> None:
        action = WatchlistActionOk(ticker="PYPL", action="add")
        assert action.model_dump()["status"] == "ok"
        assert action.model_dump()["action"] == "add"

    def test_watchlist_error_round_trip(self) -> None:
        action = WatchlistActionError(
            ticker="PYPL",
            action="add",
            error="ticker_already_in_watchlist",
            error_message="PYPL is already in your watchlist.",
        )
        assert action.model_dump()["status"] == "error"


class TestChatResponse:
    def test_actions_defaults_to_empty_list_not_none(self) -> None:
        resp = ChatResponse(message="hi")
        assert resp.actions == []
        # serialized form is also an empty list, never null
        payload = json.loads(resp.model_dump_json())
        assert payload["actions"] == []
        assert "actions" in payload  # field always present

    def test_full_response_round_trip(self) -> None:
        resp = ChatResponse(
            message="Buying 10 AAPL and adding PYPL.",
            actions=[
                TradeActionOk(
                    ticker="AAPL",
                    side="buy",
                    quantity=10,
                    fill_price=192.34,
                    cash_after=8076.60,
                ),
                WatchlistActionOk(ticker="PYPL", action="add"),
            ],
        )
        again = ChatResponse.model_validate_json(resp.model_dump_json())
        assert len(again.actions) == 2
        assert again.actions[0].kind == "trade"  # type: ignore[union-attr]
        assert again.actions[1].kind == "watchlist"  # type: ignore[union-attr]
