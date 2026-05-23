"""Executor: turn parsed LLM output into resolved actions.

Walks the trades + watchlist_changes on the parsed :class:`LLMResponse`,
calls into ``app.portfolio.execute_trade()`` and the watchlist helpers,
and packages per-call exceptions into ``status="error"`` ``ChatAction``
entries per LLM_CONTRACT.md §6.

The portfolio and watchlist modules may not yet be wired up when this
module is imported (other subagents are building them in parallel).
Imports are lazy and exception types are looked up by attribute name to
keep the chat package independently testable.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional

from .schemas import (
    ChatAction,
    LLMResponse,
    LLMTrade,
    LLMWatchlistChange,
    TradeActionError,
    TradeActionOk,
    WatchlistActionError,
    WatchlistActionOk,
)


# ---------------------------------------------------------------------------
# Exception <-> error-code mapping
# ---------------------------------------------------------------------------

# Trade exceptions: maps the class *name* (defensive against the portfolio
# module not yet being importable) to (error_code, message_builder).
_TRADE_ERROR_MAP: dict[str, tuple[str, Callable[[Exception], str]]] = {
    "InsufficientCashError": (
        "insufficient_cash",
        lambda exc: _trade_message_insufficient_cash(exc),
    ),
    "InsufficientSharesError": (
        "insufficient_shares",
        lambda exc: _trade_message_insufficient_shares(exc),
    ),
    "UnknownTickerError": (
        "unknown_ticker",
        lambda exc: _trade_message_unknown_ticker(exc),
    ),
    "InvalidQuantityError": (
        "invalid_quantity",
        lambda exc: _trade_message_invalid_quantity(exc),
    ),
}

_WATCHLIST_ERROR_MAP: dict[str, tuple[str, Callable[[Exception, str], str]]] = {
    "TickerAlreadyInWatchlistError": (
        "ticker_already_in_watchlist",
        lambda exc, ticker: f"{ticker} is already in your watchlist.",
    ),
    "NotInWatchlistError": (
        "not_in_watchlist",
        lambda exc, ticker: f"{ticker} is not in your watchlist.",
    ),
    "InvalidTickerError": (
        "invalid_ticker",
        lambda exc, ticker: f"{ticker} is not a valid ticker symbol.",
    ),
}


def _attr(exc: Exception, name: str, default: Any = None) -> Any:
    return getattr(exc, name, default)


def _trade_message_insufficient_cash(exc: Exception) -> str:
    need = _attr(exc, "need")
    have = _attr(exc, "have")
    if isinstance(need, (int, float)) and isinstance(have, (int, float)):
        return f"Need ${need:,.2f} but only ${have:,.2f} available."
    return str(exc) or "Insufficient cash for this trade."


def _trade_message_insufficient_shares(exc: Exception) -> str:
    ticker = _attr(exc, "ticker")
    have = _attr(exc, "have")
    want = _attr(exc, "want")
    if ticker is not None and have is not None and want is not None:
        return f"You hold {have} shares of {ticker}, can't sell {want}."
    return str(exc) or "Insufficient shares to sell."


def _trade_message_unknown_ticker(exc: Exception) -> str:
    ticker = _attr(exc, "ticker")
    if ticker:
        return f"{ticker} not recognized."
    return str(exc) or "Unknown ticker."


def _trade_message_invalid_quantity(exc: Exception) -> str:
    quantity = _attr(exc, "quantity")
    if quantity is not None:
        return f"Quantity must be positive; got {quantity}."
    return str(exc) or "Invalid quantity."


# ---------------------------------------------------------------------------
# Lazy lookups for the underlying portfolio / watchlist call paths
# ---------------------------------------------------------------------------


def _load_trade_callable() -> Callable[..., Any]:
    """Return ``app.portfolio.execute_trade`` (lazy import)."""
    from app import portfolio  # type: ignore[import-not-found]

    return portfolio.execute_trade


def _load_watchlist_callables() -> tuple[Callable[..., Any], Callable[..., Any]]:
    """Return (``watchlist_add``, ``watchlist_remove``) callables (lazy)."""
    # The contract describes ``watchlist.add`` / ``watchlist.remove`` (see
    # LLM_CONTRACT.md §6.3). Importing lazily so this module is testable
    # without the watchlist code being wired up yet.
    from app import watchlist  # type: ignore[import-not-found]

    return watchlist.add, watchlist.remove


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


async def _maybe_await(value: Any) -> Any:
    """Await ``value`` iff it is awaitable."""
    if isinstance(value, Awaitable):
        return await value
    return value


def _trade_error_action(trade: LLMTrade, exc: Exception) -> TradeActionError:
    name = type(exc).__name__
    if name in _TRADE_ERROR_MAP:
        code, message_builder = _TRADE_ERROR_MAP[name]
        return TradeActionError(
            ticker=trade.ticker,
            side=trade.side,
            quantity=trade.quantity,
            error=code,  # type: ignore[arg-type]
            error_message=message_builder(exc),
        )
    raise exc  # re-raise unknown exception types per §6.2 (4)


def _watchlist_error_action(
    change: LLMWatchlistChange, exc: Exception
) -> WatchlistActionError:
    name = type(exc).__name__
    if name in _WATCHLIST_ERROR_MAP:
        code, message_builder = _WATCHLIST_ERROR_MAP[name]
        return WatchlistActionError(
            ticker=change.ticker,
            action=change.action,
            error=code,  # type: ignore[arg-type]
            error_message=message_builder(exc, change.ticker),
        )
    raise exc  # re-raise unknown exception types per §6.3 (4)


def _trade_ok_action(
    trade: LLMTrade, result: Any
) -> TradeActionOk:
    """Unpack the return value of ``portfolio.execute_trade`` into a TradeActionOk.

    The contract (LLM_CONTRACT.md §6.2) says we need ``fill_price`` and
    ``cash_after``. The portfolio module is expected to return an object or
    mapping carrying those fields; we tolerate either attribute access or
    mapping access so this stays robust to the portfolio engineer's choice.
    """
    fill_price = _result_field(result, "fill_price")
    cash_after = _result_field(result, "cash_after")
    return TradeActionOk(
        ticker=trade.ticker,
        side=trade.side,
        quantity=trade.quantity,
        fill_price=float(fill_price),
        cash_after=float(cash_after),
    )


def _result_field(result: Any, name: str) -> Any:
    if isinstance(result, dict):
        if name not in result:
            raise KeyError(f"trade result missing '{name}' key")
        return result[name]
    if hasattr(result, name):
        return getattr(result, name)
    raise AttributeError(f"trade result missing '{name}' attribute / key")


async def apply(
    parsed: LLMResponse,
    *,
    user_id: str = "default",
    price_cache: Any = None,
    trade_fn: Optional[Callable[..., Any]] = None,
    watchlist_add_fn: Optional[Callable[..., Any]] = None,
    watchlist_remove_fn: Optional[Callable[..., Any]] = None,
) -> list[ChatAction]:
    """Apply ``parsed.trades`` then ``parsed.watchlist_changes``, in order.

    Returns the resolved ``actions`` list. Per LLM_CONTRACT.md §6.1, all
    trade actions come first, then all watchlist actions.

    ``price_cache`` is the live :class:`app.market.PriceCache` instance —
    it must be passed in by callers that go through the real portfolio
    code path so trade fills resolve at execution-time prices (per
    PLAN.md §9 "Trade Execution & Validation"). It is only forwarded to
    the underlying ``trade_fn``; tests that inject their own ``trade_fn``
    may leave it as ``None``.

    The ``trade_fn`` / ``watchlist_*_fn`` kwargs are escape hatches for
    tests; in production they default to the lazily-imported portfolio
    and watchlist modules.
    """
    actions: list[ChatAction] = []

    if parsed.trades:
        execute = trade_fn if trade_fn is not None else _load_trade_callable()
        for trade in parsed.trades:
            try:
                call_kwargs: dict[str, Any] = {
                    "ticker": trade.ticker,
                    "side": trade.side,
                    "quantity": trade.quantity,
                    "user_id": user_id,
                }
                # Only forward price_cache when we have one — keeps the
                # ``trade_fn`` test escape hatch (which doesn't require
                # it) backwards compatible while ensuring the real
                # ``portfolio.execute_trade`` (which does) gets it.
                if price_cache is not None:
                    call_kwargs["price_cache"] = price_cache
                result = await _maybe_await(execute(**call_kwargs))
            except Exception as exc:  # noqa: BLE001 - we re-raise unknown types
                actions.append(_trade_error_action(trade, exc))
                continue
            actions.append(_trade_ok_action(trade, result))

    if parsed.watchlist_changes:
        if watchlist_add_fn is None or watchlist_remove_fn is None:
            add_fn, remove_fn = _load_watchlist_callables()
            watchlist_add_fn = watchlist_add_fn or add_fn
            watchlist_remove_fn = watchlist_remove_fn or remove_fn

        for change in parsed.watchlist_changes:
            try:
                if change.action == "add":
                    await _maybe_await(
                        watchlist_add_fn(ticker=change.ticker, user_id=user_id)
                    )
                else:
                    await _maybe_await(
                        watchlist_remove_fn(ticker=change.ticker, user_id=user_id)
                    )
            except Exception as exc:  # noqa: BLE001 - we re-raise unknown types
                actions.append(_watchlist_error_action(change, exc))
                continue
            actions.append(
                WatchlistActionOk(ticker=change.ticker, action=change.action)
            )

    return actions
