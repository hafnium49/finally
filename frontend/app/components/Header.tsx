"use client";

import { useConnectionState } from "../hooks/useLivePrices";
import { formatUsd } from "../lib/format";
import type { PortfolioResponse } from "../lib/types";

interface HeaderProps {
  portfolio: PortfolioResponse | null;
}

function StatusDot({ state }: { state: ReturnType<typeof useConnectionState> }) {
  const color =
    state === "open"
      ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]"
      : state === "reconnecting" || state === "connecting"
        ? "bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.6)] animate-pulse"
        : "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.6)]";

  const label =
    state === "open"
      ? "Live"
      : state === "reconnecting"
        ? "Reconnecting"
        : state === "connecting"
          ? "Connecting"
          : "Disconnected";

  return (
    <div
      className="flex items-center gap-2 text-xs text-text-secondary"
      data-testid="connection-status"
      data-state={state}
    >
      <span className={`inline-block h-2 w-2 rounded-full ${color}`} />
      <span>{label}</span>
    </div>
  );
}

export function Header({ portfolio }: HeaderProps) {
  const state = useConnectionState();
  const total = portfolio?.total_value ?? null;
  const cash = portfolio?.cash_balance ?? null;
  const pnl = portfolio?.unrealized_pnl ?? null;
  const pnlPositive = pnl != null && pnl >= 0;

  return (
    <header className="border-b border-border-muted bg-surface-1 px-4 py-3">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded bg-purple-secondary text-sm font-bold text-white">
            F
          </div>
          <div>
            <div className="text-sm font-semibold tracking-wide text-text-primary">
              FinAlly
            </div>
            <div className="text-[10px] uppercase tracking-widest text-text-muted">
              AI Trading Workstation
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-6 font-mono text-sm">
          <Metric label="Portfolio" value={formatUsd(total)} highlight />
          <Metric label="Cash" value={formatUsd(cash)} />
          <Metric
            label="Unrealized P&L"
            value={formatUsd(pnl)}
            tone={pnl == null ? "neutral" : pnlPositive ? "up" : "down"}
          />
          <StatusDot state={state} />
        </div>
      </div>
    </header>
  );
}

function Metric({
  label,
  value,
  highlight = false,
  tone = "neutral",
}: {
  label: string;
  value: string;
  highlight?: boolean;
  tone?: "up" | "down" | "neutral";
}) {
  const toneClass =
    tone === "up"
      ? "text-emerald-400"
      : tone === "down"
        ? "text-rose-400"
        : highlight
          ? "text-accent-yellow"
          : "text-text-primary";
  return (
    <div className="flex flex-col leading-tight">
      <span className="text-[10px] uppercase tracking-widest text-text-muted">
        {label}
      </span>
      <span className={`text-base font-semibold ${toneClass}`}>{value}</span>
    </div>
  );
}
