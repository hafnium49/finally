"""Deterministic mock-mode LLM responses.

When ``LLM_MOCK=true``, :func:`respond` is invoked instead of the live
LiteLLM call. The mapping is the regex table from LLM_CONTRACT.md §4 —
case-insensitive matches against ``user_text.strip()``, first-match wins.

Determinism requirement: same ``user_text`` -> byte-identical
``LLMResponse``. No timestamps, no random IDs, no portfolio reads.
"""

from __future__ import annotations

import re
from typing import Callable

from .schemas import LLMResponse, LLMTrade, LLMWatchlistChange


# Pattern compiled once so re-import / repeated calls share the same objects.
_PAT_BUY = re.compile(r"^buy\s+(\d+(?:\.\d+)?)\s+([A-Za-z]{1,5})\b", re.IGNORECASE)
_PAT_SELL = re.compile(r"^sell\s+(\d+(?:\.\d+)?)\s+([A-Za-z]{1,5})\b", re.IGNORECASE)
_PAT_ADD = re.compile(
    r"^add\s+([A-Za-z]{1,5})\s+(?:to\s+)?(?:my\s+)?watchlist\b", re.IGNORECASE
)
_PAT_REMOVE = re.compile(r"^remove\s+([A-Za-z]{1,5})\b", re.IGNORECASE)
_PAT_PORTFOLIO = re.compile(
    r"(what'?s?|tell me about)\s+my\s+portfolio", re.IGNORECASE
)
_PAT_GREETING = re.compile(r"^(hi|hello|hey)\b", re.IGNORECASE)


def _format_q(q_raw: str) -> str:
    """Pass through quantity text verbatim for the message string."""
    return q_raw


def _coerce_q(q_raw: str) -> float:
    """Coerce captured quantity to float for the LLMTrade.quantity field."""
    return float(q_raw)


def _buy(match: re.Match[str]) -> LLMResponse:
    q_raw, ticker_raw = match.group(1), match.group(2)
    ticker = ticker_raw.upper()
    return LLMResponse(
        message=f"Buying {_format_q(q_raw)} {ticker}.",
        trades=[LLMTrade(ticker=ticker, side="buy", quantity=_coerce_q(q_raw))],
    )


def _sell(match: re.Match[str]) -> LLMResponse:
    q_raw, ticker_raw = match.group(1), match.group(2)
    ticker = ticker_raw.upper()
    return LLMResponse(
        message=f"Selling {_format_q(q_raw)} {ticker}.",
        trades=[LLMTrade(ticker=ticker, side="sell", quantity=_coerce_q(q_raw))],
    )


def _add(match: re.Match[str]) -> LLMResponse:
    ticker = match.group(1).upper()
    return LLMResponse(
        message=f"Adding {ticker} to your watchlist.",
        watchlist_changes=[LLMWatchlistChange(ticker=ticker, action="add")],
    )


def _remove(match: re.Match[str]) -> LLMResponse:
    ticker = match.group(1).upper()
    return LLMResponse(
        message=f"Removing {ticker} from your watchlist.",
        watchlist_changes=[LLMWatchlistChange(ticker=ticker, action="remove")],
    )


def _portfolio(_match: re.Match[str]) -> LLMResponse:
    return LLMResponse(
        message=(
            "Mock portfolio summary: you have positions; check the dashboard for details."
        ),
    )


def _greeting(_match: re.Match[str]) -> LLMResponse:
    return LLMResponse(
        message=(
            "Hello - I'm FinAlly (mock mode). I can buy/sell, manage your watchlist, "
            "or summarize your portfolio."
        ),
    )


def _default() -> LLMResponse:
    return LLMResponse(
        message=(
            "Mock mode: I received your message but only recognize buy/sell/add/"
            "remove/portfolio in mock mode."
        ),
    )


# Ordered match table. First pattern to fire wins.
_TABLE: list[tuple[re.Pattern[str], Callable[[re.Match[str]], LLMResponse]]] = [
    (_PAT_BUY, _buy),
    (_PAT_SELL, _sell),
    (_PAT_ADD, _add),
    (_PAT_REMOVE, _remove),
    (_PAT_PORTFOLIO, _portfolio),
    (_PAT_GREETING, _greeting),
]


def respond(user_text: str) -> LLMResponse:
    """Return the canned :class:`LLMResponse` for ``user_text``.

    Deterministic — same input string produces a byte-identical
    ``LLMResponse.model_dump_json()`` across calls.
    """
    text = user_text.strip()
    for pattern, builder in _TABLE:
        match = pattern.search(text) if pattern is _PAT_PORTFOLIO else pattern.match(text)
        if match:
            return builder(match)
    return _default()
