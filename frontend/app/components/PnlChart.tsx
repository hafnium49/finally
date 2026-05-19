"use client";

import { useMemo } from "react";
import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { usePortfolioHistory } from "../hooks/usePortfolio";
import { formatUsd } from "../lib/format";
import type { HistoryRange } from "../lib/types";

const RANGES: HistoryRange[] = ["1h", "6h", "24h", "7d"];

export function PnlChart() {
  const { points, range, setRange, loading, error } = usePortfolioHistory("24h");

  const data = useMemo(
    () =>
      points.map((p) => ({
        ts: new Date(p.ts).getTime(),
        value: p.total_value,
      })),
    [points],
  );

  const positive =
    data.length >= 2 ? data[data.length - 1].value >= data[0].value : true;
  const stroke = positive ? "#16a34a" : "#dc2626";

  return (
    <section
      aria-label="Portfolio P&L"
      className="flex h-full flex-col overflow-hidden rounded-md border border-border-muted bg-surface-1"
    >
      <header className="flex items-center justify-between border-b border-border-muted px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-blue-primary">
          Portfolio Value
        </h2>
        <div className="flex gap-1 text-xs">
          {RANGES.map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => setRange(r)}
              className={`rounded px-2 py-0.5 font-mono uppercase transition-colors ${
                r === range
                  ? "bg-accent-yellow text-surface-0"
                  : "bg-surface-2 text-text-secondary hover:bg-surface-3"
              }`}
            >
              {r}
            </button>
          ))}
        </div>
      </header>
      <div className="relative flex-1 px-2 py-1">
        {data.length === 0 ? (
          <div className="flex h-full items-center justify-center text-xs text-text-muted">
            {loading ? "Loading…" : error ? error : "No snapshots yet"}
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 4, right: 6, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="pnlGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={stroke} stopOpacity={0.45} />
                  <stop offset="100%" stopColor={stroke} stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="ts"
                type="number"
                domain={["dataMin", "dataMax"]}
                tickFormatter={(v) =>
                  new Date(v).toLocaleTimeString(undefined, {
                    hour: "2-digit",
                    minute: "2-digit",
                  })
                }
                stroke="#6b7785"
                tick={{ fontSize: 10 }}
                axisLine={{ stroke: "#2a3344" }}
                tickLine={false}
              />
              <YAxis
                stroke="#6b7785"
                tick={{ fontSize: 10 }}
                axisLine={{ stroke: "#2a3344" }}
                tickLine={false}
                domain={["auto", "auto"]}
                width={60}
                tickFormatter={(v) => formatUsd(v, 0)}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#141a23",
                  border: "1px solid #2a3344",
                  borderRadius: 4,
                  fontSize: 12,
                }}
                labelFormatter={(v) => new Date(Number(v)).toLocaleString()}
                formatter={(v: number) => [formatUsd(v), "Value"]}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke={stroke}
                strokeWidth={2}
                fill="url(#pnlGradient)"
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </section>
  );
}
