"use client";

import { useCallback, useEffect, useState } from "react";
import { Header } from "./components/Header";
import { Watchlist } from "./components/Watchlist";
import { MainChart } from "./components/MainChart";
import { PortfolioHeatmap } from "./components/PortfolioHeatmap";
import { PnlChart } from "./components/PnlChart";
import { PositionsTable } from "./components/PositionsTable";
import { TradeBar } from "./components/TradeBar";
import { ChatPanel } from "./components/ChatPanel";
import { usePortfolio } from "./hooks/usePortfolio";
import { startPriceStream } from "./hooks/useLivePrices";

export default function Page() {
  const { portfolio, refresh } = usePortfolio();
  const [selected, setSelected] = useState<string | null>(null);

  // Boot the SSE stream as soon as the SPA mounts.
  useEffect(() => {
    startPriceStream();
  }, []);

  // Auto-select first watchlist ticker once we know one. We watch the portfolio
  // positions first, falling back to watchlist via the Watchlist component's
  // first onSelect call.
  useEffect(() => {
    if (selected) return;
    const first = portfolio?.positions[0]?.ticker;
    if (first) setSelected(first);
  }, [portfolio, selected]);

  const handleTradeComplete = useCallback(() => {
    refresh();
  }, [refresh]);

  return (
    <div className="flex h-screen flex-col bg-surface-0 text-text-primary">
      <Header portfolio={portfolio} />

      <main className="grid flex-1 grid-cols-1 gap-3 overflow-hidden p-3 xl:grid-cols-[260px_minmax(0,1fr)_360px]">
        {/* Left rail — watchlist */}
        <div className="hidden h-full min-h-0 flex-col xl:flex">
          <Watchlist selected={selected} onSelect={setSelected} />
        </div>

        {/* Center — chart + positions + trade bar */}
        <div className="flex h-full min-h-0 flex-col gap-3">
          <div className="grid min-h-0 flex-1 grid-cols-1 gap-3 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
            <div className="min-h-[260px]">
              <MainChart ticker={selected} />
            </div>
            <div className="min-h-[260px]">
              <PortfolioHeatmap positions={portfolio?.positions ?? []} />
            </div>
          </div>

          <div className="grid min-h-0 flex-1 grid-cols-1 gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
            <div className="min-h-[180px]">
              <PnlChart />
            </div>
            <div className="min-h-[180px]">
              <PositionsTable
                positions={portfolio?.positions ?? []}
                onSelect={setSelected}
                selected={selected}
              />
            </div>
          </div>

          <TradeBar initialTicker={selected} onTradeComplete={handleTradeComplete} />

          {/* Mobile watchlist fallback */}
          <div className="block min-h-[280px] xl:hidden">
            <Watchlist selected={selected} onSelect={setSelected} />
          </div>
        </div>

        {/* Right rail — chat */}
        <div className="hidden h-full min-h-0 flex-col xl:flex">
          <ChatPanel onActivity={refresh} />
        </div>

        {/* Mobile chat — render as bottom sheet via the panel's collapsed state */}
        <div className="block min-h-[400px] xl:hidden">
          <ChatPanel onActivity={refresh} />
        </div>
      </main>
    </div>
  );
}
