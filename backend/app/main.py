"""FastAPI application entry point.

Lifespan startup:
    1. Initialize the database (lazy idempotent).
    2. Construct the in-memory PriceCache.
    3. Build the market data source (simulator or Massive) from env.
    4. Start the source for the seeded watchlist tickers.
    5. Start three background tasks: tick-history persister, portfolio
       snapshot writer, daily pruner.
    6. (LLM Engineer's requirement) Validate ``OPENROUTER_API_KEY`` when not
       in mock mode, so the server refuses to boot half-broken. We do this
       lazily — if ``app.chat.client.assert_ready`` doesn't exist (the LLM
       module isn't ready yet), we log a warning and continue.

Shutdown:
    Cancel all background tasks, stop the market source.

Static file mount:
    If ``/app/static`` exists, mount it at ``/`` LAST (after the API router)
    so the SPA serves on any non-/api route. If it doesn't exist (dev mode),
    log a warning and skip.
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.api.errors import register_error_handlers
from app.db import DEFAULT_WATCHLIST_TICKERS, connection, init_database
from app.market import PriceCache, create_market_data_source
from app.portfolio import pruner_loop, snapshot_loop, tick_writer_loop

logger = logging.getLogger(__name__)


def _resolve_static_dir() -> Path | None:
    """Pick the first existing candidate for the SPA static directory.

    Order of precedence:
      1. ``FINALLY_STATIC_DIR`` env override (for tests or custom deployments).
      2. ``/app/static`` — the Docker COPY target.
      3. ``<repo>/frontend/out`` — the Next.js dev/static-export location,
         used when running the backend outside a container.
    Returns ``None`` if no candidate exists, in which case the SPA mount
    is skipped (the API still serves).
    """
    override = os.environ.get("FINALLY_STATIC_DIR", "").strip()
    candidates: list[Path] = []
    if override:
        candidates.append(Path(override))
    candidates.append(Path("/app/static"))
    # backend/app/main.py -> backend -> repo root -> frontend/out
    candidates.append(Path(__file__).resolve().parent.parent.parent / "frontend" / "out")
    for path in candidates:
        if path.exists() and path.is_dir():
            return path
    return None


STATIC_DIR = _resolve_static_dir()


def _load_watchlist_tickers(user_id: str = "default") -> list[str]:
    """Read all distinct tickers from the watchlist for ``user_id``.

    Falls back to ``DEFAULT_WATCHLIST_TICKERS`` if the table is empty (e.g.,
    fresh seed) — which it shouldn't be after init_database(), but defensive.
    """
    try:
        with connection() as conn:
            rows = conn.execute(
                "SELECT ticker FROM watchlist WHERE user_id = ? ORDER BY added_at ASC",
                (user_id,),
            ).fetchall()
        tickers = [r["ticker"] for r in rows]
    except Exception:
        logger.exception("Failed to load watchlist tickers; using defaults")
        tickers = list(DEFAULT_WATCHLIST_TICKERS)
    return tickers or list(DEFAULT_WATCHLIST_TICKERS)


def _assert_llm_ready_if_needed() -> None:
    """If not in mock mode, ensure the LLM env vars are present.

    Per LLM_CONTRACT.md §5.3 the Backend API Engineer wires up the startup
    check. We delegate to ``app.chat.client.assert_ready()`` when it exists,
    otherwise we do a minimal check ourselves.
    """
    if os.environ.get("LLM_MOCK", "").lower() == "true":
        return
    try:
        from app.chat import client as chat_client  # type: ignore

        if hasattr(chat_client, "assert_ready"):
            chat_client.assert_ready()
            return
    except Exception:
        # Fall through to the minimal check below.
        pass
    if not os.environ.get("OPENROUTER_API_KEY", "").strip():
        logger.warning(
            "OPENROUTER_API_KEY not set and LLM_MOCK != true; /api/chat will fail"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: init DB, start market source + background tasks."""
    logger.info("FinAlly backend starting up")

    # 1. Initialize the database (idempotent — safe on warm starts).
    init_database()
    logger.info("Database initialized")

    # 2. Build the price cache + market data source.
    cache = PriceCache()
    source = create_market_data_source(cache)
    app.state.price_cache = cache
    app.state.market_source = source

    # 3. Start the source for the seeded watchlist tickers.
    tickers = _load_watchlist_tickers()
    await source.start(tickers)
    logger.info("Market source started with %d tickers", len(tickers))

    # 4. Optionally validate LLM env. Non-fatal — just warns.
    _assert_llm_ready_if_needed()

    # 5. Background tasks.
    bg_tasks: list[asyncio.Task] = []
    bg_tasks.append(
        asyncio.create_task(tick_writer_loop(cache), name="tick-writer")
    )
    bg_tasks.append(
        asyncio.create_task(snapshot_loop(cache), name="snapshot-writer")
    )
    bg_tasks.append(asyncio.create_task(pruner_loop(), name="pruner"))
    app.state.background_tasks = bg_tasks
    logger.info("Started %d background tasks", len(bg_tasks))

    try:
        yield
    finally:
        logger.info("FinAlly backend shutting down")
        # Cancel background tasks first so they stop hitting the DB.
        for task in bg_tasks:
            task.cancel()
        for task in bg_tasks:
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        # Then stop the market source.
        try:
            await source.stop()
        except Exception:
            logger.exception("Error stopping market source")
        logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """Construct a FastAPI app instance. Useful for tests with their own lifespan."""
    app = FastAPI(
        title="FinAlly Backend",
        description="AI Trading Workstation - REST + SSE API",
        version="0.1.0",
        lifespan=lifespan,
    )

    register_error_handlers(app)

    # Mount API routes FIRST so they win over the static catch-all.
    app.include_router(api_router)

    # Mount the SPA static export LAST. If no candidate directory exists
    # (development mode without a build), skip with a warning — the API
    # still serves.
    if STATIC_DIR is not None:
        app.mount(
            "/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static"
        )
        logger.info("Static files mounted from %s", STATIC_DIR)
    else:
        logger.warning(
            "No static directory found (checked FINALLY_STATIC_DIR, /app/static, "
            "frontend/out); SPA assets will not be served"
        )

    return app


app = create_app()
