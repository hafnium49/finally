# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 04-sell-shares.spec.ts >> sell 2 of 5 AAPL increases cash and drops quantity to 3
- Location: tests/04-sell-shares.spec.ts:22:5

# Error details

```
Error: expect(locator).toHaveText(expected) failed

Locator: getByRole('region', { name: 'Positions' }).locator('tbody tr').filter({ hasText: 'AAPL' }).first().locator('td').nth(1)
Expected pattern: /^5/
Received string:  "16"
Timeout: 10000ms

Call log:
  - Expect "toHaveText" with timeout 10000ms
  - waiting for getByRole('region', { name: 'Positions' }).locator('tbody tr').filter({ hasText: 'AAPL' }).first().locator('td').nth(1)
    24 × locator resolved to <td class="px-3 py-1.5 text-right tabular-nums">16</td>
       - unexpected value "16"

```

```yaml
- cell "16"
```

# Test source

```ts
  1  | import { expect, test } from "@playwright/test";
  2  | 
  3  | /**
  4  |  * Scenario 4: Sell shares.
  5  |  *
  6  |  *   - Buy 5 AAPL (set up the position).
  7  |  *   - Sell 2 AAPL.
  8  |  *   - Cash increases relative to the post-buy snapshot.
  9  |  *   - Position quantity drops to 3.
  10 |  */
  11 | 
  12 | async function readCashUsd(page: import("@playwright/test").Page): Promise<number> {
  13 |   const cashMetric = page
  14 |     .locator("text=Cash")
  15 |     .locator("xpath=following-sibling::span[1]");
  16 |   const text = (await cashMetric.textContent()) ?? "";
  17 |   // "$10,000.00" → 10000.00
  18 |   const cleaned = text.replace(/[^0-9.\-]/g, "");
  19 |   return parseFloat(cleaned);
  20 | }
  21 | 
  22 | test("sell 2 of 5 AAPL increases cash and drops quantity to 3", async ({
  23 |   page,
  24 | }) => {
  25 |   await page.goto("/");
  26 |   await expect(page.getByTestId("watchlist-row-AAPL")).toBeVisible();
  27 | 
  28 |   // -- Buy 5 -------------------------------------------------------------
  29 |   await page.getByLabel("Ticker").fill("AAPL");
  30 |   await page.getByLabel("Quantity").fill("5");
  31 |   await page.getByRole("button", { name: "Buy", exact: true }).click();
  32 |   await expect(page.getByText(/Bought 5 AAPL @ \$/)).toBeVisible({
  33 |     timeout: 10_000,
  34 |   });
  35 | 
  36 |   // Wait for cash to update from the trade response.
  37 |   await expect.poll(async () => readCashUsd(page), { timeout: 10_000 }).toBeLessThan(
  38 |     10_000,
  39 |   );
  40 |   const cashAfterBuy = await readCashUsd(page);
  41 | 
  42 |   // Confirm position quantity is 5.
  43 |   const positionsRegion = page.getByRole("region", { name: "Positions" });
  44 |   await expect(positionsRegion.getByText("AAPL", { exact: true })).toBeVisible({
  45 |     timeout: 10_000,
  46 |   });
  47 |   // The row's Qty cell.
  48 |   const aaplRow = positionsRegion.locator("tbody tr", { hasText: "AAPL" }).first();
> 49 |   await expect(aaplRow.locator("td").nth(1)).toHaveText(/^5/);
     |                                              ^ Error: expect(locator).toHaveText(expected) failed
  50 | 
  51 |   // -- Sell 2 ------------------------------------------------------------
  52 |   await page.getByLabel("Ticker").fill("AAPL");
  53 |   await page.getByLabel("Quantity").fill("2");
  54 |   await page.getByRole("button", { name: "Sell", exact: true }).click();
  55 |   await expect(page.getByText(/Sold 2 AAPL @ \$/)).toBeVisible({
  56 |     timeout: 10_000,
  57 |   });
  58 | 
  59 |   // Cash increases.
  60 |   await expect
  61 |     .poll(async () => readCashUsd(page), { timeout: 10_000 })
  62 |     .toBeGreaterThan(cashAfterBuy);
  63 | 
  64 |   // Position quantity drops to 3.
  65 |   await expect(aaplRow.locator("td").nth(1)).toHaveText(/^3/, { timeout: 10_000 });
  66 | });
  67 | 
```