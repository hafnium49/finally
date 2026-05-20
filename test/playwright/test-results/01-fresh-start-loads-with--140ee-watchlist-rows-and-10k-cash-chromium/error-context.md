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
    1) <div tabindex="0" role="button" data-testid="watchlist-row-AAPL" class="group grid cursor-pointer grid-cols-[1fr_auto_auto_auto] items-center gap-3 border-b border-border-muted/60 px-3 py-2 font-mono text-sm transition-colors hover:bg-surface-2 ">…</div> aka getByRole('button', { name: 'AAPL -0.18% 189.66 Remove' })
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
            - generic [ref=e13]: $10,000.04
          - generic [ref=e14]:
            - generic [ref=e15]: Cash
            - generic [ref=e16]: $9,431.06
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
          - button "AAPL -0.18% 189.65 Remove AAPL from watchlist" [ref=e33] [cursor=pointer]:
            - generic [ref=e34]:
              - generic [ref=e35]: AAPL
              - generic [ref=e36]: "-0.18%"
            - generic [ref=e37]: "189.65"
            - button "Remove AAPL from watchlist" [ref=e39]: ✕
          - button "AMZN +6.55% 197.12 Remove AMZN from watchlist" [ref=e40] [cursor=pointer]:
            - generic [ref=e41]:
              - generic [ref=e42]: AMZN
              - generic [ref=e43]: +6.55%
            - generic [ref=e44]: "197.12"
            - button "Remove AMZN from watchlist" [ref=e46]: ✕
          - button "GOOGL +2.67% 179.68 Remove GOOGL from watchlist" [ref=e47] [cursor=pointer]:
            - generic [ref=e48]:
              - generic [ref=e49]: GOOGL
              - generic [ref=e50]: +2.67%
            - generic [ref=e51]: "179.68"
            - button "Remove GOOGL from watchlist" [ref=e53]: ✕
          - button "JPM +0.18% 195.36 Remove JPM from watchlist" [ref=e54] [cursor=pointer]:
            - generic [ref=e55]:
              - generic [ref=e56]: JPM
              - generic [ref=e57]: +0.18%
            - generic [ref=e58]: "195.36"
            - button "Remove JPM from watchlist" [ref=e60]: ✕
          - button "META +4.28% 521.40 Remove META from watchlist" [ref=e61] [cursor=pointer]:
            - generic [ref=e62]:
              - generic [ref=e63]: META
              - generic [ref=e64]: +4.28%
            - generic [ref=e65]: "521.40"
            - button "Remove META from watchlist" [ref=e67]: ✕
          - button "MSFT +10.57% 464.39 Remove MSFT from watchlist" [ref=e68] [cursor=pointer]:
            - generic [ref=e69]:
              - generic [ref=e70]: MSFT
              - generic [ref=e71]: +10.57%
            - generic [ref=e72]: "464.39"
            - button "Remove MSFT from watchlist" [ref=e74]: ✕
          - button "NFLX +6.56% 639.39 Remove NFLX from watchlist" [ref=e75] [cursor=pointer]:
            - generic [ref=e76]:
              - generic [ref=e77]: NFLX
              - generic [ref=e78]: +6.56%
            - generic [ref=e79]: "639.39"
            - button "Remove NFLX from watchlist" [ref=e81]: ✕
          - button "NVDA +0.18% 801.46 Remove NVDA from watchlist" [ref=e82] [cursor=pointer]:
            - generic [ref=e83]:
              - generic [ref=e84]: NVDA
              - generic [ref=e85]: +0.18%
            - generic [ref=e86]: "801.46"
            - button "Remove NVDA from watchlist" [ref=e88]: ✕
          - button "TSLA -5.19% 237.03 Remove TSLA from watchlist" [ref=e89] [cursor=pointer]:
            - generic [ref=e90]:
              - generic [ref=e91]: TSLA
              - generic [ref=e92]: "-5.19%"
            - generic [ref=e93]: "237.03"
            - button "Remove TSLA from watchlist" [ref=e95]: ✕
          - button "V +3.79% 290.62 Remove V from watchlist" [ref=e96] [cursor=pointer]:
            - generic [ref=e97]:
              - generic [ref=e98]: V
              - generic [ref=e99]: +3.79%
            - generic [ref=e100]: "290.62"
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
                  - generic [ref=e152]: 0.0%
              - list [ref=e153]:
                - listitem [ref=e154]: "AAPL: $568.98 (0.00%)"
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
                - row "AAPL 3 189.66 189.65 -$0.03 -0.01%" [ref=e211] [cursor=pointer]:
                  - cell "AAPL" [ref=e212]
                  - cell "3" [ref=e213]
                  - cell "189.66" [ref=e214]
                  - cell "189.65" [ref=e215]
                  - cell "-$0.03" [ref=e216]
                  - cell "-0.01%" [ref=e217]
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