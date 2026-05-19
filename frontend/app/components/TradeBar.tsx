"use client";

import { FormEvent, useEffect, useState } from "react";
import { executeTrade } from "../lib/api";
import type { TradeResponse } from "../lib/types";

interface TradeBarProps {
  initialTicker?: string | null;
  onTradeComplete?: (res: TradeResponse) => void;
}

export function TradeBar({ initialTicker, onTradeComplete }: TradeBarProps) {
  const [ticker, setTicker] = useState(initialTicker ?? "");
  const [quantity, setQuantity] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (initialTicker) setTicker(initialTicker);
  }, [initialTicker]);

  const submit = async (side: "buy" | "sell", e?: FormEvent) => {
    e?.preventDefault();
    setError(null);
    setSuccess(null);
    const t = ticker.trim().toUpperCase();
    const qty = Number(quantity);
    if (!/^[A-Z]{1,5}$/.test(t)) {
      setError("Enter a 1-5 letter ticker.");
      return;
    }
    if (!isFinite(qty) || qty <= 0) {
      setError("Quantity must be positive.");
      return;
    }
    setBusy(true);
    try {
      const res = await executeTrade({ ticker: t, side, quantity: qty });
      setSuccess(
        `${side === "buy" ? "Bought" : "Sold"} ${qty} ${t} @ $${res.fill_price.toFixed(2)}`,
      );
      setQuantity("");
      onTradeComplete?.(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Trade failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section
      aria-label="Trade"
      className="rounded-md border border-border-muted bg-surface-1 p-3"
    >
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-blue-primary">
          Trade
        </h2>
        <span className="text-[10px] text-text-muted">market · instant fill</span>
      </div>
      <form
        onSubmit={(e) => submit("buy", e)}
        className="flex flex-wrap items-center gap-2 font-mono text-sm"
      >
        <input
          aria-label="Ticker"
          value={ticker}
          maxLength={5}
          placeholder="TICKER"
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          className="w-24 rounded border border-border-muted bg-surface-2 px-2 py-1 uppercase text-text-primary placeholder:text-text-muted focus:border-blue-primary focus:outline-none"
        />
        <input
          aria-label="Quantity"
          value={quantity}
          inputMode="decimal"
          placeholder="QTY"
          onChange={(e) => setQuantity(e.target.value)}
          className="w-24 rounded border border-border-muted bg-surface-2 px-2 py-1 tabular-nums text-text-primary placeholder:text-text-muted focus:border-blue-primary focus:outline-none"
        />
        <button
          type="button"
          disabled={busy}
          onClick={() => submit("buy")}
          className="rounded bg-purple-secondary px-4 py-1 font-semibold text-white transition-colors hover:bg-purple-secondary/80 disabled:opacity-40"
        >
          Buy
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => submit("sell")}
          className="rounded bg-purple-secondary px-4 py-1 font-semibold text-white transition-colors hover:bg-purple-secondary/80 disabled:opacity-40"
        >
          Sell
        </button>
        {success && (
          <span className="text-xs text-emerald-400">{success}</span>
        )}
        {error && <span className="text-xs text-rose-400">{error}</span>}
      </form>
    </section>
  );
}
