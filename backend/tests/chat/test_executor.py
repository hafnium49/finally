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


# ---------------------------------------------------------------------------
# B006 regression: executor must forward price_cache into execute_trade
# ---------------------------------------------------------------------------


class TestPriceCacheWiring:
    """B006 regression suite.

    Before the fix, ``apply()`` called ``execute_trade(ticker=..., side=...,
    quantity=..., user_id=...)`` with no ``price_cache``, which raised
    ``TypeError`` and surfaced as HTTP 500 ``internal_error`` from
    ``/api/chat``. The executor must now forward the live cache so the
    real ``portfolio.execute_trade`` resolves a fill price at execution
    time (PLAN.md §9).
    """

    @pytest.mark.asyncio
    async def test_executor_uses_live_price_cache(self) -> None:
        """The cache passed to apply() must reach execute_trade and drive fill_price."""

        class StubPriceCache:
            def __init__(self, price: float) -> None:
                self._price = price

            def get_price(self, ticker: str) -> float:
                return self._price

        cache = StubPriceCache(price=205.55)
        seen_caches: list[Any] = []

        async def trade_fn(**kwargs: Any) -> dict[str, Any]:
            # B006: this kwarg MUST be present and must be the same
            # live cache object handed to apply() — not None, not a copy.
            assert "price_cache" in kwargs, (
                "B006 regression: apply() failed to forward price_cache "
                "into execute_trade"
            )
            seen_caches.append(kwargs["price_cache"])
            fill_price = kwargs["price_cache"].get_price(kwargs["ticker"])
            return {"fill_price": fill_price, "cash_after": 1000.0}

        parsed = LLMResponse(
            message="ok",
            trades=[LLMTrade(ticker="AAPL", side="buy", quantity=2)],
        )
        actions = await apply(parsed, price_cache=cache, trade_fn=trade_fn)

        assert seen_caches == [cache], "executor must pass through the live cache reference"
        assert len(actions) == 1
        assert actions[0].status == "ok"
        # Fill price comes from the cache at apply-time — not None, not stale.
        assert actions[0].fill_price == 205.55

    @pytest.mark.asyncio
    async def test_price_cache_omitted_when_none_for_test_stubs(self) -> None:
        """When no cache is passed, the trade_fn escape hatch still works.

        Existing tests inject a ``trade_fn`` that doesn't accept
        ``price_cache``. The signature change must remain backwards
        compatible with those tests.
        """
        observed: list[dict[str, Any]] = []

        async def trade_fn(**kwargs: Any) -> dict[str, Any]:
            observed.append(kwargs)
            return _ok_trade_result(100.0, 1000.0)

        parsed = LLMResponse(
            message="ok",
            trades=[LLMTrade(ticker="AAPL", side="buy", quantity=1)],
        )
        actions = await apply(parsed, trade_fn=trade_fn)
        assert actions[0].status == "ok"
        assert "price_cache" not in observed[0], (
            "When apply() is called without price_cache, it must NOT inject "
            "a None key — test stubs would reject that as an unexpected kwarg."
        )
