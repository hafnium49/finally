"""Fixtures for portfolio + trade tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.db import init_database
from app.market import PriceCache


@pytest.fixture
def tmp_db_path(tmp_path: Path, monkeypatch) -> Path:
    """Isolated SQLite DB; sets ``FINALLY_DB_PATH`` so all module imports see it."""
    path = tmp_path / "finally.db"
    monkeypatch.setenv("FINALLY_DB_PATH", str(path))
    init_database()
    return path


@pytest.fixture
def price_cache() -> PriceCache:
    return PriceCache()
