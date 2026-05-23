"use client";

import { useEffect, useRef } from "react";
import type { SparkPoint } from "../hooks/useLivePrices";

interface SparklineProps {
  points: SparkPoint[];
  width?: number;
  height?: number;
  positive?: boolean;
}

/**
 * Lightweight canvas sparkline. Drawing on a canvas (rather than dozens of SVG
 * paths) keeps a watchlist of 10+ tickers rendering cheaply when ticks arrive.
 */
export function Sparkline({
  points,
  width = 88,
  height = 24,
  positive,
}: SparklineProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dpr = typeof window !== "undefined" ? window.devicePixelRatio || 1 : 1;

    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    if (points.length < 2) {
      // Render a faint baseline to communicate "no data yet"
      ctx.strokeStyle = "#2a3344";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, height / 2);
      ctx.lineTo(width, height / 2);
      ctx.stroke();
      return;
    }

    const ys = points.map((p) => p.price);
    const min = Math.min(...ys);
    const max = Math.max(...ys);
    const range = max - min || 1;

    ctx.strokeStyle = positive === false ? "#dc2626" : positive === true ? "#16a34a" : "#209dd7";
    ctx.lineWidth = 1.25;
    ctx.beginPath();

    points.forEach((p, i) => {
      const x = (i / (points.length - 1)) * (width - 2) + 1;
      const y = height - ((p.price - min) / range) * (height - 2) - 1;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }, [points, width, height, positive]);

  return <canvas ref={canvasRef} aria-hidden="true" />;
}
