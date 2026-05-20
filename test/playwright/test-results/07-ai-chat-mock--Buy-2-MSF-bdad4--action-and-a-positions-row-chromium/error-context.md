# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 07-ai-chat-mock.spec.ts >> 'Buy 2 MSFT' yields success action and a positions row
- Location: tests/07-ai-chat-mock.spec.ts:46:5

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: getByTestId('chat-message-assistant').last()
Expected substring: "Buying 2 MSFT"
Received string:    "Chat failed: The chat pipeline failed unexpectedly."
Timeout: 15000ms

Call log:
  - Expect "toContainText" with timeout 15000ms
  - waiting for getByTestId('chat-message-assistant').last()
    34 × locator resolved to <div class="flex justify-start" data-testid="chat-message-assistant">…</div>
       - unexpected value "Chat failed: The chat pipeline failed unexpectedly."

```

```yaml
- text: "Chat failed: The chat pipeline failed unexpectedly."
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
  48 |   await expect(page.getByTestId("watchlist-row-MSFT")).toBeVisible();
  49 | 
  50 |   await sendChat(page, "Buy 2 MSFT");
  51 | 
  52 |   // Assistant text from mock: "Buying 2 MSFT."
  53 |   const assistantMessages = page.getByTestId("chat-message-assistant");
> 54 |   await expect(assistantMessages.last()).toContainText("Buying 2 MSFT", {
     |                                          ^ Error: expect(locator).toContainText(expected) failed
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