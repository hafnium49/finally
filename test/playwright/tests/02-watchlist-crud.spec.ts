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
 */

test("add PYPL then remove NFLX (persisted across reload)", async ({ page }) => {
  await page.goto("/");

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
  // it. We use the accessible name instead of relying on hover state.
  const nflxRow = page.getByTestId("watchlist-row-NFLX");
  await nflxRow.hover();
  await page
    .getByRole("button", { name: "Remove NFLX from watchlist" })
    .click();

  await expect(page.getByTestId("watchlist-row-NFLX")).toHaveCount(0);

  // -- Reload and assert persistence ------------------------------------
  await page.reload();
  await expect(page.getByTestId("watchlist-row-PYPL")).toBeVisible({
    timeout: 10_000,
  });
  await expect(page.getByTestId("watchlist-row-NFLX")).toHaveCount(0);
});
