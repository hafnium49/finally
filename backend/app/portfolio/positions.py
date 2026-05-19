"""Pure position math helpers.

These functions are intentionally pure (no DB, no asyncio, no globals) so they
are trivial to unit-test. The DB-bound trade orchestration in :mod:`trade`
calls into these to compute new average cost / quantity values, then writes
the result.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.market import PriceCache


def update_position_buy(
    existing_quantity: float,
    existing_avg_cost: float,
    buy_quantity: float,
    buy_price: float,
) -> tuple[float, float]:
    """Apply a buy: return (new_quantity, new_avg_cost).

    The new average cost is the size-weighted average of the existing basis
    and the buy fill price:

        new_avg = (old_qty * old_avg + buy_qty * buy_price) / (old_qty + buy_qty)

    For a brand new position (``existing_quantity == 0``) this reduces to
    ``new_avg = buy_price`` cleanly.
    """
    new_quantity = existing_quantity + buy_quantity
    if new_quantity <= 0:
        # Defensive: should never happen because callers validate, but avoid
        # division-by-zero on degenerate inputs.
        return new_quantity, buy_price
    new_avg_cost = (
        (existing_quantity * existing_avg_cost) + (buy_quantity * buy_price)
    ) / new_quantity
    return new_quantity, new_avg_cost


def update_position_sell(
    existing_quantity: float,
    existing_avg_cost: float,
    sell_quantity: float,
) -> tuple[float, float]:
    """Apply a sell: return (new_quantity, new_avg_cost).

    Selling reduces the quantity but leaves the average cost unchanged
    (realized P&L is what the cash side captures). A full-sell returns
    ``(0.0, 0.0)`` so the caller can detect "position is gone" with a single
    check.
    """
    new_quantity = existing_quantity - sell_quantity
    if new_quantity <= 0:
        return 0.0, 0.0
    return new_quantity, existing_avg_cost


def position_unrealized(
    quantity: float,
    avg_cost: float,
    current_price: Optional[float],
) -> tuple[Optional[float], Optional[float]]:
    """Return (unrealized_pnl, unrealized_pnl_pct) for a single position.

    Both are ``None`` when ``current_price`` is ``None`` (no tick yet).
    ``unrealized_pnl_pct`` is rounded to 4 decimal places; it is ``0.0`` if
    ``avg_cost == 0`` (degenerate case, shouldn't occur for real trades).
    """
    if current_price is None:
        return None, None
    pnl = (current_price - avg_cost) * quantity
    if avg_cost == 0:
        pct = 0.0
    else:
        pct = round((current_price - avg_cost) / avg_cost * 100, 4)
    return round(pnl, 4), pct


def compute_portfolio(
    cash_balance: float,
    positions: list[dict],
    price_cache: "PriceCache",
) -> dict:
    """Build the ``GET /api/portfolio`` response body from raw inputs.

    ``positions`` is a list of dicts each with at least ``ticker``,
    ``quantity``, ``avg_cost`` (typically the rows from the ``positions``
    table). The function reads the latest price from the cache for each
    ticker, computes per-position P&L, and rolls up ``total_value`` and
    ``unrealized_pnl``.

    Positions with no cached price contribute ``0`` to the totals (so a
    single unpriced ticker doesn't collapse the whole sum to ``None``), and
    their per-row P&L fields are ``None``.
    """
    rows: list[dict] = []
    total_position_value = 0.0
    total_unrealized = 0.0
    for pos in positions:
        ticker = pos["ticker"]
        quantity = float(pos["quantity"])
        avg_cost = float(pos["avg_cost"])
        current_price = price_cache.get_price(ticker)
        pnl, pnl_pct = position_unrealized(quantity, avg_cost, current_price)
        if current_price is not None:
            total_position_value += quantity * current_price
            total_unrealized += (current_price - avg_cost) * quantity
        rows.append(
            {
                "ticker": ticker,
                "quantity": quantity,
                "avg_cost": round(avg_cost, 4),
                "current_price": current_price,
                "unrealized_pnl": pnl,
                "unrealized_pnl_pct": pnl_pct,
            }
        )
    return {
        "cash_balance": round(cash_balance, 4),
        "total_value": round(cash_balance + total_position_value, 4),
        "unrealized_pnl": round(total_unrealized, 4),
        "positions": rows,
    }
