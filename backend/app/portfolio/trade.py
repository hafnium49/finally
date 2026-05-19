"""Trade execution path.

This is **the single trade path** in the system. Both ``POST /api/portfolio/trade``
and the LLM auto-trade flow (``backend/app/chat``) call into
:func:`execute_trade`, which acquires a per-user :class:`asyncio.Lock` from a
module-level ``dict[str, asyncio.Lock]`` so concurrent UI clicks and
LLM-initiated trades cannot race on ``cash_balance`` / ``positions`` (PLAN.md
§7 "Concurrent Trade Safety").

Fill price is **always** the latest value in the shared ``PriceCache`` at the
moment the lock is held — never a price the caller passed in or saw in a
prior request. Drift between client/LLM context and server execution is
authoritative on the server side (PLAN.md §9 "Trade Execution & Validation").
"""

from __future__ import annotations

import asyncio
import math
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Literal

from app.db import connection
from app.portfolio import positions as positions_math

if TYPE_CHECKING:
    from app.market import PriceCache


# ---------------------------------------------------------------------------
# Typed exceptions surfaced by the executor + the trade HTTP endpoint
# ---------------------------------------------------------------------------


class TradeError(Exception):
    """Base class for expected trade-validation failures."""


class InvalidQuantityError(TradeError):
    """Quantity is non-positive or non-finite."""

    def __init__(self, quantity: float) -> None:
        self.quantity = quantity
        super().__init__(f"Quantity must be positive; got {quantity}.")


class UnknownTickerError(TradeError):
    """Ticker has no price in the cache (not produced by the active source)."""

    def __init__(self, ticker: str) -> None:
        self.ticker = ticker
        super().__init__(f"{ticker} not recognized.")


class InsufficientCashError(TradeError):
    """Buy would overdraw the cash balance."""

    def __init__(self, need: float, have: float) -> None:
        self.need = need
        self.have = have
        super().__init__(f"Need ${need:,.2f} but only ${have:,.2f} available.")


class InsufficientSharesError(TradeError):
    """Sell exceeds current position quantity."""

    def __init__(self, ticker: str, have: float, want: float) -> None:
        self.ticker = ticker
        self.have = have
        self.want = want
        super().__init__(
            f"You hold {have} shares of {ticker}, can't sell {want}."
        )


# ---------------------------------------------------------------------------
# Trade result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TradeResult:
    """Return value of :func:`execute_trade` (used by the HTTP route + chat)."""

    trade_id: str
    ticker: str
    side: Literal["buy", "sell"]
    quantity: float
    fill_price: float
    cash_after: float
    position_quantity: float
    position_avg_cost: float


# ---------------------------------------------------------------------------
# Per-user lock registry
# ---------------------------------------------------------------------------


# Lazily populated; one Lock per user_id. Lookups are not themselves
# protected because dict assignment is atomic under the GIL and we always
# read-or-create through `_get_user_lock` which guards setdefault.
_user_locks: dict[str, asyncio.Lock] = {}


def _get_user_lock(user_id: str) -> asyncio.Lock:
    """Return the asyncio.Lock for ``user_id``, creating one on first access."""
    # `dict.setdefault` is atomic under the GIL, so two coroutines racing to
    # populate the same key will agree on a single Lock instance.
    lock = _user_locks.get(user_id)
    if lock is None:
        lock = _user_locks.setdefault(user_id, asyncio.Lock())
    return lock


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def execute_trade(
    ticker: str,
    side: Literal["buy", "sell"],
    quantity: float,
    price_cache: "PriceCache",
    user_id: str = "default",
) -> TradeResult:
    """Execute a market order at the latest cached price.

    Acquires the per-user :class:`asyncio.Lock`, reads cash + position,
    validates, computes the fill at the latest ``PriceCache`` price, writes
    the ``trades`` row and updates ``positions`` / ``users_profile`` in a
    single transaction, then releases the lock. Snapshotting
    ``portfolio_snapshots`` happens immediately after via the snapshot
    writer.

    Raises:
        InvalidQuantityError: ``quantity`` is non-positive or NaN/inf.
        UnknownTickerError: no price is cached for ``ticker``.
        InsufficientCashError: buy total exceeds ``cash_balance``.
        InsufficientSharesError: sell ``quantity`` exceeds current position.
    """
    # Structural validation first (no lock, no DB) — these are caller bugs.
    if not isinstance(quantity, (int, float)) or quantity <= 0 or not math.isfinite(quantity):
        raise InvalidQuantityError(float(quantity) if isinstance(quantity, (int, float)) else 0.0)
    if side not in ("buy", "sell"):
        # The HTTP layer's Pydantic validation rejects this earlier, but the
        # chat executor calls this directly.
        raise ValueError(f"Invalid side: {side!r}")

    ticker_u = ticker.upper()

    lock = _get_user_lock(user_id)
    async with lock:
        return await asyncio.to_thread(
            _execute_trade_blocking,
            ticker=ticker_u,
            side=side,
            quantity=float(quantity),
            price_cache=price_cache,
            user_id=user_id,
        )


def _execute_trade_blocking(
    ticker: str,
    side: Literal["buy", "sell"],
    quantity: float,
    price_cache: "PriceCache",
    user_id: str,
) -> TradeResult:
    """Synchronous DB-touching half of execute_trade.

    Runs under the caller's lock; offloaded via ``asyncio.to_thread`` so the
    sqlite3 calls don't stall the event loop. The lock is held while this
    runs, so no other coroutine for the same user can race us between read
    and commit.
    """
    fill_price = price_cache.get_price(ticker)
    if fill_price is None:
        raise UnknownTickerError(ticker)

    with connection() as conn:
        cash_row = conn.execute(
            "SELECT cash_balance FROM users_profile WHERE id = ?",
            (user_id,),
        ).fetchone()
        if cash_row is None:
            # Defensive: the seed step should have inserted this row, but if
            # someone wiped the DB by hand we surface a coherent error.
            raise UnknownTickerError(ticker)
        cash_balance = float(cash_row["cash_balance"])

        pos_row = conn.execute(
            "SELECT id, quantity, avg_cost FROM positions "
            "WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        ).fetchone()
        existing_quantity = float(pos_row["quantity"]) if pos_row else 0.0
        existing_avg_cost = float(pos_row["avg_cost"]) if pos_row else 0.0

        if side == "buy":
            cost = fill_price * quantity
            if cost > cash_balance + 1e-9:  # Tiny epsilon for FP noise
                raise InsufficientCashError(need=cost, have=cash_balance)
            new_quantity, new_avg_cost = positions_math.update_position_buy(
                existing_quantity, existing_avg_cost, quantity, fill_price
            )
            new_cash = cash_balance - cost
        else:  # sell
            if quantity > existing_quantity + 1e-9:
                raise InsufficientSharesError(
                    ticker=ticker, have=existing_quantity, want=quantity
                )
            new_quantity, new_avg_cost = positions_math.update_position_sell(
                existing_quantity, existing_avg_cost, quantity
            )
            new_cash = cash_balance + fill_price * quantity

        now = _utc_now_iso()
        trade_id = str(uuid.uuid4())

        # Insert trades row (append-only).
        conn.execute(
            "INSERT INTO trades (id, user_id, ticker, side, quantity, price, executed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (trade_id, user_id, ticker, side, quantity, fill_price, now),
        )

        # Upsert positions row, or delete on a full-sell.
        if new_quantity <= 0:
            if pos_row is not None:
                conn.execute(
                    "DELETE FROM positions WHERE id = ?", (pos_row["id"],)
                )
        else:
            if pos_row is not None:
                conn.execute(
                    "UPDATE positions SET quantity = ?, avg_cost = ?, updated_at = ? "
                    "WHERE id = ?",
                    (new_quantity, new_avg_cost, now, pos_row["id"]),
                )
            else:
                conn.execute(
                    "INSERT INTO positions (id, user_id, ticker, quantity, avg_cost, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), user_id, ticker, new_quantity, new_avg_cost, now),
                )

        # Update cash.
        conn.execute(
            "UPDATE users_profile SET cash_balance = ? WHERE id = ?",
            (new_cash, user_id),
        )

    return TradeResult(
        trade_id=trade_id,
        ticker=ticker,
        side=side,
        quantity=quantity,
        fill_price=fill_price,
        cash_after=new_cash,
        position_quantity=new_quantity,
        position_avg_cost=new_avg_cost,
    )


def current_portfolio(price_cache: "PriceCache", user_id: str = "default") -> dict:
    """Build the GET /api/portfolio response body for ``user_id``.

    Reads from the DB and the in-memory ``PriceCache``; does not require the
    per-user lock (read-only — concurrent trade writes may make this view
    momentarily stale but never invalid).
    """
    with connection() as conn:
        cash_row = conn.execute(
            "SELECT cash_balance FROM users_profile WHERE id = ?",
            (user_id,),
        ).fetchone()
        cash_balance = float(cash_row["cash_balance"]) if cash_row else 0.0
        pos_rows = conn.execute(
            "SELECT ticker, quantity, avg_cost FROM positions "
            "WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
        positions = [dict(r) for r in pos_rows]
    return positions_math.compute_portfolio(cash_balance, positions, price_cache)
