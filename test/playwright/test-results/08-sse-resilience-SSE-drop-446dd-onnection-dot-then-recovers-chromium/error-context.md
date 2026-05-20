# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 08-sse-resilience.spec.ts >> SSE drop is reflected in the connection dot then recovers
- Location: tests/08-sse-resilience.spec.ts:20:5

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: "open"
Received: "closed"

Call Log:
- Timeout 20000ms exceeded while waiting on the predicate
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
          - generic [ref=e22]: Disconnected
    - main [ref=e23]:
      - region "Watchlist" [ref=e25]:
        - generic [ref=e26]:
          - heading "Watchlist" [level=2] [ref=e27]
          - generic [ref=e28]: 10 symbols
        - generic [ref=e29]:
          - textbox "Add ticker" [ref=e30]
          - button "Add" [disabled] [ref=e31]
        - generic [ref=e32]:
          - button "AAPL -0.03% 189.94 Remove AAPL from watchlist" [ref=e33] [cursor=pointer]:
            - generic [ref=e34]:
              - generic [ref=e35]: AAPL
              - generic [ref=e36]: "-0.03%"
            - generic [ref=e37]: "189.94"
            - button "Remove AAPL from watchlist" [ref=e39]: ✕
          - button "AMZN +0.06% 185.12 Remove AMZN from watchlist" [ref=e40] [cursor=pointer]:
            - generic [ref=e41]:
              - generic [ref=e42]: AMZN
              - generic [ref=e43]: +0.06%
            - generic [ref=e44]: "185.12"
            - button "Remove AMZN from watchlist" [ref=e46]: ✕
          - button "GOOGL -4.54% 167.05 Remove GOOGL from watchlist" [ref=e47] [cursor=pointer]:
            - generic [ref=e48]:
              - generic [ref=e49]: GOOGL
              - generic [ref=e50]: "-4.54%"
            - generic [ref=e51]: "167.05"
            - button "Remove GOOGL from watchlist" [ref=e53]: ✕
          - button "JPM -0.02% 194.97 Remove JPM from watchlist" [ref=e54] [cursor=pointer]:
            - generic [ref=e55]:
              - generic [ref=e56]: JPM
              - generic [ref=e57]: "-0.02%"
            - generic [ref=e58]: "194.97"
            - button "Remove JPM from watchlist" [ref=e60]: ✕
          - button "META +0.06% 500.32 Remove META from watchlist" [ref=e61] [cursor=pointer]:
            - generic [ref=e62]:
              - generic [ref=e63]: META
              - generic [ref=e64]: +0.06%
            - generic [ref=e65]: "500.32"
            - button "Remove META from watchlist" [ref=e67]: ✕
          - button "MSFT +0.01% 420.03 Remove MSFT from watchlist" [ref=e68] [cursor=pointer]:
            - generic [ref=e69]:
              - generic [ref=e70]: MSFT
              - generic [ref=e71]: +0.01%
            - generic [ref=e72]: "420.03"
            - button "Remove MSFT from watchlist" [ref=e74]: ✕
          - button "NFLX +0.01% 600.08 Remove NFLX from watchlist" [ref=e75] [cursor=pointer]:
            - generic [ref=e76]:
              - generic [ref=e77]: NFLX
              - generic [ref=e78]: +0.01%
            - generic [ref=e79]: "600.08"
            - button "Remove NFLX from watchlist" [ref=e81]: ✕
          - button "NVDA -0.06% 799.51 Remove NVDA from watchlist" [ref=e82] [cursor=pointer]:
            - generic [ref=e83]:
              - generic [ref=e84]: NVDA
              - generic [ref=e85]: "-0.06%"
            - generic [ref=e86]: "799.51"
            - button "Remove NVDA from watchlist" [ref=e88]: ✕
          - button "TSLA +0.12% 250.31 Remove TSLA from watchlist" [ref=e89] [cursor=pointer]:
            - generic [ref=e90]:
              - generic [ref=e91]: TSLA
              - generic [ref=e92]: +0.12%
            - generic [ref=e93]: "250.31"
            - button "Remove TSLA from watchlist" [ref=e95]: ✕
          - button "V -0.07% 279.80 Remove V from watchlist" [ref=e96] [cursor=pointer]:
            - generic [ref=e97]:
              - generic [ref=e98]: V
              - generic [ref=e99]: "-0.07%"
            - generic [ref=e100]: "279.80"
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
  4  |  * Scenario 8: SSE resilience.
  5  |  *
  6  |  * Use Playwright's `route()` API to intercept the first request to
  7  |  * /api/stream/prices and fail it (so the EventSource enters its
  8  |  * reconnecting/disconnected state). The browser auto-reconnects (retry: 1000
  9  |  * hint), and once we stop failing the route the connection comes back online.
  10 |  *
  11 |  * Assertion path: the Header's StatusDot renders
  12 |  *   data-testid="connection-status"
  13 |  *   data-state="open" | "reconnecting" | "connecting" | "closed"
  14 |  * We watch for "closed"/"connecting"/"reconnecting" and then "open".
  15 |  *
  16 |  * Note: `route()` only intercepts the *first* SSE request once `times: 1`.
  17 |  * After that, the genuine handler takes over and EventSource reconnects.
  18 |  */
  19 | 
  20 | test("SSE drop is reflected in the connection dot then recovers", async ({
  21 |   page,
  22 | }) => {
  23 |   // Fail the FIRST SSE request only.
  24 |   await page.route("**/api/stream/prices", async (route) => {
  25 |     await route.fulfill({
  26 |       status: 503,
  27 |       contentType: "text/plain",
  28 |       body: "service unavailable",
  29 |     });
  30 |   }, { times: 1 });
  31 | 
  32 |   await page.goto("/");
  33 | 
  34 |   const dot = page.getByTestId("connection-status");
  35 |   await expect(dot).toBeVisible();
  36 | 
  37 |   // First, the dot should leave the steady "open" state — i.e., it should
  38 |   // be in connecting / reconnecting / closed at some point shortly after
  39 |   // load.
  40 |   await expect
  41 |     .poll(
  42 |       async () => await dot.getAttribute("data-state"),
  43 |       { timeout: 15_000, intervals: [250, 500, 1_000] },
  44 |     )
  45 |     .not.toBe("open");
  46 | 
  47 |   // EventSource native retry kicks in (~1s per the SSE `retry: 1000` hint
  48 |   // emitted by the server). The second connection should succeed because
  49 |   // the route was intercepted with `times: 1`.
  50 |   await expect
  51 |     .poll(async () => await dot.getAttribute("data-state"), {
  52 |       timeout: 20_000,
  53 |       intervals: [500, 1_000, 2_000],
  54 |     })
> 55 |     .toBe("open");
     |      ^ Error: expect(received).toBe(expected) // Object.is equality
  56 | });
  57 | 
```