import { expect, test } from "@playwright/test";

/**
 * Scenario 4: Sell shares.
 *
 *   - Buy 5 AAPL (set up the position).
 *   - Sell 2 AAPL.
 *   - Cash increases relative to the post-buy snapshot.
 *   - Position quantity drops by 2 (net change vs. pre-test).
 *
 * Suite-ordering note (BUGS.md B004, option d):
 *   Spec 03 buys 5 AAPL before this spec runs. So the AAPL position
 *   quantity at the start of this spec is likely ~5 (from spec 03), not 0.
 *   This spec is order-independent: it reads the pre-existing AAPL
 *   quantity, buys 5 more, then sells 2, and asserts a NET delta of +3
 *   between start and finish — and that cash drops then rises across the
 *   buy/sell pair.
 */

async function readPortfolioState(
  request: import("@playwright/test").APIRequestContext,
): Promise<{ cash: number; aaplQty: number }> {
  const res = await request.get("/api/portfolio");
  const body = await res.json();
  const aapl = (body.positions ?? []).find(
    (p: { ticker: string; quantity: number }) => p.ticker === "AAPL",
  );
  return { cash: body.cash_balance, aaplQty: aapl?.quantity ?? 0 };
}

test("sell 2 of 5 AAPL increases cash and drops quantity by 2", async ({
  page,
  request,
}) => {
  await page.goto("/");
  await expect(page.getByTestId("watchlist-row-AAPL")).toBeVisible();

  const start = await readPortfolioState(request);

  // -- Buy 5 -------------------------------------------------------------
  await page.getByLabel("Ticker").fill("AAPL");
  await page.getByLabel("Quantity").fill("5");
  await page.getByRole("button", { name: "Buy", exact: true }).click();
  await expect(page.getByText(/Bought 5 AAPL @ \$/)).toBeVisible({
    timeout: 10_000,
  });

  // Wait for the buy to reflect in the API.
  await expect
    .poll(async () => (await readPortfolioState(request)).aaplQty, {
      timeout: 10_000,
    })
    .toBeCloseTo(start.aaplQty + 5, 5);
  const afterBuy = await readPortfolioState(request);
  // Cash dropped after the buy.
  expect(afterBuy.cash).toBeLessThan(start.cash);

  // Confirm position quantity is start+5 in the UI.
  const positionsRegion = page.getByRole("region", { name: "Positions" });
  await expect(positionsRegion.getByText("AAPL", { exact: true })).toBeVisible({
    timeout: 10_000,
  });

  // -- Sell 2 ------------------------------------------------------------
  await page.getByLabel("Ticker").fill("AAPL");
  await page.getByLabel("Quantity").fill("2");
  await page.getByRole("button", { name: "Sell", exact: true }).click();
  await expect(page.getByText(/Sold 2 AAPL @ \$/)).toBeVisible({
    timeout: 10_000,
  });

  // After sell: quantity dropped by 2 from afterBuy → net (start+3) from spec start.
  await expect
    .poll(async () => (await readPortfolioState(request)).aaplQty, {
      timeout: 10_000,
    })
    .toBeCloseTo(start.aaplQty + 3, 5);

  const afterSell = await readPortfolioState(request);
  // Cash increased relative to the post-buy snapshot.
  expect(afterSell.cash).toBeGreaterThan(afterBuy.cash);
});
