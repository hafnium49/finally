"""Fixtures for the chat subsystem tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.db import init_database


@pytest.fixture
def chat_db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Initialize a fresh SQLite DB under tmp_path and pin FINALLY_DB_PATH at it."""
    db_path = tmp_path / "nested" / "finally.db"
    monkeypatch.setenv("FINALLY_DB_PATH", str(db_path))
    init_database(db_path)
    return db_path


@pytest.fixture(autouse=True)
def _force_mock_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests in this directory must never call out to OpenRouter."""
    monkeypatch.setenv("LLM_MOCK", "true")
