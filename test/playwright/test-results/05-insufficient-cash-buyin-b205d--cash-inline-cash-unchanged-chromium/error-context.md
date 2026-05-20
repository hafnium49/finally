# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 05-insufficient-cash.spec.ts >> buying 1,000,000 NVDA surfaces insufficient_cash inline; cash unchanged
- Location: tests/05-insufficient-cash.spec.ts:18:5

# Error details

```
Error: expect(locator).toHaveText(expected) failed

Locator: locator('text=Cash').locator('xpath=following-sibling::span[1]')
Expected pattern: /\$10,000\.00/
Received string:  "$6,957.02"
Timeout: 10000ms

Call log:
  - Expect "toHaveText" with timeout 10000ms
  - waiting for locator('text=Cash').locator('xpath=following-sibling::span[1]')
    24 × locator resolved to <span class="text-base font-semibold text-text-primary">$6,957.02</span>
       - unexpected value "$6,957.02"

```

```yaml
- text: $6,957.02
```

# Test source

```ts
  1  | import { expect, test } from "@playwright/test";
  2  | 
  3  | /**
  4  |  * Scenario 5: Insufficient cash error.
  5  |  *
  6  |  *   - Attempt to buy 1,000,000 NVDA on a fresh $10k account.
  7  |  *   - Inline error mentions "insufficient_cash" (machine code) or the
  8  |  *     human-readable equivalent.
  9  |  *   - Cash balance unchanged.
  10 |  *
  11 |  * API_CONTRACT.md §4.2 says the 400 response body is the error envelope:
  12 |  *   {"error":"insufficient_cash","error_message":"Need $X but only $Y available."}
  13 |  *
  14 |  * The TradeBar component surfaces the API's error message (see TradeBar.tsx:
  15 |  *   `setError(err instanceof Error ? err.message : "Trade failed")`).
  16 |  */
  17 | 
  18 | test("buying 1,000,000 NVDA surfaces insufficient_cash inline; cash unchanged", async ({
  19 |   page,
  20 | }) => {
  21 |   await page.goto("/");
  22 |   await expect(page.getByTestId("watchlist-row-NVDA")).toBeVisible();
  23 | 
  24 |   const cashMetric = page
  25 |     .locator("text=Cash")
  26 |     .locator("xpath=following-sibling::span[1]");
> 27 |   await expect(cashMetric).toHaveText(/\$10,000\.00/);
     |                            ^ Error: expect(locator).toHaveText(expected) failed
  28 | 
  29 |   // -- Attempt the trade -------------------------------------------------
  30 |   await page.getByLabel("Ticker").fill("NVDA");
  31 |   await page.getByLabel("Quantity").fill("1000000");
  32 |   await page.getByRole("button", { name: "Buy", exact: true }).click();
  33 | 
  34 |   // The TradeBar renders the API error message in a rose-coloured span. We
  35 |   // assert either the machine code OR the human message — whichever the
  36 |   // frontend chose to surface. API_CONTRACT.md guarantees one of:
  37 |   //   - "insufficient_cash" (machine code), OR
  38 |   //   - "Need $X but only $Y available." (human)
  39 |   // The current TradeBar passes through `err.message`, which is the
  40 |   // human-readable text from the error envelope.
  41 |   const errorLocator = page.locator("text=/insufficient|Need \\$.*available/i");
  42 |   await expect(errorLocator).toBeVisible({ timeout: 10_000 });
  43 | 
  44 |   // -- Cash unchanged ---------------------------------------------------
  45 |   await expect(cashMetric).toHaveText(/\$10,000\.00/);
  46 | });
  47 | 
```