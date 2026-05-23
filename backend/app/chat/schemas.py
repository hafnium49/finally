"""Pydantic v2 models for the FinAlly chat subsystem.

These models are the source of truth for:
- the structured output we request from the LLM (LLMResponse + nested LLMTrade / LLMWatchlistChange)
- the resolved per-action records persisted to chat_messages.actions and returned on the /api/chat wire (ChatAction)
- the /api/chat response envelope (ChatResponse)
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Inputs from the LLM (structured output)
# ---------------------------------------------------------------------------

TICKER_REGEX = r"^[A-Z]{1,5}$"


class LLMTrade(BaseModel):
    """A trade the LLM wants the backend to execute on the user's behalf."""

    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(..., description="Uppercase ticker symbol, 1-5 letters.")
    side: Literal["buy", "sell"]
    quantity: float = Field(..., gt=0, description="Positive; fractional shares allowed.")

    @field_validator("ticker", mode="before")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.upper() if isinstance(v, str) else v


class LLMWatchlistChange(BaseModel):
    """A watchlist mutation the LLM wants the backend to apply."""

    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(..., description="Uppercase ticker symbol, 1-5 letters.")
    action: Literal["add", "remove"]

    @field_validator("ticker", mode="before")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.upper() if isinstance(v, str) else v


class LLMResponse(BaseModel):
    """What the LLM emits. This is the `response_format` we hand to LiteLLM."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(
        ..., min_length=1, description="Conversational text shown to the user."
    )
    trades: list[LLMTrade] = Field(default_factory=list)
    watchlist_changes: list[LLMWatchlistChange] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Resolved actions persisted + returned on the wire
# ---------------------------------------------------------------------------


class _ChatActionBase(BaseModel):
    """Shared base for the discriminated ChatAction union."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["trade", "watchlist"]
    status: Literal["ok", "error"]
    ticker: str


class TradeActionOk(_ChatActionBase):
    kind: Literal["trade"] = "trade"
    status: Literal["ok"] = "ok"
    side: Literal["buy", "sell"]
    quantity: float
    fill_price: float
    cash_after: float


class TradeActionError(_ChatActionBase):
    kind: Literal["trade"] = "trade"
    status: Literal["error"] = "error"
    side: Literal["buy", "sell"]
    quantity: float
    error: Literal[
        "insufficient_cash",
        "insufficient_shares",
        "unknown_ticker",
        "invalid_quantity",
    ]
    error_message: str


class WatchlistActionOk(_ChatActionBase):
    kind: Literal["watchlist"] = "watchlist"
    status: Literal["ok"] = "ok"
    action: Literal["add", "remove"]


class WatchlistActionError(_ChatActionBase):
    kind: Literal["watchlist"] = "watchlist"
    status: Literal["error"] = "error"
    action: Literal["add", "remove"]
    error: Literal[
        "ticker_already_in_watchlist",
        "not_in_watchlist",
        "invalid_ticker",
    ]
    error_message: str


# Discriminated union. Pydantic v2 picks the right variant from (kind, status).
ChatAction = Annotated[
    Union[TradeActionOk, TradeActionError, WatchlistActionOk, WatchlistActionError],
    Field(discriminator=None),  # disambiguated by Literal kind/status combination
]


# ---------------------------------------------------------------------------
# Wire / handler-return envelope
# ---------------------------------------------------------------------------


class ChatResponse(BaseModel):
    """Returned from handle_message(...) and serialized verbatim by /api/chat.

    `actions` is ALWAYS a list (possibly empty) - never None. Both the
    persisted form in chat_messages.actions and the wire form mirror this.
    See API_CONTRACT.md §5.
    """

    model_config = ConfigDict(extra="forbid")

    message: str
    actions: list[ChatAction] = Field(default_factory=list)
