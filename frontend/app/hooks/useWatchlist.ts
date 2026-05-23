"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  addWatchlist as apiAdd,
  getWatchlist,
  removeWatchlist as apiRemove,
} from "../lib/api";
import type { WatchlistItem } from "../lib/types";

export interface UseWatchlistReturn {
  items: WatchlistItem[];
  loading: boolean;
  error: string | null;
  add: (ticker: string) => Promise<void>;
  remove: (ticker: string) => Promise<void>;
  refresh: () => Promise<void>;
}

export function useWatchlist(): UseWatchlistReturn {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mounted = useRef(true);

  const refresh = useCallback(async () => {
    try {
      const res = await getWatchlist();
      if (!mounted.current) return;
      setItems(res.items);
      setError(null);
    } catch (err) {
      if (!mounted.current) return;
      setError(err instanceof Error ? err.message : "Failed to load watchlist");
    } finally {
      if (mounted.current) setLoading(false);
    }
  }, []);

  const add = useCallback(
    async (ticker: string) => {
      try {
        await apiAdd(ticker);
        await refresh();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to add ticker");
        throw err;
      }
    },
    [refresh],
  );

  const remove = useCallback(
    async (ticker: string) => {
      try {
        await apiRemove(ticker);
        await refresh();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to remove ticker");
        throw err;
      }
    },
    [refresh],
  );

  useEffect(() => {
    mounted.current = true;
    refresh();
    // Watchlist itself rarely changes; poll slowly to pick up LLM-driven changes.
    const id = setInterval(refresh, 8000);
    return () => {
      mounted.current = false;
      clearInterval(id);
    };
  }, [refresh]);

  return { items, loading, error, add, remove, refresh };
}
