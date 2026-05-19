"use client";

import type { ChatAction } from "../lib/types";
import { formatPrice, formatQuantity, formatUsd } from "../lib/format";

interface ActionCardProps {
  action: ChatAction;
}

export function ActionCard({ action }: ActionCardProps) {
  const isError = action.status === "error";
  const borderTone = isError
    ? "border-rose-700/60 bg-rose-500/10"
    : "border-emerald-700/60 bg-emerald-500/10";
  const iconTone = isError ? "text-rose-300" : "text-emerald-300";
  const label = isError ? "FAILED" : "EXECUTED";

  if (action.kind === "trade") {
    return (
      <div
        data-testid={`action-${action.kind}-${action.status}`}
        className={`mt-1 rounded border ${borderTone} px-2 py-1.5 text-xs`}
      >
        <div className="flex items-center justify-between gap-2">
          <span className={`font-mono text-[10px] font-bold uppercase ${iconTone}`}>
            {label} · {action.side.toUpperCase()}
          </span>
          <span className="font-mono text-text-primary">
            {formatQuantity(action.quantity)} {action.ticker}
          </span>
        </div>
        {action.status === "ok" ? (
          <div className="mt-0.5 flex flex-wrap gap-x-3 gap-y-0.5 font-mono text-[11px] text-text-secondary">
            <span>
              @ <span className="text-text-primary">{formatPrice(action.fill_price)}</span>
            </span>
            <span>
              cash → <span className="text-text-primary">{formatUsd(action.cash_after)}</span>
            </span>
          </div>
        ) : (
          <div className="mt-0.5 text-[11px] text-rose-200/90">
            {action.error_message}
          </div>
        )}
      </div>
    );
  }

  // watchlist
  return (
    <div
      data-testid={`action-${action.kind}-${action.status}`}
      className={`mt-1 rounded border ${borderTone} px-2 py-1.5 text-xs`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className={`font-mono text-[10px] font-bold uppercase ${iconTone}`}>
          {label} · WATCHLIST {action.action.toUpperCase()}
        </span>
        <span className="font-mono text-text-primary">{action.ticker}</span>
      </div>
      {action.status === "error" && (
        <div className="mt-0.5 text-[11px] text-rose-200/90">{action.error_message}</div>
      )}
    </div>
  );
}
