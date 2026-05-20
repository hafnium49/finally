import { expect, test } from "@playwright/test";

/**
 * Scenario 1: Fresh start.
 *
 * Acceptance criteria (PLAN.md §12):
 *   - 10 default watchlist rows render within 5s.
 *   - $10,000 cash balance shown in the header.
 *
 * The default seed list (SCHEMA.md / PLAN.md §7) is:
 *   AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, JPM, V, NFLX.
 *
 * Suite-ordering note (BUGS.md B004, option d):
 *   This spec MUST be the first spec to run because it asserts the seeded
 *   baseline: cash == $10,000.00 and exactly the ten default tickers. The
 *   filename is prefixed `01-` so Playwright (with `workers: 1` and
 *   `fullyParallel: false`) picks it first. Do NOT rename this file
 *   without also adjusting the suite-ordering plan in BUGS.md B004.
 */
const DEFAULT_TICKERS = [
  "AAPL",
  "GOOGL",
  "MSFT",
  "AMZN",
  "TSLA",
  "NVDA",
  "META",
  "JPM",
  "V",
  "NFLX",
];

test("loads with 10 default watchlist rows and $10k cash", async ({ page }) => {
  await page.goto("/");

  // Every default ticker appears.
  for (const ticker of DEFAULT_TICKERS) {
    const row = page.getByTestId(`watchlist-row-${ticker}`);
    await expect(row, `expected default ticker ${ticker} in watchlist`).toBeVisible({
      timeout: 5_000,
    });
  }

  // Exactly 10 rows.
  await expect(page.locator('[data-testid^="watchlist-row-"]')).toHaveCount(10);

  // Cash balance reads "$10,000.00" — the Header renders cash via
  // formatUsd(10000) → "$10,000.00".
  const cashMetric = page
    .locator("text=Cash")
    .locator("xpath=following-sibling::span[1]");
  await expect(cashMetric).toHaveText(/\$10,000\.00/);
});
