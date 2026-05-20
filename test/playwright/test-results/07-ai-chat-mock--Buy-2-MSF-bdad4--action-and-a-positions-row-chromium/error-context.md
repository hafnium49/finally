# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 07-ai-chat-mock.spec.ts >> 'Buy 2 MSFT' yields success action and a positions row
- Location: tests/07-ai-chat-mock.spec.ts:46:5

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByTestId('watchlist-row-MSFT')
Expected: visible
Error: strict mode violation: getByTestId('watchlist-row-MSFT') resolved to 2 elements:
    1) <div tabindex="0" role="button" data-testid="watchlist-row-MSFT" class="group grid cursor-pointer grid-cols-[1fr_auto_auto_auto] items-center gap-3 border-b border-border-muted/60 px-3 py-2 font-mono text-sm transition-colors hover:bg-surface-2 ">…</div> aka getByRole('button', { name: 'MSFT +10.56% 464.37 Remove' })
    2) <div tabindex="0" role="button" data-testid="watchlist-row-MSFT" class="group grid cursor-pointer grid-cols-[1fr_auto_auto_auto] items-center gap-3 border-b border-border-muted/60 px-3 py-2 font-mono text-sm transition-colors hover:bg-surface-2 ">…</div> aka getByTestId('watchlist-row-MSFT').nth(1)

Call log:
  - Expect "toBeVisible" with timeout 10000ms
  - waiting for getByTestId('watchlist-row-MSFT')

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
            - generic [ref=e13]: $9,999.98
          - generic [ref=e14]:
            - generic [ref=e15]: Cash
            - generic [ref=e16]: $9,431.06
          - generic [ref=e17]:
            - generic [ref=e18]: Unrealized P&L
            - generic [ref=e19]: "-$0.06"
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
          - button "AAPL -0.19% 189.64 Remove AAPL from watchlist" [ref=e33] [cursor=pointer]:
            - generic [ref=e34]:
              - generic [ref=e35]: AAPL
              - generic [ref=e36]: "-0.19%"
            - generic [ref=e37]: "189.64"
            - button "Remove AAPL from watchlist" [ref=e39]: ✕
          - button "AMZN +6.51% 197.04 Remove AMZN from watchlist" [ref=e40] [cursor=pointer]:
            - generic [ref=e41]:
              - generic [ref=e42]: AMZN
              - generic [ref=e43]: +6.51%
            - generic [ref=e44]: "197.04"
            - button "Remove AMZN from watchlist" [ref=e46]: ✕
          - button "GOOGL +2.66% 179.65 Remove GOOGL from watchlist" [ref=e47] [cursor=pointer]:
            - generic [ref=e48]:
              - generic [ref=e49]: GOOGL
              - generic [ref=e50]: +2.66%
            - generic [ref=e51]: "179.65"
            - button "Remove GOOGL from watchlist" [ref=e53]: ✕
          - button "JPM +0.14% 195.27 Remove JPM from watchlist" [ref=e54] [cursor=pointer]:
            - generic [ref=e55]:
              - generic [ref=e56]: JPM
              - generic [ref=e57]: +0.14%
            - generic [ref=e58]: "195.27"
            - button "Remove JPM from watchlist" [ref=e60]: ✕
          - button "META +4.26% 521.32 Remove META from watchlist" [ref=e61] [cursor=pointer]:
            - generic [ref=e62]:
              - generic [ref=e63]: META
              - generic [ref=e64]: +4.26%
            - generic [ref=e65]: "521.32"
            - button "Remove META from watchlist" [ref=e67]: ✕
          - button "MSFT +10.57% 464.38 Remove MSFT from watchlist" [ref=e68] [cursor=pointer]:
            - generic [ref=e69]:
              - generic [ref=e70]: MSFT
              - generic [ref=e71]: +10.57%
            - generic [ref=e72]: "464.38"
            - button "Remove MSFT from watchlist" [ref=e74]: ✕
          - button "NFLX +6.51% 639.07 Remove NFLX from watchlist" [ref=e75] [cursor=pointer]:
            - generic [ref=e76]:
              - generic [ref=e77]: NFLX
              - generic [ref=e78]: +6.51%
            - generic [ref=e79]: "639.07"
            - button "Remove NFLX from watchlist" [ref=e81]: ✕
          - button "NVDA +0.17% 801.39 Remove NVDA from watchlist" [ref=e82] [cursor=pointer]:
            - generic [ref=e83]:
              - generic [ref=e84]: NVDA
              - generic [ref=e85]: +0.17%
            - generic [ref=e86]: "801.39"
            - button "Remove NVDA from watchlist" [ref=e88]: ✕
          - button "TSLA -5.21% 236.97 Remove TSLA from watchlist" [ref=e89] [cursor=pointer]:
            - generic [ref=e90]:
              - generic [ref=e91]: TSLA
              - generic [ref=e92]: "-5.21%"
            - generic [ref=e93]: "236.97"
            - button "Remove TSLA from watchlist" [ref=e95]: ✕
          - button "V +3.74% 290.48 Remove V from watchlist" [ref=e96] [cursor=pointer]:
            - generic [ref=e97]:
              - generic [ref=e98]: V
              - generic [ref=e99]: +3.74%
            - generic [ref=e100]: "290.48"
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
                - listitem [ref=e154]: "AAPL: $568.92 (-0.01%)"
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
                - row "AAPL 3 189.66 189.64 -$0.06 -0.01%" [ref=e211] [cursor=pointer]:
                  - cell "AAPL" [ref=e212]
                  - cell "3" [ref=e213]
                  - cell "189.66" [ref=e214]
                  - cell "189.64" [ref=e215]
                  - cell "-$0.06" [ref=e216]
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
  4  |  * Scenario 7: AI chat (mock mode).
  5  |  *
  6  |  * Three sub-flows that exercise the LLM_MOCK regex table from
  7  |  * LLM_CONTRACT.md §4.2:
  8  |  *   - "what's my portfolio" → portfolio summary string, no actions.
  9  |  *   - "Buy 2 MSFT"         → assistant message + success ActionCard;
  10 |  *                             MSFT then visible in positions.
  11 |  *   - "buy 9999 TSLA"      → assistant message + error ActionCard
  12 |  *                             (insufficient_cash).
  13 |  *
  14 |  * Selectors we rely on:
  15 |  *   - data-testid="chat-message-assistant" — the assistant's bubble
  16 |  *   - data-testid="action-trade-ok" / "action-trade-error"
  17 |  *   - data-testid="action-watchlist-ok"   (not used here but documented)
  18 |  */
  19 | 
  20 | async function sendChat(page: import("@playwright/test").Page, text: string) {
  21 |   const input = page.getByLabel("Chat input");
  22 |   await input.click();
  23 |   await input.fill(text);
  24 |   await page.getByRole("button", { name: "Send", exact: true }).click();
  25 | }
  26 | 
  27 | test("portfolio summary mock response renders without actions", async ({ page }) => {
  28 |   await page.goto("/");
  29 |   await expect(page.getByTestId("watchlist-row-AAPL")).toBeVisible();
  30 | 
  31 |   await sendChat(page, "what's my portfolio");
  32 | 
  33 |   // Last assistant message: matches the LLM_CONTRACT mock string.
  34 |   const assistantMessages = page.getByTestId("chat-message-assistant");
  35 |   await expect(assistantMessages.last()).toContainText(
  36 |     "Mock portfolio summary",
  37 |     { timeout: 15_000 },
  38 |   );
  39 | 
  40 |   // No ActionCards should have rendered in that last bubble.
  41 |   await expect(
  42 |     assistantMessages.last().locator('[data-testid^="action-"]'),
  43 |   ).toHaveCount(0);
  44 | });
  45 | 
  46 | test("'Buy 2 MSFT' yields success action and a positions row", async ({ page }) => {
  47 |   await page.goto("/");
> 48 |   await expect(page.getByTestId("watchlist-row-MSFT")).toBeVisible();
     |                                                        ^ Error: expect(locator).toBeVisible() failed
  49 | 
  50 |   await sendChat(page, "Buy 2 MSFT");
  51 | 
  52 |   // Assistant text from mock: "Buying 2 MSFT."
  53 |   const assistantMessages = page.getByTestId("chat-message-assistant");
  54 |   await expect(assistantMessages.last()).toContainText("Buying 2 MSFT", {
  55 |     timeout: 15_000,
  56 |   });
  57 | 
  58 |   // Success ActionCard in the same bubble.
  59 |   await expect(
  60 |     assistantMessages.last().getByTestId("action-trade-ok"),
  61 |   ).toBeVisible({ timeout: 10_000 });
  62 | 
  63 |   // MSFT now appears in the positions table.
  64 |   const positionsRegion = page.getByRole("region", { name: "Positions" });
  65 |   await expect(positionsRegion.getByText("MSFT", { exact: true })).toBeVisible({
  66 |     timeout: 10_000,
  67 |   });
  68 | });
  69 | 
  70 | test("'buy 9999 TSLA' yields an insufficient_cash error action", async ({
  71 |   page,
  72 | }) => {
  73 |   await page.goto("/");
  74 |   await expect(page.getByTestId("watchlist-row-TSLA")).toBeVisible();
  75 | 
  76 |   await sendChat(page, "buy 9999 TSLA");
  77 | 
  78 |   const assistantMessages = page.getByTestId("chat-message-assistant");
  79 |   await expect(assistantMessages.last()).toContainText("Buying 9999 TSLA", {
  80 |     timeout: 15_000,
  81 |   });
  82 | 
  83 |   // Error ActionCard.
  84 |   const errorCard = assistantMessages.last().getByTestId("action-trade-error");
  85 |   await expect(errorCard).toBeVisible({ timeout: 10_000 });
  86 |   // Action card surfaces the error_message; we look for the substring
  87 |   // "available" (from "Need $X but only $Y available.") or "insufficient" as
  88 |   // a defensive net in case the human text differs.
  89 |   await expect(errorCard).toContainText(/insufficient|available/i);
  90 | });
  91 | 
```