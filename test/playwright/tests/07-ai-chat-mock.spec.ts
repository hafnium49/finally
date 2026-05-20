import { expect, test } from "@playwright/test";

/**
 * Scenario 7: AI chat (mock mode).
 *
 * Three sub-flows that exercise the LLM_MOCK regex table from
 * LLM_CONTRACT.md §4.2:
 *   - "what's my portfolio" → portfolio summary string, no actions.
 *   - "Buy 2 MSFT"         → assistant message + success ActionCard;
 *                             MSFT then visible in positions.
 *   - "buy 9999 TSLA"      → assistant message + error ActionCard
 *                             (insufficient_cash).
 *
 * Selectors we rely on:
 *   - data-testid="chat-message-assistant" — the assistant's bubble
 *   - data-testid="action-trade-ok" / "action-trade-error"
 *   - data-testid="action-watchlist-ok"   (not used here but documented)
 */

async function sendChat(page: import("@playwright/test").Page, text: string) {
  const input = page.getByLabel("Chat input");
  await input.click();
  await input.fill(text);
  await page.getByRole("button", { name: "Send", exact: true }).click();
}

test("portfolio summary mock response renders without actions", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("watchlist-row-AAPL")).toBeVisible();

  await sendChat(page, "what's my portfolio");

  // Last assistant message: matches the LLM_CONTRACT mock string.
  const assistantMessages = page.getByTestId("chat-message-assistant");
  await expect(assistantMessages.last()).toContainText(
    "Mock portfolio summary",
    { timeout: 15_000 },
  );

  // No ActionCards should have rendered in that last bubble.
  await expect(
    assistantMessages.last().locator('[data-testid^="action-"]'),
  ).toHaveCount(0);
});

test("'Buy 2 MSFT' yields success action and a positions row", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("watchlist-row-MSFT")).toBeVisible();

  await sendChat(page, "Buy 2 MSFT");

  // Assistant text from mock: "Buying 2 MSFT."
  const assistantMessages = page.getByTestId("chat-message-assistant");
  await expect(assistantMessages.last()).toContainText("Buying 2 MSFT", {
    timeout: 15_000,
  });

  // Success ActionCard in the same bubble.
  await expect(
    assistantMessages.last().getByTestId("action-trade-ok"),
  ).toBeVisible({ timeout: 10_000 });

  // MSFT now appears in the positions table.
  const positionsRegion = page.getByRole("region", { name: "Positions" });
  await expect(positionsRegion.getByText("MSFT", { exact: true })).toBeVisible({
    timeout: 10_000,
  });
});

test("'buy 9999 TSLA' yields an insufficient_cash error action", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByTestId("watchlist-row-TSLA")).toBeVisible();

  await sendChat(page, "buy 9999 TSLA");

  const assistantMessages = page.getByTestId("chat-message-assistant");
  await expect(assistantMessages.last()).toContainText("Buying 9999 TSLA", {
    timeout: 15_000,
  });

  // Error ActionCard.
  const errorCard = assistantMessages.last().getByTestId("action-trade-error");
  await expect(errorCard).toBeVisible({ timeout: 10_000 });
  // Action card surfaces the error_message; we look for the substring
  // "available" (from "Need $X but only $Y available.") or "insufficient" as
  // a defensive net in case the human text differs.
  await expect(errorCard).toContainText(/insufficient|available/i);
});
