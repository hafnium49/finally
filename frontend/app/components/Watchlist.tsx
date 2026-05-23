"use client";

import { FormEvent, useState } from "react";
import { useWatchlist } from "../hooks/useWatchlist";
import { WatchlistRow } from "./WatchlistRow";

interface WatchlistProps {
  selected: string | null;
  onSelect: (ticker: string) => void;
}

export function Watchlist({ selected, onSelect }: WatchlistProps) {
  const { items, loading, error, add, remove } = useWatchlist();
  const [input, setInput] = useState("");
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  const handleAdd = async (e: FormEvent) => {
    e.preventDefault();
    const value = input.trim().toUpperCase();
    if (!value) return;
    if (!/^[A-Z]{1,5}$/.test(value)) {
      setAddError("Ticker must be 1-5 letters.");
      return;
    }
    setAdding(true);
    setAddError(null);
    try {
      await add(value);
      setInput("");
    } catch (err) {
      setAddError(err instanceof Error ? err.message : "Failed to add ticker");
    } finally {
      setAdding(false);
    }
  };

  return (
    <section
      aria-label="Watchlist"
      className="flex h-full flex-col overflow-hidden rounded-md border border-border-muted bg-surface-1"
    >
      <header className="flex items-center justify-between border-b border-border-muted px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-blue-primary">
          Watchlist
        </h2>
        <span className="text-[10px] text-text-muted">{items.length} symbols</span>
      </header>

      <form onSubmit={handleAdd} className="flex gap-2 border-b border-border-muted px-3 py-2">
        <input
          type="text"
          value={input}
          maxLength={5}
          placeholder="Add ticker"
          onChange={(e) => setInput(e.target.value.toUpperCase())}
          className="flex-1 rounded border border-border-muted bg-surface-2 px-2 py-1 font-mono text-sm uppercase text-text-primary placeholder:text-text-muted focus:border-blue-primary focus:outline-none"
        />
        <button
          type="submit"
          disabled={adding || !input.trim()}
          className="rounded bg-blue-primary px-3 py-1 text-xs font-semibold text-white transition-colors hover:bg-blue-primary/80 disabled:opacity-40"
        >
          Add
        </button>
      </form>

      {addError && (
        <div className="border-b border-rose-900/40 bg-rose-500/10 px-3 py-1 text-xs text-rose-300">
          {addError}
        </div>
      )}

      <div className="flex-1 overflow-y-auto">
        {loading && items.length === 0 ? (
          <div className="p-4 text-xs text-text-muted">Loading watchlist…</div>
        ) : items.length === 0 ? (
          <div className="p-4 text-xs text-text-muted">No tickers yet. Add one above.</div>
        ) : (
          items.map((item) => (
            <WatchlistRow
              key={item.ticker}
              item={item}
              selected={selected === item.ticker}
              onSelect={onSelect}
              onRemove={(t) => {
                remove(t).catch(() => {
                  /* error surfaced via hook state */
                });
              }}
            />
          ))
        )}
      </div>

      {error && (
        <div className="border-t border-rose-900/40 bg-rose-500/10 px-3 py-1 text-xs text-rose-300">
          {error}
        </div>
      )}
    </section>
  );
}
