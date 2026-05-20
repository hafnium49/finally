# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 02-watchlist-crud.spec.ts >> add PYPL then remove NFLX (persisted across reload)
- Location: tests/02-watchlist-crud.spec.ts:17:5

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByTestId('watchlist-row-NFLX')
Expected: visible
Error: strict mode violation: getByTestId('watchlist-row-NFLX') resolved to 2 elements:
    1) <div tabindex="0" role="button" data-testid="watchlist-row-NFLX" class="group grid cursor-pointer grid-cols-[1fr_auto_auto_auto] items-center gap-3 border-b border-border-muted/60 px-3 py-2 font-mono text-sm transition-colors hover:bg-surface-2 ">…</div> aka getByRole('button', { name: 'NFLX +6.54% 639.25 Remove' })
    2) <div tabindex="0" role="button" data-testid="watchlist-row-NFLX" class="group grid cursor-pointer grid-cols-[1fr_auto_auto_auto] items-center gap-3 border-b border-border-muted/60 px-3 py-2 font-mono text-sm transition-colors hover:bg-surface-2 ">…</div> aka getByTestId('watchlist-row-NFLX').nth(1)

Call log:
  - Expect "toBeVisible" with timeout 10000ms
  - waiting for getByTestId('watchlist-row-NFLX')

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
            - generic [ref=e13]: $10,000.07
          - generic [ref=e14]:
            - generic [ref=e15]: Cash
            - generic [ref=e16]: $9,431.06
          - generic [ref=e17]:
            - generic [ref=e18]: Unrealized P&L
            - generic [ref=e19]: $0.03
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
          - button "AAPL -0.18% 189.66 Remove AAPL from watchlist" [ref=e33] [cursor=pointer]:
            - generic [ref=e34]:
              - generic [ref=e35]: AAPL
              - generic [ref=e36]: "-0.18%"
            - generic [ref=e37]: "189.66"
            - button "Remove AAPL from watchlist" [ref=e39]: ✕
          - button "AMZN +6.56% 197.14 Remove AMZN from watchlist" [ref=e40] [cursor=pointer]:
            - generic [ref=e41]:
              - generic [ref=e42]: AMZN
              - generic [ref=e43]: +6.56%
            - generic [ref=e44]: "197.14"
            - button "Remove AMZN from watchlist" [ref=e46]: ✕
          - button "GOOGL +2.69% 179.70 Remove GOOGL from watchlist" [ref=e47] [cursor=pointer]:
            - generic [ref=e48]:
              - generic [ref=e49]: GOOGL
              - generic [ref=e50]: +2.69%
            - generic [ref=e51]: "179.70"
            - button "Remove GOOGL from watchlist" [ref=e53]: ✕
          - button "JPM +0.18% 195.36 Remove JPM from watchlist" [ref=e54] [cursor=pointer]:
            - generic [ref=e55]:
              - generic [ref=e56]: JPM
              - generic [ref=e57]: +0.18%
            - generic [ref=e58]: "195.36"
            - button "Remove JPM from watchlist" [ref=e60]: ✕
          - button "META +4.28% 521.38 Remove META from watchlist" [ref=e61] [cursor=pointer]:
            - generic [ref=e62]:
              - generic [ref=e63]: META
              - generic [ref=e64]: +4.28%
            - generic [ref=e65]: "521.38"
            - button "Remove META from watchlist" [ref=e67]: ✕
          - button "MSFT +10.57% 464.40 Remove MSFT from watchlist" [ref=e68] [cursor=pointer]:
            - generic [ref=e69]:
              - generic [ref=e70]: MSFT
              - generic [ref=e71]: +10.57%
            - generic [ref=e72]: "464.40"
            - button "Remove MSFT from watchlist" [ref=e74]: ✕
          - button "NFLX +6.54% 639.24 Remove NFLX from watchlist" [ref=e75] [cursor=pointer]:
            - generic [ref=e76]:
              - generic [ref=e77]: NFLX
              - generic [ref=e78]: +6.54%
            - generic [ref=e79]: "639.24"
            - button "Remove NFLX from watchlist" [ref=e81]: ✕
          - button "NVDA +0.20% 801.60 Remove NVDA from watchlist" [ref=e82] [cursor=pointer]:
            - generic [ref=e83]:
              - generic [ref=e84]: NVDA
              - generic [ref=e85]: +0.20%
            - generic [ref=e86]: "801.60"
            - button "Remove NVDA from watchlist" [ref=e88]: ✕
          - button "TSLA -5.19% 237.02 Remove TSLA from watchlist" [ref=e89] [cursor=pointer]:
            - generic [ref=e90]:
              - generic [ref=e91]: TSLA
              - generic [ref=e92]: "-5.19%"
            - generic [ref=e93]: "237.02"
            - button "Remove TSLA from watchlist" [ref=e95]: ✕
          - button "V +3.80% 290.63 Remove V from watchlist" [ref=e96] [cursor=pointer]:
            - generic [ref=e97]:
              - generic [ref=e98]: V
              - generic [ref=e99]: +3.80%
            - generic [ref=e100]: "290.63"
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
                  - generic [ref=e152]: +0.0%
              - list [ref=e153]:
                - listitem [ref=e154]: "AAPL: $569.01 (+0.01%)"
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
                - row "AAPL 3 189.66 189.66 $0.00 0.00%" [ref=e211] [cursor=pointer]:
                  - cell "AAPL" [ref=e212]
                  - cell "3" [ref=e213]
                  - cell "189.66" [ref=e214]
                  - cell "189.66" [ref=e215]
                  - cell "$0.00" [ref=e216]
                  - cell "0.00%" [ref=e217]
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
  4  |  * Scenario 2: Watchlist CRUD.
  5  |  *
  6  |  *   - Add PYPL via the input control; assert row appears.
  7  |  *   - Remove a default ticker (NFLX); assert it disappears and is NOT
  8  |  *     restored after reload.
  9  |  *
  10 |  * The watchlist add control is the form inside the Watchlist component:
  11 |  *   <input placeholder="Add ticker" />  +  <button>Add</button>
  12 |  *
  13 |  * The remove control is a per-row "✕" button labelled
  14 |  *   "Remove <TICKER> from watchlist".
  15 |  */
  16 | 
  17 | test("add PYPL then remove NFLX (persisted across reload)", async ({ page }) => {
  18 |   await page.goto("/");
  19 | 
  20 |   // Wait for the seed watchlist to render so we know the page is hot.
> 21 |   await expect(page.getByTestId("watchlist-row-NFLX")).toBeVisible();
     |                                                        ^ Error: expect(locator).toBeVisible() failed
  22 | 
  23 |   // -- Add PYPL ----------------------------------------------------------
  24 |   const addInput = page.getByPlaceholder("Add ticker");
  25 |   await addInput.fill("PYPL");
  26 |   await page.getByRole("button", { name: "Add", exact: true }).click();
  27 | 
  28 |   await expect(page.getByTestId("watchlist-row-PYPL")).toBeVisible({
  29 |     timeout: 10_000,
  30 |   });
  31 | 
  32 |   // -- Remove NFLX -------------------------------------------------------
  33 |   // The remove button is hidden until hover, but Playwright's click forces
  34 |   // it. We use the accessible name instead of relying on hover state.
  35 |   const nflxRow = page.getByTestId("watchlist-row-NFLX");
  36 |   await nflxRow.hover();
  37 |   await page
  38 |     .getByRole("button", { name: "Remove NFLX from watchlist" })
  39 |     .click();
  40 | 
  41 |   await expect(page.getByTestId("watchlist-row-NFLX")).toHaveCount(0);
  42 | 
  43 |   // -- Reload and assert persistence ------------------------------------
  44 |   await page.reload();
  45 |   await expect(page.getByTestId("watchlist-row-PYPL")).toBeVisible({
  46 |     timeout: 10_000,
  47 |   });
  48 |   await expect(page.getByTestId("watchlist-row-NFLX")).toHaveCount(0);
  49 | });
  50 | 
```