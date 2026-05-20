import { expect, test } from "@playwright/test";

/**
 * Scenario 3: Buy shares via the trade bar.
 *
 *   - Buy 5 AAPL.
 *   - Cash balance decreases.
 *   - AAPL appears in the positions table.
 */

test("buy 5 AAPL via trade bar reduces cash and creates a position", async ({
  page,
}) => {
  await page.goto("/");

  // Wait for boot.
  await expect(page.getByTestId("watchlist-row-AAPL")).toBeVisible();

  // Read starting cash (should be the seeded $10,000.00).
  const cashMetric = page
    .locator("text=Cash")
    .locator("xpath=following-sibling::span[1]");
  await expect(cashMetric).toHaveText(/\$10,000\.00/);

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

  // -- Cash decreased ----------------------------------------------------
  // The cash metric should no longer show $10,000.00.
  await expect(cashMetric).not.toHaveText(/\$10,000\.00/, { timeout: 10_000 });
});
