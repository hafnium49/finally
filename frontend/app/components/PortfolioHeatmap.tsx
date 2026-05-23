"use client";

import { useMemo } from "react";
import type { Position } from "../lib/types";
import { formatPct, formatUsd } from "../lib/format";

interface PortfolioHeatmapProps {
  positions: Position[];
}

interface Tile {
  ticker: string;
  weight: number; // 0..1
  pnlPct: number | null;
  marketValue: number | null;
}

/**
 * Squarified treemap-ish layout — a simple slice-and-dice variant that's good
 * enough for a 10-30 position portfolio. We avoid pulling in a heavyweight
 * treemap library for one visualization.
 */
function layoutTiles(
  tiles: Tile[],
  width: number,
  height: number,
): Array<Tile & { x: number; y: number; w: number; h: number }> {
  if (tiles.length === 0) return [];
  const total = tiles.reduce((acc, t) => acc + t.weight, 0) || 1;
  // Sort by weight desc so the biggest goes top-left.
  const sorted = [...tiles].sort((a, b) => b.weight - a.weight);
  const placed: Array<Tile & { x: number; y: number; w: number; h: number }> = [];

  let x = 0;
  let y = 0;
  let rowWidth = width;
  let rowHeight = height;
  let horizontal = width >= height;
  let remaining = total;
  let i = 0;

  while (i < sorted.length) {
    // Decide a row of items that fit within rowWidth/rowHeight while keeping
    // aspect ratios reasonable. We use a simple heuristic: take items until
    // adding the next would worsen the worst aspect ratio.
    const row: Tile[] = [];
    let rowSum = 0;
    let worst = Infinity;

    const evaluate = (items: Tile[], sum: number): number => {
      if (items.length === 0 || sum === 0) return Infinity;
      const sideLength = horizontal ? rowHeight : rowWidth;
      const sideArea = (sum / remaining) * (rowWidth * rowHeight);
      let worstRatio = 1;
      for (const it of items) {
        const itArea = (it.weight / sum) * sideArea;
        const itLength = itArea / sideLength;
        const ratio = Math.max(itLength / sideLength, sideLength / itLength);
        if (ratio > worstRatio) worstRatio = ratio;
      }
      return worstRatio;
    };

    while (i < sorted.length) {
      const candidate = [...row, sorted[i]];
      const candSum = rowSum + sorted[i].weight;
      const candWorst = evaluate(candidate, candSum);
      if (candWorst > worst && row.length > 0) break;
      row.push(sorted[i]);
      rowSum = candSum;
      worst = candWorst;
      i += 1;
    }

    // Place this row.
    const sideLength = horizontal ? rowHeight : rowWidth;
    const rowArea = (rowSum / remaining) * (rowWidth * rowHeight);
    const rowSize = rowArea / sideLength; // thickness perpendicular to layout dir
    let cursor = 0;
    for (const it of row) {
      const itArea = (it.weight / rowSum) * rowArea;
      const itLength = itArea / rowSize;
      if (horizontal) {
        placed.push({ ...it, x: x + rowWidth - rowSize, y: y + cursor, w: rowSize, h: itLength });
      } else {
        placed.push({ ...it, x: x + cursor, y: y + rowHeight - rowSize, w: itLength, h: rowSize });
      }
      cursor += itLength;
    }

    // Consume the row strip from the rectangle.
    if (horizontal) {
      rowWidth -= rowSize;
    } else {
      rowHeight -= rowSize;
    }
    remaining -= rowSum;
    horizontal = rowWidth >= rowHeight;
    if (remaining <= 0 || rowWidth <= 0 || rowHeight <= 0) break;
  }

  return placed;
}

function pnlColor(pnlPct: number | null): string {
  if (pnlPct == null) return "#222c3d";
  // clamp to ±10% for color saturation purposes
  const clamped = Math.max(-10, Math.min(10, pnlPct));
  if (clamped >= 0) {
    const alpha = 0.25 + (clamped / 10) * 0.55;
    return `rgba(22, 163, 74, ${alpha.toFixed(2)})`;
  }
  const alpha = 0.25 + (Math.abs(clamped) / 10) * 0.55;
  return `rgba(220, 38, 38, ${alpha.toFixed(2)})`;
}

export function PortfolioHeatmap({ positions }: PortfolioHeatmapProps) {
  const tiles = useMemo<Tile[]>(() => {
    const valued = positions
      .filter((p) => p.current_price != null && p.quantity > 0)
      .map((p) => ({
        ticker: p.ticker,
        marketValue: (p.current_price as number) * p.quantity,
        pnlPct: p.unrealized_pnl_pct,
        weight: 0,
      }));
    const total = valued.reduce((a, t) => a + (t.marketValue ?? 0), 0) || 1;
    for (const t of valued) {
      t.weight = (t.marketValue ?? 0) / total;
    }
    return valued;
  }, [positions]);

  return (
    <section
      aria-label="Portfolio heatmap"
      className="flex h-full flex-col overflow-hidden rounded-md border border-border-muted bg-surface-1"
    >
      <header className="border-b border-border-muted px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-blue-primary">
          Allocation
        </h2>
      </header>
      <div className="relative flex-1">
        {tiles.length === 0 ? (
          <div className="flex h-full items-center justify-center text-xs text-text-muted">
            No priced positions yet
          </div>
        ) : (
          <HeatmapCanvas tiles={tiles} />
        )}
      </div>
    </section>
  );
}

function HeatmapCanvas({ tiles }: { tiles: Tile[] }) {
  return (
    <div className="absolute inset-0 p-1">
      <div className="relative h-full w-full">
        <HeatmapAutoLayout tiles={tiles} />
      </div>
    </div>
  );
}

function HeatmapAutoLayout({ tiles }: { tiles: Tile[] }) {
  // We can't measure container size deterministically without a ResizeObserver
  // dance. Use a fixed virtual canvas (200x100) and let CSS scale.
  const placed = useMemo(() => layoutTiles(tiles, 200, 100), [tiles]);
  return (
    <div className="absolute inset-0">
      <svg
        viewBox="0 0 200 100"
        preserveAspectRatio="none"
        className="absolute inset-0 h-full w-full"
      >
        {placed.map((p) => (
          <g key={p.ticker}>
            <rect
              x={p.x + 0.5}
              y={p.y + 0.5}
              width={Math.max(0, p.w - 1)}
              height={Math.max(0, p.h - 1)}
              fill={pnlColor(p.pnlPct)}
              stroke="#0d1117"
              strokeWidth={0.5}
            />
            {p.w > 14 && p.h > 8 && (
              <>
                <text
                  x={p.x + p.w / 2}
                  y={p.y + p.h / 2 - 1}
                  textAnchor="middle"
                  fontSize={Math.min(p.w / 4, p.h / 2.5, 6)}
                  fill="#e6edf3"
                  fontFamily="ui-monospace, monospace"
                  fontWeight={600}
                >
                  {p.ticker}
                </text>
                <text
                  x={p.x + p.w / 2}
                  y={p.y + p.h / 2 + Math.min(p.h / 3, 4)}
                  textAnchor="middle"
                  fontSize={Math.min(p.w / 6, p.h / 4, 4)}
                  fill="#e6edf3"
                  fontFamily="ui-monospace, monospace"
                  opacity={0.85}
                >
                  {formatPct(p.pnlPct, 1)}
                </text>
              </>
            )}
          </g>
        ))}
      </svg>
      {/* Tooltip helpers (hidden but accessible) */}
      <ul className="sr-only">
        {placed.map((p) => (
          <li key={p.ticker}>
            {p.ticker}: {formatUsd(p.marketValue)} ({formatPct(p.pnlPct)})
          </li>
        ))}
      </ul>
    </div>
  );
}
