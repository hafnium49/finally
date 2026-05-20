import { expect, test } from "@playwright/test";

/**
 * Scenario 6: Portfolio visualizations.
 *
 *   - Buy something so the heatmap has at least one rectangle.
 *   - Wait for the P&L chart to have at least one data point. The snapshot
 *     writer runs every 30s (PLAN.md §6 / portfolio module), and the contract
 *     also writes a snapshot immediately after each trade (API_CONTRACT.md
 *     §4.2). We poll the API directly because the chart's recharts SVG path
 *     is hard to assert on visually.
 */

test("heatmap renders a rectangle and P&L chart has a snapshot", async ({
  page,
  request,
}) => {
  test.setTimeout(75_000);

  await page.goto("/");
  await expect(page.getByTestId("watchlist-row-AAPL")).toBeVisible();

  // Buy 1 AAPL so a position exists for the heatmap.
  await page.getByLabel("Ticker").fill("AAPL");
  await page.getByLabel("Quantity").fill("1");
  await page.getByRole("button", { name: "Buy", exact: true }).click();
  await expect(page.getByText(/Bought 1 AAPL @ \$/)).toBeVisible({
    timeout: 10_000,
  });

  // -- Heatmap rectangle ------------------------------------------------
  const heatmap = page.getByRole("region", { name: "Portfolio heatmap" });
  // The heatmap renders <rect> SVG elements inside an <svg> when there is at
  // least one priced position. Wait for one to appear.
  await expect(heatmap.locator("svg rect").first()).toBeVisible({
    timeout: 20_000,
  });

  // -- P&L chart has at least one snapshot ------------------------------
  // Poll the backend API directly — this avoids brittle SVG selectors and is
  // the canonical source of truth.
  await expect
    .poll(
      async () => {
        const res = await request.get("/api/portfolio/history?range=1h");
        if (!res.ok()) return 0;
        const body = await res.json();
        return Array.isArray(body.points) ? body.points.length : 0;
      },
      { timeout: 60_000, intervals: [1_000, 2_000, 5_000] },
    )
    .toBeGreaterThan(0);
});
