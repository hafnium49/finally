"""Tests for ``POST /api/chat`` (API_CONTRACT.md §5).

These cover the wrapper-level behavior owned by the Backend API Engineer:
body validation, the 503 graceful degradation when ``app.chat`` is missing,
and the wire-shape normalization (e.g. ``actions=None`` → ``[]``).

End-to-end LLM behavior is owned by the LLM Engineer's tests in
``tests/chat/``.
"""

from __future__ import annotations

import sys
import types

import pytest


@pytest.fixture
def stub_chat_module(monkeypatch):
    """Install a stub ``app.chat`` module exposing ``handle_message``.

    Yields the stub so tests can swap its ``handle_message`` per-case.
    """
    mod = types.ModuleType("app.chat")

    async def default_handler(message: str):
        return {"message": "ok", "actions": []}

    mod.handle_message = default_handler  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "app.chat", mod)
    yield mod


async def test_chat_503_when_app_chat_missing(client, monkeypatch):
    """If ``app.chat`` is not importable, the route returns 503 ``chat_not_ready``."""
    # Block import: make `app.chat` raise ImportError on access.
    monkeypatch.setitem(sys.modules, "app.chat", None)
    response = await client.post("/api/chat", json={"message": "hello"})
    assert response.status_code == 503
    assert response.json()["error"] == "chat_not_ready"


async def test_chat_delegates_to_handle_message(client, stub_chat_module):
    captured: dict = {}

    async def handler(message: str):
        captured["message"] = message
        return {
            "message": "Hello — I'm FinAlly (mock mode).",
            "actions": [],
        }

    stub_chat_module.handle_message = handler

    response = await client.post("/api/chat", json={"message": "hi"})
    assert response.status_code == 200
    assert captured == {"message": "hi"}
    assert response.json() == {
        "message": "Hello — I'm FinAlly (mock mode).",
        "actions": [],
    }


async def test_chat_normalizes_none_actions_to_empty_list(client, stub_chat_module):
    async def handler(message: str):
        return {"message": "fine", "actions": None}

    stub_chat_module.handle_message = handler
    response = await client.post("/api/chat", json={"message": "yo"})
    assert response.status_code == 200
    assert response.json()["actions"] == []


async def test_chat_accepts_pydantic_model_return(client, stub_chat_module):
    """If the LLM Engineer returns a Pydantic ``ChatResponse``, we dump it."""

    class FakeResponse:
        def model_dump(self):
            return {"message": "via pydantic", "actions": []}

    async def handler(message: str):
        return FakeResponse()

    stub_chat_module.handle_message = handler
    response = await client.post("/api/chat", json={"message": "yo"})
    assert response.status_code == 200
    assert response.json()["message"] == "via pydantic"


async def test_chat_empty_message_returns_422(client):
    response = await client.post("/api/chat", json={"message": ""})
    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


async def test_chat_oversized_message_returns_422(client):
    response = await client.post(
        "/api/chat", json={"message": "x" * 5000}
    )
    assert response.status_code == 422


async def test_chat_missing_body_returns_422(client):
    response = await client.post("/api/chat", json={})
    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


async def test_chat_handler_exception_returns_500(client, stub_chat_module):
    async def handler(message: str):
        raise RuntimeError("LLM exploded")

    stub_chat_module.handle_message = handler
    response = await client.post("/api/chat", json={"message": "hello"})
    assert response.status_code == 500
    assert response.json()["error"] == "internal_error"
