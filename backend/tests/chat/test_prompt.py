"""Tests for app.chat.prompt.build_system_prompt."""

from __future__ import annotations

import json

from app.chat.prompt import build_system_prompt
from app.chat.schemas import LLMResponse
from app.chat.system_prompt import SYSTEM_PROMPT_VOICE


def test_voice_block_is_user_authored() -> None:
    """SYSTEM_PROMPT_VOICE must be non-empty user-authored content (no longer a TODO stub)."""
    assert SYSTEM_PROMPT_VOICE.strip()
    assert "TODO(user)" not in SYSTEM_PROMPT_VOICE
    # Sanity: should be in the 5-10 line range the spec calls for, not a one-liner.
    assert SYSTEM_PROMPT_VOICE.count("\n") >= 2


def test_prompt_includes_voice_verbatim() -> None:
    prompt = build_system_prompt({}, "", [])
    assert SYSTEM_PROMPT_VOICE in prompt


def test_prompt_includes_llm_response_schema() -> None:
    """The compact LLMResponse JSON schema is embedded so the LLM sees the shape."""
    prompt = build_system_prompt({}, "", [])
    schema_substr = json.dumps(LLMResponse.model_json_schema(), separators=(",", ":"))
    assert schema_substr in prompt


def test_prompt_includes_portfolio_context() -> None:
    ctx = {"cash_balance": 8076.60, "positions": []}
    prompt = build_system_prompt(ctx, "", [])
    # Compact JSON form is in the prompt
    assert '"cash_balance":8076.6' in prompt


def test_prompt_includes_summary_or_none_yet_marker() -> None:
    empty = build_system_prompt({}, "", [])
    assert "(none yet)" in empty
    populated = build_system_prompt({}, "previous summary text", [])
    assert "previous summary text" in populated


def test_prompt_includes_history_lines() -> None:
    history = [
        {"role": "user", "content": "Buy 5 AAPL"},
        {"role": "assistant", "content": "Buying 5 AAPL."},
        {"role": "user", "content": "What's my exposure?"},
    ]
    prompt = build_system_prompt({}, "", history)
    assert "[user] Buy 5 AAPL" in prompt
    assert "[assistant] Buying 5 AAPL." in prompt
    assert "[user] What's my exposure?" in prompt


def test_prompt_empty_history_renders_marker() -> None:
    prompt = build_system_prompt({}, "", [])
    assert "(no prior turns)" in prompt


def test_prompt_contains_all_five_slot_headers() -> None:
    """All five slots from LLM_CONTRACT.md §2 must be wired up."""
    prompt = build_system_prompt({"x": 1}, "rolling summary", [{"role": "user", "content": "hi"}])
    # Section headers from the template
    assert "## Response format" in prompt
    assert "## Current portfolio" in prompt
    assert "## Conversation summary" in prompt
    assert "## Recent conversation" in prompt
    # Voice slot rendered (any non-empty content from SYSTEM_PROMPT_VOICE)
    assert SYSTEM_PROMPT_VOICE in prompt
    # Schema slot rendered
    assert "LLMResponse" in prompt or "trades" in prompt  # one of them must show
    # Portfolio slot rendered
    assert '"x":1' in prompt
    # Summary slot rendered
    assert "rolling summary" in prompt
    # History slot rendered
    assert "[user] hi" in prompt
