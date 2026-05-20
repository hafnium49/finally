# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 04-sell-shares.spec.ts >> sell 2 of 5 AAPL increases cash and drops quantity to 3
- Location: tests/04-sell-shares.spec.ts:22:5

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByTestId('watchlist-row-AAPL')
Expected: visible
Error: strict mode violation: getByTestId('watchlist-row-AAPL') resolved to 2 elements:
    1) <div tabindex="0" role="button" data-testid="watchlist-row-AAPL" class="group grid cursor-pointer grid-cols-[1fr_auto_auto_auto] items-center gap-3 border-b border-border-muted/60 px-3 py-2 font-mono text-sm transition-colors hover:bg-surface-2 ">…</div> aka getByRole('button', { name: 'AAPL -0.20% 189.62 Remove' })
    2) <div tabindex="0" role="button" data-testid="watchlist-row-AAPL" class="group grid cursor-pointer grid-cols-[1fr_auto_auto_auto] items-center gap-3 border-b border-border-muted/60 px-3 py-2 font-mono text-sm transition-colors hover:bg-surface-2 ">…</div> aka getByTestId('watchlist-row-AAPL').nth(1)

Call log:
  - Expect "toBeVisible" with timeout 10000ms
  - waiting for getByTestId('watchlist-row-AAPL')

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e2]:
    - banner [ref=e3]:
      - generic [ref=e4]:
        - generic [ref=e5]:
          - generic [ref=e6]: F
          - generic [ref=e7]:
            - generic [ref=e8]: FinAlly
            - generic [ref=e9]: AI Trading Workstation
        - generic [ref=e10]:
          - generic [ref=e11]:
            - generic [ref=e12]: Portfolio
            - generic [ref=e13]: $9,999.92
          - generic [ref=e14]:
            - generic [ref=e15]: Cash
            - generic [ref=e16]: $9,431.06
          - generic [ref=e17]:
            - generic [ref=e18]: Unrealized P&L
            - generic [ref=e19]: "-$0.12"
          - generic [ref=e22]: Live
    - main [ref=e23]:
      - region "Watchlist" [ref=e25]:
        - generic [ref=e26]:
          - heading "Watchlist" [level=2] [ref=e27]
          - generic [ref=e28]: 10 symbols
        - generic [ref=e29]:
          - textbox "Add ticker" [ref=e30]
          - button "Add" [disabled] [ref=e31]
        - generic [ref=e32]:
          - button "AAPL -0.19% 189.63 Remove AAPL from watchlist" [ref=e33] [cursor=pointer]:
            - generic [ref=e34]:
              - generic [ref=e35]: AAPL
              - generic [ref=e36]: "-0.19%"
            - generic [ref=e37]: "189.63"
            - button "Remove AAPL from watchlist" [ref=e39]: ✕
          - button "AMZN +6.59% 197.19 Remove AMZN from watchlist" [ref=e40] [cursor=pointer]:
            - generic [ref=e41]:
              - generic [ref=e42]: AMZN
              - generic [ref=e43]: +6.59%
            - generic [ref=e44]: "197.19"
            - button "Remove AMZN from watchlist" [ref=e46]: ✕
          - button "GOOGL +2.69% 179.70 Remove GOOGL from watchlist" [ref=e47] [cursor=pointer]:
            - generic [ref=e48]:
              - generic [ref=e49]: GOOGL
              - generic [ref=e50]: +2.69%
            - generic [ref=e51]: "179.70"
            - button "Remove GOOGL from watchlist" [ref=e53]: ✕
          - button "JPM +0.16% 195.32 Remove JPM from watchlist" [ref=e54] [cursor=pointer]:
            - generic [ref=e55]:
              - generic [ref=e56]: JPM
              - generic [ref=e57]: +0.16%
            - generic [ref=e58]: "195.32"
            - button "Remove JPM from watchlist" [ref=e60]: ✕
          - button "META +4.30% 521.49 Remove META from watchlist" [ref=e61] [cursor=pointer]:
            - generic [ref=e62]:
              - generic [ref=e63]: META
              - generic [ref=e64]: +4.30%
            - generic [ref=e65]: "521.49"
            - button "Remove META from watchlist" [ref=e67]: ✕
          - button "MSFT +10.60% 464.51 Remove MSFT from watchlist" [ref=e68] [cursor=pointer]:
            - generic [ref=e69]:
              - generic [ref=e70]: MSFT
              - generic [ref=e71]: +10.60%
            - generic [ref=e72]: "464.51"
            - button "Remove MSFT from watchlist" [ref=e74]: ✕
          - button "NFLX +6.54% 639.23 Remove NFLX from watchlist" [ref=e75] [cursor=pointer]:
            - generic [ref=e76]:
              - generic [ref=e77]: NFLX
              - generic [ref=e78]: +6.54%
            - generic [ref=e79]: "639.23"
            - button "Remove NFLX from watchlist" [ref=e81]: ✕
          - button "NVDA +0.21% 801.71 Remove NVDA from watchlist" [ref=e82] [cursor=pointer]:
            - generic [ref=e83]:
              - generic [ref=e84]: NVDA
              - generic [ref=e85]: +0.21%
            - generic [ref=e86]: "801.71"
            - button "Remove NVDA from watchlist" [ref=e88]: ✕
          - button "TSLA -5.11% 237.23 Remove TSLA from watchlist" [ref=e89] [cursor=pointer]:
            - generic [ref=e90]:
              - generic [ref=e91]: TSLA
              - generic [ref=e92]: "-5.11%"
            - generic [ref=e93]: "237.23"
            - button "Remove TSLA from watchlist" [ref=e95]: ✕
          - button "V +3.75% 290.50 Remove V from watchlist" [ref=e96] [cursor=pointer]:
            - generic [ref=e97]:
              - generic [ref=e98]: V
              - generic [ref=e99]: +3.75%
            - generic [ref=e100]: "290.50"
            - button "Remove V from watchlist" [ref=e102]: ✕
      - generic [ref=e103]:
        - generic [ref=e104]:
          - region "Main chart" [ref=e106]:
            - generic [ref=e107]:
              - heading "Chart · AAPL" [level=2] [ref=e108]
              - tablist "Range" [ref=e109]:
                - tab "1h" [selected] [ref=e110] [cursor=pointer]
                - tab "6h" [ref=e111] [cursor=pointer]
                - tab "24h" [ref=e112] [cursor=pointer]
                - tab "7d" [ref=e113] [cursor=pointer]
            - table [ref=e117]:
              - row [ref=e118]:
                - cell
                - cell [ref=e119]:
                  - link "Charting by TradingView" [ref=e123] [cursor=pointer]:
                    - /url: https://www.tradingview.com/?utm_medium=lwc-link&utm_campaign=lwc-chart&utm_source=localhost/
                    - img [ref=e124]
                - cell [ref=e128]
              - row [ref=e132]:
                - cell
                - cell [ref=e133]
                - cell [ref=e137]
          - region "Portfolio heatmap" [ref=e141]:
            - heading "Allocation" [level=2] [ref=e143]
            - generic [ref=e147]:
              - img [ref=e148]:
                - generic [ref=e149]:
                  - generic [ref=e151]: AAPL
                  - generic [ref=e152]: "-0.0%"
              - list [ref=e153]:
                - listitem [ref=e154]: "AAPL: $568.86 (-0.02%)"
        - generic [ref=e155]:
          - region "Portfolio P&L" [ref=e157]:
            - generic [ref=e158]:
              - heading "Portfolio Value" [level=2] [ref=e159]
              - generic [ref=e160]:
                - button "1h" [ref=e161] [cursor=pointer]
                - button "6h" [ref=e162] [cursor=pointer]
                - button "24h" [ref=e163] [cursor=pointer]
                - button "7d" [ref=e164] [cursor=pointer]
            - img [ref=e168]:
              - generic [ref=e170]:
                - generic [ref=e172]: 06:17 AM
                - generic [ref=e174]: 06:20 AM
                - generic [ref=e176]: 06:23 AM
                - generic [ref=e178]: 06:28 AM
              - generic [ref=e180]:
                - generic [ref=e182]: $10,000
                - generic [ref=e184]: $10,000
                - generic [ref=e186]: $10,000
                - generic [ref=e188]: $10,000
                - generic [ref=e190]: $10,000
          - region "Positions" [ref=e196]:
            - generic [ref=e197]:
              - heading "Positions" [level=2] [ref=e198]
              - generic [ref=e199]: 1 open
            - table [ref=e201]:
              - rowgroup [ref=e202]:
                - row "Ticker Qty Avg Cost Last P&L %" [ref=e203]:
                  - columnheader "Ticker" [ref=e204]
                  - columnheader "Qty" [ref=e205]
                  - columnheader "Avg Cost" [ref=e206]
                  - columnheader "Last" [ref=e207]
                  - columnheader "P&L" [ref=e208]
                  - columnheader "%" [ref=e209]
              - rowgroup [ref=e210]:
                - row "AAPL 3 189.66 189.63 -$0.09 -0.02%" [ref=e211] [cursor=pointer]:
                  - cell "AAPL" [ref=e212]
                  - cell "3" [ref=e213]
                  - cell "189.66" [ref=e214]
                  - cell "189.63" [ref=e215]
                  - cell "-$0.09" [ref=e216]
                  - cell "-0.02%" [ref=e217]
        - region "Trade" [ref=e218]:
          - generic [ref=e219]:
            - heading "Trade" [level=2] [ref=e220]
            - generic [ref=e221]: market · instant fill
          - generic [ref=e222]:
            - textbox "Ticker" [ref=e223]:
              - /placeholder: TICKER
              - text: AAPL
            - textbox "Quantity" [ref=e224]:
              - /placeholder: QTY
            - button "Buy" [ref=e225] [cursor=pointer]
            - button "Sell" [ref=e226] [cursor=pointer]
      - complementary "AI chat" [ref=e228]:
        - generic [ref=e229]:
          - heading "FinAlly Assistant" [level=2] [ref=e232]
          - button "Hide chat panel" [ref=e233] [cursor=pointer]: —
        - generic [ref=e235]:
          - paragraph [ref=e236]: Ask FinAlly about your portfolio, request a trade, or manage your watchlist. Trades execute automatically.
          - generic [ref=e237]:
            - button "What's my portfolio?" [ref=e238] [cursor=pointer]
            - button "Buy 5 AAPL" [ref=e239] [cursor=pointer]
            - button "Add PYPL to watchlist" [ref=e240] [cursor=pointer]
        - generic [ref=e241]:
          - textbox "Chat input" [ref=e242]:
            - /placeholder: Ask FinAlly…
          - button "Send" [disabled] [ref=e243]
  - alert [ref=e244]
  - generic [ref=e245]: $10,000
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
> 26 |   await expect(page.getByTestId("watchlist-row-AAPL")).toBeVisible();
     |                                                        ^ Error: expect(locator).toBeVisible() failed
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
  49 |   await expect(aaplRow.locator("td").nth(1)).toHaveText(/^5/);
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