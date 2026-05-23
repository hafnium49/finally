import { expect, test } from "@playwright/test";

/**
 * Scenario 8: SSE resilience.
 *
 * Use Playwright's `route()` API to intercept the first request to
 * /api/stream/prices and fail it at the TRANSPORT level (so the EventSource
 * enters its reconnecting/disconnected state). The browser auto-reconnects
 * (retry: 1000 hint), and once we stop failing the route the connection
 * comes back online.
 *
 * Assertion path: the Header's StatusDot renders
 *   data-testid="connection-status"
 *   data-state="open" | "reconnecting" | "connecting" | "closed"
 * We watch for "closed"/"connecting"/"reconnecting" and then "open".
 *
 * Note: `route()` only intercepts the *first* SSE request once `times: 1`.
 * After that, the genuine handler takes over and EventSource reconnects.
 *
 * History: previously this test used `route.fulfill({ status: 503 })`. Per
 * the EventSource spec, an HTTP error response transitions the connection
 * to a *permanent* CLOSED state — the browser does NOT auto-reconnect after
 * a non-2xx response. To exercise the native retry path we must instead
 * simulate a TRANSPORT-level disconnect via `route.abort('failed')`, which
 * behaves like a network hiccup. EventSource then re-attempts the
 * connection after its retry interval and we observe the dot returning to
 * "open" once the route block is lifted. See planning/BUGS.md B002.
 */

test("SSE drop is reflected in the connection dot then recovers", async ({
  page,
}) => {
  // Abort the FIRST SSE request at the transport layer only. A network-level
  // failure (rather than a 5xx HTTP response) is what triggers EventSource's
  // native reconnect logic.
  await page.route("**/api/stream/prices", async (route) => {
    await route.abort("failed");
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
