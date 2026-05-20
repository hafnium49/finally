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
    1) <div tabindex="0" role="button" data-testid="watchlist-row-MSFT" class="group grid cursor-pointer grid-cols-[1fr_auto_auto_auto] items-center gap-3 border-b border-border-muted/60 px-3 py-2 font-mono text-sm transition-colors hover:bg-surface-2 ">…</div> aka getByRole('button', { name: 'MSFT +0.03% 420.13 Remove' })
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
          - button "AMZN +0.10% 185.19 Remove AMZN from watchlist" [ref=e40] [cursor=pointer]:
            - generic [ref=e41]:
              - generic [ref=e42]: AMZN
              - generic [ref=e43]: +0.10%
            - generic [ref=e44]: "185.19"
            - button "Remove AMZN from watchlist" [ref=e46]: ✕
          - button "GOOGL -4.53% 167.08 Remove GOOGL from watchlist" [ref=e47] [cursor=pointer]:
            - generic [ref=e48]:
              - generic [ref=e49]: GOOGL
              - generic [ref=e50]: "-4.53%"
            - generic [ref=e51]: "167.08"
            - button "Remove GOOGL from watchlist" [ref=e53]: ✕
          - button "JPM +0.04% 195.07 Remove JPM from watchlist" [ref=e54] [cursor=pointer]:
            - generic [ref=e55]:
              - generic [ref=e56]: JPM
              - generic [ref=e57]: +0.04%
            - generic [ref=e58]: "195.07"
            - button "Remove JPM from watchlist" [ref=e60]: ✕
          - button "META +0.11% 500.55 Remove META from watchlist" [ref=e61] [cursor=pointer]:
            - generic [ref=e62]:
              - generic [ref=e63]: META
              - generic [ref=e64]: +0.11%
            - generic [ref=e65]: "500.55"
            - button "Remove META from watchlist" [ref=e67]: ✕
          - button "MSFT +0.03% 420.13 Remove MSFT from watchlist" [ref=e68] [cursor=pointer]:
            - generic [ref=e69]:
              - generic [ref=e70]: MSFT
              - generic [ref=e71]: +0.03%
            - generic [ref=e72]: "420.13"
            - button "Remove MSFT from watchlist" [ref=e74]: ✕
          - button "NFLX +0.04% 600.22 Remove NFLX from watchlist" [ref=e75] [cursor=pointer]:
            - generic [ref=e76]:
              - generic [ref=e77]: NFLX
              - generic [ref=e78]: +0.04%
            - generic [ref=e79]: "600.22"
            - button "Remove NFLX from watchlist" [ref=e81]: ✕
          - button "NVDA +0.05% 800.41 Remove NVDA from watchlist" [ref=e82] [cursor=pointer]:
            - generic [ref=e83]:
              - generic [ref=e84]: NVDA
              - generic [ref=e85]: +0.05%
            - generic [ref=e86]: "800.41"
            - button "Remove NVDA from watchlist" [ref=e88]: ✕
          - button "TSLA +0.18% 250.44 Remove TSLA from watchlist" [ref=e89] [cursor=pointer]:
            - generic [ref=e90]:
              - generic [ref=e91]: TSLA
              - generic [ref=e92]: +0.18%
            - generic [ref=e93]: "250.44"
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