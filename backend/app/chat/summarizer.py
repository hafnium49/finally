"""Rolling conversation summary maintenance.

Per LLM_CONTRACT.md §3, the chat handler keeps the 10 most recent messages
verbatim and folds older ones into ``chat_state.summary``. When adding the
new user message would push the verbatim window past 10, the oldest
message is selected, the LLM is asked to rewrite the rolling summary, and
the row is deleted.

This module implements the pure summarization step: given the current
summary text and the message to fold in, return the new summary text.
The handler is responsible for the DB read/write side of the trigger.

Mock mode (``LLM_MOCK=true``) uses a simple deterministic truncation so
tests stay byte-stable.
"""

from __future__ import annotations

import os
from typing import Any, Mapping, Optional, Sequence

from .schemas import _ChatActionBase


SUMMARIZER_PROMPT_TEMPLATE = """\
You are folding old conversation history into a rolling summary.

Existing summary (may be empty):
<<<
{existing}
>>>

Newly evicted message ([role] content):
<<<
{evicted}
>>>

Rewrite the existing summary so it incorporates the newly evicted message.
Keep it under 200 words. Preserve concrete facts (tickers traded, decisions made,
user preferences expressed). Drop pleasantries and fillers. Output the new summary
as plain prose with no preamble.
"""

VERBATIM_WINDOW_SIZE = 10


def _is_mock_mode() -> bool:
    return os.environ.get("LLM_MOCK", "").strip().lower() == "true"


def _format_actions_trace(actions: Sequence[Any] | None) -> str:
    """Render a compact `(actions: 2 trades, 1 watchlist add)` summary.

    ``actions`` may be a list of dicts (as stored in chat_messages) or a
    list of pydantic ChatAction models. Returns an empty string when there
    are no actions worth noting.
    """
    if not actions:
        return ""
    trade_count = 0
    add_count = 0
    remove_count = 0
    for action in actions:
        if isinstance(action, _ChatActionBase):
            kind = action.kind
            sub = getattr(action, "action", None)
        elif isinstance(action, dict):
            kind = action.get("kind")
            sub = action.get("action")
        else:
            kind = getattr(action, "kind", None)
            sub = getattr(action, "action", None)
        if kind == "trade":
            trade_count += 1
        elif kind == "watchlist":
            if sub == "add":
                add_count += 1
            elif sub == "remove":
                remove_count += 1
    parts: list[str] = []
    if trade_count:
        parts.append(f"{trade_count} trade{'s' if trade_count != 1 else ''}")
    if add_count:
        parts.append(f"{add_count} watchlist add{'s' if add_count != 1 else ''}")
    if remove_count:
        parts.append(f"{remove_count} watchlist remove{'s' if remove_count != 1 else ''}")
    if not parts:
        return ""
    return f" (actions: {', '.join(parts)})"


def format_evicted_message(message: Mapping[str, Any]) -> str:
    """Format a chat_messages row into the role-tagged line the summarizer expects."""
    role = message.get("role", "user")
    if role not in ("user", "assistant"):
        role = "user"
    content = message.get("content", "")
    trace = _format_actions_trace(message.get("actions"))
    return f"[{role}] {content}{trace}"


def _mock_summary(current_summary: str, evicted_line: str) -> str:
    """Deterministic mock summary: prepend the evicted line, truncate verbosely."""
    if current_summary:
        return f"{evicted_line} | {current_summary}"
    return evicted_line


def _live_summary(current_summary: str, evicted_line: str) -> str:
    from litellm import completion  # type: ignore[import-not-found]

    from .client import EXTRA_BODY, MODEL

    prompt = SUMMARIZER_PROMPT_TEMPLATE.format(
        existing=current_summary or "(none yet)",
        evicted=evicted_line,
    )
    response = completion(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        extra_body=EXTRA_BODY,
        temperature=0.0,
        max_tokens=512,
        reasoning_effort="low",
    )
    content = response.choices[0].message.content or ""
    return content.strip()


def summarize(current_summary: str, evicted_message: Mapping[str, Any]) -> str:
    """Fold ``evicted_message`` into ``current_summary`` and return the new summary.

    In mock mode this is a deterministic string concatenation. In live
    mode it invokes the LLM with :data:`SUMMARIZER_PROMPT_TEMPLATE`.
    """
    evicted_line = format_evicted_message(evicted_message)
    if _is_mock_mode():
        return _mock_summary(current_summary, evicted_line)
    return _live_summary(current_summary, evicted_line)


def needs_summarization(history_count: int) -> bool:
    """Return True iff adding one more message would push the window past the cap."""
    return history_count > VERBATIM_WINDOW_SIZE


def maybe_summarize(
    history: Sequence[Mapping[str, Any]],
    current_summary: str,
) -> tuple[Optional[Mapping[str, Any]], str]:
    """Possibly fold the oldest history message into the rolling summary.

    If ``len(history)`` does not exceed :data:`VERBATIM_WINDOW_SIZE`, the
    summary is returned unchanged and the evicted-message slot is None.

    Otherwise the oldest message (``history[0]``) is folded into the
    existing summary and a tuple ``(evicted_message, new_summary)`` is
    returned. The caller is responsible for deleting the evicted row
    from ``chat_messages`` and persisting the new summary in
    ``chat_state``.
    """
    if not needs_summarization(len(history)):
        return None, current_summary
    evicted = history[0]
    new_summary = summarize(current_summary, evicted)
    return evicted, new_summary
