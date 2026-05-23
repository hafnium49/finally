import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ActionCard } from "../app/components/ActionCard";
import type { ChatAction } from "../app/lib/types";

describe("ActionCard", () => {
  it("renders a successful trade with fill price and cash_after", () => {
    const action: ChatAction = {
      kind: "trade",
      status: "ok",
      ticker: "AAPL",
      side: "buy",
      quantity: 10,
      fill_price: 192.34,
      cash_after: 8076.6,
    };
    render(<ActionCard action={action} />);
    expect(screen.getByTestId("action-trade-ok")).toBeInTheDocument();
    expect(screen.getByText(/EXECUTED · BUY/)).toBeInTheDocument();
    expect(screen.getByText(/10 AAPL/)).toBeInTheDocument();
    expect(screen.getByText(/192\.34/)).toBeInTheDocument();
    expect(screen.getByText(/\$8,076\.60/)).toBeInTheDocument();
  });

  it("renders a failed trade with the error message", () => {
    const action: ChatAction = {
      kind: "trade",
      status: "error",
      ticker: "TSLA",
      side: "buy",
      quantity: 50,
      error: "insufficient_cash",
      error_message: "Need $12,400 but only $8,076.60 available.",
    };
    render(<ActionCard action={action} />);
    expect(screen.getByTestId("action-trade-error")).toBeInTheDocument();
    expect(screen.getByText(/FAILED · BUY/)).toBeInTheDocument();
    expect(screen.getByText(/Need \$12,400 but only \$8,076\.60 available\./)).toBeInTheDocument();
  });

  it("renders a successful watchlist add", () => {
    const action: ChatAction = {
      kind: "watchlist",
      status: "ok",
      ticker: "PYPL",
      action: "add",
    };
    render(<ActionCard action={action} />);
    expect(screen.getByTestId("action-watchlist-ok")).toBeInTheDocument();
    expect(screen.getByText(/EXECUTED · WATCHLIST ADD/)).toBeInTheDocument();
    expect(screen.getByText(/PYPL/)).toBeInTheDocument();
  });

  it("renders a failed watchlist removal with the error message", () => {
    const action: ChatAction = {
      kind: "watchlist",
      status: "error",
      ticker: "NFLX",
      action: "remove",
      error: "not_in_watchlist",
      error_message: "NFLX is not in your watchlist.",
    };
    render(<ActionCard action={action} />);
    expect(screen.getByTestId("action-watchlist-error")).toBeInTheDocument();
    expect(screen.getByText(/NFLX is not in your watchlist\./)).toBeInTheDocument();
  });
});
