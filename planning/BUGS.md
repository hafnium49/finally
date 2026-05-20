# BUGS.md — FinAlly E2E defect log

Structured bug report file owned by the Integration Tester. Each iteration
appends entries; previous entries are preserved so the orchestrator can see the
fix history. Format is YAML embedded in markdown blocks.

Owner enum: `frontend-engineer` | `backend-api-engineer` | `database-engineer` |
`llm-engineer` | `devops-engineer` | `orchestrator`.

Severity enum: `blocker` (suite cannot proceed) | `major` (scenario fails but
others pass) | `minor` (flake or low-impact deviation).

Artifact paths in the `actual` field are absolute under
`/home/hafnium/finally/test/playwright/test-results/`.

---

## Iteration 0 — Phase 3 initial Playwright run

Stack info captured at filing time:
- Docker image `finally:test` built successfully from `/home/hafnium/finally/Dockerfile` (all layers cached on rebuild).
- Stack started via `docker compose -f /home/hafnium/finally/test/docker-compose.test.yml up -d`.
- `/api/health` returns `{"status":"ok","db":"ok","market":"simulator"}` within 2s.
- Playwright 1.49 with chromium-1223 from `~/.cache/ms-playwright/`.
- Suite run with a freshly-recreated `finally_test_db` volume (no carry-over
  state from prior runs).
- Result: **0 passed, 10 failed** out of 10 tests. All ten are blocked by the
  single root cause in B001.

```yaml
- id: B001
  owner: frontend-engineer
  severity: blocker
  scenario: "Every E2E test that touches the watchlist, chat, or trade-bar grid"
  repro: |
    1. Build image: `docker build -t finally:test /home/hafnium/finally`
    2. Start stack: `docker compose -f /home/hafnium/finally/test/docker-compose.test.yml up -d`
    3. Open http://localhost:8000 at a viewport ≥ Tailwind's `xl` breakpoint (1280px+).
    4. Inspect DOM for any of: `[data-testid="watchlist-row-AAPL"]`, `[aria-label="Chat input"]`.
  expected: |
    Each test-id / accessible label appears exactly ONCE in the DOM so that
    Playwright locators (which run in strict mode by default) resolve to a
    single element. PLAN.md §10 specifies a single watchlist and a single chat
    panel.
  actual: |
    `/home/hafnium/finally/frontend/app/page.tsx` (lines 42-87) mounts every
    primary panel TWICE — once in the desktop layout (`hidden xl:flex` /
    `hidden xl:hidden`) and once in a mobile fallback (`block xl:hidden`).
    Both mounts render the SAME components (Watchlist, ChatPanel) with the
    SAME `data-testid` / `aria-label` attributes. Tailwind hides one branch via
    CSS but it still exists in the DOM.

    Concrete consequences (Playwright strict-mode-violation in EVERY spec):
      - `getByTestId("watchlist-row-AAPL")` resolves to 2 elements → test 01 fails.
      - `getByTestId("watchlist-row-NFLX")` resolves to 2 elements → test 02 fails.
      - `getByTestId("watchlist-row-AAPL")` → test 03, 04 fail.
      - `getByTestId("watchlist-row-NVDA")` → test 05 fails.
      - `getByTestId("watchlist-row-AAPL")` → test 06 fails.
      - `getByLabel("Chat input")` resolves to 2 elements → tests 07a/07b/07c all fail.
      - The same root cause cascades into test 08's pre-flight (`getByTestId("connection-status")`)
        because the connection dot lives inside `<Header>` once but the suite's
        prerequisites depend on `<Watchlist>` rendering, which is doubled.

    The duplicated React subtrees also waste two parallel fetch loops per
    panel (one `usePortfolio` per ChatPanel mount via `onActivity`, one
    `useWatchlist` per Watchlist mount), which is a separate concern but a
    downstream symptom of the same defect.

    Screenshots and traces for every failing test:
      /home/hafnium/finally/test/playwright/test-results/01-fresh-start-loads-with--140ee-watchlist-rows-and-10k-cash-chromium/test-failed-1.png
      /home/hafnium/finally/test/playwright/test-results/01-fresh-start-loads-with--140ee-watchlist-rows-and-10k-cash-chromium/trace.zip
      /home/hafnium/finally/test/playwright/test-results/02-watchlist-crud-add-PYPL-e3981-LX-persisted-across-reload--chromium/test-failed-1.png
      /home/hafnium/finally/test/playwright/test-results/02-watchlist-crud-add-PYPL-e3981-LX-persisted-across-reload--chromium/trace.zip
      /home/hafnium/finally/test/playwright/test-results/03-buy-shares-buy-5-AAPL-v-d4251-cash-and-creates-a-position-chromium/test-failed-1.png
      /home/hafnium/finally/test/playwright/test-results/03-buy-shares-buy-5-AAPL-v-d4251-cash-and-creates-a-position-chromium/trace.zip
      /home/hafnium/finally/test/playwright/test-results/04-sell-shares-sell-2-of-5-05d97-ash-and-drops-quantity-to-3-chromium/test-failed-1.png
      /home/hafnium/finally/test/playwright/test-results/04-sell-shares-sell-2-of-5-05d97-ash-and-drops-quantity-to-3-chromium/trace.zip
      /home/hafnium/finally/test/playwright/test-results/05-insufficient-cash-buyin-b205d--cash-inline-cash-unchanged-chromium/test-failed-1.png
      /home/hafnium/finally/test/playwright/test-results/05-insufficient-cash-buyin-b205d--cash-inline-cash-unchanged-chromium/trace.zip
      /home/hafnium/finally/test/playwright/test-results/06-portfolio-viz-heatmap-r-baa1d-nd-P-L-chart-has-a-snapshot-chromium/test-failed-1.png
      /home/hafnium/finally/test/playwright/test-results/06-portfolio-viz-heatmap-r-baa1d-nd-P-L-chart-has-a-snapshot-chromium/trace.zip
      /home/hafnium/finally/test/playwright/test-results/07-ai-chat-mock-portfolio--3d23e-nse-renders-without-actions-chromium/test-failed-1.png
      /home/hafnium/finally/test/playwright/test-results/07-ai-chat-mock-portfolio--3d23e-nse-renders-without-actions-chromium/trace.zip
      /home/hafnium/finally/test/playwright/test-results/07-ai-chat-mock--Buy-2-MSF-bdad4--action-and-a-positions-row-chromium/test-failed-1.png
      /home/hafnium/finally/test/playwright/test-results/07-ai-chat-mock--Buy-2-MSF-bdad4--action-and-a-positions-row-chromium/trace.zip
      /home/hafnium/finally/test/playwright/test-results/07-ai-chat-mock--buy-9999--a2815-ufficient-cash-error-action-chromium/test-failed-1.png
      /home/hafnium/finally/test/playwright/test-results/07-ai-chat-mock--buy-9999--a2815-ufficient-cash-error-action-chromium/trace.zip
      /home/hafnium/finally/test/playwright/test-results/08-sse-resilience-SSE-drop-446dd-onnection-dot-then-recovers-chromium/test-failed-1.png
      /home/hafnium/finally/test/playwright/test-results/08-sse-resilience-SSE-drop-446dd-onnection-dot-then-recovers-chromium/trace.zip

    Sample strict-mode violation (from test 01):
      `strict mode violation: getByTestId('watchlist-row-AAPL') resolved to 2 elements:
         1) <div ... data-testid="watchlist-row-AAPL" ...>
         2) <div ... data-testid="watchlist-row-AAPL" ...> aka getByTestId('watchlist-row-AAPL').nth(1)`
  fix_hint: |
    Render the watchlist and chat panels conditionally (e.g., via a
    `useIsXl()` hook + JS-gated single mount), or move the responsive panes
    into a single component that flips its layout via Tailwind classes rather
    than duplicating the entire subtree. Whichever approach is chosen, the
    invariant must be: each `data-testid` and each `aria-label` appears at
    most once in the DOM.
  iteration: 0
  fixed_in_commit: null
```

```yaml
- id: B002
  owner: integration-tester
  severity: minor
  scenario: "SSE resilience — connection dot recovery after a server-side 5xx"
  repro: |
    1. With the stack up, run:
       `cd /home/hafnium/finally/test/playwright && npx playwright test 08-sse-resilience --reporter=list`
    2. The test installs `page.route("**/api/stream/prices", route.fulfill({status: 503}), {times: 1})`
       so the FIRST SSE request returns 503, then routing falls through to the
       real endpoint.
  expected: |
    Dot transitions away from "open" (asserted) and then back to "open"
    (asserted) within ~20s after the first SSE attempt fails.
  actual: |
    Dot stays "closed" indefinitely. The EventSource specification
    (https://html.spec.whatwg.org/multipage/server-sent-events.html#fail-the-connection)
    requires a permanent failure when the server returns an HTTP status other
    than 200 with the right content-type. `frontend/app/lib/sse.ts`
    correctly detects `readyState === 2 (CLOSED)` and sets the connection
    state to "closed" — the browser will NOT auto-reconnect.

    Consequence: the test's premise (route.fulfill({status:503}, {times:1})
    causes a recoverable disconnect) is wrong. The fulfill response makes
    EventSource permanently CLOSED. To exercise the reconnect path, the test
    must simulate a transport-level failure (e.g. `route.abort("failed")`)
    rather than a 5xx HTTP response.

    Artifacts:
      /home/hafnium/finally/test/playwright/test-results/08-sse-resilience-SSE-drop-446dd-onnection-dot-then-recovers-chromium/test-failed-1.png
      /home/hafnium/finally/test/playwright/test-results/08-sse-resilience-SSE-drop-446dd-onnection-dot-then-recovers-chromium/trace.zip

    Marking minor and self-owned because the application behaviour matches
    the EventSource spec; the test design needs to use `route.abort()`
    (network-level failure) instead of `route.fulfill({status:503})` so the
    browser's native retry actually fires. Will be revised once B001 is
    resolved and the full suite can re-run cleanly.
  iteration: 0
  fixed_in_commit: null
```

```yaml
- id: B003
  owner: integration-tester
  severity: minor
  scenario: "Test-suite DB isolation between consecutive `playwright test` invocations"
  repro: |
    1. `docker compose -f /home/hafnium/finally/test/docker-compose.test.yml up -d` (without `down -v` first)
    2. Run the suite, then run it again.
    3. Tests 03/04 use the trade bar and mutate `cash_balance`; tests 02 mutates
       the watchlist. Their assertions ("starting cash is $10,000.00",
       "ten default tickers visible") fail if leftover state survives.
  expected: |
    Each invocation of the Playwright suite begins from the same seeded baseline:
    `cash_balance = 10000.00`, default 10-ticker watchlist, no positions.
  actual: |
    The named docker volume `finally_test_db` persists across `up -d` /
    `down` cycles. Re-running the suite without `docker compose down -v`
    in between produces stale cash balances (e.g. "$9,431.06" observed at
    the start of test 03 in run 2 because run 1 left a position behind).

    Mitigation used during this iteration: `docker compose ... down -v`
    before the second clean-DB run.

    This bug is the Integration Tester's responsibility (the docker-compose
    file uses a named volume specifically to allow this kind of isolation;
    the harness just needs to wire `down -v` into the run script). Not a
    blocker for iteration-0 reporting because we re-ran cleanly, but it
    will be revisited in iteration-1 when a `make test` / shell-script
    wrapper around the compose + Playwright run is added.
  iteration: 0
  fixed_in_commit: null
```

```yaml
- id: B004
  owner: integration-tester
  severity: minor
  scenario: "Inter-test isolation within a single Playwright run"
  repro: |
    1. With a freshly-seeded DB, run the full suite once:
       `cd /home/hafnium/finally/test/playwright && npx playwright test`
    2. Test 03 buys 5 AAPL. Test 04 then expects to start from the seeded
       $10,000 cash baseline (it re-buys 5 AAPL, then sells 2).
  expected: |
    Each test starts from a known seeded state regardless of which prior
    tests have run.
  actual: |
    Once B001 unblocks the suite, the next layer of failures will surface:
    tests 03, 04, 05, 06 mutate the portfolio without restoring it, and
    tests 02 mutates the watchlist. The current spec files assert against
    a fixed baseline that drifts as each test runs. This is foreseeable
    but cannot be measured until B001 is fixed.

    Planned mitigation (deferred to iteration 1 of the test suite, NOT a
    fix for application code):
      - Add a `test.beforeEach` that POSTs to a small reset endpoint, OR
      - Restart the container between tests, OR
      - Rewrite individual assertions to be deltas instead of absolute
        values (e.g., "cash decreased by ~price*qty" instead of
        "cash != $10,000.00").

    No backend reset endpoint exists today and adding one would be backend
    work (out of scope for this agent). The container-restart approach is
    slow but bulletproof; the delta-assertion approach keeps the suite
    fast but more verbose. Decision pending orchestrator feedback.

    Severity is minor because tests can be made deterministic by the
    Integration Tester without any application change.
  iteration: 0
  fixed_in_commit: null
```

```yaml
- id: B005
  owner: orchestrator
  severity: minor
  scenario: "Sandbox restrictions on `npm install` / `npx playwright install`"
  repro: |
    1. Run `cd /home/hafnium/finally/test/playwright && npm install` inside the
       Claude Code sandbox (default mode).
    2. Run `npx playwright install --with-deps chromium` inside the sandbox.
  expected: |
    Standard package install / browser install. Both should complete without
    requiring elevated privileges (the test machine already has docker access).
  actual: |
    `npm install` fails with `EROFS: read-only file system, open '/home/hafnium/.npm/_cacache/tmp/...'`
    because npm's global cache directory is not writable from inside the sandbox.

    `npx playwright install --with-deps chromium` invokes `sudo apt-get`, which
    fails with `sudo: a terminal is required to read the password`.

    Workaround used during this iteration: run both commands with
    `dangerouslyDisableSandbox: true`. The chromium binaries from a prior
    pre-installed cache (`~/.cache/ms-playwright/chromium-1223`) were
    already present, so the `--with-deps` step was skipped.

    Not a code defect — just a sandbox configuration note for the next
    Integration Tester run. The current sandbox allowlist does not include
    `/home/hafnium/.npm` for writes and disallows `sudo` operations.
  iteration: 0
  fixed_in_commit: null
```
