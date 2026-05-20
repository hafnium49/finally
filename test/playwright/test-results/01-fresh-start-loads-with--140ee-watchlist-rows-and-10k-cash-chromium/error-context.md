# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 01-fresh-start.spec.ts >> loads with 10 default watchlist rows and $10k cash
- Location: tests/01-fresh-start.spec.ts:26:5

# Error details

```
Error: expected default ticker AAPL in watchlist

expect(locator).toBeVisible() failed

Locator: getByTestId('watchlist-row-AAPL')
Expected: visible
Error: strict mode violation: getByTestId('watchlist-row-AAPL') resolved to 2 elements:
    1) <div tabindex="0" role="button" data-testid="watchlist-row-AAPL" class="group grid cursor-pointer grid-cols-[1fr_auto_auto_auto] items-center gap-3 border-b border-border-muted/60 px-3 py-2 font-mono text-sm transition-colors hover:bg-surface-2 ">…</div> aka getByRole('button', { name: 'AAPL +0.01% 190.01 Remove' })
    2) <div tabindex="0" role="button" data-testid="watchlist-row-AAPL" class="group grid cursor-pointer grid-cols-[1fr_auto_auto_auto] items-center gap-3 border-b border-border-muted/60 px-3 py-2 font-mono text-sm transition-colors hover:bg-surface-2 ">…</div> aka getByTestId('watchlist-row-AAPL').nth(1)

Call log:
  - expected default ticker AAPL in watchlist with timeout 5000ms
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
          - button "AAPL +0.01% 190.01 Remove AAPL from watchlist" [ref=e33] [cursor=pointer]:
            - generic [ref=e34]:
              - generic [ref=e35]: AAPL
              - generic [ref=e36]: +0.01%
            - generic [ref=e37]: "190.01"
            - button "Remove AAPL from watchlist" [ref=e39]: ✕
          - button "AMZN +0.06% 185.11 Remove AMZN from watchlist" [ref=e40] [cursor=pointer]:
            - generic [ref=e41]:
              - generic [ref=e42]: AMZN
              - generic [ref=e43]: +0.06%
            - generic [ref=e44]: "185.11"
            - button "Remove AMZN from watchlist" [ref=e46]: ✕
          - button "GOOGL +0.06% 175.10 Remove GOOGL from watchlist" [ref=e47] [cursor=pointer]:
            - generic [ref=e48]:
              - generic [ref=e49]: GOOGL
              - generic [ref=e50]: +0.06%
            - generic [ref=e51]: "175.10"
            - button "Remove GOOGL from watchlist" [ref=e53]: ✕
          - button "JPM +0.01% 195.02 Remove JPM from watchlist" [ref=e54] [cursor=pointer]:
            - generic [ref=e55]:
              - generic [ref=e56]: JPM
              - generic [ref=e57]: +0.01%
            - generic [ref=e58]: "195.02"
            - button "Remove JPM from watchlist" [ref=e60]: ✕
          - button "META +0.05% 500.27 Remove META from watchlist" [ref=e61] [cursor=pointer]:
            - generic [ref=e62]:
              - generic [ref=e63]: META
              - generic [ref=e64]: +0.05%
            - generic [ref=e65]: "500.27"
            - button "Remove META from watchlist" [ref=e67]: ✕
          - button "MSFT +0.03% 420.14 Remove MSFT from watchlist" [ref=e68] [cursor=pointer]:
            - generic [ref=e69]:
              - generic [ref=e70]: MSFT
              - generic [ref=e71]: +0.03%
            - generic [ref=e72]: "420.14"
            - button "Remove MSFT from watchlist" [ref=e74]: ✕
          - button "NFLX +0.00% 600.01 Remove NFLX from watchlist" [ref=e75] [cursor=pointer]:
            - generic [ref=e76]:
              - generic [ref=e77]: NFLX
              - generic [ref=e78]: +0.00%
            - generic [ref=e79]: "600.01"
            - button "Remove NFLX from watchlist" [ref=e81]: ✕
          - button "NVDA -0.01% 799.94 Remove NVDA from watchlist" [ref=e82] [cursor=pointer]:
            - generic [ref=e83]:
              - generic [ref=e84]: NVDA
              - generic [ref=e85]: "-0.01%"
            - generic [ref=e86]: "799.94"
            - button "Remove NVDA from watchlist" [ref=e88]: ✕
          - button "TSLA +0.04% 250.10 Remove TSLA from watchlist" [ref=e89] [cursor=pointer]:
            - generic [ref=e90]:
              - generic [ref=e91]: TSLA
              - generic [ref=e92]: +0.04%
            - generic [ref=e93]: "250.10"
            - button "Remove TSLA from watchlist" [ref=e95]: ✕
          - button "V -0.02% 279.93 Remove V from watchlist" [ref=e96] [cursor=pointer]:
            - generic [ref=e97]:
              - generic [ref=e98]: V
              - generic [ref=e99]: "-0.02%"
            - generic [ref=e100]: "279.93"
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
  4  |  * Scenario 1: Fresh start.
  5  |  *
  6  |  * Acceptance criteria (PLAN.md §12):
  7  |  *   - 10 default watchlist rows render within 5s.
  8  |  *   - $10,000 cash balance shown in the header.
  9  |  *
  10 |  * The default seed list (SCHEMA.md / PLAN.md §7) is:
  11 |  *   AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, JPM, V, NFLX.
  12 |  */
  13 | const DEFAULT_TICKERS = [
  14 |   "AAPL",
  15 |   "GOOGL",
  16 |   "MSFT",
  17 |   "AMZN",
  18 |   "TSLA",
  19 |   "NVDA",
  20 |   "META",
  21 |   "JPM",
  22 |   "V",
  23 |   "NFLX",
  24 | ];
  25 | 
  26 | test("loads with 10 default watchlist rows and $10k cash", async ({ page }) => {
  27 |   await page.goto("/");
  28 | 
  29 |   // Every default ticker appears.
  30 |   for (const ticker of DEFAULT_TICKERS) {
  31 |     const row = page.getByTestId(`watchlist-row-${ticker}`);
> 32 |     await expect(row, `expected default ticker ${ticker} in watchlist`).toBeVisible({
     |                                                                         ^ Error: expected default ticker AAPL in watchlist
  33 |       timeout: 5_000,
  34 |     });
  35 |   }
  36 | 
  37 |   // Exactly 10 rows.
  38 |   await expect(page.locator('[data-testid^="watchlist-row-"]')).toHaveCount(10);
  39 | 
  40 |   // Cash balance reads "$10,000.00" — the Header renders cash via
  41 |   // formatUsd(10000) → "$10,000.00".
  42 |   const cashMetric = page
  43 |     .locator("text=Cash")
  44 |     .locator("xpath=following-sibling::span[1]");
  45 |   await expect(cashMetric).toHaveText(/\$10,000\.00/);
  46 | });
  47 | 
```