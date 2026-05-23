"""End-to-end tests for app.chat.handler.handle_message."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from app.chat import handler as chat_handler
from app.chat.handler import handle_message
from app.db import connection


def _open(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _stub_trade_fn(success: bool = True) -> Any:
    async def _fn(**kwargs: Any) -> dict[str, Any]:
        if not success:
            class InsufficientCashError(Exception):
                def __init__(self) -> None:
                    super().__init__("nope")
                    self.need = 1000.0
                    self.have = 10.0

            raise InsufficientCashError()
        return {"fill_price": 192.34, "cash_after": 8076.60}

    return _fn


@pytest.mark.asyncio
async def test_buy_message_persists_user_and_assistant_rows(
    chat_db_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sending 'buy 5 AAPL' triggers the mock buy + stubbed trade execution + DB persistence."""
    # Patch the executor's lazy import so it uses our stub trade_fn.
    trade_fn = _stub_trade_fn(success=True)
    original_apply = chat_handler.llm_executor.apply

    async def patched_apply(parsed, **kwargs: Any):  # type: ignore[no-untyped-def]
        kwargs.setdefault("trade_fn", trade_fn)
        kwargs.setdefault("watchlist_add_fn", lambda **_: None)
        kwargs.setdefault("watchlist_remove_fn", lambda **_: None)
        return await original_apply(parsed, **kwargs)

    monkeypatch.setattr(chat_handler.llm_executor, "apply", patched_apply)

    response = await handle_message("Buy 5 AAPL")

    # Response shape
    assert response.message == "Buying 5 AAPL."
    assert len(response.actions) == 1
    action = response.actions[0]
    assert action.kind == "trade"
    assert action.status == "ok"
    assert action.ticker == "AAPL"
    assert action.side == "buy"
    assert action.quantity == 5.0
    assert action.fill_price == 192.34
    assert action.cash_after == 8076.60

    # DB rows
    conn = _open(chat_db_path)
    rows = conn.execute(
        "SELECT role, content, actions FROM chat_messages ORDER BY created_at ASC, role ASC"
    ).fetchall()
    conn.close()

    assert len(rows) == 2
    user_row = next(r for r in rows if r["role"] == "user")
    assistant_row = next(r for r in rows if r["role"] == "assistant")

    assert user_row["content"] == "Buy 5 AAPL"
    assert user_row["actions"] is None  # user rows: NULL
    assert assistant_row["content"] == "Buying 5 AAPL."
    # assistant rows: always JSON, never NULL
    parsed_actions = json.loads(assistant_row["actions"])
    assert isinstance(parsed_actions, list)
    assert parsed_actions[0]["kind"] == "trade"
    assert parsed_actions[0]["status"] == "ok"


@pytest.mark.asyncio
async def test_greeting_persists_with_empty_actions(
    chat_db_path: Path,
) -> None:
    """A 'hello' message produces actions=[] both on the wire and in DB ('[]' string)."""
    response = await handle_message("hello")
    assert response.actions == []
    # response.actions must be a list (never None)
    assert isinstance(response.actions, list)

    conn = _open(chat_db_path)
    row = conn.execute(
        "SELECT actions FROM chat_messages WHERE role = 'assistant'"
    ).fetchone()
    conn.close()

    # Stored as the literal '[]' JSON string (LLM_CONTRACT.md §6.5).
    assert row["actions"] == "[]"


@pytest.mark.asyncio
async def test_trade_error_surfaces_in_actions(
    chat_db_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trade_fn = _stub_trade_fn(success=False)
    original_apply = chat_handler.llm_executor.apply

    async def patched_apply(parsed, **kwargs: Any):  # type: ignore[no-untyped-def]
        kwargs.setdefault("trade_fn", trade_fn)
        kwargs.setdefault("watchlist_add_fn", lambda **_: None)
        kwargs.setdefault("watchlist_remove_fn", lambda **_: None)
        return await original_apply(parsed, **kwargs)

    monkeypatch.setattr(chat_handler.llm_executor, "apply", patched_apply)

    response = await handle_message("buy 100 AAPL")
    # The LLM's message text is unchanged — it doesn't know about the failure.
    assert response.message == "Buying 100 AAPL."
    assert len(response.actions) == 1
    action = response.actions[0]
    assert action.status == "error"
    assert action.error == "insufficient_cash"


@pytest.mark.asyncio
async def test_history_is_loaded_into_prompt(
    chat_db_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A previous turn should appear in the prompt the LLM sees."""
    # Seed an old assistant message.
    with connection(chat_db_path) as conn:
        conn.execute(
            """
            INSERT INTO chat_messages (id, user_id, role, content, actions, created_at)
            VALUES ('seed-1', 'default', 'user', 'first msg', NULL, '2026-01-01T00:00:00+00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO chat_messages (id, user_id, role, content, actions, created_at)
            VALUES ('seed-2', 'default', 'assistant', 'first reply', '[]', '2026-01-01T00:00:01+00:00')
            """
        )

    captured: dict[str, str] = {}

    def fake_complete(system_prompt: str, user_text: str, **kwargs: Any) -> Any:
        captured["prompt"] = system_prompt
        captured["user_text"] = user_text
        # Pass through to the real mock dispatcher so we still get a valid response.
        from app.chat.mock import respond

        return respond(user_text)

    monkeypatch.setattr(chat_handler.llm_client, "complete", fake_complete)

    response = await handle_message("hello")
    assert response.message  # something came back
    assert "[user] first msg" in captured["prompt"]
    assert "[assistant] first reply" in captured["prompt"]
    # The new turn is appended as the trailing [user] line.
    assert captured["prompt"].rstrip().endswith("[user] hello")


@pytest.mark.asyncio
async def test_handler_passes_real_portfolio_context_to_prompt(
    chat_db_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression for B017: the handler must wire real portfolio context into the prompt.

    Seeds a position via the real ``execute_trade`` path, then asks
    ``handle_message`` "what's my portfolio?". The prompt builder is
    monkeypatched so we can inspect the ``portfolio_ctx`` argument it
    receives — proving the context reached the prompt, not just the
    response. The mock LLM is used (``LLM_MOCK=true`` from conftest).
    """
    from app.market import PriceCache
    from app.portfolio import execute_trade

    # Live cache: seed prices and buy 3 AAPL so a position exists.
    price_cache = PriceCache()
    price_cache.update("AAPL", 192.00)
    result = await execute_trade("AAPL", "buy", 3.0, price_cache)
    assert result.position_quantity == 3.0

    captured: dict[str, Any] = {}
    original_build = chat_handler.build_system_prompt

    def recording_build(portfolio_ctx, summary, verbatim_history):  # type: ignore[no-untyped-def]
        captured["portfolio_ctx"] = portfolio_ctx
        captured["summary"] = summary
        captured["verbatim_history"] = list(verbatim_history)
        return original_build(portfolio_ctx, summary, verbatim_history)

    monkeypatch.setattr(chat_handler, "build_system_prompt", recording_build)

    response = await handle_message(
        "what's my portfolio?", price_cache=price_cache
    )

    # The mock dispatcher answers something; we don't care exactly what.
    assert response.message

    ctx = captured["portfolio_ctx"]
    assert isinstance(ctx, dict)
    assert ctx, "portfolio context was empty — B017 regression"

    # The new position must be visible to the LLM.
    tickers = {p["ticker"] for p in ctx["positions"]}
    assert "AAPL" in tickers, f"AAPL position missing from context: {ctx}"
    aapl = next(p for p in ctx["positions"] if p["ticker"] == "AAPL")
    assert aapl["quantity"] == 3.0
    assert aapl["current_price"] == 192.00

    # Cash decreased; total_value approximately preserved.
    assert ctx["cash_balance"] == pytest.approx(10000.0 - 3 * 192.00)


@pytest.mark.asyncio
async def test_malformed_llm_response_returns_fallback(
    chat_db_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If client.complete raises LLMResponseError the handler returns a fallback."""
    from app.chat.client import LLMResponseError

    def broken_complete(system_prompt: str, user_text: str, **kwargs: Any) -> Any:
        raise LLMResponseError("malformed")

    monkeypatch.setattr(chat_handler.llm_client, "complete", broken_complete)

    response = await handle_message("hello")
    assert response.actions == []
    assert "couldn't" in response.message.lower() or "sorry" in response.message.lower()
