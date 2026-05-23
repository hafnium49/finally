import { expect, test } from "@playwright/test";

/**
 * Scenario 2: Watchlist CRUD.
 *
 *   - Add PYPL via the input control; assert row appears.
 *   - Remove a default ticker (NFLX); assert it disappears and is NOT
 *     restored after reload.
 *
 * The watchlist add control is the form inside the Watchlist component:
 *   <input placeholder="Add ticker" />  +  <button>Add</button>
 *
 * The remove control is a per-row "✕" button labelled
 *   "Remove <TICKER> from watchlist".
 *
 * Suite-ordering note (BUGS.md B004, option d):
 *   Spec files are numbered 01..08 and run serially with `workers: 1` and
 *   `fullyParallel: false` so the order is deterministic. This spec mutates
 *   the watchlist. Tests after this one must not assume NFLX is in the
 *   watchlist (it is removed here) and must tolerate PYPL being present
 *   (it is added here).
 */

test("add PYPL then remove NFLX (persisted across reload)", async ({ page }) => {
  await page.goto("/");

  // Pre-flight: make this spec idempotent. If a prior partial run left PYPL
  // in the watchlist, remove it via the API so the "Add PYPL" assertion can
  // observe a state transition. Similarly, if NFLX was removed by a prior
  // partial run, re-add it via the API so the "Remove NFLX" assertion is
  // meaningful. We use the API rather than the UI to keep the spec focused
  // on the UI control under test.
  await page.request.delete("/api/watchlist/PYPL").catch(() => {});
  await page.request.post("/api/watchlist", { data: { ticker: "NFLX" } })
    .catch(() => {});
  await page.reload();

  // Wait for the seed watchlist to render so we know the page is hot.
  await expect(page.getByTestId("watchlist-row-NFLX")).toBeVisible();

  // -- Add PYPL ----------------------------------------------------------
  const addInput = page.getByPlaceholder("Add ticker");
  await addInput.fill("PYPL");
  await page.getByRole("button", { name: "Add", exact: true }).click();

  await expect(page.getByTestId("watchlist-row-PYPL")).toBeVisible({
    timeout: 10_000,
  });

  // -- Remove NFLX -------------------------------------------------------
  // The remove button is hidden until hover, but Playwright's click forces
  // it. Scope the locator to the actual <button> inside the row — the row's
  // wrapper <div> also has role="button" with an accessible name that
  // INCLUDES the X button's aria-label, which would otherwise produce a
  // strict-mode violation (two elements match "Remove NFLX from watchlist").
  const nflxRow = page.getByTestId("watchlist-row-NFLX");
  await nflxRow.hover();
  await nflxRow
    .locator('button[aria-label="Remove NFLX from watchlist"]')
    .click();

  await expect(page.getByTestId("watchlist-row-NFLX")).toHaveCount(0);

  // -- Reload and assert persistence ------------------------------------
  await page.reload();
  await expect(page.getByTestId("watchlist-row-PYPL")).toBeVisible({
    timeout: 10_000,
  });
  await expect(page.getByTestId("watchlist-row-NFLX")).toHaveCount(0);
});
