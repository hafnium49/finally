"""FinAlly chat subsystem.

Public surface:

    handle_message(user_text, ...) -> ChatResponse
        End-to-end orchestrator backing POST /api/chat.

    validate_config()
        Called from the FastAPI lifespan startup hook so the server fails
        fast when LLM_MOCK != "true" but OPENROUTER_API_KEY is missing.

    schemas: LLMResponse, LLMTrade, LLMWatchlistChange, ChatAction, ChatResponse
        Pydantic v2 models defined in LLM_CONTRACT.md §1.
"""

from .client import LLMConfigError, LLMResponseError, assert_ready, validate_config
from .handler import handle_message
from .schemas import (
    ChatAction,
    ChatResponse,
    LLMResponse,
    LLMTrade,
    LLMWatchlistChange,
    TradeActionError,
    TradeActionOk,
    WatchlistActionError,
    WatchlistActionOk,
)

__all__ = [
    "ChatAction",
    "ChatResponse",
    "LLMConfigError",
    "LLMResponse",
    "LLMResponseError",
    "LLMTrade",
    "LLMWatchlistChange",
    "TradeActionError",
    "TradeActionOk",
    "WatchlistActionError",
    "WatchlistActionOk",
    "assert_ready",
    "handle_message",
    "validate_config",
]
