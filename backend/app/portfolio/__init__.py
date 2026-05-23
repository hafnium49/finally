"""Portfolio + trade execution subsystem.

Public API:
    execute_trade        - Single trade path used by HTTP route + chat executor
    current_portfolio    - GET /api/portfolio body (cash + positions + P&L)
    snapshot_now         - Write one portfolio_snapshots row immediately
    snapshot_loop        - Background task (every 30s)
    tick_writer_loop     - Background task (every ~5s)
    pruner_loop          - Background task (daily)

Typed trade exceptions:
    InvalidQuantityError, UnknownTickerError, InsufficientCashError,
    InsufficientSharesError
"""

from .positions import (
    compute_portfolio,
    get_portfolio_context,
    position_unrealized,
    update_position_buy,
    update_position_sell,
)
from .snapshots import snapshot_loop, snapshot_now
from .tick_history import (
    prune_old_ticks,
    pruner_loop,
    tick_writer_loop,
    write_tick_snapshot,
)
from .trade import (
    InsufficientCashError,
    InsufficientSharesError,
    InvalidQuantityError,
    TradeError,
    TradeResult,
    UnknownTickerError,
    current_portfolio,
    execute_trade,
)

__all__ = [
    "InsufficientCashError",
    "InsufficientSharesError",
    "InvalidQuantityError",
    "TradeError",
    "TradeResult",
    "UnknownTickerError",
    "compute_portfolio",
    "current_portfolio",
    "execute_trade",
    "get_portfolio_context",
    "position_unrealized",
    "prune_old_ticks",
    "pruner_loop",
    "snapshot_loop",
    "snapshot_now",
    "tick_writer_loop",
    "update_position_buy",
    "update_position_sell",
    "write_tick_snapshot",
]
