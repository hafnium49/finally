"""Tests for app.chat.summarizer."""

from __future__ import annotations

import pytest

from app.chat.summarizer import (
    VERBATIM_WINDOW_SIZE,
    format_evicted_message,
    maybe_summarize,
    needs_summarization,
)


@pytest.fixture(autouse=True)
def _enable_mock_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """All tests in this module run in mock mode (no LLM calls)."""
    monkeypatch.setenv("LLM_MOCK", "true")


class TestTriggerThreshold:
    def test_under_threshold_does_not_summarize(self) -> None:
        history = [{"role": "user", "content": f"msg {i}"} for i in range(VERBATIM_WINDOW_SIZE)]
        evicted, summary = maybe_summarize(history, "existing")
        assert evicted is None
        assert summary == "existing"

    def test_at_threshold_does_not_summarize(self) -> None:
        history = [{"role": "user", "content": "x"}] * VERBATIM_WINDOW_SIZE
        assert not needs_summarization(len(history))

    def test_over_threshold_summarizes_oldest(self) -> None:
        history = [
            {"role": "user", "content": f"msg-{i}"}
            for i in range(VERBATIM_WINDOW_SIZE + 1)
        ]
        # First message must be the evicted candidate.
        evicted, new_summary = maybe_summarize(history, "prior")
        assert evicted is not None
        assert evicted["content"] == "msg-0"
        assert "msg-0" in new_summary
        # Existing summary preserved.
        assert "prior" in new_summary


class TestEvictedMessageFormatting:
    def test_user_message_no_actions(self) -> None:
        line = format_evicted_message({"role": "user", "content": "Buy 5 AAPL"})
        assert line == "[user] Buy 5 AAPL"

    def test_assistant_message_with_trade_action(self) -> None:
        line = format_evicted_message(
            {
                "role": "assistant",
                "content": "Buying 5 AAPL.",
                "actions": [
                    {
                        "kind": "trade",
                        "status": "ok",
                        "ticker": "AAPL",
                        "side": "buy",
                        "quantity": 5,
                        "fill_price": 190.0,
                        "cash_after": 9050.0,
                    }
                ],
            }
        )
        assert "[assistant] Buying 5 AAPL." in line
        assert "(actions: 1 trade)" in line

    def test_assistant_message_with_watchlist_actions(self) -> None:
        line = format_evicted_message(
            {
                "role": "assistant",
                "content": "Adding PYPL.",
                "actions": [
                    {"kind": "watchlist", "status": "ok", "ticker": "PYPL", "action": "add"},
                    {"kind": "watchlist", "status": "ok", "ticker": "META", "action": "remove"},
                ],
            }
        )
        assert "1 watchlist add" in line
        assert "1 watchlist remove" in line

    def test_unknown_role_defaults_to_user(self) -> None:
        line = format_evicted_message({"role": "system", "content": "x"})
        assert line.startswith("[user] ")


class TestMockSummary:
    def test_empty_prior_summary(self) -> None:
        history = [
            {"role": "user", "content": f"msg-{i}"}
            for i in range(VERBATIM_WINDOW_SIZE + 1)
        ]
        evicted, new_summary = maybe_summarize(history, "")
        assert evicted is not None
        assert new_summary == "[user] msg-0"

    def test_nonempty_prior_summary_concatenated(self) -> None:
        history = [
            {"role": "user", "content": f"msg-{i}"}
            for i in range(VERBATIM_WINDOW_SIZE + 1)
        ]
        evicted, new_summary = maybe_summarize(history, "older context")
        assert evicted is not None
        assert "older context" in new_summary
        assert "msg-0" in new_summary
