"""Fixtures for ``app.db`` tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    """Return an isolated SQLite file path under pytest's ``tmp_path``.

    The file itself is not created — callers (typically ``init_database``)
    are responsible for that. Using a nested directory lets us also exercise
    the "parent directory does not yet exist" branch.
    """
    return tmp_path / "nested" / "finally.db"
