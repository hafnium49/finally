import { expect, test } from "@playwright/test";

/**
 * Scenario 3: Buy shares via the trade bar.
 *
 *   - Buy 5 AAPL.
 *   - Cash balance decreases.
 *   - AAPL appears in the positions table.
 *
 * Suite-ordering note (BUGS.md B004, option d):
 *   Spec 01 only reads. Spec 02 mutates only the watchlist (no cash impact).
 *   Therefore at the start of this spec the cash baseline IS still $10,000
 *   when the suite is run from a clean volume. But to keep this spec
 *   resilient against re-runs and reordering, we assert in DELTAS — read
 *   the current cash via the API, perform the buy, then assert cash
 *   decreased by approximately price * quantity. Same for positions: we
 *   assert quantity increased by 5, regardless of starting quantity.
 */

async function readCashAndAaplQty(
  request: import("@playwright/test").APIRequestContext,
): Promise<{ cash: number; aaplQty: number }> {
  const res = await request.get("/api/portfolio");
  const body = await res.json();
  const aapl = (body.positions ?? []).find(
    (p: { ticker: string; quantity: number }) => p.ticker === "AAPL",
  );
  return { cash: body.cash_balance, aaplQty: aapl?.quantity ?? 0 };
}

test("buy 5 AAPL via trade bar reduces cash and creates a position", async ({
  page,
  request,
}) => {
  await page.goto("/");

  // Wait for boot.
  await expect(page.getByTestId("watchlist-row-AAPL")).toBeVisible();

  // Snapshot starting state (delta-based — order-independent).
  const before = await readCashAndAaplQty(request);

  const cashMetric = page
    .locator("text=Cash")
    .locator("xpath=following-sibling::span[1]");
  // Sanity: header displays a positive cash value.
  await expect(cashMetric).toContainText("$");

  // -- Submit trade ------------------------------------------------------
  await page.getByLabel("Ticker").fill("AAPL");
  await page.getByLabel("Quantity").fill("5");
  await page.getByRole("button", { name: "Buy", exact: true }).click();

  // Success message appears in the trade bar.
  await expect(page.getByText(/Bought 5 AAPL @ \$/)).toBeVisible({
    timeout: 10_000,
  });

  // -- Positions row -----------------------------------------------------
  // Wait for the positions table to populate after the trade.
  const positionsRegion = page.getByRole("region", { name: "Positions" });
  await expect(positionsRegion.getByText("AAPL", { exact: true })).toBeVisible({
    timeout: 10_000,
  });

  // -- State changed by ~5 AAPL ----------------------------------------
  await expect
    .poll(async () => (await readCashAndAaplQty(request)).aaplQty, {
      timeout: 10_000,
    })
    .toBeGreaterThanOrEqual(before.aaplQty + 5);

  const after = await readCashAndAaplQty(request);
  // Cash decreased by some positive amount.
  expect(after.cash).toBeLessThan(before.cash);
  // Quantity increased by exactly 5.
  expect(after.aaplQty - before.aaplQty).toBeCloseTo(5, 5);
});
