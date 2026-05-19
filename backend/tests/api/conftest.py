"""Fixtures for API route tests.

Each test gets:
  - An isolated SQLite DB under tmp_path (via FINALLY_DB_PATH).
  - A FastAPI app instance with a custom lifespan that:
      * runs init_database() against the tmp DB
      * creates a PriceCache (no background tasks, no live market source —
        we don't want randomness or asyncio loops in unit tests).
      * registers the api_router + error handlers
  - An ``httpx.AsyncClient`` bound to ``ASGITransport(app=app)``.

This keeps the tests fast and deterministic. The market source is replaced
with a stub that records add/remove calls but never produces ticks; tests
seed the PriceCache by hand.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI

from app.api import api_router
from app.api.errors import register_error_handlers
from app.db import init_database
from app.market import PriceCache


class _StubMarketSource:
    """A no-op MarketDataSource used in API tests.

    Tests poke prices directly into the PriceCache via ``app.state.price_cache``;
    the stub just records add/remove calls so we can assert wiring.
    """

    def __init__(self) -> None:
        self.added: list[str] = []
        self.removed: list[str] = []
        self.tickers: list[str] = []

    async def start(self, tickers):  # noqa: D401
        self.tickers = list(tickers)

    async def stop(self):
        pass

    async def add_ticker(self, ticker: str) -> None:
        self.added.append(ticker)
        if ticker not in self.tickers:
            self.tickers.append(ticker)

    async def remove_ticker(self, ticker: str) -> None:
        self.removed.append(ticker)
        if ticker in self.tickers:
            self.tickers.remove(ticker)

    def get_tickers(self):
        return list(self.tickers)


@pytest.fixture
def tmp_db_path(tmp_path: Path, monkeypatch) -> Path:
    """Isolated DB file for one test; sets FINALLY_DB_PATH for the process."""
    path = tmp_path / "finally.db"
    monkeypatch.setenv("FINALLY_DB_PATH", str(path))
    monkeypatch.setenv("LLM_MOCK", "true")
    return path


@pytest.fixture
def price_cache() -> PriceCache:
    return PriceCache()


@pytest.fixture
def stub_market_source() -> _StubMarketSource:
    return _StubMarketSource()


@pytest.fixture
def app(tmp_db_path: Path, price_cache: PriceCache, stub_market_source) -> FastAPI:
    """Build a FastAPI app wired with the test's PriceCache + stub source."""
    init_database()

    @asynccontextmanager
    async def _test_lifespan(app: FastAPI):
        app.state.price_cache = price_cache
        app.state.market_source = stub_market_source
        yield

    test_app = FastAPI(lifespan=_test_lifespan)
    register_error_handlers(test_app)
    test_app.include_router(api_router)
    return test_app


@pytest_asyncio.fixture
async def client(app: FastAPI):
    """``httpx.AsyncClient`` bound to the test app via ASGI transport."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        # Trigger the lifespan startup so app.state is populated.
        async with httpx.AsyncClient(transport=transport, base_url="http://test"):
            pass
        # Simpler: explicit lifespan via LifespanManager. httpx ASGITransport
        # does NOT run lifespan by default, so wire it up manually.
        yield c


# ---------------------------------------------------------------------------
# Lifespan-aware client (httpx ASGITransport does not call lifespan by default).
# We use a small async lifespan manager so the test's lifespan populates
# ``app.state`` before any request runs.
# ---------------------------------------------------------------------------


class _LifespanManager:
    """Minimal context manager that exercises an ASGI app's lifespan protocol."""

    def __init__(self, app):
        self.app = app
        self._receive_q: asyncio.Queue = asyncio.Queue()
        self._send_q: asyncio.Queue = asyncio.Queue()
        self._task: asyncio.Task | None = None

    async def __aenter__(self):
        self._task = asyncio.create_task(self._run())
        await self._receive_q.put({"type": "lifespan.startup"})
        await self._wait_for("lifespan.startup.complete")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._receive_q.put({"type": "lifespan.shutdown"})
        try:
            await self._wait_for("lifespan.shutdown.complete")
        finally:
            if self._task and not self._task.done():
                self._task.cancel()
                try:
                    await self._task
                except (asyncio.CancelledError, Exception):
                    pass

    async def _run(self):
        async def receive():
            return await self._receive_q.get()

        async def send(message):
            await self._send_q.put(message)

        await self.app({"type": "lifespan"}, receive, send)

    async def _wait_for(self, type_):
        while True:
            msg = await self._send_q.get()
            if msg["type"] == type_:
                return
            if msg["type"].endswith(".failed"):
                raise RuntimeError(f"Lifespan failed: {msg!r}")


@pytest_asyncio.fixture
async def lifespan_client(app: FastAPI):
    """A client whose lifespan startup has actually run (populating app.state)."""
    async with _LifespanManager(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
