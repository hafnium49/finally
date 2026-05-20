# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 01-fresh-start.spec.ts >> loads with 10 default watchlist rows and $10k cash
- Location: tests/01-fresh-start.spec.ts:26:5

# Error details

```
Error: expect(locator).toHaveCount(expected) failed

Locator:  locator('[data-testid^="watchlist-row-"]')
Expected: 10
Received: 11
Timeout:  10000ms

Call log:
  - Expect "toHaveCount" with timeout 10000ms
  - waiting for locator('[data-testid^="watchlist-row-"]')
    24 × locator resolved to 11 elements
       - unexpected value "11"

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
            - generic [ref=e13]: $9,998.13
          - generic [ref=e14]:
            - generic [ref=e15]: Cash
            - generic [ref=e16]: $7,907.47
          - generic [ref=e17]:
            - generic [ref=e18]: Unrealized P&L
            - generic [ref=e19]: "-$1.87"
          - generic [ref=e22]: Live
    - main [ref=e23]:
      - region "Watchlist" [ref=e25]:
        - generic [ref=e26]:
          - heading "Watchlist" [level=2] [ref=e27]
          - generic [ref=e28]: 11 symbols
        - generic [ref=e29]:
          - textbox "Add ticker" [ref=e30]
          - button "Add" [disabled] [ref=e31]
        - generic [ref=e32]:
          - button "AAPL +0.05% 190.10 Remove AAPL from watchlist" [ref=e33] [cursor=pointer]:
            - generic [ref=e34]:
              - generic [ref=e35]: AAPL
              - generic [ref=e36]: +0.05%
            - generic [ref=e37]: "190.10"
            - button "Remove AAPL from watchlist" [ref=e39]: ✕
          - button "AMZN -4.69% 176.33 Remove AMZN from watchlist" [ref=e40] [cursor=pointer]:
            - generic [ref=e41]:
              - generic [ref=e42]: AMZN
              - generic [ref=e43]: "-4.69%"
            - generic [ref=e44]: "176.33"
            - button "Remove AMZN from watchlist" [ref=e46]: ✕
          - button "GOOGL +0.07% 175.13 Remove GOOGL from watchlist" [ref=e47] [cursor=pointer]:
            - generic [ref=e48]:
              - generic [ref=e49]: GOOGL
              - generic [ref=e50]: +0.07%
            - generic [ref=e51]: "175.13"
            - button "Remove GOOGL from watchlist" [ref=e53]: ✕
          - button "JPM -1.88% 191.33 Remove JPM from watchlist" [ref=e54] [cursor=pointer]:
            - generic [ref=e55]:
              - generic [ref=e56]: JPM
              - generic [ref=e57]: "-1.88%"
            - generic [ref=e58]: "191.33"
            - button "Remove JPM from watchlist" [ref=e60]: ✕
          - button "META +3.63% 518.15 Remove META from watchlist" [ref=e61] [cursor=pointer]:
            - generic [ref=e62]:
              - generic [ref=e63]: META
              - generic [ref=e64]: +3.63%
            - generic [ref=e65]: "518.15"
            - button "Remove META from watchlist" [ref=e67]: ✕
          - button "MSFT -0.07% 419.72 Remove MSFT from watchlist" [ref=e68] [cursor=pointer]:
            - generic [ref=e69]:
              - generic [ref=e70]: MSFT
              - generic [ref=e71]: "-0.07%"
            - generic [ref=e72]: "419.72"
            - button "Remove MSFT from watchlist" [ref=e74]: ✕
          - button "NFLX +2.44% 614.62 Remove NFLX from watchlist" [ref=e75] [cursor=pointer]:
            - generic [ref=e76]:
              - generic [ref=e77]: NFLX
              - generic [ref=e78]: +2.44%
            - generic [ref=e79]: "614.62"
            - button "Remove NFLX from watchlist" [ref=e81]: ✕
          - button "NVDA +4.02% 832.14 Remove NVDA from watchlist" [ref=e82] [cursor=pointer]:
            - generic [ref=e83]:
              - generic [ref=e84]: NVDA
              - generic [ref=e85]: +4.02%
            - generic [ref=e86]: "832.14"
            - button "Remove NVDA from watchlist" [ref=e88]: ✕
          - button "TSLA +0.03% 250.07 Remove TSLA from watchlist" [ref=e89] [cursor=pointer]:
            - generic [ref=e90]:
              - generic [ref=e91]: TSLA
              - generic [ref=e92]: +0.03%
            - generic [ref=e93]: "250.07"
            - button "Remove TSLA from watchlist" [ref=e95]: ✕
          - button "V -0.10% 279.72 Remove V from watchlist" [ref=e96] [cursor=pointer]:
            - generic [ref=e97]:
              - generic [ref=e98]: V
              - generic [ref=e99]: "-0.10%"
            - generic [ref=e100]: "279.72"
            - button "Remove V from watchlist" [ref=e102]: ✕
          - button "PYPL -0.08% 183.54 Remove PYPL from watchlist" [ref=e103] [cursor=pointer]:
            - generic [ref=e104]:
              - generic [ref=e105]: PYPL
              - generic [ref=e106]: "-0.08%"
            - generic [ref=e107]: "183.54"
            - button "Remove PYPL from watchlist" [ref=e109]: ✕
      - generic [ref=e110]:
        - generic [ref=e111]:
          - region "Main chart" [ref=e113]:
            - generic [ref=e114]:
              - heading "Chart · AAPL" [level=2] [ref=e115]
              - tablist "Range" [ref=e116]:
                - tab "1h" [selected] [ref=e117] [cursor=pointer]
                - tab "6h" [ref=e118] [cursor=pointer]
                - tab "24h" [ref=e119] [cursor=pointer]
                - tab "7d" [ref=e120] [cursor=pointer]
            - table [ref=e124]:
              - row [ref=e125]:
                - cell
                - cell [ref=e126]:
                  - link "Charting by TradingView" [ref=e130] [cursor=pointer]:
                    - /url: https://www.tradingview.com/?utm_medium=lwc-link&utm_campaign=lwc-chart&utm_source=localhost/
                    - img [ref=e131]
                - cell [ref=e135]
              - row [ref=e139]:
                - cell
                - cell [ref=e140]
                - cell [ref=e144]
          - region "Portfolio heatmap" [ref=e148]:
            - heading "Allocation" [level=2] [ref=e150]
            - generic [ref=e154]:
              - img [ref=e155]:
                - generic [ref=e156]:
                  - generic [ref=e158]: AAPL
                  - generic [ref=e159]: "-0.1%"
              - list [ref=e160]:
                - listitem [ref=e161]: "AAPL: $2,090.66 (-0.09%)"
        - generic [ref=e162]:
          - region "Portfolio P&L" [ref=e164]:
            - generic [ref=e165]:
              - heading "Portfolio Value" [level=2] [ref=e166]
              - generic [ref=e167]:
                - button "1h" [ref=e168] [cursor=pointer]
                - button "6h" [ref=e169] [cursor=pointer]
                - button "24h" [ref=e170] [cursor=pointer]
                - button "7d" [ref=e171] [cursor=pointer]
            - img [ref=e175]:
              - generic [ref=e177]:
                - generic [ref=e179]: 06:43 AM
                - generic [ref=e181]: 06:45 AM
                - generic [ref=e183]: 06:46 AM
                - generic [ref=e185]: 06:48 AM
              - generic [ref=e187]:
                - generic [ref=e189]: $9,998
                - generic [ref=e191]: $9,998
                - generic [ref=e193]: $9,999
                - generic [ref=e195]: $10,000
                - generic [ref=e197]: $10,000
          - region "Positions" [ref=e203]:
            - generic [ref=e204]:
              - heading "Positions" [level=2] [ref=e205]
              - generic [ref=e206]: 1 open
            - table [ref=e208]:
              - rowgroup [ref=e209]:
                - row "Ticker Qty Avg Cost Last P&L %" [ref=e210]:
                  - columnheader "Ticker" [ref=e211]
                  - columnheader "Qty" [ref=e212]
                  - columnheader "Avg Cost" [ref=e213]
                  - columnheader "Last" [ref=e214]
                  - columnheader "P&L" [ref=e215]
                  - columnheader "%" [ref=e216]
              - rowgroup [ref=e217]:
                - row "AAPL 11 190.23 190.10 -$1.43 -0.07%" [ref=e218] [cursor=pointer]:
                  - cell "AAPL" [ref=e219]
                  - cell "11" [ref=e220]
                  - cell "190.23" [ref=e221]
                  - cell "190.10" [ref=e222]
                  - cell "-$1.43" [ref=e223]
                  - cell "-0.07%" [ref=e224]
        - region "Trade" [ref=e225]:
          - generic [ref=e226]:
            - heading "Trade" [level=2] [ref=e227]
            - generic [ref=e228]: market · instant fill
          - generic [ref=e229]:
            - textbox "Ticker" [ref=e230]:
              - /placeholder: TICKER
              - text: AAPL
            - textbox "Quantity" [ref=e231]:
              - /placeholder: QTY
            - button "Buy" [ref=e232] [cursor=pointer]
            - button "Sell" [ref=e233] [cursor=pointer]
      - complementary "AI chat" [ref=e235]:
        - generic [ref=e236]:
          - heading "FinAlly Assistant" [level=2] [ref=e239]
          - button "Hide chat panel" [ref=e240] [cursor=pointer]: —
        - generic [ref=e242]:
          - paragraph [ref=e243]: Ask FinAlly about your portfolio, request a trade, or manage your watchlist. Trades execute automatically.
          - generic [ref=e244]:
            - button "What's my portfolio?" [ref=e245] [cursor=pointer]
            - button "Buy 5 AAPL" [ref=e246] [cursor=pointer]
            - button "Add PYPL to watchlist" [ref=e247] [cursor=pointer]
        - generic [ref=e248]:
          - textbox "Chat input" [ref=e249]:
            - /placeholder: Ask FinAlly…
          - button "Send" [disabled] [ref=e250]
  - alert [ref=e251]
  - generic [ref=e252]: $9,998
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
  32 |     await expect(row, `expected default ticker ${ticker} in watchlist`).toBeVisible({
  33 |       timeout: 5_000,
  34 |     });
  35 |   }
  36 | 
  37 |   // Exactly 10 rows.
> 38 |   await expect(page.locator('[data-testid^="watchlist-row-"]')).toHaveCount(10);
     |                                                                 ^ Error: expect(locator).toHaveCount(expected) failed
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