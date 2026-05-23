"""System-prompt assembly for the FinAlly chat subsystem.

`build_system_prompt(portfolio_ctx, summary, verbatim_history)` substitutes
into the LLM_CONTRACT.md §2 skeleton in this exact order:

    1. {{SYSTEM_PROMPT_VOICE}}            -- user-authored voice block
    2. {{LLM_RESPONSE_JSON_SCHEMA}}       -- LLMResponse.model_json_schema()
    3. {{PORTFOLIO_CONTEXT_JSON}}         -- compact JSON snapshot
    4. {{CONVERSATION_SUMMARY}}           -- chat_state.summary (or "(none yet)")
    5. {{VERBATIM_HISTORY}}               -- last <=10 messages, role-tagged

The slots are placeholder tokens only; they do not appear in the final string.
"""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from .schemas import LLMResponse
from .system_prompt import SYSTEM_PROMPT_VOICE


_TEMPLATE = """\
You are FinAlly, an AI trading assistant.

{voice}

## Response format
You must respond with valid JSON matching this schema:
{schema}
Trades execute automatically. Watchlist changes apply automatically. Be concise.

## Current portfolio
{portfolio}

## Conversation summary (older turns folded)
{summary}

## Recent conversation
{history}
"""


def _format_history(verbatim_history: Sequence[Mapping[str, Any]]) -> str:
    """Render verbatim history as role-tagged lines, oldest first.

    Each entry is expected to be a mapping with at least ``role`` and
    ``content`` keys (mirroring ``chat_messages`` rows). Unknown roles fall
    back to ``[user]`` to avoid silently dropping content.
    """
    if not verbatim_history:
        return "(no prior turns)"
    lines: list[str] = []
    for entry in verbatim_history:
        role = entry.get("role", "user")
        if role not in ("user", "assistant"):
            role = "user"
        content = entry.get("content", "")
        lines.append(f"[{role}] {content}")
    return "\n".join(lines)


def _format_portfolio(portfolio_ctx: Mapping[str, Any] | None) -> str:
    """Render the portfolio snapshot as a compact JSON object.

    Falls back to ``{}`` if ``portfolio_ctx`` is None — keeps the slot
    syntactically valid even on a cold start before any positions exist.
    """
    if portfolio_ctx is None:
        return "{}"
    return json.dumps(portfolio_ctx, separators=(",", ":"), default=str)


def _format_summary(summary: str | None) -> str:
    """Render the rolling summary, or '(none yet)' when empty."""
    if not summary:
        return "(none yet)"
    return summary


def _llm_response_schema_json() -> str:
    """Compact JSON-Schema rendering of LLMResponse for embedding in the prompt."""
    return json.dumps(LLMResponse.model_json_schema(), separators=(",", ":"))


def build_system_prompt(
    portfolio_ctx: Mapping[str, Any] | None,
    summary: str | None,
    verbatim_history: Sequence[Mapping[str, Any]],
) -> str:
    """Assemble the full FinAlly system prompt by substituting into the template.

    See LLM_CONTRACT.md §2 for the slot semantics. Returns a single string
    suitable for the ``role: "system"`` message handed to LiteLLM.
    """
    return _TEMPLATE.format(
        voice=SYSTEM_PROMPT_VOICE,
        schema=_llm_response_schema_json(),
        portfolio=_format_portfolio(portfolio_ctx),
        summary=_format_summary(summary),
        history=_format_history(verbatim_history),
    )
