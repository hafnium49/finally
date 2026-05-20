# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 06-portfolio-viz.spec.ts >> heatmap renders a rectangle and P&L chart has a snapshot
- Location: tests/06-portfolio-viz.spec.ts:14:5

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByTestId('watchlist-row-AAPL')
Expected: visible
Error: strict mode violation: getByTestId('watchlist-row-AAPL') resolved to 2 elements:
    1) <div tabindex="0" role="button" data-testid="watchlist-row-AAPL" class="group grid cursor-pointer grid-cols-[1fr_auto_auto_auto] items-center gap-3 border-b border-border-muted/60 px-3 py-2 font-mono text-sm transition-colors hover:bg-surface-2 ">…</div> aka getByRole('button', { name: 'AAPL -0.01% 189.99 Remove' })
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
          - button "AAPL -0.01% 189.99 Remove AAPL from watchlist" [ref=e33] [cursor=pointer]:
            - generic [ref=e34]:
              - generic [ref=e35]: AAPL
              - generic [ref=e36]: "-0.01%"
            - generic [ref=e37]: "189.99"
            - button "Remove AAPL from watchlist" [ref=e39]: ✕
          - button "AMZN +0.06% 185.11 Remove AMZN from watchlist" [ref=e40] [cursor=pointer]:
            - generic [ref=e41]:
              - generic [ref=e42]: AMZN
              - generic [ref=e43]: +0.06%
            - generic [ref=e44]: "185.11"
            - button "Remove AMZN from watchlist" [ref=e46]: ✕
          - button "GOOGL -4.55% 167.03 Remove GOOGL from watchlist" [ref=e47] [cursor=pointer]:
            - generic [ref=e48]:
              - generic [ref=e49]: GOOGL
              - generic [ref=e50]: "-4.55%"
            - generic [ref=e51]: "167.03"
            - button "Remove GOOGL from watchlist" [ref=e53]: ✕
          - button "JPM +0.02% 195.04 Remove JPM from watchlist" [ref=e54] [cursor=pointer]:
            - generic [ref=e55]:
              - generic [ref=e56]: JPM
              - generic [ref=e57]: +0.02%
            - generic [ref=e58]: "195.04"
            - button "Remove JPM from watchlist" [ref=e60]: ✕
          - button "META +0.07% 500.35 Remove META from watchlist" [ref=e61] [cursor=pointer]:
            - generic [ref=e62]:
              - generic [ref=e63]: META
              - generic [ref=e64]: +0.07%
            - generic [ref=e65]: "500.35"
            - button "Remove META from watchlist" [ref=e67]: ✕
          - button "MSFT +0.02% 420.08 Remove MSFT from watchlist" [ref=e68] [cursor=pointer]:
            - generic [ref=e69]:
              - generic [ref=e70]: MSFT
              - generic [ref=e71]: +0.02%
            - generic [ref=e72]: "420.08"
            - button "Remove MSFT from watchlist" [ref=e74]: ✕
          - button "NFLX +0.01% 600.05 Remove NFLX from watchlist" [ref=e75] [cursor=pointer]:
            - generic [ref=e76]:
              - generic [ref=e77]: NFLX
              - generic [ref=e78]: +0.01%
            - generic [ref=e79]: "600.05"
            - button "Remove NFLX from watchlist" [ref=e81]: ✕
          - button "NVDA +0.00% 800.04 Remove NVDA from watchlist" [ref=e82] [cursor=pointer]:
            - generic [ref=e83]:
              - generic [ref=e84]: NVDA
              - generic [ref=e85]: +0.00%
            - generic [ref=e86]: "800.04"
            - button "Remove NVDA from watchlist" [ref=e88]: ✕
          - button "TSLA +0.15% 250.37 Remove TSLA from watchlist" [ref=e89] [cursor=pointer]:
            - generic [ref=e90]:
              - generic [ref=e91]: TSLA
              - generic [ref=e92]: +0.15%
            - generic [ref=e93]: "250.37"
            - button "Remove TSLA from watchlist" [ref=e95]: ✕
          - button "V -0.02% 279.94 Remove V from watchlist" [ref=e96] [cursor=pointer]:
            - generic [ref=e97]:
              - generic [ref=e98]: V
              - generic [ref=e99]: "-0.02%"
            - generic [ref=e100]: "279.94"
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
            - img [ref=e160]:
              - generic [ref=e164]: 06:34 AM
              - generic [ref=e166]:
                - generic [ref=e168]: $9,998
                - generic [ref=e170]: $9,999
                - generic [ref=e172]: $10,000
                - generic [ref=e174]: $10,001
                - generic [ref=e176]: $10,002
          - region "Positions" [ref=e181]:
            - generic [ref=e182]:
              - heading "Positions" [level=2] [ref=e183]
              - generic [ref=e184]: 0 open
            - generic [ref=e186]: No open positions.
        - region "Trade" [ref=e187]:
          - generic [ref=e188]:
            - heading "Trade" [level=2] [ref=e189]
            - generic [ref=e190]: market · instant fill
          - generic [ref=e191]:
            - textbox "Ticker" [ref=e192]:
              - /placeholder: TICKER
            - textbox "Quantity" [ref=e193]:
              - /placeholder: QTY
            - button "Buy" [ref=e194] [cursor=pointer]
            - button "Sell" [ref=e195] [cursor=pointer]
      - complementary "AI chat" [ref=e197]:
        - generic [ref=e198]:
          - heading "FinAlly Assistant" [level=2] [ref=e201]
          - button "Hide chat panel" [ref=e202] [cursor=pointer]: —
        - generic [ref=e204]:
          - paragraph [ref=e205]: Ask FinAlly about your portfolio, request a trade, or manage your watchlist. Trades execute automatically.
          - generic [ref=e206]:
            - button "What's my portfolio?" [ref=e207] [cursor=pointer]
            - button "Buy 5 AAPL" [ref=e208] [cursor=pointer]
            - button "Add PYPL to watchlist" [ref=e209] [cursor=pointer]
        - generic [ref=e210]:
          - textbox "Chat input" [ref=e211]:
            - /placeholder: Ask FinAlly…
          - button "Send" [disabled] [ref=e212]
  - alert [ref=e213]
  - generic [ref=e214]: $9,998
```

# Test source

```ts
  1  | import { expect, test } from "@playwright/test";
  2  | 
  3  | /**
  4  |  * Scenario 6: Portfolio visualizations.
  5  |  *
  6  |  *   - Buy something so the heatmap has at least one rectangle.
  7  |  *   - Wait for the P&L chart to have at least one data point. The snapshot
  8  |  *     writer runs every 30s (PLAN.md §6 / portfolio module), and the contract
  9  |  *     also writes a snapshot immediately after each trade (API_CONTRACT.md
  10 |  *     §4.2). We poll the API directly because the chart's recharts SVG path
  11 |  *     is hard to assert on visually.
  12 |  */
  13 | 
  14 | test("heatmap renders a rectangle and P&L chart has a snapshot", async ({
  15 |   page,
  16 |   request,
  17 | }) => {
  18 |   test.setTimeout(75_000);
  19 | 
  20 |   await page.goto("/");
> 21 |   await expect(page.getByTestId("watchlist-row-AAPL")).toBeVisible();
     |                                                        ^ Error: expect(locator).toBeVisible() failed
  22 | 
  23 |   // Buy 1 AAPL so a position exists for the heatmap.
  24 |   await page.getByLabel("Ticker").fill("AAPL");
  25 |   await page.getByLabel("Quantity").fill("1");
  26 |   await page.getByRole("button", { name: "Buy", exact: true }).click();
  27 |   await expect(page.getByText(/Bought 1 AAPL @ \$/)).toBeVisible({
  28 |     timeout: 10_000,
  29 |   });
  30 | 
  31 |   // -- Heatmap rectangle ------------------------------------------------
  32 |   const heatmap = page.getByRole("region", { name: "Portfolio heatmap" });
  33 |   // The heatmap renders <rect> SVG elements inside an <svg> when there is at
  34 |   // least one priced position. Wait for one to appear.
  35 |   await expect(heatmap.locator("svg rect").first()).toBeVisible({
  36 |     timeout: 20_000,
  37 |   });
  38 | 
  39 |   // -- P&L chart has at least one snapshot ------------------------------
  40 |   // Poll the backend API directly — this avoids brittle SVG selectors and is
  41 |   // the canonical source of truth.
  42 |   await expect
  43 |     .poll(
  44 |       async () => {
  45 |         const res = await request.get("/api/portfolio/history?range=1h");
  46 |         if (!res.ok()) return 0;
  47 |         const body = await res.json();
  48 |         return Array.isArray(body.points) ? body.points.length : 0;
  49 |       },
  50 |       { timeout: 60_000, intervals: [1_000, 2_000, 5_000] },
  51 |     )
  52 |     .toBeGreaterThan(0);
  53 | });
  54 | 
```