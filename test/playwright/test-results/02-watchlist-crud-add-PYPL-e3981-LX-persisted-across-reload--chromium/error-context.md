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
    1) <div tabindex="0" role="button" data-testid="watchlist-row-NFLX" class="group grid cursor-pointer grid-cols-[1fr_auto_auto_auto] items-center gap-3 border-b border-border-muted/60 px-3 py-2 font-mono text-sm transition-colors hover:bg-surface-2 ">…</div> aka getByRole('button', { name: 'NFLX +0.00% 600.03 Remove' })
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
            - generic [ref=e13]: $10,000.00
          - generic [ref=e14]:
            - generic [ref=e15]: Cash
            - generic [ref=e16]: $10,000.00
          - generic [ref=e17]:
            - generic [ref=e18]: Unrealized P&L
            - generic [ref=e19]: $0.00
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
          - button "AAPL +0.01% 190.02 Remove AAPL from watchlist" [ref=e33] [cursor=pointer]:
            - generic [ref=e34]:
              - generic [ref=e35]: AAPL
              - generic [ref=e36]: +0.01%
            - generic [ref=e37]: "190.02"
            - button "Remove AAPL from watchlist" [ref=e39]: ✕
          - button "AMZN +0.06% 185.11 Remove AMZN from watchlist" [ref=e40] [cursor=pointer]:
            - generic [ref=e41]:
              - generic [ref=e42]: AMZN
              - generic [ref=e43]: +0.06%
            - generic [ref=e44]: "185.11"
            - button "Remove AMZN from watchlist" [ref=e46]: ✕
          - button "GOOGL +0.06% 175.11 Remove GOOGL from watchlist" [ref=e47] [cursor=pointer]:
            - generic [ref=e48]:
              - generic [ref=e49]: GOOGL
              - generic [ref=e50]: +0.06%
            - generic [ref=e51]: "175.11"
            - button "Remove GOOGL from watchlist" [ref=e53]: ✕
          - button "JPM +0.02% 195.04 Remove JPM from watchlist" [ref=e54] [cursor=pointer]:
            - generic [ref=e55]:
              - generic [ref=e56]: JPM
              - generic [ref=e57]: +0.02%
            - generic [ref=e58]: "195.04"
            - button "Remove JPM from watchlist" [ref=e60]: ✕
          - button "META +0.05% 500.26 Remove META from watchlist" [ref=e61] [cursor=pointer]:
            - generic [ref=e62]:
              - generic [ref=e63]: META
              - generic [ref=e64]: +0.05%
            - generic [ref=e65]: "500.26"
            - button "Remove META from watchlist" [ref=e67]: ✕
          - button "MSFT +0.03% 420.13 Remove MSFT from watchlist" [ref=e68] [cursor=pointer]:
            - generic [ref=e69]:
              - generic [ref=e70]: MSFT
              - generic [ref=e71]: +0.03%
            - generic [ref=e72]: "420.13"
            - button "Remove MSFT from watchlist" [ref=e74]: ✕
          - button "NFLX +0.00% 600.03 Remove NFLX from watchlist" [ref=e75] [cursor=pointer]:
            - generic [ref=e76]:
              - generic [ref=e77]: NFLX
              - generic [ref=e78]: +0.00%
            - generic [ref=e79]: "600.03"
            - button "Remove NFLX from watchlist" [ref=e81]: ✕
          - button "NVDA +0.00% 800.01 Remove NVDA from watchlist" [ref=e82] [cursor=pointer]:
            - generic [ref=e83]:
              - generic [ref=e84]: NVDA
              - generic [ref=e85]: +0.00%
            - generic [ref=e86]: "800.01"
            - button "Remove NVDA from watchlist" [ref=e88]: ✕
          - button "TSLA +0.06% 250.14 Remove TSLA from watchlist" [ref=e89] [cursor=pointer]:
            - generic [ref=e90]:
              - generic [ref=e91]: TSLA
              - generic [ref=e92]: +0.06%
            - generic [ref=e93]: "250.14"
            - button "Remove TSLA from watchlist" [ref=e95]: ✕
          - button "V -0.02% 279.95 Remove V from watchlist" [ref=e96] [cursor=pointer]:
            - generic [ref=e97]:
              - generic [ref=e98]: V
              - generic [ref=e99]: "-0.02%"
            - generic [ref=e100]: "279.95"
            - button "Remove V from watchlist" [ref=e102]: ✕
      - generic [ref=e103]:
        - generic [ref=e104]:
          - region "Main chart" [ref=e106]:
            - generic [ref=e107]:
              - heading "Chart" [level=2] [ref=e108]
              - tablist "Range" [ref=e109]:
                - tab "1h" [selected] [ref=e110] [cursor=pointer]
                - tab "6h" [ref=e111] [cursor=pointer]
                - tab "24h" [ref=e112] [cursor=pointer]
                - tab "7d" [ref=e113] [cursor=pointer]
            - generic [ref=e114]:
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
              - generic [ref=e140]: Select a ticker from the watchlist
          - region "Portfolio heatmap" [ref=e142]:
            - heading "Allocation" [level=2] [ref=e144]
            - generic [ref=e146]: No priced positions yet
        - generic [ref=e147]:
          - region "Portfolio P&L" [ref=e149]:
            - generic [ref=e150]:
              - heading "Portfolio Value" [level=2] [ref=e151]
              - generic [ref=e152]:
                - button "1h" [ref=e153] [cursor=pointer]
                - button "6h" [ref=e154] [cursor=pointer]
                - button "24h" [ref=e155] [cursor=pointer]
                - button "7d" [ref=e156] [cursor=pointer]
            - generic [ref=e158]: No snapshots yet
          - region "Positions" [ref=e160]:
            - generic [ref=e161]:
              - heading "Positions" [level=2] [ref=e162]
              - generic [ref=e163]: 0 open
            - generic [ref=e165]: No open positions.
        - region "Trade" [ref=e166]:
          - generic [ref=e167]:
            - heading "Trade" [level=2] [ref=e168]
            - generic [ref=e169]: market · instant fill
          - generic [ref=e170]:
            - textbox "Ticker" [ref=e171]:
              - /placeholder: TICKER
            - textbox "Quantity" [ref=e172]:
              - /placeholder: QTY
            - button "Buy" [ref=e173] [cursor=pointer]
            - button "Sell" [ref=e174] [cursor=pointer]
      - complementary "AI chat" [ref=e176]:
        - generic [ref=e177]:
          - heading "FinAlly Assistant" [level=2] [ref=e180]
          - button "Hide chat panel" [ref=e181] [cursor=pointer]: —
        - generic [ref=e183]:
          - paragraph [ref=e184]: Ask FinAlly about your portfolio, request a trade, or manage your watchlist. Trades execute automatically.
          - generic [ref=e185]:
            - button "What's my portfolio?" [ref=e186] [cursor=pointer]
            - button "Buy 5 AAPL" [ref=e187] [cursor=pointer]
            - button "Add PYPL to watchlist" [ref=e188] [cursor=pointer]
        - generic [ref=e189]:
          - textbox "Chat input" [ref=e190]:
            - /placeholder: Ask FinAlly…
          - button "Send" [disabled] [ref=e191]
  - alert [ref=e192]
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