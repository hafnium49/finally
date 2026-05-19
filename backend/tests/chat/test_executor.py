"""Tests for app.chat.executor.

Stub out the portfolio + watchlist call paths via the ``trade_fn`` /
``watchlist_*_fn`` kwargs so this test does not require the (in-flight)
portfolio module.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.chat.executor import apply
from app.chat.schemas import LLMResponse, LLMTrade, LLMWatchlistChange


# ---------------------------------------------------------------------------
# Exception stand-ins
# ---------------------------------------------------------------------------


class InsufficientCashError(Exception):
    def __init__(self, need: float, have: float) -> None:
        super().__init__(f"need {need} have {have}")
        self.need = need
        self.have = have


class InsufficientSharesError(Exception):
    def __init__(self, ticker: str, have: float, want: float) -> None:
        super().__init__(f"{ticker}: have {have} want {want}")
        self.ticker = ticker
        self.have = have
        self.want = want


class UnknownTickerError(Exception):
    def __init__(self, ticker: str) -> None:
        super().__init__(ticker)
        self.ticker = ticker


class InvalidQuantityError(Exception):
    def __init__(self, quantity: float) -> None:
        super().__init__(str(quantity))
        self.quantity = quantity


class TickerAlreadyInWatchlistError(Exception):
    def __init__(self, ticker: str) -> None:
        super().__init__(ticker)
        self.ticker = ticker


class NotInWatchlistError(Exception):
    def __init__(self, ticker: str) -> None:
        super().__init__(ticker)
        self.ticker = ticker


class InvalidTickerError(Exception):
    def __init__(self, ticker: str) -> None:
        super().__init__(ticker)
        self.ticker = ticker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ok_trade_result(fill_price: float, cash_after: float) -> dict[str, Any]:
    return {"fill_price": fill_price, "cash_after": cash_after}


# ---------------------------------------------------------------------------
# Trade tests
# ---------------------------------------------------------------------------


class TestTradeExecution:
    @pytest.mark.asyncio
    async def test_single_buy_success(self) -> None:
        async def trade_fn(**kwargs: Any) -> dict[str, Any]:
            assert kwargs == {
                "ticker": "AAPL",
                "side": "buy",
                "quantity": 10.0,
                "user_id": "default",
            }
            return _ok_trade_result(192.34, 8076.60)

        parsed = LLMResponse(
            message="ok",
            trades=[LLMTrade(ticker="AAPL", side="buy", quantity=10)],
        )
        actions = await apply(parsed, trade_fn=trade_fn)
        assert len(actions) == 1
        assert actions[0].kind == "trade"
        assert actions[0].status == "ok"
        assert actions[0].fill_price == 192.34
        assert actions[0].cash_after == 8076.60

    @pytest.mark.asyncio
    async def test_insufficient_cash(self) -> None:
        async def trade_fn(**kwargs: Any) -> dict[str, Any]:
            raise InsufficientCashError(need=12400.0, have=8076.60)

        parsed = LLMResponse(
            message="ok",
            trades=[LLMTrade(ticker="TSLA", side="buy", quantity=50)],
        )
        actions = await apply(parsed, trade_fn=trade_fn)
        assert actions[0].status == "error"
        assert actions[0].error == "insufficient_cash"
        assert "12,400.00" in actions[0].error_message
        assert "8,076.60" in actions[0].error_message

    @pytest.mark.asyncio
    async def test_insufficient_shares(self) -> None:
        async def trade_fn(**kwargs: Any) -> dict[str, Any]:
            raise InsufficientSharesError(ticker="AAPL", have=2, want=10)

        parsed = LLMResponse(
            message="ok",
            trades=[LLMTrade(ticker="AAPL", side="sell", quantity=10)],
        )
        actions = await apply(parsed, trade_fn=trade_fn)
        assert actions[0].status == "error"
        assert actions[0].error == "insufficient_shares"
        assert "AAPL" in actions[0].error_message

    @pytest.mark.asyncio
    async def test_unknown_ticker(self) -> None:
        async def trade_fn(**kwargs: Any) -> dict[str, Any]:
            raise UnknownTickerError(ticker="ZZZZ")

        parsed = LLMResponse(
            message="ok",
            trades=[LLMTrade(ticker="ZZZZ", side="buy", quantity=1)],
        )
        actions = await apply(parsed, trade_fn=trade_fn)
        assert actions[0].status == "error"
        assert actions[0].error == "unknown_ticker"
        assert "ZZZZ" in actions[0].error_message

    @pytest.mark.asyncio
    async def test_invalid_quantity(self) -> None:
        async def trade_fn(**kwargs: Any) -> dict[str, Any]:
            raise InvalidQuantityError(quantity=-3)

        # Note: pydantic gt=0 would normally catch -3 at parse time. We
        # construct the LLMResponse manually to bypass that and exercise the
        # executor path.
        parsed = LLMResponse(
            message="ok",
            trades=[LLMTrade(ticker="AAPL", side="buy", quantity=1)],
        )
        actions = await apply(parsed, trade_fn=trade_fn)
        assert actions[0].status == "error"
        assert actions[0].error == "invalid_quantity"

    @pytest.mark.asyncio
    async def test_unknown_exception_reraised(self) -> None:
        async def trade_fn(**kwargs: Any) -> dict[str, Any]:
            raise RuntimeError("backend on fire")

        parsed = LLMResponse(
            message="ok",
            trades=[LLMTrade(ticker="AAPL", side="buy", quantity=1)],
        )
        with pytest.raises(RuntimeError, match="backend on fire"):
            await apply(parsed, trade_fn=trade_fn)

    @pytest.mark.asyncio
    async def test_sync_trade_fn_supported(self) -> None:
        def trade_fn(**kwargs: Any) -> dict[str, Any]:
            return _ok_trade_result(100.0, 9000.0)

        parsed = LLMResponse(
            message="ok",
            trades=[LLMTrade(ticker="AAPL", side="buy", quantity=1)],
        )
        actions = await apply(parsed, trade_fn=trade_fn)
        assert actions[0].status == "ok"

    @pytest.mark.asyncio
    async def test_multi_trade_order_preserved(self) -> None:
        calls: list[tuple[str, str]] = []

        async def trade_fn(**kwargs: Any) -> dict[str, Any]:
            calls.append((kwargs["ticker"], kwargs["side"]))
            if kwargs["ticker"] == "TSLA":
                raise InsufficientCashError(need=999.0, have=10.0)
            return _ok_trade_result(100.0, 1000.0)

        parsed = LLMResponse(
            message="ok",
            trades=[
                LLMTrade(ticker="TSLA", side="buy", quantity=5),
                LLMTrade(ticker="AAPL", side="buy", quantity=10),
            ],
        )
        actions = await apply(parsed, trade_fn=trade_fn)
        assert calls == [("TSLA", "buy"), ("AAPL", "buy")]
        assert actions[0].status == "error"
        assert actions[1].status == "ok"


# ---------------------------------------------------------------------------
# Watchlist tests
# ---------------------------------------------------------------------------


class TestWatchlistExecution:
    @pytest.mark.asyncio
    async def test_add_success(self) -> None:
        calls: list[str] = []

        async def add_fn(**kwargs: Any) -> None:
            calls.append(kwargs["ticker"])

        async def remove_fn(**kwargs: Any) -> None:
            raise AssertionError("remove should not be called")

        parsed = LLMResponse(
            message="ok",
            watchlist_changes=[LLMWatchlistChange(ticker="PYPL", action="add")],
        )
        actions = await apply(
            parsed, watchlist_add_fn=add_fn, watchlist_remove_fn=remove_fn
        )
        assert calls == ["PYPL"]
        assert actions[0].kind == "watchlist"
        assert actions[0].status == "ok"
        assert actions[0].action == "add"

    @pytest.mark.asyncio
    async def test_remove_success(self) -> None:
        async def add_fn(**kwargs: Any) -> None:
            raise AssertionError("add should not be called")

        async def remove_fn(**kwargs: Any) -> None:
            return None

        parsed = LLMResponse(
            message="ok",
            watchlist_changes=[LLMWatchlistChange(ticker="META", action="remove")],
        )
        actions = await apply(
            parsed, watchlist_add_fn=add_fn, watchlist_remove_fn=remove_fn
        )
        assert actions[0].status == "ok"
        assert actions[0].action == "remove"

    @pytest.mark.asyncio
    async def test_ticker_already_in_watchlist(self) -> None:
        async def add_fn(**kwargs: Any) -> None:
            raise TickerAlreadyInWatchlistError(ticker="AAPL")

        parsed = LLMResponse(
            message="ok",
            watchlist_changes=[LLMWatchlistChange(ticker="AAPL", action="add")],
        )
        actions = await apply(
            parsed,
            watchlist_add_fn=add_fn,
            watchlist_remove_fn=lambda **_: None,
        )
        assert actions[0].status == "error"
        assert actions[0].error == "ticker_already_in_watchlist"

    @pytest.mark.asyncio
    async def test_not_in_watchlist(self) -> None:
        async def remove_fn(**kwargs: Any) -> None:
            raise NotInWatchlistError(ticker="META")

        parsed = LLMResponse(
            message="ok",
            watchlist_changes=[LLMWatchlistChange(ticker="META", action="remove")],
        )
        actions = await apply(
            parsed,
            watchlist_add_fn=lambda **_: None,
            watchlist_remove_fn=remove_fn,
        )
        assert actions[0].status == "error"
        assert actions[0].error == "not_in_watchlist"

    @pytest.mark.asyncio
    async def test_invalid_ticker(self) -> None:
        async def add_fn(**kwargs: Any) -> None:
            raise InvalidTickerError(ticker="XX1")

        parsed = LLMResponse(
            message="ok",
            watchlist_changes=[LLMWatchlistChange(ticker="XXAAA", action="add")],
        )
        actions = await apply(
            parsed,
            watchlist_add_fn=add_fn,
            watchlist_remove_fn=lambda **_: None,
        )
        assert actions[0].status == "error"
        assert actions[0].error == "invalid_ticker"


# ---------------------------------------------------------------------------
# Ordering across trade + watchlist
# ---------------------------------------------------------------------------


class TestOrdering:
    @pytest.mark.asyncio
    async def test_trades_first_then_watchlist(self) -> None:
        async def trade_fn(**kwargs: Any) -> dict[str, Any]:
            return _ok_trade_result(100.0, 1000.0)

        async def add_fn(**kwargs: Any) -> None:
            return None

        parsed = LLMResponse(
            message="ok",
            trades=[LLMTrade(ticker="AAPL", side="buy", quantity=1)],
            watchlist_changes=[LLMWatchlistChange(ticker="PYPL", action="add")],
        )
        actions = await apply(
            parsed,
            trade_fn=trade_fn,
            watchlist_add_fn=add_fn,
            watchlist_remove_fn=lambda **_: None,
        )
        assert [a.kind for a in actions] == ["trade", "watchlist"]
