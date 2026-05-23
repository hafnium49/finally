"""Aggregated FastAPI router for all ``/api/*`` routes.

The top-level :data:`api_router` is mounted by ``app.main`` with prefix
``/api``. Each sub-router below carries its own intra-prefix (e.g.
``/portfolio``, ``/watchlist``) so the route hierarchy mirrors the
documentation in ``planning/API_CONTRACT.md``.

Mount order matters in ``main.py``: ``api_router`` is registered before any
static-file catch-all, so the SPA fallback never shadows ``/api/*``.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.chat import router as chat_router
from app.api.market import router as market_router
from app.api.portfolio import router as portfolio_router
from app.api.system import router as system_router
from app.api.watchlist import router as watchlist_router

api_router = APIRouter(prefix="/api")
api_router.include_router(market_router)
api_router.include_router(watchlist_router)
api_router.include_router(portfolio_router)
api_router.include_router(chat_router)
api_router.include_router(system_router)

__all__ = ["api_router"]
