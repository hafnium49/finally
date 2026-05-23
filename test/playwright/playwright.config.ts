import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright configuration for the FinAlly Phase 3 E2E suite.
 *
 * The app is expected to already be running at PLAYWRIGHT_BASE_URL (default
 * http://localhost:8000) — typically via `docker compose -f
 * test/docker-compose.test.yml up -d`. This config does NOT start a webServer
 * itself; the integration tester orchestrates that step explicitly so the
 * docker container's startup logs are visible.
 */
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:8000",
    actionTimeout: 10_000,
    navigationTimeout: 15_000,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"], viewport: { width: 1600, height: 1000 } },
    },
  ],
});
