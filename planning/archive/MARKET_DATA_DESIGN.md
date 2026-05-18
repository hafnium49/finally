# Market Data Backend — Detailed Design

Implementation-ready design for the FinAlly market data subsystem. Everything described here lives under `backend/app/market/` and is consumed by the rest of the backend through a single public API exported from `app.market`.

The design honors the contracts in `planning/PLAN.md` (§6 Market Data, §7 Database, §8 API Endpoints, §10 Frontend Design) and incorporates the lessons from the previous review cycle archived in `planning/archive/MARKET_DATA_REVIEW.md`.

---

## Table of Contents

1. [Goals & Non-Goals](#1-goals--non-goals)
2. [Architecture at a Glance](#2-architecture-at-a-glance)
3. [File Layout](#3-file-layout)
4. [Data Model — `models.py`](#4-data-model--modelspy)
5. [Price Cache — `cache.py`](#5-price-cache--cachepy)
6. [Abstract Interface — `interface.py`](#6-abstract-interface--interfacepy)
7. [Seed Prices & Parameters — `seed_prices.py`](#7-seed-prices--parameters--seed_pricespy)
8. [GBM Simulator — `simulator.py`](#8-gbm-simulator--simulatorpy)
9. [Massive API Client — `massive_client.py`](#9-massive-api-client--massive_clientpy)
10. [Factory — `factory.py`](#10-factory--factorypy)
11. [SSE Streaming — `stream.py`](#11-sse-streaming--streampy)
12. [Session Anchor & `change_pct` — `session.py`](#12-session-anchor--change_pct--sessionpy)
13. [Tick Persister — `persister.py`](#13-tick-persister--persisterpy)
14. [Historical Price Endpoint](#14-historical-price-endpoint)
15. [FastAPI Lifespan Wiring](#15-fastapi-lifespan-wiring)
16. [Watchlist Coordination](#16-watchlist-coordination)
17. [Testing Strategy](#17-testing-strategy)
18. [Error Handling & Edge Cases](#18-error-handling--edge-cases)
19. [Configuration Summary](#19-configuration-summary)
20. [Public API (`__init__.py`)](#20-public-api-__init__py)

---

## 1. Goals & Non-Goals

### Goals

- A **single unified interface** (`MarketDataSource`) that both the simulator and the Massive API client implement, so downstream code (SSE, trade execution, portfolio valuation) is source-agnostic.
- An **in-memory `PriceCache`** that is the single point of truth for "the latest price right now". One writer (the active data source), many readers (SSE, trades, snapshots).
- A **GBM simulator** that produces realistic-looking, correlated, sub-second price ticks with no external dependencies.
- A **Massive REST poller** that gracefully degrades on rate-limit / network errors and runs on a configurable cadence (15 s on the free tier).
- A **push-on-change SSE endpoint** that only emits when the cache actually advances, plus periodic keepalive comments to stop proxies closing idle connections.
- A **tick-history persister** that writes `price_ticks` rows on a fixed cadence regardless of how chatty the upstream feed is, plus a daily pruner.
- A **REST history endpoint** (`GET /api/prices/history/{ticker}`) that serves the main chart's initial load.

### Non-Goals

- No order book, no limit orders, no partial fills (per PLAN §3 "Why These Choices").
- No multi-user prices — prices are global; positions/watchlist are per-user.
- No retention strategy for `portfolio_snapshots` (PLAN §7 explicitly defers that).
- No WebSocket fallback. SSE handles disconnection natively via `EventSource`'s built-in retry.

---

## 2. Architecture at a Glance

```
                       ┌──────────────────────────────────┐
                       │   MarketDataSource  (interface)  │
                       └───────────────┬──────────────────┘
                                       │ implements
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
   SimulatorDataSource (GBM)                       MassiveDataSource (REST poll)
                \                                             /
                 \   exactly one is active per process       /
                  \                                         /
                   ▼                                       ▼
                       ┌──────────────────────────────┐
                       │     PriceCache (in-memory)   │  ← single writer, many readers
                       │  versioned, thread-safe      │
                       └──────────────┬───────────────┘
                                      │
       ┌───────────────────┬──────────┼──────────┬────────────────────────┐
       ▼                   ▼          ▼          ▼                        ▼
  SSE stream     Trade execution  Portfolio  Tick persister      Session anchor /
  (push-on-      (`fill_price` =  snapshot   (writes             change_pct
   change)        cache value)    writer     `price_ticks`)      computation
```

Three background tasks read the cache on independent schedules (PLAN §6):

| Task | Cadence | Purpose | Owner |
|------|---------|---------|-------|
| Price source (sim or Massive) | 0.5 s (sim) / 15 s (Massive) | **Only writer** to the cache | `market/` |
| SSE stream | check every 0.5 s, emit on version bump | Push prices to browsers | `market/stream.py` |
| Tick persister | every 5 s per ticker | Append to `price_ticks` | `market/persister.py` |
| Portfolio snapshot writer | every 30 s + after each trade | Append to `portfolio_snapshots` | `portfolio/` (not market) |

The portfolio snapshot writer lives in `portfolio/`, not `market/`, because it depends on the positions table. It is mentioned here only for completeness of the cache-reader picture.

---

## 3. File Layout

```
backend/app/market/
├── __init__.py            # Public re-exports
├── models.py              # PriceUpdate dataclass
├── cache.py               # PriceCache (versioned, thread-safe)
├── interface.py           # MarketDataSource ABC
├── seed_prices.py         # SEED_PRICES, TICKER_PARAMS, correlation constants
├── simulator.py           # GBMSimulator (math) + SimulatorDataSource (async wrapper)
├── massive_client.py      # MassiveDataSource (REST poller)
├── factory.py             # create_market_data_source()
├── stream.py              # SSE endpoint factory + generator
├── session.py             # Session-anchor store for change_pct
└── persister.py           # price_ticks writer + pruner
```

Each file has a single responsibility. `__init__.py` is the only entry point the rest of the backend should import from.

---

## 4. Data Model — `models.py`

`PriceUpdate` is the *only* shape that leaves the market data layer. SSE serializes it, trade execution reads `price` from it, portfolio valuation reads `price` from it. Keeping it as a frozen dataclass means there is no accidental mutation across the read paths.

```python
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PriceUpdate:
    """Immutable snapshot of one ticker's price at a point in time."""

    ticker: str
    price: float
    previous_price: float
    timestamp: float = field(default_factory=time.time)  # Unix seconds

    @property
    def change(self) -> float:
        return round(self.price - self.previous_price, 4)

    @property
    def change_percent(self) -> float:
        if self.previous_price == 0:
            return 0.0
        return round((self.price - self.previous_price) / self.previous_price * 100, 4)

    @property
    def direction(self) -> str:
        if self.price > self.previous_price:
            return "up"
        if self.price < self.previous_price:
            return "down"
        return "flat"

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "price": self.price,
            "previous_price": self.previous_price,
            "timestamp": self.timestamp,
            "change": self.change,
            "change_percent": self.change_percent,
            "direction": self.direction,
        }
```

Notes:

- `change`, `change_percent`, `direction` are derived properties — they can never go stale relative to `price`.
- `slots=True` shaves per-instance memory; we create millions of these per day.
- `to_dict()` is the single SSE/REST serialization point.
- `change_percent` here is the **tick-to-tick** delta, not the session change. The session-anchored "daily change %" lives separately in `session.py` (§12).

---

## 5. Price Cache — `cache.py`

The cache holds the latest `PriceUpdate` per ticker plus a monotonic version counter. The version counter is what lets the SSE generator avoid emitting redundant frames when the upstream (e.g. Massive on free tier) only updates every 15 seconds.

```python
from __future__ import annotations

import time
from threading import Lock

from .models import PriceUpdate


class PriceCache:
    """Versioned, thread-safe store of the latest price per ticker.

    Concurrency model:
        - Exactly one writer at a time (the active MarketDataSource).
        - Many readers across asyncio tasks and the SSE generator.
        - Massive's REST client is synchronous and runs via asyncio.to_thread,
          so a `threading.Lock` (not asyncio.Lock) is the correct primitive.
    """

    def __init__(self) -> None:
        self._prices: dict[str, PriceUpdate] = {}
        self._lock = Lock()
        self._version: int = 0  # bumped only when a price actually changes

    def update(self, ticker: str, price: float, timestamp: float | None = None) -> PriceUpdate:
        """Record a new price. Returns the created PriceUpdate.

        Version is incremented only when `price` differs from the previously
        cached price (rounded to 2 dp). This is what makes SSE push-on-change.
        """
        with self._lock:
            ts = timestamp if timestamp is not None else time.time()
            prev = self._prices.get(ticker)
            previous_price = prev.price if prev is not None else price
            rounded = round(price, 2)
            previous_rounded = round(previous_price, 2)

            update = PriceUpdate(
                ticker=ticker,
                price=rounded,
                previous_price=previous_rounded,
                timestamp=ts,
            )
            self._prices[ticker] = update

            # Only bump version when the visible price actually moves.
            # First-ever update counts as a change so consumers see it.
            if prev is None or rounded != previous_rounded:
                self._version += 1

            return update

    def get(self, ticker: str) -> PriceUpdate | None:
        with self._lock:
            return self._prices.get(ticker)

    def get_price(self, ticker: str) -> float | None:
        u = self.get(ticker)
        return u.price if u is not None else None

    def get_all(self) -> dict[str, PriceUpdate]:
        with self._lock:
            return dict(self._prices)

    def remove(self, ticker: str) -> None:
        with self._lock:
            if self._prices.pop(ticker, None) is not None:
                self._version += 1

    @property
    def version(self) -> int:
        # CPython int-load is atomic under the GIL; under no-GIL Python 3.13t+
        # we'd want a lock. Acceptable for v1.
        with self._lock:
            return self._version

    def __len__(self) -> int:
        with self._lock:
            return len(self._prices)

    def __contains__(self, ticker: str) -> bool:
        with self._lock:
            return ticker in self._prices
```

### Why `threading.Lock`, not `asyncio.Lock`

Massive's `RESTClient.get_snapshot_all()` is synchronous; we run it via `asyncio.to_thread(...)`, which actually executes in a real OS thread. An `asyncio.Lock` would not protect that thread. `threading.Lock` is correct on both sides.

### Why bump version only on change

If Massive polls every 15 s and re-writes the same price, we don't want the SSE loop to fire a frame. Version-bump-on-change collapses the two cases — "no upstream update" and "upstream update with same price" — into the same no-op behavior downstream. This was a finding in the archived review (§3.4); we now lock the `version` read for consistency.

---

## 6. Abstract Interface — `interface.py`

The contract every data source obeys. Note the **lifecycle**: `start` once, `add_ticker`/`remove_ticker` as the watchlist mutates, `stop` once on shutdown.

```python
from __future__ import annotations

from abc import ABC, abstractmethod


class MarketDataSource(ABC):
    """Contract for market data providers.

    Implementations push price updates into a shared PriceCache on their own
    schedule. Downstream code never asks the source for prices — it reads
    the cache.
    """

    @abstractmethod
    async def start(self, tickers: list[str]) -> None:
        """Begin producing updates for `tickers`. Call exactly once."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop the background task. Idempotent: safe to call twice."""

    @abstractmethod
    async def add_ticker(self, ticker: str) -> None:
        """Track a new ticker. No-op if already tracked."""

    @abstractmethod
    async def remove_ticker(self, ticker: str) -> None:
        """Stop tracking a ticker. No-op if not tracked.
        Also evicts the ticker from the PriceCache."""

    @abstractmethod
    def get_tickers(self) -> list[str]:
        """Return the current list of tracked tickers (snapshot copy)."""
```

The push-model decouples cadence: the simulator ticks at 0.5 s, Massive polls at 15 s, but the cache always has *some* answer for "what's the latest price for AAPL?". Consumers don't care which source is active.

---

## 7. Seed Prices & Parameters — `seed_prices.py`

Pure data, no logic. Used by the simulator for initial prices and GBM params.

```python
"""Seed prices, GBM parameters, and correlation groups for the simulator."""

SEED_PRICES: dict[str, float] = {
    "AAPL": 190.00,
    "GOOGL": 175.00,
    "MSFT": 420.00,
    "AMZN": 185.00,
    "TSLA": 250.00,
    "NVDA": 800.00,
    "META": 500.00,
    "JPM": 195.00,
    "V": 280.00,
    "NFLX": 600.00,
}

# Annualized drift (mu) and volatility (sigma) per ticker.
TICKER_PARAMS: dict[str, dict[str, float]] = {
    "AAPL":  {"sigma": 0.22, "mu": 0.05},
    "GOOGL": {"sigma": 0.25, "mu": 0.05},
    "MSFT":  {"sigma": 0.20, "mu": 0.05},
    "AMZN":  {"sigma": 0.28, "mu": 0.05},
    "TSLA":  {"sigma": 0.50, "mu": 0.03},
    "NVDA":  {"sigma": 0.40, "mu": 0.08},
    "META":  {"sigma": 0.30, "mu": 0.05},
    "JPM":   {"sigma": 0.18, "mu": 0.04},
    "V":     {"sigma": 0.17, "mu": 0.04},
    "NFLX":  {"sigma": 0.35, "mu": 0.05},
}

DEFAULT_PARAMS: dict[str, float] = {"sigma": 0.25, "mu": 0.05}

# Plausible seed-price range for unknown tickers added at runtime.
UNKNOWN_SEED_PRICE_RANGE: tuple[float, float] = (20.0, 400.0)

CORRELATION_GROUPS: dict[str, set[str]] = {
    "tech":    {"AAPL", "GOOGL", "MSFT", "AMZN", "META", "NVDA", "NFLX"},
    "finance": {"JPM", "V"},
}

INTRA_TECH_CORR    = 0.6  # tech stocks move together
INTRA_FINANCE_CORR = 0.5  # finance stocks move together
CROSS_GROUP_CORR   = 0.3  # cross-sector default (also used for unknown tickers)
TSLA_CORR          = 0.3  # TSLA does its own thing
```

`CROSS_GROUP_CORR` doubles as the fallback for unknown tickers — the previous review flagged the redundant `DEFAULT_CORR` constant and we have removed it here.

---

## 8. GBM Simulator — `simulator.py`

Two classes:

- `GBMSimulator` — pure math, stateful, single-threaded.
- `SimulatorDataSource` — `MarketDataSource` implementation that runs `step()` on an `asyncio` cadence and writes to the cache.

### 8.1 `GBMSimulator`

```python
from __future__ import annotations

import asyncio
import logging
import math
import random

import numpy as np

from .cache import PriceCache
from .interface import MarketDataSource
from .seed_prices import (
    CORRELATION_GROUPS,
    CROSS_GROUP_CORR,
    DEFAULT_PARAMS,
    INTRA_FINANCE_CORR,
    INTRA_TECH_CORR,
    SEED_PRICES,
    TICKER_PARAMS,
    TSLA_CORR,
    UNKNOWN_SEED_PRICE_RANGE,
)

logger = logging.getLogger(__name__)


class GBMSimulator:
    """Geometric Brownian Motion price simulator with correlated draws.

    S(t+dt) = S(t) * exp((mu - sigma^2/2) * dt + sigma * sqrt(dt) * Z)

    `Z` is a correlated standard normal draw produced from independent
    draws via a Cholesky factor of the correlation matrix.
    """

    # 252 trading days * 6.5 hrs * 3600 s = 5,896,800 s in a trading year.
    TRADING_SECONDS_PER_YEAR = 252 * 6.5 * 3600
    DEFAULT_DT = 0.5 / TRADING_SECONDS_PER_YEAR  # ~8.48e-8

    def __init__(
        self,
        tickers: list[str],
        dt: float = DEFAULT_DT,
        event_probability: float = 0.001,
    ) -> None:
        self._dt = dt
        self._event_prob = event_probability
        self._tickers: list[str] = []
        self._prices: dict[str, float] = {}
        self._params: dict[str, dict[str, float]] = {}
        self._cholesky: np.ndarray | None = None

        for t in tickers:
            self._add_ticker_internal(t)
        self._rebuild_cholesky()

    # ---------- Public API ----------

    def step(self) -> dict[str, float]:
        """Advance all tickers by one time step. Returns {ticker: new_price}."""
        n = len(self._tickers)
        if n == 0:
            return {}

        z_indep = np.random.standard_normal(n)
        z_corr = self._cholesky @ z_indep if self._cholesky is not None else z_indep

        out: dict[str, float] = {}
        for i, ticker in enumerate(self._tickers):
            p = self._params[ticker]
            mu, sigma = p["mu"], p["sigma"]
            drift = (mu - 0.5 * sigma * sigma) * self._dt
            diffusion = sigma * math.sqrt(self._dt) * z_corr[i]
            self._prices[ticker] *= math.exp(drift + diffusion)

            # Occasional dramatic shock: 2–5% in either direction.
            if random.random() < self._event_prob:
                shock = random.uniform(0.02, 0.05) * random.choice((-1, 1))
                self._prices[ticker] *= 1.0 + shock
                logger.debug("Shock event on %s: %+.2f%%", ticker, shock * 100)

            out[ticker] = round(self._prices[ticker], 2)
        return out

    def add_ticker(self, ticker: str) -> None:
        if ticker in self._prices:
            return
        self._add_ticker_internal(ticker)
        self._rebuild_cholesky()

    def remove_ticker(self, ticker: str) -> None:
        if ticker not in self._prices:
            return
        self._tickers.remove(ticker)
        del self._prices[ticker]
        del self._params[ticker]
        self._rebuild_cholesky()

    def get_tickers(self) -> list[str]:
        """Public accessor — used by SimulatorDataSource.get_tickers()."""
        return list(self._tickers)

    def get_price(self, ticker: str) -> float | None:
        return self._prices.get(ticker)

    # ---------- Internals ----------

    def _add_ticker_internal(self, ticker: str) -> None:
        if ticker in self._prices:
            return
        self._tickers.append(ticker)
        if ticker in SEED_PRICES:
            self._prices[ticker] = SEED_PRICES[ticker]
        else:
            lo, hi = UNKNOWN_SEED_PRICE_RANGE
            self._prices[ticker] = round(random.uniform(lo, hi), 2)
        self._params[ticker] = dict(TICKER_PARAMS.get(ticker, DEFAULT_PARAMS))

    def _rebuild_cholesky(self) -> None:
        n = len(self._tickers)
        if n <= 1:
            self._cholesky = None
            return
        corr = np.eye(n)
        for i in range(n):
            for j in range(i + 1, n):
                rho = self._pairwise_correlation(self._tickers[i], self._tickers[j])
                corr[i, j] = rho
                corr[j, i] = rho
        self._cholesky = np.linalg.cholesky(corr)

    @staticmethod
    def _pairwise_correlation(a: str, b: str) -> float:
        tech    = CORRELATION_GROUPS["tech"]
        finance = CORRELATION_GROUPS["finance"]
        if a == "TSLA" or b == "TSLA":
            return TSLA_CORR
        if a in tech and b in tech:
            return INTRA_TECH_CORR
        if a in finance and b in finance:
            return INTRA_FINANCE_CORR
        return CROSS_GROUP_CORR
```

Per the prior review (§3.5, §3.7) we have:

- A **public** `get_tickers()` so `SimulatorDataSource` does not reach into private state.
- Removed `DEFAULT_CORR`; the fallback is `CROSS_GROUP_CORR`.

### 8.2 `SimulatorDataSource`

```python
class SimulatorDataSource(MarketDataSource):
    """Async wrapper that drives GBMSimulator and writes to PriceCache."""

    def __init__(
        self,
        price_cache: PriceCache,
        update_interval: float = 0.5,
        event_probability: float = 0.001,
    ) -> None:
        self._cache = price_cache
        self._interval = update_interval
        self._event_prob = event_probability
        self._sim: GBMSimulator | None = None
        self._task: asyncio.Task | None = None

    async def start(self, tickers: list[str]) -> None:
        self._sim = GBMSimulator(tickers=tickers, event_probability=self._event_prob)
        # Seed cache immediately so SSE has data on its first frame.
        for t in tickers:
            p = self._sim.get_price(t)
            if p is not None:
                self._cache.update(ticker=t, price=p)
        self._task = asyncio.create_task(self._run_loop(), name="simulator-loop")
        logger.info("Simulator started: %d tickers", len(tickers))

    async def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        logger.info("Simulator stopped")

    async def add_ticker(self, ticker: str) -> None:
        if not self._sim:
            return
        self._sim.add_ticker(ticker)
        p = self._sim.get_price(ticker)
        if p is not None:
            self._cache.update(ticker=ticker, price=p)
        logger.info("Simulator added %s", ticker)

    async def remove_ticker(self, ticker: str) -> None:
        if self._sim:
            self._sim.remove_ticker(ticker)
        self._cache.remove(ticker)
        logger.info("Simulator removed %s", ticker)

    def get_tickers(self) -> list[str]:
        return self._sim.get_tickers() if self._sim else []

    async def _run_loop(self) -> None:
        while True:
            try:
                if self._sim is not None:
                    for ticker, price in self._sim.step().items():
                        self._cache.update(ticker=ticker, price=price)
            except Exception:
                logger.exception("Simulator step failed; continuing")
            await asyncio.sleep(self._interval)
```

Key behaviors:

- **Immediate cache seeding** in `start()` and `add_ticker()` so the SSE endpoint and trade execution never see a "no price available yet" gap.
- **Per-step exception safety** so one bad tick doesn't end the feed.
- **Clean cancellation** for FastAPI lifespan shutdown.

---

## 9. Massive API Client — `massive_client.py`

Polls the Polygon-style snapshot endpoint on a fixed cadence. The underlying `RESTClient` from the `massive` package is synchronous and is dispatched via `asyncio.to_thread()`.

```python
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from .cache import PriceCache
from .interface import MarketDataSource

if TYPE_CHECKING:  # pragma: no cover
    from massive import RESTClient  # noqa: F401

logger = logging.getLogger(__name__)


class MassiveDataSource(MarketDataSource):
    """REST poller for Polygon.io via the `massive` Python client.

    Cadence:
      - Free tier  (5 req/min): poll every 15 s (default).
      - Paid tiers: poll every 2–5 s by passing a smaller `poll_interval`.

    A single snapshot call returns all watched tickers, so we make one
    request per cycle regardless of how many tickers are watched.
    """

    def __init__(
        self,
        api_key: str,
        price_cache: PriceCache,
        poll_interval: float = 15.0,
    ) -> None:
        self._api_key = api_key
        self._cache = price_cache
        self._interval = poll_interval
        self._tickers: list[str] = []
        self._task: asyncio.Task | None = None
        self._client: Any = None  # set in start()
        self._lock = asyncio.Lock()  # serializes ticker-set mutations

    async def start(self, tickers: list[str]) -> None:
        from massive import RESTClient  # top-level import; massive is a core dep

        self._client = RESTClient(api_key=self._api_key)
        self._tickers = list({t.upper().strip() for t in tickers})

        # First poll inline so the cache is warm before SSE clients connect.
        await self._poll_once()
        self._task = asyncio.create_task(self._poll_loop(), name="massive-poller")
        logger.info(
            "Massive poller started: %d tickers, %.1fs interval",
            len(self._tickers), self._interval,
        )

    async def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        self._client = None
        logger.info("Massive poller stopped")

    async def add_ticker(self, ticker: str) -> None:
        t = ticker.upper().strip()
        async with self._lock:
            if t not in self._tickers:
                self._tickers.append(t)
        logger.info("Massive added %s (appears on next poll)", t)

    async def remove_ticker(self, ticker: str) -> None:
        t = ticker.upper().strip()
        async with self._lock:
            self._tickers = [x for x in self._tickers if x != t]
        self._cache.remove(t)
        logger.info("Massive removed %s", t)

    def get_tickers(self) -> list[str]:
        return list(self._tickers)

    # ---------- Internals ----------

    async def _poll_loop(self) -> None:
        while True:
            await asyncio.sleep(self._interval)
            await self._poll_once()

    async def _poll_once(self) -> None:
        if not self._tickers or self._client is None:
            return
        async with self._lock:
            snapshot_tickers = list(self._tickers)
        try:
            snapshots = await asyncio.to_thread(self._fetch_snapshots, snapshot_tickers)
        except Exception as e:
            # 401 (bad key), 429 (rate limit), network errors — log and continue.
            logger.error("Massive poll failed: %s", e)
            return

        processed = 0
        for snap in snapshots:
            try:
                price = float(snap.last_trade.price)
                ts = snap.last_trade.timestamp / 1000.0  # ms → seconds
                self._cache.update(ticker=snap.ticker, price=price, timestamp=ts)
                processed += 1
            except (AttributeError, TypeError, ValueError) as e:
                logger.warning(
                    "Skipping malformed snapshot for %s: %s",
                    getattr(snap, "ticker", "???"), e,
                )
        logger.debug("Massive poll: %d/%d updates applied",
                     processed, len(snapshot_tickers))

    def _fetch_snapshots(self, tickers: list[str]) -> list:
        """Sync call into the Massive REST client. Runs in a thread."""
        from massive.rest.models import SnapshotMarketType
        return self._client.get_snapshot_all(
            market_type=SnapshotMarketType.STOCKS,
            tickers=tickers,
        )
```

### Decisions and lessons applied

- **Top-level import** of `massive` (with `TYPE_CHECKING` shim for type checkers). The previous review showed lazy imports inside methods made `patch("...RESTClient")` fragile in tests; the spec lists `massive` as a core dependency anyway.
- **Snapshot list copy under lock** so a concurrent `add_ticker`/`remove_ticker` cannot mutate the list while we hand it to a worker thread.
- **Always-resilient loop**: a 401/429/network error logs and waits for the next interval. Stale data is better than no data.
- **Per-snapshot try/except** so one bad row doesn't poison the batch.

### Error table

| Failure | Behavior | User-visible effect |
|---------|----------|---------------------|
| 401 Unauthorized | Logged once per poll, loop continues | SSE keeps streaming, prices don't update until key is fixed |
| 429 Rate limited | Logged, next poll waits `poll_interval` | Same |
| Network timeout | Logged, retry on next cycle | Same |
| Malformed snapshot row | Warning, that ticker skipped, others processed | Other tickers update normally |
| All snapshots fail | Cache retains last-known prices | Frontend shows stale prices but the UI keeps functioning |

---

## 10. Factory — `factory.py`

```python
from __future__ import annotations

import logging
import os

from .cache import PriceCache
from .interface import MarketDataSource

logger = logging.getLogger(__name__)


def create_market_data_source(price_cache: PriceCache) -> MarketDataSource:
    """Pick the data source based on env vars.

    MASSIVE_API_KEY present and non-empty → MassiveDataSource (real prices).
    Otherwise                              → SimulatorDataSource (GBM).
    """
    api_key = os.environ.get("MASSIVE_API_KEY", "").strip()
    if api_key:
        from .massive_client import MassiveDataSource
        logger.info("Market data: Massive (real)")
        return MassiveDataSource(api_key=api_key, price_cache=price_cache)
    from .simulator import SimulatorDataSource
    logger.info("Market data: GBM simulator")
    return SimulatorDataSource(price_cache=price_cache)
```

---

## 11. SSE Streaming — `stream.py`

This is the *only* network endpoint owned by the market subsystem (the REST history endpoint lives next door in §14). It uses **push-on-change** semantics with **periodic keepalive comments** so intermediaries don't kill idle connections.

```python
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from .cache import PriceCache

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 0.5
KEEPALIVE_SECONDS = 15.0
RECONNECT_RETRY_MS = 1000


def create_stream_router(price_cache: PriceCache) -> APIRouter:
    """Build a fresh APIRouter bound to this PriceCache.

    A fresh router per call avoids the "module-level router registered
    twice in tests" footgun flagged in the prior review (§3.6).
    """
    router = APIRouter(prefix="/api/stream", tags=["streaming"])

    @router.get("/prices")
    async def stream_prices(request: Request) -> StreamingResponse:
        return StreamingResponse(
            _generate_events(price_cache, request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # in case we're ever behind nginx
            },
        )

    return router


async def _generate_events(
    price_cache: PriceCache,
    request: Request,
    poll_interval: float = POLL_INTERVAL_SECONDS,
    keepalive_seconds: float = KEEPALIVE_SECONDS,
) -> AsyncGenerator[str, None]:
    """Yield SSE frames.

    - Emits a `data:` frame only when `price_cache.version` advances.
    - Emits a `: keepalive` comment every `keepalive_seconds` of silence,
      so proxies treat the connection as alive.
    - Includes a `retry:` directive so `EventSource` reconnects after 1 s.
    """
    yield f"retry: {RECONNECT_RETRY_MS}\n\n"

    last_version = -1
    last_emit = time.monotonic()
    client = request.client.host if request.client else "unknown"
    logger.info("SSE client connected: %s", client)

    try:
        # Initial snapshot so a freshly-connected browser sees the world.
        snap = price_cache.get_all()
        if snap:
            yield _format_data(snap)
            last_version = price_cache.version
            last_emit = time.monotonic()

        while True:
            if await request.is_disconnected():
                logger.info("SSE client disconnected: %s", client)
                return

            v = price_cache.version
            if v != last_version:
                last_version = v
                snap = price_cache.get_all()
                if snap:
                    yield _format_data(snap)
                    last_emit = time.monotonic()
            elif time.monotonic() - last_emit >= keepalive_seconds:
                yield ": keepalive\n\n"
                last_emit = time.monotonic()

            await asyncio.sleep(poll_interval)
    except asyncio.CancelledError:
        logger.info("SSE stream cancelled for %s", client)
        raise


def _format_data(snap: dict) -> str:
    payload = {ticker: u.to_dict() for ticker, u in snap.items()}
    return f"data: {json.dumps(payload)}\n\n"
```

### Wire format example

```
retry: 1000

data: {"AAPL":{"ticker":"AAPL","price":190.50,"previous_price":190.42,"timestamp":1707580800.5,"change":0.08,"change_percent":0.042,"direction":"up"}, "GOOGL":{...}}

: keepalive

data: {"AAPL":{...new price...}}
```

### Client-side use (illustrative)

```javascript
const es = new EventSource("/api/stream/prices");
es.onmessage = (event) => {
  const prices = JSON.parse(event.data);
  for (const [ticker, update] of Object.entries(prices)) {
    applyTickerUpdate(ticker, update);  // flash green/red, append sparkline, ...
  }
};
```

`EventSource` honors the `retry:` directive automatically.

---

## 12. Session Anchor & `change_pct` — `session.py`

PLAN.md §10 specifies that the watchlist row shows a session-anchored `change_pct`, computed against the **first price the backend observed for that ticker at process start**, and computed **server-side** so every client agrees.

This is intentionally separate from `PriceUpdate.change_percent` (which is tick-to-tick). The session anchor needs to survive across many ticks, reset on process restart, and persist nothing to disk.

```python
from __future__ import annotations

from threading import Lock

from .cache import PriceCache


class SessionAnchors:
    """In-memory store of the first price observed for each ticker this session.

    Used by GET /api/watchlist to compute change_pct relative to a stable
    anchor that resets only on process restart.
    """

    def __init__(self) -> None:
        self._anchors: dict[str, float] = {}
        self._lock = Lock()

    def observe(self, ticker: str, price: float) -> None:
        """Record the anchor for a ticker if we haven't already."""
        with self._lock:
            if ticker not in self._anchors:
                self._anchors[ticker] = price

    def get(self, ticker: str) -> float | None:
        with self._lock:
            return self._anchors.get(ticker)

    def discard(self, ticker: str) -> None:
        """Drop a ticker's anchor (e.g. on watchlist removal). Optional —
        keeping the anchor is also harmless."""
        with self._lock:
            self._anchors.pop(ticker, None)


def annotate_with_session_change(
    cache: PriceCache,
    anchors: SessionAnchors,
    tickers: list[str],
) -> list[dict]:
    """Build the GET /api/watchlist response payload for `tickers`.

    Returns one dict per ticker:
        {ticker, price, session_anchor_price, change_pct}

    where change_pct = (price - anchor) / anchor * 100, rounded to 2 dp.
    `price` and `session_anchor_price` may be None if the ticker has no
    cached price yet (newly added, Massive hasn't polled).
    """
    rows: list[dict] = []
    for t in tickers:
        update = cache.get(t)
        price = update.price if update is not None else None
        if price is not None:
            anchors.observe(t, price)
        anchor = anchors.get(t)
        change_pct: float | None = None
        if price is not None and anchor not in (None, 0):
            change_pct = round((price - anchor) / anchor * 100, 2)
        rows.append({
            "ticker": t,
            "price": price,
            "session_anchor_price": anchor,
            "change_pct": change_pct,
        })
    return rows
```

Two integration points:

1. The `add_ticker` flow on the data source seeds the cache (simulator immediately, Massive on the next poll). When `GET /api/watchlist` runs and reads a price for a ticker for the first time, `SessionAnchors.observe()` captures it.
2. `SessionAnchors` lives on `app.state.session_anchors` alongside the cache, set up in the lifespan (§15).

The frontend doesn't compute anything — it just renders `change_pct` from the API response.

---

## 13. Tick Persister — `persister.py`

PLAN.md §7 specifies a `price_ticks` table:

```
ticker TEXT, price REAL, recorded_at TEXT
PRIMARY KEY (ticker, recorded_at)
INDEX on recorded_at for pruning
```

Cadence: write every ~5 s **per ticker**, for every ticker in any watchlist. Retention: 7 days. This is independent of SSE cadence.

```python
from __future__ import annotations

import asyncio
import datetime as dt
import logging
from typing import Awaitable, Callable

from .cache import PriceCache
from .interface import MarketDataSource

logger = logging.getLogger(__name__)

# A callable returning the union of all watchlist tickers. The persister
# doesn't reach into the DB itself; the wiring layer injects this.
WatchedTickersProvider = Callable[[], Awaitable[list[str]]]

# A callable that performs the actual SQLite write. Injected so this module
# stays free of DB imports and is easy to test.
TickWriter = Callable[[list[tuple[str, float, str]]], Awaitable[None]]


class TickPersister:
    """Periodically snapshots the cache into the `price_ticks` table.

    Runs two tasks:
      - Writer loop: every `write_interval_s` seconds, append one row per
        watched ticker with the current cached price.
      - Pruner loop: once per day, delete rows older than `retention_days`.
    """

    def __init__(
        self,
        cache: PriceCache,
        get_watched: WatchedTickersProvider,
        write_rows: TickWriter,
        prune_older_than: Callable[[dt.datetime], Awaitable[int]],
        write_interval_s: float = 5.0,
        prune_interval_s: float = 24 * 3600.0,
        retention_days: int = 7,
    ) -> None:
        self._cache = cache
        self._get_watched = get_watched
        self._write_rows = write_rows
        self._prune = prune_older_than
        self._write_interval = write_interval_s
        self._prune_interval = prune_interval_s
        self._retention = dt.timedelta(days=retention_days)
        self._writer_task: asyncio.Task | None = None
        self._pruner_task: asyncio.Task | None = None

    async def start(self) -> None:
        self._writer_task = asyncio.create_task(self._writer_loop(), name="tick-writer")
        self._pruner_task = asyncio.create_task(self._pruner_loop(), name="tick-pruner")
        logger.info("Tick persister started (write=%.1fs, retention=%s)",
                    self._write_interval, self._retention)

    async def stop(self) -> None:
        for task in (self._writer_task, self._pruner_task):
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self._writer_task = self._pruner_task = None

    async def _writer_loop(self) -> None:
        while True:
            try:
                tickers = await self._get_watched()
                now_iso = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
                rows: list[tuple[str, float, str]] = []
                for t in tickers:
                    p = self._cache.get_price(t)
                    if p is not None:
                        rows.append((t, p, now_iso))
                if rows:
                    await self._write_rows(rows)
            except Exception:
                logger.exception("Tick persister write failed; continuing")
            await asyncio.sleep(self._write_interval)

    async def _pruner_loop(self) -> None:
        while True:
            await asyncio.sleep(self._prune_interval)
            try:
                cutoff = dt.datetime.utcnow() - self._retention
                deleted = await self._prune(cutoff)
                logger.info("Tick pruner: deleted %d rows older than %s",
                            deleted, cutoff.isoformat())
            except Exception:
                logger.exception("Tick pruner failed; continuing")
```

The wiring layer supplies the two callbacks (`write_rows`, `prune_older_than`). A concrete sketch in the lifespan integration:

```python
async def _write_rows(rows: list[tuple[str, float, str]]) -> None:
    # Single executemany under a short connection.
    async with db.connection() as conn:
        await conn.executemany(
            "INSERT OR IGNORE INTO price_ticks (ticker, price, recorded_at) VALUES (?, ?, ?)",
            rows,
        )
        await conn.commit()

async def _prune(cutoff: dt.datetime) -> int:
    iso = cutoff.isoformat(timespec="seconds") + "Z"
    async with db.connection() as conn:
        cur = await conn.execute("DELETE FROM price_ticks WHERE recorded_at < ?", (iso,))
        await conn.commit()
        return cur.rowcount
```

`INSERT OR IGNORE` protects against the rare case where two writer ticks land on the same ISO second for the same ticker.

---

## 14. Historical Price Endpoint

PLAN.md §8 specifies `GET /api/prices/history/{ticker}?range=1h|6h|24h|7d`. It is a **plain REST** endpoint that reads from `price_ticks`. It lives in `app/api/prices.py` rather than `app/market/`, because the market layer should not import the DB layer; but the design fits in this document for completeness.

```python
# backend/app/api/prices.py
from __future__ import annotations

import datetime as dt
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/prices", tags=["prices"])

RANGES = {
    "1h":  dt.timedelta(hours=1),
    "6h":  dt.timedelta(hours=6),
    "24h": dt.timedelta(hours=24),
    "7d":  dt.timedelta(days=7),
}


@router.get("/history/{ticker}")
async def history(
    ticker: str,
    range: Literal["1h", "6h", "24h", "7d"] = Query("1h"),
):
    if range not in RANGES:
        raise HTTPException(400, f"Unsupported range: {range}")
    cutoff = (dt.datetime.utcnow() - RANGES[range]).isoformat(timespec="seconds") + "Z"
    rows = await db.fetch_all(
        """
        SELECT recorded_at, price
        FROM price_ticks
        WHERE ticker = ? AND recorded_at >= ?
        ORDER BY recorded_at ASC
        """,
        (ticker.upper(), cutoff),
    )
    return {
        "ticker": ticker.upper(),
        "range": range,
        "points": [{"t": r["recorded_at"], "p": r["price"]} for r in rows],
    }
```

The frontend calls this once on chart selection to fill the chart, then appends live ticks from the SSE stream (PLAN.md §10 "Main chart area").

---

## 15. FastAPI Lifespan Wiring

Everything is wired up once, in the FastAPI `lifespan`.

```python
# backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.market import (
    PriceCache,
    create_market_data_source,
    create_stream_router,
)
from app.market.session import SessionAnchors
from app.market.persister import TickPersister
from app.db import init_db, list_all_watched_tickers, insert_price_ticks, prune_price_ticks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Database (creates schema + seeds defaults on first run)
    await init_db()

    # 2. In-memory shared state
    cache = PriceCache()
    anchors = SessionAnchors()
    app.state.price_cache = cache
    app.state.session_anchors = anchors

    # 3. Market data source (simulator or Massive)
    source = create_market_data_source(cache)
    app.state.market_source = source
    initial = await list_all_watched_tickers()
    await source.start(initial)

    # 4. Tick history persister
    persister = TickPersister(
        cache=cache,
        get_watched=list_all_watched_tickers,
        write_rows=insert_price_ticks,
        prune_older_than=prune_price_ticks,
    )
    app.state.tick_persister = persister
    await persister.start()

    # 5. SSE router (built per-process so route registration isn't duplicated)
    app.include_router(create_stream_router(cache))

    try:
        yield
    finally:
        await persister.stop()
        await source.stop()


app = FastAPI(title="FinAlly", lifespan=lifespan)


# Dependency helpers for other routers
def get_price_cache() -> PriceCache:
    return app.state.price_cache

def get_market_source():
    return app.state.market_source

def get_session_anchors() -> SessionAnchors:
    return app.state.session_anchors
```

---

## 16. Watchlist Coordination

When the watchlist changes — whether from the REST API or from the LLM — the data source must be told.

### Add

```python
@router.post("/watchlist")
async def add(
    payload: WatchlistAdd,
    source = Depends(get_market_source),
    cache: PriceCache = Depends(get_price_cache),
    anchors: SessionAnchors = Depends(get_session_anchors),
):
    ticker = payload.ticker.upper().strip()
    if not ticker.isalpha():
        raise HTTPException(400, "ticker must be alphabetic")
    await db.insert_watchlist_entry(ticker)
    await source.add_ticker(ticker)
    # Seed the session anchor with whatever price we have (sim is immediate;
    # Massive may take one poll cycle).
    p = cache.get_price(ticker)
    if p is not None:
        anchors.observe(ticker, p)
    return {"status": "ok", "ticker": ticker, "price": p}
```

### Remove (with open-position guard)

```python
@router.delete("/watchlist/{ticker}")
async def remove(
    ticker: str,
    source = Depends(get_market_source),
):
    ticker = ticker.upper().strip()
    await db.delete_watchlist_entry(ticker)
    # If the user still holds shares, keep tracking the ticker so
    # portfolio valuation stays accurate even though it's off the watchlist.
    pos = await db.get_position(ticker)
    if pos is None or pos.quantity == 0:
        await source.remove_ticker(ticker)
    return {"status": "ok"}
```

### Read (with `change_pct`)

```python
@router.get("/watchlist")
async def list_watchlist(
    cache: PriceCache = Depends(get_price_cache),
    anchors: SessionAnchors = Depends(get_session_anchors),
):
    tickers = await db.list_user_watchlist("default")
    from app.market.session import annotate_with_session_change
    return annotate_with_session_change(cache, anchors, tickers)
```

This is the only place that produces `change_pct`. The SSE stream still sends tick-to-tick `change_percent`; the two are intentionally distinct.

---

## 17. Testing Strategy

Tests live under `backend/tests/market/`, mirroring the module layout.

### 17.1 `test_models.py`

Tests for `PriceUpdate`:

```python
from app.market.models import PriceUpdate

def test_direction_up():
    u = PriceUpdate("AAPL", price=101.0, previous_price=100.0)
    assert u.direction == "up"
    assert u.change == 1.0
    assert u.change_percent == 1.0

def test_direction_flat_when_first_tick():
    u = PriceUpdate("AAPL", price=100.0, previous_price=100.0)
    assert u.direction == "flat"
    assert u.change == 0.0

def test_to_dict_round_trip():
    u = PriceUpdate("AAPL", price=100.5, previous_price=100.0, timestamp=1.0)
    d = u.to_dict()
    assert d["ticker"] == "AAPL"
    assert d["direction"] == "up"
    assert d["timestamp"] == 1.0

def test_immutable():
    import dataclasses
    u = PriceUpdate("AAPL", 100.0, 100.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        u.price = 101.0
```

### 17.2 `test_cache.py`

```python
from app.market.cache import PriceCache

def test_version_bumps_on_change_only():
    c = PriceCache()
    c.update("AAPL", 100.0)
    v1 = c.version
    c.update("AAPL", 100.0)   # same price, no bump
    assert c.version == v1
    c.update("AAPL", 100.5)   # different price, bump
    assert c.version == v1 + 1

def test_first_update_counts_as_change():
    c = PriceCache()
    v0 = c.version
    c.update("AAPL", 100.0)
    assert c.version == v0 + 1

def test_remove_bumps_version():
    c = PriceCache()
    c.update("AAPL", 100.0)
    v = c.version
    c.remove("AAPL")
    assert c.version == v + 1
    assert c.get("AAPL") is None

def test_concurrent_writes_are_safe():
    import threading
    c = PriceCache()
    def writer(ticker):
        for i in range(1000):
            c.update(ticker, 100.0 + i * 0.01)
    threads = [threading.Thread(target=writer, args=(f"T{i}",)) for i in range(8)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert len(c) == 8
    # Each ticker received 1000 distinct prices; each bumps version.
    assert c.version == 8 * 1000
```

### 17.3 `test_simulator.py`

```python
from app.market.simulator import GBMSimulator
from app.market.seed_prices import SEED_PRICES

def test_seeded_initial_price():
    sim = GBMSimulator(["AAPL"])
    assert sim.get_price("AAPL") == SEED_PRICES["AAPL"]

def test_unknown_ticker_gets_sensible_seed():
    sim = GBMSimulator(["ZZZZ"])
    p = sim.get_price("ZZZZ")
    assert 20.0 <= p <= 400.0

def test_step_keeps_prices_positive():
    sim = GBMSimulator(["AAPL", "TSLA"])
    for _ in range(10_000):
        for ticker, p in sim.step().items():
            assert p > 0

def test_cholesky_built_for_full_default_watchlist():
    sim = GBMSimulator(list(SEED_PRICES.keys()))
    # No exception on construction → Cholesky succeeded for the full set.
    assert sim.get_tickers() == list(SEED_PRICES.keys())

def test_add_and_remove_rebuilds_cholesky():
    sim = GBMSimulator(["AAPL"])
    assert sim._cholesky is None
    sim.add_ticker("GOOGL")
    assert sim._cholesky is not None
    sim.remove_ticker("GOOGL")
    assert sim._cholesky is None
```

### 17.4 `test_simulator_source.py` (async integration)

```python
import asyncio, pytest
from app.market.cache import PriceCache
from app.market.simulator import SimulatorDataSource

@pytest.mark.asyncio
async def test_start_immediately_seeds_cache():
    cache = PriceCache()
    src = SimulatorDataSource(cache, update_interval=0.05)
    await src.start(["AAPL", "GOOGL"])
    assert cache.get("AAPL") is not None
    assert cache.get("GOOGL") is not None
    await src.stop()

@pytest.mark.asyncio
async def test_stop_is_idempotent():
    cache = PriceCache()
    src = SimulatorDataSource(cache, update_interval=0.05)
    await src.start(["AAPL"])
    await src.stop()
    await src.stop()  # must not raise

@pytest.mark.asyncio
async def test_add_remove_ticker_round_trip():
    cache = PriceCache()
    src = SimulatorDataSource(cache, update_interval=0.05)
    await src.start(["AAPL"])
    await src.add_ticker("TSLA")
    assert "TSLA" in src.get_tickers()
    assert cache.get("TSLA") is not None
    await src.remove_ticker("TSLA")
    assert "TSLA" not in src.get_tickers()
    assert cache.get("TSLA") is None
    await src.stop()
```

### 17.5 `test_massive.py` (mocked)

```python
import pytest
from unittest.mock import MagicMock, patch
from app.market.cache import PriceCache
from app.market.massive_client import MassiveDataSource

def _snap(ticker, price, ts_ms):
    m = MagicMock()
    m.ticker = ticker
    m.last_trade.price = price
    m.last_trade.timestamp = ts_ms
    return m

@pytest.mark.asyncio
async def test_poll_writes_cache(monkeypatch):
    cache = PriceCache()
    src = MassiveDataSource("k", cache, poll_interval=60.0)
    src._tickers = ["AAPL"]
    src._client = MagicMock()

    with patch.object(src, "_fetch_snapshots", return_value=[_snap("AAPL", 190.5, 1707580800000)]):
        await src._poll_once()
    assert cache.get_price("AAPL") == 190.5

@pytest.mark.asyncio
async def test_malformed_snapshot_is_skipped():
    cache = PriceCache()
    src = MassiveDataSource("k", cache, poll_interval=60.0)
    src._tickers = ["A", "BAD"]
    src._client = MagicMock()

    bad = MagicMock(); bad.ticker = "BAD"; bad.last_trade = None
    good = _snap("A", 10.0, 1)
    with patch.object(src, "_fetch_snapshots", return_value=[good, bad]):
        await src._poll_once()
    assert cache.get_price("A") == 10.0
    assert cache.get_price("BAD") is None

@pytest.mark.asyncio
async def test_api_exception_is_swallowed():
    cache = PriceCache()
    src = MassiveDataSource("k", cache, poll_interval=60.0)
    src._tickers = ["A"]
    src._client = MagicMock()
    with patch.object(src, "_fetch_snapshots", side_effect=RuntimeError("429")):
        await src._poll_once()  # must not raise
    assert cache.get_price("A") is None
```

### 17.6 `test_factory.py`

```python
def test_factory_picks_simulator_when_no_key(monkeypatch):
    monkeypatch.delenv("MASSIVE_API_KEY", raising=False)
    from app.market import PriceCache, create_market_data_source
    from app.market.simulator import SimulatorDataSource
    s = create_market_data_source(PriceCache())
    assert isinstance(s, SimulatorDataSource)

def test_factory_picks_massive_when_key_set(monkeypatch):
    monkeypatch.setenv("MASSIVE_API_KEY", "abc")
    from app.market import PriceCache, create_market_data_source
    from app.market.massive_client import MassiveDataSource
    s = create_market_data_source(PriceCache())
    assert isinstance(s, MassiveDataSource)

def test_empty_string_treated_as_unset(monkeypatch):
    monkeypatch.setenv("MASSIVE_API_KEY", "   ")
    from app.market import PriceCache, create_market_data_source
    from app.market.simulator import SimulatorDataSource
    assert isinstance(create_market_data_source(PriceCache()), SimulatorDataSource)
```

### 17.7 `test_stream.py` (SSE integration)

```python
import asyncio, json, pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from app.market.cache import PriceCache
from app.market.stream import create_stream_router

@pytest.mark.asyncio
async def test_sse_emits_on_version_change():
    cache = PriceCache()
    app = FastAPI()
    app.include_router(create_stream_router(cache))

    cache.update("AAPL", 100.0)  # warm
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream("GET", "/api/stream/prices") as resp:
            assert resp.status_code == 200
            collected = b""
            async def consumer():
                nonlocal collected
                async for chunk in resp.aiter_bytes():
                    collected += chunk
                    if b"GOOGL" in collected:
                        return
            consumer_task = asyncio.create_task(consumer())
            await asyncio.sleep(0.6)
            cache.update("GOOGL", 175.0)  # version bump → SSE frame
            await asyncio.wait_for(consumer_task, timeout=2.0)
    assert b"data:" in collected
    assert b"GOOGL" in collected

@pytest.mark.asyncio
async def test_sse_keepalive_when_idle():
    """When no version changes for keepalive_seconds, emit `: keepalive`."""
    # Same scaffolding, but pass keepalive_seconds=0.1 via a custom call into
    # _generate_events; verify the first idle window yields a ': keepalive' line.
```

### 17.8 `test_session.py`

```python
from app.market.cache import PriceCache
from app.market.session import SessionAnchors, annotate_with_session_change

def test_anchor_captured_on_first_observation():
    cache = PriceCache(); anchors = SessionAnchors()
    cache.update("AAPL", 100.0)
    rows = annotate_with_session_change(cache, anchors, ["AAPL"])
    assert rows[0]["session_anchor_price"] == 100.0
    assert rows[0]["change_pct"] == 0.0

def test_change_pct_after_movement():
    cache = PriceCache(); anchors = SessionAnchors()
    cache.update("AAPL", 100.0)
    annotate_with_session_change(cache, anchors, ["AAPL"])  # capture anchor
    cache.update("AAPL", 110.0)
    rows = annotate_with_session_change(cache, anchors, ["AAPL"])
    assert rows[0]["change_pct"] == 10.0

def test_no_price_yet_returns_nulls():
    rows = annotate_with_session_change(PriceCache(), SessionAnchors(), ["TSLA"])
    assert rows[0]["price"] is None
    assert rows[0]["session_anchor_price"] is None
    assert rows[0]["change_pct"] is None
```

### 17.9 `test_persister.py`

```python
import asyncio, pytest
from app.market.cache import PriceCache
from app.market.persister import TickPersister

@pytest.mark.asyncio
async def test_writer_emits_only_for_tickers_with_prices():
    cache = PriceCache()
    cache.update("AAPL", 100.0)

    written: list = []
    async def get_watched(): return ["AAPL", "MISSING"]
    async def write_rows(rows): written.extend(rows)
    async def prune(_): return 0

    p = TickPersister(cache, get_watched, write_rows, prune, write_interval_s=0.05)
    await p.start()
    await asyncio.sleep(0.15)
    await p.stop()
    assert all(row[0] == "AAPL" for row in written)
    assert len(written) >= 2  # at least two write cycles
```

### Coverage targets

| Module | Target |
|--------|--------|
| `models.py`, `cache.py`, `interface.py`, `seed_prices.py`, `factory.py`, `session.py` | 100% |
| `simulator.py` | ≥95% |
| `massive_client.py` | ≥80% (rest blocked by real SDK; mock-friendly thanks to `_fetch_snapshots` seam) |
| `stream.py` | ≥80% (SSE generator covered by ASGI test client) |
| `persister.py` | ≥90% |

---

## 18. Error Handling & Edge Cases

| Case | Behavior |
|------|----------|
| Empty initial watchlist | `start()` runs cleanly; sim produces no prices, Massive skips its API call. |
| Trade on ticker with no cached price | Trade endpoint returns `HTTP 400 "Price not yet available, retry"`. Simulator avoids this entirely because `add_ticker` seeds the cache. |
| Massive returns 401 | Logged each poll; SSE keeps streaming whatever was last cached (likely nothing). User fixes `.env` and restarts. |
| Massive returns 429 | Logged; next poll runs after `poll_interval`. We never hammer on failure. |
| Single malformed Massive row | That ticker skipped with a warning; rest of the batch processed. |
| Simulator step throws (e.g. bad numpy input) | Per-step `try/except` keeps the loop alive; logged with stack trace. |
| Client disconnects from SSE mid-frame | `request.is_disconnected()` short-circuits the loop; task ends cleanly. |
| Idle connection (no price moves for 15 s) | `: keepalive` comment sent to keep proxies happy. |
| Two concurrent `add_ticker` calls (Massive) | Serialized by `self._lock` in the data source. |
| Process restart | Session anchors reset (intentional — `change_pct` rebases). `price_ticks` and DB state persist. |
| Daily pruner failure | Logged; resumes next cycle. Worst case the table grows for a few days. |

---

## 19. Configuration Summary

| Parameter | Where | Default | Notes |
|-----------|-------|---------|-------|
| `MASSIVE_API_KEY` | env | empty | Switches the factory between sim and Massive |
| `LLM_MOCK` | env | `false` | Unrelated to market data; documented in PLAN §5 |
| `update_interval` | `SimulatorDataSource` | `0.5 s` | Simulator tick cadence |
| `poll_interval` | `MassiveDataSource` | `15.0 s` | Free-tier safe; lower on paid tiers |
| `event_probability` | `GBMSimulator` | `0.001` | ~1 shock event per ~50 s across 10 tickers |
| `dt` | `GBMSimulator` | `0.5 / 5_896_800` | 500 ms over one trading year |
| `POLL_INTERVAL_SECONDS` | `stream.py` | `0.5 s` | How often SSE checks the cache version |
| `KEEPALIVE_SECONDS` | `stream.py` | `15.0 s` | Idle-comment cadence |
| `RECONNECT_RETRY_MS` | `stream.py` | `1000` | Sent as `retry:` directive |
| `write_interval_s` | `TickPersister` | `5.0 s` | `price_ticks` write cadence |
| `retention_days` | `TickPersister` | `7` | Pruner cutoff |

---

## 20. Public API (`__init__.py`)

```python
"""Market data subsystem for FinAlly.

Public API surface — everything else should be considered internal.
"""

from .cache import PriceCache
from .factory import create_market_data_source
from .interface import MarketDataSource
from .models import PriceUpdate
from .persister import TickPersister
from .session import SessionAnchors, annotate_with_session_change
from .stream import create_stream_router

__all__ = [
    "PriceUpdate",
    "PriceCache",
    "MarketDataSource",
    "create_market_data_source",
    "create_stream_router",
    "SessionAnchors",
    "annotate_with_session_change",
    "TickPersister",
]
```

---

## Summary

The market data backend is built from small, focused modules that compose into a coherent flow:

- **One writer, one cache, many readers.** `PriceCache` is the seam.
- **One interface, two implementations.** `SimulatorDataSource` and `MassiveDataSource` are interchangeable behind `MarketDataSource`.
- **Push-on-change SSE with keepalive.** Avoids redundant frames; keeps connections alive through proxies.
- **Server-computed `change_pct`.** Stable across clients, resets on process restart, honest about the lack of a real "market open".
- **Independent tick persistence.** The `price_ticks` table grows on a steady 5-second cadence regardless of feed source, prunes daily, and powers the main chart's initial load via `GET /api/prices/history/{ticker}`.

All review findings from the prior cycle are baked in: top-level `massive` import, public `get_tickers()` on the simulator, removed redundant `DEFAULT_CORR`, locked version reads, factory-built SSE router, and explicit `AsyncGenerator[str, None]` return annotation on the event generator.
