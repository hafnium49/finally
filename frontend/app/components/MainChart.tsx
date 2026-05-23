"use client";

import { useEffect, useRef, useState } from "react";
import {
  ColorType,
  createChart,
  IChartApi,
  ISeriesApi,
  LineData,
  Time,
} from "lightweight-charts";
import { getPriceHistory } from "../lib/api";
import { subscribePriceUpdates } from "../hooks/useLivePrices";
import type { HistoryRange } from "../lib/types";

interface MainChartProps {
  ticker: string | null;
}

const RANGES: HistoryRange[] = ["1h", "6h", "24h", "7d"];

export function MainChart({ ticker }: MainChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const [range, setRange] = useState<HistoryRange>("1h");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Create the chart once.
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "#0d1117" },
        textColor: "#9ba8b8",
        fontFamily: "ui-monospace, monospace",
      },
      grid: {
        vertLines: { color: "#1a2230" },
        horzLines: { color: "#1a2230" },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: "#2a3344",
      },
      rightPriceScale: {
        borderColor: "#2a3344",
      },
      crosshair: { mode: 1 },
    });

    const series = chart.addLineSeries({
      color: "#ecad0a", // accent yellow — primary chart highlight
      lineWidth: 2,
      priceLineVisible: true,
      priceLineColor: "#ecad0a",
    });
    chartRef.current = chart;
    seriesRef.current = series;

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  // Load historical data whenever ticker or range changes.
  useEffect(() => {
    if (!ticker) {
      seriesRef.current?.setData([]);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);

    getPriceHistory(ticker, range)
      .then((res) => {
        if (cancelled) return;
        const data: LineData[] = res.points.map((p) => ({
          time: Math.floor(new Date(p.ts).getTime() / 1000) as Time,
          value: p.price,
        }));
        seriesRef.current?.setData(data);
        chartRef.current?.timeScale().fitContent();
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load chart");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [ticker, range]);

  // Append live ticks from SSE.
  useEffect(() => {
    if (!ticker) return;
    const unsub = subscribePriceUpdates((frame) => {
      const update = frame[ticker];
      if (!update || !seriesRef.current) return;
      seriesRef.current.update({
        time: Math.floor(update.timestamp) as Time,
        value: update.price,
      });
    });
    return unsub;
  }, [ticker]);

  return (
    <section
      aria-label="Main chart"
      className="flex h-full flex-col overflow-hidden rounded-md border border-border-muted bg-surface-1"
    >
      <header className="flex items-center justify-between border-b border-border-muted px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-blue-primary">
          {ticker ? (
            <>
              Chart · <span className="text-accent-yellow">{ticker}</span>
            </>
          ) : (
            "Chart"
          )}
        </h2>
        <div role="tablist" aria-label="Range" className="flex gap-1 text-xs">
          {RANGES.map((r) => (
            <button
              key={r}
              type="button"
              role="tab"
              aria-selected={r === range}
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
      <div className="relative flex-1">
        <div ref={containerRef} className="absolute inset-0" />
        {!ticker && (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-text-muted">
            Select a ticker from the watchlist
          </div>
        )}
        {ticker && loading && (
          <div className="absolute right-3 top-3 rounded bg-surface-2/80 px-2 py-1 text-[10px] text-text-muted">
            Loading…
          </div>
        )}
        {error && (
          <div className="absolute bottom-3 left-3 rounded bg-rose-500/10 px-2 py-1 text-xs text-rose-300">
            {error}
          </div>
        )}
      </div>
    </section>
  );
}
