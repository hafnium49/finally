import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { WatchlistRow } from "../app/components/WatchlistRow";
import type { WatchlistItem } from "../app/lib/types";

describe("WatchlistRow", () => {
  const item: WatchlistItem = {
    ticker: "AAPL",
    price: 192.34,
    session_anchor_price: 190.0,
    change_pct: 1.2316,
  };

  it("renders ticker symbol and formatted price + change", () => {
    render(
      <WatchlistRow item={item} selected={false} onSelect={() => {}} onRemove={() => {}} />,
    );
    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText(/192\.34/)).toBeInTheDocument();
    expect(screen.getByText(/\+1\.23%/)).toBeInTheDocument();
  });

  it("fires onSelect when clicked", () => {
    const onSelect = vi.fn();
    render(
      <WatchlistRow item={item} selected={false} onSelect={onSelect} onRemove={() => {}} />,
    );
    fireEvent.click(screen.getByTestId("watchlist-row-AAPL"));
    expect(onSelect).toHaveBeenCalledWith("AAPL");
  });

  it("fires onRemove (and stops propagation) when the remove button is clicked", () => {
    const onSelect = vi.fn();
    const onRemove = vi.fn();
    render(
      <WatchlistRow item={item} selected={false} onSelect={onSelect} onRemove={onRemove} />,
    );
    fireEvent.click(screen.getByLabelText(/Remove AAPL/));
    expect(onRemove).toHaveBeenCalledWith("AAPL");
    expect(onSelect).not.toHaveBeenCalled();
  });

  it("shows '—' placeholders when the row has no cached price yet", () => {
    render(
      <WatchlistRow
        item={{
          ticker: "PYPL",
          price: null,
          session_anchor_price: null,
          change_pct: null,
        }}
        selected={false}
        onSelect={() => {}}
        onRemove={() => {}}
      />,
    );
    expect(screen.getByText("PYPL")).toBeInTheDocument();
    // formatPrice and formatPct both render '—' for null
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
  });

  it("renders the selected ticker style hook when selected", () => {
    render(
      <WatchlistRow item={item} selected={true} onSelect={() => {}} onRemove={() => {}} />,
    );
    const row = screen.getByTestId("watchlist-row-AAPL");
    expect(row.className).toContain("ticker-selected");
  });
});
