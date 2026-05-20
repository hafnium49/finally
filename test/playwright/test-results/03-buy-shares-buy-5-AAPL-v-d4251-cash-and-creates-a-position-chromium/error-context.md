# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 03-buy-shares.spec.ts >> buy 5 AAPL via trade bar reduces cash and creates a position
- Location: tests/03-buy-shares.spec.ts:11:5

# Error details

```
Error: expect(locator).toHaveText(expected) failed

Locator: locator('text=Cash').locator('xpath=following-sibling::span[1]')
Expected pattern: /\$10,000\.00/
Received string:  "$9,431.06"
Timeout: 10000ms

Call log:
  - Expect "toHaveText" with timeout 10000ms
  - waiting for locator('text=Cash').locator('xpath=following-sibling::span[1]')
    23 × locator resolved to <span class="text-base font-semibold text-text-primary">$9,431.06</span>
       - unexpected value "$9,431.06"

```

```yaml
- text: $9,431.06
```

# Test source

```ts
  1  | import { expect, test } from "@playwright/test";
  2  | 
  3  | /**
  4  |  * Scenario 3: Buy shares via the trade bar.
  5  |  *
  6  |  *   - Buy 5 AAPL.
  7  |  *   - Cash balance decreases.
  8  |  *   - AAPL appears in the positions table.
  9  |  */
  10 | 
  11 | test("buy 5 AAPL via trade bar reduces cash and creates a position", async ({
  12 |   page,
  13 | }) => {
  14 |   await page.goto("/");
  15 | 
  16 |   // Wait for boot.
  17 |   await expect(page.getByTestId("watchlist-row-AAPL")).toBeVisible();
  18 | 
  19 |   // Read starting cash (should be the seeded $10,000.00).
  20 |   const cashMetric = page
  21 |     .locator("text=Cash")
  22 |     .locator("xpath=following-sibling::span[1]");
> 23 |   await expect(cashMetric).toHaveText(/\$10,000\.00/);
     |                            ^ Error: expect(locator).toHaveText(expected) failed
  24 | 
  25 |   // -- Submit trade ------------------------------------------------------
  26 |   await page.getByLabel("Ticker").fill("AAPL");
  27 |   await page.getByLabel("Quantity").fill("5");
  28 |   await page.getByRole("button", { name: "Buy", exact: true }).click();
  29 | 
  30 |   // Success message appears in the trade bar.
  31 |   await expect(page.getByText(/Bought 5 AAPL @ \$/)).toBeVisible({
  32 |     timeout: 10_000,
  33 |   });
  34 | 
  35 |   // -- Positions row -----------------------------------------------------
  36 |   // Wait for the positions table to populate after the trade.
  37 |   const positionsRegion = page.getByRole("region", { name: "Positions" });
  38 |   await expect(positionsRegion.getByText("AAPL", { exact: true })).toBeVisible({
  39 |     timeout: 10_000,
  40 |   });
  41 | 
  42 |   // -- Cash decreased ----------------------------------------------------
  43 |   // The cash metric should no longer show $10,000.00.
  44 |   await expect(cashMetric).not.toHaveText(/\$10,000\.00/, { timeout: 10_000 });
  45 | });
  46 | 
```