import { expect, test } from "@playwright/test";

/**
 * Scenario 5: Insufficient cash error.
 *
 *   - Attempt to buy 1,000,000 NVDA on a fresh $10k account.
 *   - Inline error mentions "insufficient_cash" (machine code) or the
 *     human-readable equivalent.
 *   - Cash balance unchanged.
 *
 * API_CONTRACT.md §4.2 says the 400 response body is the error envelope:
 *   {"error":"insufficient_cash","error_message":"Need $X but only $Y available."}
 *
 * The TradeBar component surfaces the API's error message (see TradeBar.tsx:
 *   `setError(err instanceof Error ? err.message : "Trade failed")`).
 */

test("buying 1,000,000 NVDA surfaces insufficient_cash inline; cash unchanged", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByTestId("watchlist-row-NVDA")).toBeVisible();

  const cashMetric = page
    .locator("text=Cash")
    .locator("xpath=following-sibling::span[1]");
  await expect(cashMetric).toHaveText(/\$10,000\.00/);

  // -- Attempt the trade -------------------------------------------------
  await page.getByLabel("Ticker").fill("NVDA");
  await page.getByLabel("Quantity").fill("1000000");
  await page.getByRole("button", { name: "Buy", exact: true }).click();

  // The TradeBar renders the API error message in a rose-coloured span. We
  // assert either the machine code OR the human message — whichever the
  // frontend chose to surface. API_CONTRACT.md guarantees one of:
  //   - "insufficient_cash" (machine code), OR
  //   - "Need $X but only $Y available." (human)
  // The current TradeBar passes through `err.message`, which is the
  // human-readable text from the error envelope.
  const errorLocator = page.locator("text=/insufficient|Need \\$.*available/i");
  await expect(errorLocator).toBeVisible({ timeout: 10_000 });

  // -- Cash unchanged ---------------------------------------------------
  await expect(cashMetric).toHaveText(/\$10,000\.00/);
});
