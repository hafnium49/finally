// Portfolio totals math — verifies the frontend's derived values stay consistent
// with API_CONTRACT.md §4.1.

import { describe, it, expect } from "vitest";
import type { PortfolioResponse } from "../app/lib/types";

function computeTotals(portfolio: PortfolioResponse) {
  let positionsValue = 0;
  let pnl = 0;
  for (const p of portfolio.positions) {
    if (p.current_price == null) continue;
    positionsValue += p.current_price * p.quantity;
    pnl += (p.current_price - p.avg_cost) * p.quantity;
  }
  return {
    total_value: portfolio.cash_balance + positionsValue,
    unrealized_pnl: pnl,
  };
}

describe("portfolio totals math", () => {
  it("sums priced positions and skips null current_price (contract: zero contribution)", () => {
    const portfolio: PortfolioResponse = {
      cash_balance: 8000,
      total_value: 0,
      unrealized_pnl: 0,
      positions: [
        {
          ticker: "AAPL",
          quantity: 10,
          avg_cost: 190,
          current_price: 200,
          unrealized_pnl: 100,
          unrealized_pnl_pct: 5.2632,
        },
        {
          ticker: "TSLA",
          quantity: 5,
          avg_cost: 220,
          current_price: null,
          unrealized_pnl: null,
          unrealized_pnl_pct: null,
        },
      ],
    };
    const totals = computeTotals(portfolio);
    expect(totals.total_value).toBe(10000); // 8000 cash + 10*200 AAPL; TSLA contributes 0
    expect(totals.unrealized_pnl).toBe(100);
  });

  it("returns cash only when all positions are unpriced", () => {
    const portfolio: PortfolioResponse = {
      cash_balance: 10000,
      total_value: 0,
      unrealized_pnl: 0,
      positions: [
        {
          ticker: "AAPL",
          quantity: 10,
          avg_cost: 190,
          current_price: null,
          unrealized_pnl: null,
          unrealized_pnl_pct: null,
        },
      ],
    };
    const totals = computeTotals(portfolio);
    expect(totals.total_value).toBe(10000);
    expect(totals.unrealized_pnl).toBe(0);
  });

  it("handles fractional shares", () => {
    const portfolio: PortfolioResponse = {
      cash_balance: 1000,
      total_value: 0,
      unrealized_pnl: 0,
      positions: [
        {
          ticker: "AAPL",
          quantity: 2.5,
          avg_cost: 100,
          current_price: 110,
          unrealized_pnl: 25,
          unrealized_pnl_pct: 10,
        },
      ],
    };
    const totals = computeTotals(portfolio);
    expect(totals.total_value).toBeCloseTo(1275, 5);
    expect(totals.unrealized_pnl).toBeCloseTo(25, 5);
  });
});
