"""End-to-end orchestration for ``/api/chat``.

Per LLM_CONTRACT.md §7:

    1. Load portfolio context, summary, and the last <=10 messages.
    2. Build the system prompt.
    3. Call the LLM client (live or mock).
    4. Execute the parsed trades + watchlist changes.
    5. Persist the user message and the assistant message (with actions JSON).
    6. (after returning) fold the oldest message into the rolling summary if needed.
    7. Return the ChatResponse.

The portfolio / watchlist modules may not be wired up while this module
is imported (other subagents are building them in parallel). Imports are
lazy and the handler tolerates their absence: if context cannot be loaded
the prompt is built with an empty dict, and trade / watchlist execution
errors that match no known exception type are re-raised (per §6.2).
"""

from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence

from . import client as llm_client
from . import executor as llm_executor
from . import summarizer as llm_summarizer
from .prompt import build_system_prompt
from .schemas import ChatResponse, LLMResponse


_logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Portfolio context loading (best-effort)
# ---------------------------------------------------------------------------


def _load_portfolio_context(
    user_id: str, price_cache: Optional[Any]
) -> dict[str, Any]:
    """Return the snapshot dict for the prompt, or ``{}`` if loading fails.

    Imports :func:`app.portfolio.get_portfolio_context` directly — the
    earlier ``getattr`` lookup silently returned ``None`` when the symbol
    did not exist, which let the LLM see an empty context for users who
    actually held positions (defect B017). Any unexpected failure during
    context load (e.g., DB not initialized in a stripped-down test) is
    logged and downgraded to an empty dict so chat still responds.

    ``price_cache`` may be ``None`` when the handler is called without one
    (e.g., a fallback path in tests). In that case we skip context entirely;
    ``compute_portfolio`` requires the cache for per-position pricing.
    """
    if price_cache is None:
        return {}
    try:
        from app.portfolio import get_portfolio_context
    except ImportError:
        _logger.warning(
            "Portfolio module unavailable; chat prompt will run with empty context"
        )
        return {}
    try:
        ctx = get_portfolio_context(price_cache, user_id=user_id)
        if isinstance(ctx, Mapping):
            return dict(ctx)
        return {}
    except Exception:
        _logger.exception("Failed to load portfolio context for chat prompt")
        return {}


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


def _load_history(
    conn: sqlite3.Connection, user_id: str, limit: int = 10
) -> list[dict[str, Any]]:
    """Return the most-recent ``limit`` chat_messages rows, oldest-first."""
    rows = conn.execute(
        """
        SELECT id, role, content, actions, created_at
        FROM chat_messages
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()
    history: list[dict[str, Any]] = []
    for row in reversed(rows):
        entry: dict[str, Any] = {
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "created_at": row["created_at"],
        }
        raw_actions = row["actions"]
        if raw_actions is None:
            entry["actions"] = None
        else:
            try:
                entry["actions"] = json.loads(raw_actions)
            except json.JSONDecodeError:
                entry["actions"] = None
        history.append(entry)
    return history


def _load_summary(conn: sqlite3.Connection, user_id: str) -> str:
    row = conn.execute(
        "SELECT summary FROM chat_state WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        return ""
    return row["summary"] or ""


def _insert_user_message(
    conn: sqlite3.Connection, user_id: str, content: str
) -> str:
    msg_id = _new_uuid()
    conn.execute(
        """
        INSERT INTO chat_messages (id, user_id, role, content, actions, created_at)
        VALUES (?, ?, 'user', ?, NULL, ?)
        """,
        (msg_id, user_id, content, _now_iso()),
    )
    return msg_id


def _insert_assistant_message(
    conn: sqlite3.Connection,
    user_id: str,
    content: str,
    actions_payload: list[Any],
) -> str:
    msg_id = _new_uuid()
    # LLM_CONTRACT.md §6.5: assistant rows ALWAYS store JSON (even '[]'), never NULL.
    actions_json = json.dumps([
        a.model_dump() if hasattr(a, "model_dump") else a for a in actions_payload
    ])
    conn.execute(
        """
        INSERT INTO chat_messages (id, user_id, role, content, actions, created_at)
        VALUES (?, ?, 'assistant', ?, ?, ?)
        """,
        (msg_id, user_id, content, actions_json, _now_iso()),
    )
    return msg_id


def _count_messages(conn: sqlite3.Connection, user_id: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM chat_messages WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    return int(row["c"]) if row else 0


def _oldest_message(
    conn: sqlite3.Connection, user_id: str
) -> Optional[dict[str, Any]]:
    row = conn.execute(
        """
        SELECT id, role, content, actions, created_at
        FROM chat_messages
        WHERE user_id = ?
        ORDER BY created_at ASC, id ASC
        LIMIT 1
        """,
        (user_id,),
    ).fetchone()
    if row is None:
        return None
    raw_actions = row["actions"]
    actions = None
    if raw_actions is not None:
        try:
            actions = json.loads(raw_actions)
        except json.JSONDecodeError:
            actions = None
    return {
        "id": row["id"],
        "role": row["role"],
        "content": row["content"],
        "actions": actions,
        "created_at": row["created_at"],
    }


def _persist_summary(
    conn: sqlite3.Connection, user_id: str, summary: str
) -> None:
    conn.execute(
        """
        INSERT INTO chat_state (user_id, summary, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET summary = excluded.summary,
                                            updated_at = excluded.updated_at
        """,
        (user_id, summary, _now_iso()),
    )


def _delete_message(conn: sqlite3.Connection, message_id: str) -> None:
    conn.execute("DELETE FROM chat_messages WHERE id = ?", (message_id,))


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


async def handle_message(
    user_text: str,
    *,
    user_id: str = "default",
    db_path: Optional[Any] = None,
    price_cache: Optional[Any] = None,
) -> ChatResponse:
    """Run the full chat pipeline and return the wire response.

    ``price_cache`` is the live :class:`app.market.PriceCache` instance.
    The HTTP layer (``app.api.chat``) resolves it from ``app.state`` and
    threads it through so LLM-triggered trades fill at the latest cached
    price — the same source the UI trade path uses (B006 regression
    guard).

    The DB connection is opened by this function (via ``app.db.connection``)
    so the handler can be called from any context (HTTP route, CLI, tests).
    """
    from app.db import connection  # lazy import to avoid circulars during tests

    # 1. Load context + history + summary; build prompt.
    with connection(db_path) as conn:
        history = _load_history(conn, user_id)
        summary = _load_summary(conn, user_id)
    portfolio_ctx = _load_portfolio_context(user_id, price_cache)

    # The new user turn is included in the verbatim history slot so the
    # model sees it in-context (LLM_CONTRACT.md §2.4 + §2.1 slot semantics).
    prompt_history: list[Mapping[str, Any]] = [
        {"role": h["role"], "content": h["content"]} for h in history
    ]
    prompt_history.append({"role": "user", "content": user_text})

    system_prompt = build_system_prompt(portfolio_ctx, summary, prompt_history)

    # 2. Run the LLM (mock or live).
    try:
        llm_response: LLMResponse = llm_client.complete(system_prompt, user_text)
    except llm_client.LLMResponseError:
        _logger.exception("LLM produced malformed response; returning fallback")
        return ChatResponse(
            message="Sorry, I couldn't process that response. Please try again.",
            actions=[],
        )

    # 3. Execute trades + watchlist changes.
    actions = await llm_executor.apply(
        llm_response, user_id=user_id, price_cache=price_cache
    )

    # 4. Persist user + assistant rows.
    with connection(db_path) as conn:
        _insert_user_message(conn, user_id, user_text)
        _insert_assistant_message(conn, user_id, llm_response.message, list(actions))

    # 5. Build the response now so the caller is unblocked before summarization.
    response = ChatResponse(message=llm_response.message, actions=list(actions))

    # 6. Maybe-summarize: fold the oldest message into chat_state.summary.
    try:
        _run_summarization_if_needed(user_id, db_path)
    except Exception:
        # Per §3.2: if summarization fails, keep the row; retry next turn.
        _logger.exception("Summarization step failed; will retry on next turn")

    return response


def _run_summarization_if_needed(
    user_id: str, db_path: Optional[Any]
) -> None:
    from app.db import connection  # lazy

    with connection(db_path) as conn:
        count = _count_messages(conn, user_id)
        if not llm_summarizer.needs_summarization(count):
            return
        evicted = _oldest_message(conn, user_id)
        if evicted is None:
            return
        current = _load_summary(conn, user_id)
        new_summary = llm_summarizer.summarize(current, evicted)
        _persist_summary(conn, user_id, new_summary)
        _delete_message(conn, evicted["id"])


# Re-exported for tests that want to drive the steps independently.
__all__ = [
    "handle_message",
]


# Backwards-compat aliases (Sequence imported only for type checkers).
_ = Sequence
