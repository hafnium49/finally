"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getPortfolio, getPortfolioHistory } from "../lib/api";
import type {
  HistoryRange,
  PortfolioHistoryPoint,
  PortfolioResponse,
} from "../lib/types";

const POLL_INTERVAL_MS = 4000;

export interface UsePortfolioReturn {
  portfolio: PortfolioResponse | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function usePortfolio(): UsePortfolioReturn {
  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mounted = useRef(true);

  const refresh = useCallback(async () => {
    try {
      const next = await getPortfolio();
      if (!mounted.current) return;
      setPortfolio(next);
      setError(null);
    } catch (err) {
      if (!mounted.current) return;
      setError(err instanceof Error ? err.message : "Failed to load portfolio");
    } finally {
      if (mounted.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    refresh();
    const id = setInterval(refresh, POLL_INTERVAL_MS);
    return () => {
      mounted.current = false;
      clearInterval(id);
    };
  }, [refresh]);

  return { portfolio, loading, error, refresh };
}

export interface UsePortfolioHistoryReturn {
  points: PortfolioHistoryPoint[];
  loading: boolean;
  error: string | null;
  range: HistoryRange;
  setRange: (r: HistoryRange) => void;
  refresh: () => Promise<void>;
}

export function usePortfolioHistory(
  initialRange: HistoryRange = "24h",
): UsePortfolioHistoryReturn {
  const [range, setRange] = useState<HistoryRange>(initialRange);
  const [points, setPoints] = useState<PortfolioHistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mounted = useRef(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getPortfolioHistory(range);
      if (!mounted.current) return;
      setPoints(res.points);
      setError(null);
    } catch (err) {
      if (!mounted.current) return;
      setError(err instanceof Error ? err.message : "Failed to load history");
    } finally {
      if (mounted.current) setLoading(false);
    }
  }, [range]);

  useEffect(() => {
    mounted.current = true;
    refresh();
    // Snapshot writer cadence is 30s — poll every 15s.
    const id = setInterval(refresh, 15000);
    return () => {
      mounted.current = false;
      clearInterval(id);
    };
  }, [refresh]);

  return { points, loading, error, range, setRange, refresh };
}
