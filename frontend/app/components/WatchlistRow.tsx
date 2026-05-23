"use client";

import { useEffect, useRef } from "react";
import { useLatestPrice, useSparkHistory } from "../hooks/useLivePrices";
import { computeDirection, flashElement } from "../lib/priceFlash";
import { formatPct, formatPrice } from "../lib/format";
import type { WatchlistItem } from "../lib/types";
import { Sparkline } from "./Sparkline";

interface WatchlistRowProps {
  item: WatchlistItem;
  selected: boolean;
  onSelect: (ticker: string) => void;
  onRemove: (ticker: string) => void;
}

export function WatchlistRow({ item, selected, onSelect, onRemove }: WatchlistRowProps) {
  const live = useLatestPrice(item.ticker);
  const history = useSparkHistory(item.ticker);
  const rowRef = useRef<HTMLDivElement | null>(null);
  const prevPriceRef = useRef<number | null>(item.price);

  // Live override: prefer SSE-cached price when we have it, otherwise the
  // server-rendered initial value from /api/watchlist.
  const price = live?.price ?? item.price;
  const changePct =
    live && item.session_anchor_price != null && item.session_anchor_price !== 0
      ? ((live.price - item.session_anchor_price) / item.session_anchor_price) * 100
      : item.change_pct;

  useEffect(() => {
    if (price == null) return;
    const prev = prevPriceRef.current;
    const dir = computeDirection(prev, price);
    if (dir !== "flat" && rowRef.current) {
      flashElement(rowRef.current, dir);
    }
    prevPriceRef.current = price;
  }, [price]);

  const positive = changePct == null ? undefined : changePct >= 0;
  const changeClass =
    changePct == null
      ? "text-text-muted"
      : positive
        ? "text-emerald-400"
        : "text-rose-400";

  return (
    <div
      ref={rowRef}
      role="button"
      tabIndex={0}
      data-testid={`watchlist-row-${item.ticker}`}
      onClick={() => onSelect(item.ticker)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect(item.ticker);
        }
      }}
      className={`group grid cursor-pointer grid-cols-[1fr_auto_auto_auto] items-center gap-3 border-b border-border-muted/60 px-3 py-2 font-mono text-sm transition-colors hover:bg-surface-2 ${
        selected ? "ticker-selected bg-surface-2" : ""
      }`}
    >
      <div className="flex flex-col">
        <span className="text-text-primary font-semibold tracking-wider">
          {item.ticker}
        </span>
        <span className={`text-xs ${changeClass}`}>{formatPct(changePct)}</span>
      </div>
      <div className="text-right tabular-nums text-text-primary">
        {formatPrice(price)}
      </div>
      <Sparkline points={history} positive={positive} />
      <button
        type="button"
        aria-label={`Remove ${item.ticker} from watchlist`}
        onClick={(e) => {
          e.stopPropagation();
          onRemove(item.ticker);
        }}
        className="rounded px-2 py-0.5 text-xs text-text-muted opacity-0 transition-opacity hover:bg-surface-3 hover:text-rose-400 group-hover:opacity-100"
      >
        ✕
      </button>
    </div>
  );
}
