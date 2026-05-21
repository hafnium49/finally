"""Chat route.

Thin wrapper around ``app.chat.handle_message()``. The LLM Engineer owns
the implementation; this route just validates the request body and
delegates. If ``app.chat`` isn't importable yet (e.g. the LLM Engineer is
still building it), the route returns 503 ``chat_not_ready`` so the
endpoint still exists for integration tests.

Per API_CONTRACT.md §5 this endpoint is **always 200** as long as the
body parses — per-action failures travel inside the ``actions[]`` array,
not as HTTP errors. The only non-200 paths are 422 (validation) and 500
(unhandled exception in the chat pipeline).
"""

from __future__ import annotations

import inspect
import logging
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import get_price_cache
from app.api.errors import APIError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatBody(BaseModel):
    """Request body for ``POST /api/chat`` (API_CONTRACT.md §5.1)."""

    model_config = ConfigDict(extra="forbid")
    message: str = Field(..., min_length=1, max_length=4000)


def _coerce_chat_response(value: Any) -> dict:
    """Best-effort conversion of whatever ``handle_message`` returns into a dict.

    The LLM Engineer's contract is a ``ChatResponse`` Pydantic model
    (LLM_CONTRACT.md §1). If we receive that, dump it. If we receive a dict
    already, normalize ``actions`` to ``[]`` per the wire invariant
    (API_CONTRACT.md §5).
    """
    if hasattr(value, "model_dump"):
        data = value.model_dump()
    elif isinstance(value, dict):
        data = dict(value)
    else:
        raise TypeError(
            f"chat.handle_message returned unsupported type: {type(value)!r}"
        )
    if data.get("actions") is None:
        data["actions"] = []
    return data


@router.post("")
async def post_chat(body: ChatBody, request: Request) -> dict:
    """Send a message to FinAlly; receive a complete ``ChatResponse`` payload."""
    try:
        # Imported lazily so a missing chat module still allows the rest of
        # the app to boot (parallel-build friendliness).
        from app import chat as chat_module
    except ImportError:
        logger.warning("app.chat not importable yet; returning 503")
        raise APIError(
            status_code=503,
            error="chat_not_ready",
            error_message="Chat subsystem is not initialized yet.",
        )

    handler = getattr(chat_module, "handle_message", None)
    if handler is None:
        logger.warning("app.chat.handle_message not defined; returning 503")
        raise APIError(
            status_code=503,
            error="chat_not_ready",
            error_message="Chat subsystem is not initialized yet.",
        )

    # B006: pass the live PriceCache so LLM-triggered trades fill at the
    # same execution-time price the UI trade path uses. The cache is a
    # live reference, not a snapshot — execute_trade reads it inside the
    # per-user lock.
    #
    # ``price_cache`` is forwarded only if the handler's signature accepts
    # it. The production handler (``app.chat.handle_message``) does; test
    # stubs that pre-date the B006 wiring may not, and we don't want this
    # route to break them. ``inspect`` lets us stay backwards compatible
    # without imposing a kwarg contract on stubs.
    cache = get_price_cache(request)
    handler_kwargs: dict[str, Any] = {}
    if _handler_accepts_kwarg(handler, "price_cache"):
        handler_kwargs["price_cache"] = cache

    try:
        result = await handler(body.message, **handler_kwargs)
    except APIError:
        raise
    except Exception:
        logger.exception("chat.handle_message raised")
        raise APIError(
            status_code=500,
            error="internal_error",
            error_message="The chat pipeline failed unexpectedly.",
        )

    return _coerce_chat_response(result)


def _handler_accepts_kwarg(handler: Any, name: str) -> bool:
    """Return True iff ``handler``'s signature accepts a keyword named ``name``.

    Treats ``**kwargs`` as accepting anything. Falls back to ``False`` if
    the signature can't be introspected (e.g. C-implemented callables).
    """
    try:
        sig = inspect.signature(handler)
    except (TypeError, ValueError):
        return False
    params = sig.parameters
    if name in params:
        return True
    return any(
        p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()
    )
