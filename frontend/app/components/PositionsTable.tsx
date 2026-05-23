"use client";

import { useAllLatestPrices } from "../hooks/useLivePrices";
import { formatPct, formatPrice, formatQuantity, formatUsd } from "../lib/format";
import type { Position } from "../lib/types";

interface PositionsTableProps {
  positions: Position[];
  onSelect?: (ticker: string) => void;
  selected?: string | null;
}

export function PositionsTable({ positions, onSelect, selected }: PositionsTableProps) {
  const live = useAllLatestPrices();

  return (
    <section
      aria-label="Positions"
      className="flex h-full flex-col overflow-hidden rounded-md border border-border-muted bg-surface-1"
    >
      <header className="flex items-center justify-between border-b border-border-muted px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-blue-primary">
          Positions
        </h2>
        <span className="text-[10px] text-text-muted">{positions.length} open</span>
      </header>
      <div className="flex-1 overflow-auto">
        {positions.length === 0 ? (
          <div className="p-4 text-xs text-text-muted">No open positions.</div>
        ) : (
          <table className="min-w-full font-mono text-xs">
            <thead className="sticky top-0 bg-surface-2 text-text-muted">
              <tr className="border-b border-border-muted">
                <th className="px-3 py-2 text-left">Ticker</th>
                <th className="px-3 py-2 text-right">Qty</th>
                <th className="px-3 py-2 text-right">Avg Cost</th>
                <th className="px-3 py-2 text-right">Last</th>
                <th className="px-3 py-2 text-right">P&L</th>
                <th className="px-3 py-2 text-right">%</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((p) => {
                const current = live[p.ticker]?.price ?? p.current_price;
                const pnl =
                  current != null
                    ? (current - p.avg_cost) * p.quantity
                    : p.unrealized_pnl;
                const pnlPct =
                  current != null && p.avg_cost > 0
                    ? ((current - p.avg_cost) / p.avg_cost) * 100
                    : p.unrealized_pnl_pct;
                const positive = pnl != null && pnl >= 0;
                return (
                  <tr
                    key={p.ticker}
                    onClick={() => onSelect?.(p.ticker)}
                    className={`cursor-pointer border-b border-border-muted/40 transition-colors hover:bg-surface-2 ${
                      selected === p.ticker ? "ticker-selected bg-surface-2" : ""
                    }`}
                  >
                    <td className="px-3 py-1.5 text-text-primary font-semibold">
                      {p.ticker}
                    </td>
                    <td className="px-3 py-1.5 text-right tabular-nums">
                      {formatQuantity(p.quantity)}
                    </td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-text-secondary">
                      {formatPrice(p.avg_cost)}
                    </td>
                    <td className="px-3 py-1.5 text-right tabular-nums">
                      {formatPrice(current)}
                    </td>
                    <td
                      className={`px-3 py-1.5 text-right tabular-nums ${
                        pnl == null
                          ? "text-text-muted"
                          : positive
                            ? "text-emerald-400"
                            : "text-rose-400"
                      }`}
                    >
                      {formatUsd(pnl)}
                    </td>
                    <td
                      className={`px-3 py-1.5 text-right tabular-nums ${
                        pnlPct == null
                          ? "text-text-muted"
                          : positive
                            ? "text-emerald-400"
                            : "text-rose-400"
                      }`}
                    >
                      {formatPct(pnlPct)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}
