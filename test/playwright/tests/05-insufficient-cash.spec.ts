import { expect, test } from "@playwright/test";

/**
 * Scenario 5: Insufficient cash error.
 *
 *   - Attempt to buy 1,000,000 NVDA.
 *   - Inline error mentions "insufficient_cash" (machine code) or the
 *     human-readable equivalent.
 *   - Cash balance unchanged.
 *
 * API_CONTRACT.md §4.2 says the 400 response body is the error envelope:
 *   {"error":"insufficient_cash","error_message":"Need $X but only $Y available."}
 *
 * The TradeBar component surfaces the API's error message (see TradeBar.tsx:
 *   `setError(err instanceof Error ? err.message : "Trade failed")`).
 *
 * Suite-ordering note (BUGS.md B004, option d):
 *   Prior specs (03 buys 5 AAPL, 04 buys 5 AAPL then sells 2) leave the
 *   cash balance below the seeded $10,000. The assertion "cash unchanged"
 *   is therefore against whatever cash value is current at the start of
 *   this spec — read once via the API and compared before/after, not
 *   against a hard-coded $10,000 string.
 */

async function readCash(
  request: import("@playwright/test").APIRequestContext,
): Promise<number> {
  const res = await request.get("/api/portfolio");
  return (await res.json()).cash_balance;
}

test("buying 1,000,000 NVDA surfaces insufficient_cash inline; cash unchanged", async ({
  page,
  request,
}) => {
  await page.goto("/");
  await expect(page.getByTestId("watchlist-row-NVDA")).toBeVisible();

  const cashBefore = await readCash(request);

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
  const cashAfter = await readCash(request);
  expect(cashAfter).toBeCloseTo(cashBefore, 2);
});
