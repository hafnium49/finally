"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { PriceStream, type ConnectionState } from "../lib/sse";
import type { PriceFrame, PriceUpdate } from "../lib/types";

/**
 * The price store keeps the latest PriceUpdate for every ticker we've seen and
 * a per-ticker history of {ts, price} points accumulated since page load. The
 * history powers the sparklines (PLAN.md §10).
 *
 * Implemented as a module-level singleton so multiple components can subscribe
 * without coupling, and so SSE bytes are deserialized exactly once.
 */

export interface SparkPoint {
  ts: number; // unix seconds
  price: number;
}

const MAX_SPARK_POINTS = 60;

class PriceStore {
  private latest: Record<string, PriceUpdate> = {};
  private history: Record<string, SparkPoint[]> = {};
  private listeners = new Set<() => void>();
  private snapshot: {
    latest: Record<string, PriceUpdate>;
    history: Record<string, SparkPoint[]>;
  } = { latest: {}, history: {} };

  ingest(frame: PriceFrame): void {
    let changed = false;
    for (const [ticker, update] of Object.entries(frame)) {
      if (!update || typeof update.price !== "number") continue;
      const prev = this.latest[ticker];
      // Defensive: skip no-op updates so we never trigger flash on a flat tick.
      if (prev && prev.price === update.price && prev.timestamp === update.timestamp) {
        continue;
      }
      this.latest[ticker] = update;
      const hist = this.history[ticker] ?? [];
      hist.push({ ts: update.timestamp, price: update.price });
      if (hist.length > MAX_SPARK_POINTS) {
        hist.splice(0, hist.length - MAX_SPARK_POINTS);
      }
      this.history[ticker] = hist;
      changed = true;
    }
    if (changed) this.emit();
  }

  reset(): void {
    this.latest = {};
    this.history = {};
    this.emit();
  }

  subscribe = (l: () => void): (() => void) => {
    this.listeners.add(l);
    return () => this.listeners.delete(l);
  };

  getSnapshot = () => this.snapshot;

  private emit() {
    // Rebuild snapshot references so React detects the change.
    this.snapshot = {
      latest: { ...this.latest },
      history: { ...this.history },
    };
    for (const l of this.listeners) {
      try {
        l();
      } catch {
        // ignore
      }
    }
  }
}

const store = new PriceStore();
let stream: PriceStream | null = null;
let started = false;

export function startPriceStream(): PriceStream {
  if (!stream) {
    stream = new PriceStream();
    stream.onFrame((frame) => store.ingest(frame));
  }
  if (!started) {
    stream.start();
    started = true;
  }
  return stream;
}

export function getPriceStream(): PriceStream | null {
  return stream;
}

/** Hook returning the latest cached PriceUpdate for a ticker (or null). */
export function useLatestPrice(ticker: string): PriceUpdate | null {
  const snap = useSyncExternalStore(store.subscribe, store.getSnapshot, store.getSnapshot);
  return snap.latest[ticker] ?? null;
}

/** Hook returning the in-memory sparkline history accumulated since page load. */
export function useSparkHistory(ticker: string): SparkPoint[] {
  const snap = useSyncExternalStore(store.subscribe, store.getSnapshot, store.getSnapshot);
  return snap.history[ticker] ?? [];
}

/** Hook returning the entire latest-prices map (for components that need many). */
export function useAllLatestPrices(): Record<string, PriceUpdate> {
  const snap = useSyncExternalStore(store.subscribe, store.getSnapshot, store.getSnapshot);
  return snap.latest;
}

/** Hook returning the current SSE connection state. */
export function useConnectionState(): ConnectionState {
  const [state, setState] = useState<ConnectionState>(() =>
    stream ? stream.getState() : "closed",
  );

  // We need a stable ref so the effect's cleanup uses the right listener.
  const setStateRef = useRef(setState);
  setStateRef.current = setState;

  useEffect(() => {
    const s = startPriceStream();
    const unsub = s.onState((next) => setStateRef.current(next));
    return () => {
      unsub();
    };
  }, []);

  return state;
}

/** Imperative listener for ticker-specific updates (used for the main chart). */
export function subscribePriceUpdates(
  listener: (frame: PriceFrame) => void,
): () => void {
  const s = startPriceStream();
  return s.onFrame(listener);
}

// Exported for tests only.
export const __internal__ = { store };
