import { expect, test } from "@playwright/test";

/**
 * Scenario 8: SSE resilience.
 *
 * Use Playwright's `route()` API to intercept the first request to
 * /api/stream/prices and fail it (so the EventSource enters its
 * reconnecting/disconnected state). The browser auto-reconnects (retry: 1000
 * hint), and once we stop failing the route the connection comes back online.
 *
 * Assertion path: the Header's StatusDot renders
 *   data-testid="connection-status"
 *   data-state="open" | "reconnecting" | "connecting" | "closed"
 * We watch for "closed"/"connecting"/"reconnecting" and then "open".
 *
 * Note: `route()` only intercepts the *first* SSE request once `times: 1`.
 * After that, the genuine handler takes over and EventSource reconnects.
 */

test("SSE drop is reflected in the connection dot then recovers", async ({
  page,
}) => {
  // Fail the FIRST SSE request only.
  await page.route("**/api/stream/prices", async (route) => {
    await route.fulfill({
      status: 503,
      contentType: "text/plain",
      body: "service unavailable",
    });
  }, { times: 1 });

  await page.goto("/");

  const dot = page.getByTestId("connection-status");
  await expect(dot).toBeVisible();

  // First, the dot should leave the steady "open" state — i.e., it should
  // be in connecting / reconnecting / closed at some point shortly after
  // load.
  await expect
    .poll(
      async () => await dot.getAttribute("data-state"),
      { timeout: 15_000, intervals: [250, 500, 1_000] },
    )
    .not.toBe("open");

  // EventSource native retry kicks in (~1s per the SSE `retry: 1000` hint
  // emitted by the server). The second connection should succeed because
  // the route was intercepted with `times: 1`.
  await expect
    .poll(async () => await dot.getAttribute("data-state"), {
      timeout: 20_000,
      intervals: [500, 1_000, 2_000],
    })
    .toBe("open");
});
