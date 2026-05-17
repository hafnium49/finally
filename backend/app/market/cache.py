"""Thread-safe in-memory price cache."""

from __future__ import annotations

import time
from threading import Lock

from .models import PriceUpdate


class PriceCache:
    """Thread-safe in-memory cache of the latest price for each ticker.

    Writers: SimulatorDataSource or MassiveDataSource (one at a time).
    Readers: SSE streaming endpoint, portfolio valuation, trade execution.

    Session anchor prices: the first observed price per ticker since process start,
    used to compute session change % for the watchlist (resets on backend restart).
    """

    def __init__(self) -> None:
        self._prices: dict[str, PriceUpdate] = {}
        self._session_anchors: dict[str, float] = {}  # ticker → first observed price
        self._lock = Lock()
        self._version: int = 0  # Monotonically increasing; bumped on every update

    def update(self, ticker: str, price: float, timestamp: float | None = None) -> PriceUpdate:
        """Record a new price for a ticker. Returns the created PriceUpdate.

        Automatically computes direction and change from the previous price.
        If this is the first update for the ticker, previous_price == price (direction='flat').
        The first price is also stored as the session anchor for change_pct calculation.
        """
        with self._lock:
            ts = timestamp or time.time()
            prev = self._prices.get(ticker)
            previous_price = prev.price if prev else price

            # Record session anchor on first observation
            if ticker not in self._session_anchors:
                self._session_anchors[ticker] = round(price, 2)

            update = PriceUpdate(
                ticker=ticker,
                price=round(price, 2),
                previous_price=round(previous_price, 2),
                timestamp=ts,
            )
            self._prices[ticker] = update
            self._version += 1
            return update

    def get(self, ticker: str) -> PriceUpdate | None:
        """Get the latest price for a single ticker, or None if unknown."""
        with self._lock:
            return self._prices.get(ticker)

    def get_all(self) -> dict[str, PriceUpdate]:
        """Snapshot of all current prices. Returns a shallow copy."""
        with self._lock:
            return dict(self._prices)

    def get_price(self, ticker: str) -> float | None:
        """Convenience: get just the price float, or None."""
        update = self.get(ticker)
        return update.price if update else None

    def get_session_anchor(self, ticker: str) -> float | None:
        """Return the session anchor price (first observed price) for a ticker.

        Used by the watchlist API to compute session change_pct.
        Returns None if the ticker has never been seen.
        """
        with self._lock:
            return self._session_anchors.get(ticker)

    def get_session_change_pct(self, ticker: str) -> float | None:
        """Return the session percentage change vs the session anchor.

        Returns None if the ticker has no price yet.
        Returns 0.0 if the anchor is zero (edge case).
        """
        with self._lock:
            anchor = self._session_anchors.get(ticker)
            current = self._prices.get(ticker)
            if anchor is None or current is None:
                return None
            if anchor == 0:
                return 0.0
            return round((current.price - anchor) / anchor * 100, 4)

    def remove(self, ticker: str) -> None:
        """Remove a ticker from the cache (e.g., when removed from watchlist).

        Also clears the session anchor so a re-add gets a fresh anchor.
        """
        with self._lock:
            self._prices.pop(ticker, None)
            self._session_anchors.pop(ticker, None)

    @property
    def version(self) -> int:
        """Current version counter. Useful for SSE change detection."""
        return self._version

    def __len__(self) -> int:
        with self._lock:
            return len(self._prices)

    def __contains__(self, ticker: str) -> bool:
        with self._lock:
            return ticker in self._prices
