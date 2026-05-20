import { expect, test } from "@playwright/test";

/**
 * Scenario 4: Sell shares.
 *
 *   - Buy 5 AAPL (set up the position).
 *   - Sell 2 AAPL.
 *   - Cash increases relative to the post-buy snapshot.
 *   - Position quantity drops to 3.
 */

async function readCashUsd(page: import("@playwright/test").Page): Promise<number> {
  const cashMetric = page
    .locator("text=Cash")
    .locator("xpath=following-sibling::span[1]");
  const text = (await cashMetric.textContent()) ?? "";
  // "$10,000.00" → 10000.00
  const cleaned = text.replace(/[^0-9.\-]/g, "");
  return parseFloat(cleaned);
}

test("sell 2 of 5 AAPL increases cash and drops quantity to 3", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByTestId("watchlist-row-AAPL")).toBeVisible();

  // -- Buy 5 -------------------------------------------------------------
  await page.getByLabel("Ticker").fill("AAPL");
  await page.getByLabel("Quantity").fill("5");
  await page.getByRole("button", { name: "Buy", exact: true }).click();
  await expect(page.getByText(/Bought 5 AAPL @ \$/)).toBeVisible({
    timeout: 10_000,
  });

  // Wait for cash to update from the trade response.
  await expect.poll(async () => readCashUsd(page), { timeout: 10_000 }).toBeLessThan(
    10_000,
  );
  const cashAfterBuy = await readCashUsd(page);

  // Confirm position quantity is 5.
  const positionsRegion = page.getByRole("region", { name: "Positions" });
  await expect(positionsRegion.getByText("AAPL", { exact: true })).toBeVisible({
    timeout: 10_000,
  });
  // The row's Qty cell.
  const aaplRow = positionsRegion.locator("tbody tr", { hasText: "AAPL" }).first();
  await expect(aaplRow.locator("td").nth(1)).toHaveText(/^5/);

  // -- Sell 2 ------------------------------------------------------------
  await page.getByLabel("Ticker").fill("AAPL");
  await page.getByLabel("Quantity").fill("2");
  await page.getByRole("button", { name: "Sell", exact: true }).click();
  await expect(page.getByText(/Sold 2 AAPL @ \$/)).toBeVisible({
    timeout: 10_000,
  });

  // Cash increases.
  await expect
    .poll(async () => readCashUsd(page), { timeout: 10_000 })
    .toBeGreaterThan(cashAfterBuy);

  // Position quantity drops to 3.
  await expect(aaplRow.locator("td").nth(1)).toHaveText(/^3/, { timeout: 10_000 });
});
