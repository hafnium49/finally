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
  # ITERATION 1 STATUS: FIXED. `frontend/app/page.tsx` was rewritten to mount
  # <Watchlist> and <ChatPanel> exactly once each, using Tailwind `order-*`
  # classes to reorder the same DOM tree across breakpoints instead of
  # duplicating subtrees behind `hidden xl:flex` / `block xl:hidden`. Grep on
  # iteration 1: each component appears in `page.tsx` exactly once. The
  # strict-mode violations that blocked all 10 specs in iteration 0 are gone.
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
  iteration: 1
  fixed_in_commit: "5385833"
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
  iteration: 1
  fixed_in_commit: "5385833"
  # ITERATION 1 STATUS: FIXED. `test/playwright/tests/08-sse-resilience.spec.ts`
  # now uses `route.abort('failed')` (transport-level error) instead of
  # `route.fulfill({status:503})` (HTTP error that permanently closes
  # EventSource). The connection-status dot is now observed to leave "open",
  # then return to "open" once the route block lifts. Spec 08 passes in 4.2s
  # with the latest image.
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
  iteration: 1
  fixed_in_commit: "5385833"
  # ITERATION 1 STATUS: FIXED. Added `test/run-e2e.sh` which ALWAYS passes
  # `-v` on `docker compose down`, both as a pre-flight cleanup and via an
  # EXIT trap. The script is the canonical entry point for the suite. Inline
  # comments document the constraint so a future change can't silently drop
  # the `-v` flag. Verified: after a full run + teardown, `docker volume ls`
  # no longer shows `test_finally_test_db`.
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
  iteration: 1
  fixed_in_commit: "5385833"
  # ITERATION 1 STATUS: FIXED via option (d) per orchestrator instruction.
  # Spec files were already named `01-…` through `08-…`, and
  # playwright.config.ts already runs with `workers: 1` /
  # `fullyParallel: false`, so the order is deterministic. The remaining
  # work was making each spec idempotent against its predecessor's
  # leftover state. Done as follows:
  #
  #   01-fresh-start.spec.ts  — READ-ONLY; added an explicit "MUST be first"
  #                             comment so the position in the run order is
  #                             documented.
  #   02-watchlist-crud.spec.ts — pre-flight removes any leftover PYPL and
  #                               re-adds NFLX via the API so the "add" /
  #                               "remove" UI assertions always observe a
  #                               state transition. Also fixed a pre-existing
  #                               strict-mode violation on the remove button:
  #                               the row's wrapper div has role="button"
  #                               with an accessible name that subsumes the
  #                               X-button's aria-label. Scoped the locator
  #                               to `button[aria-label="…"]`.
  #   03-buy-shares.spec.ts   — switched to DELTA assertions: snapshot cash
  #                             and AAPL qty via the API before the trade,
  #                             then assert cash decreased and qty
  #                             increased by exactly 5. No more "$10,000.00"
  #                             string match.
  #   04-sell-shares.spec.ts  — similar delta refactor. Buys 5 AAPL on top
  #                             of whatever spec 03 left, then sells 2;
  #                             asserts a net +3 quantity delta and that
  #                             cash dropped (after buy) and rose (after
  #                             sell). Test name updated to "drops quantity
  #                             by 2" (was "to 3").
  #   05-insufficient-cash.spec.ts — reads cash via API before/after the
  #                                  failed buy and asserts equality;
  #                                  no longer hard-codes $10,000.
  #   06-portfolio-viz.spec.ts — was already idempotent (only requires a
  #                              position to exist, which prior specs
  #                              provide).
  #   07-ai-chat-mock.spec.ts — was already idempotent (no cross-spec
  #                              assertions; just relies on the watchlist
  #                              having MSFT and TSLA, which the default
  #                              seed always provides).
  #   08-sse-resilience.spec.ts — read-only.
  #
  # Where a later spec depends on a prior spec's mutation, the dependency
  # is now called out in a "Suite-ordering note" comment at the top of the
  # spec file.
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
  iteration: 1
  fixed_in_commit: null
  # ITERATION 1 STATUS: still informational only. No code change required;
  # iteration 1 used `dangerouslyDisableSandbox: true` for docker / npx /
  # curl-against-localhost commands as before. Leaving open for the
  # orchestrator to consider widening the default sandbox allowlist.
```

---

## Iteration 1 — Phase 3 re-run after B001 fix + test-suite hardening

Stack info captured at filing time:
- Docker image `finally:test` rebuilt successfully from commit `5385833`
  (`docker build -t finally:test /home/hafnium/finally`). The frontend
  layer rebuilt (Next.js static export) because `page.tsx` changed.
- Stack started via `docker compose -f /home/hafnium/finally/test/docker-compose.test.yml up -d`
  with a freshly-recreated `finally_test_db` volume (the prior volume was
  removed with `down -v` first; see B003 fix).
- `/api/health` returned `{"status":"ok","db":"ok","market":"simulator"}`
  within 1s of `up -d`.
- Playwright 1.49 with chromium-1223 from `~/.cache/ms-playwright/`.
- Suite run: `cd /home/hafnium/finally/test/playwright && npx playwright test --reporter=list`.

Per-spec results (10 tests in 8 spec files):

| Spec file                          | Tests | Pass | Fail |
|------------------------------------|------:|-----:|-----:|
| 01-fresh-start.spec.ts             |   1   |   1  |   0  |
| 02-watchlist-crud.spec.ts          |   1   |   1  |   0  |
| 03-buy-shares.spec.ts              |   1   |   1  |   0  |
| 04-sell-shares.spec.ts             |   1   |   1  |   0  |
| 05-insufficient-cash.spec.ts       |   1   |   1  |   0  |
| 06-portfolio-viz.spec.ts           |   1   |   1  |   0  |
| 07-ai-chat-mock.spec.ts            |   3   |   1  |   2  |
| 08-sse-resilience.spec.ts          |   1   |   1  |   0  |
| **Total**                          | **10**| **8**| **2**|

Total run time: ~45s.

The two failures are BOTH the same root cause — a backend defect in
`backend/app/chat/executor.py` where `execute_trade()` is called without
the required `price_cache` argument. Filed as B006.

```yaml
- id: B006
  owner: llm-engineer
  severity: major
  scenario: "Any chat message that triggers a trade via the LLM (mock or real)"
  repro: |
    1. With the stack up (LLM_MOCK=true), run:
       `curl -s -X POST http://localhost:8000/api/chat \
          -H "Content-Type: application/json" \
          -d '{"message":"Buy 2 MSFT"}'`
    2. Or via Playwright:
       `cd /home/hafnium/finally/test/playwright && npx playwright test 07-ai-chat-mock --reporter=list`
  expected: |
    Per LLM_CONTRACT.md §6.1 and the mock response table in §4.2, the
    chat handler should execute the LLM-emitted trade, return a
    structured `actions` array entry of kind="trade" with status="ok"
    (or status="error" for insufficient cash), and 200 OK.
  actual: |
    The /api/chat endpoint returns HTTP 500 with body
      {"error":"internal_error","error_message":"The chat pipeline failed unexpectedly."}

    Backend traceback (captured from `docker logs finally-test`):
      File "/app/app/chat/handler.py", line 262, in handle_message
        actions = await llm_executor.apply(llm_response, user_id=user_id)
      File "/app/app/chat/executor.py", line 232, in apply
        actions.append(_trade_error_action(trade, exc))
      File "/app/app/chat/executor.py", line 151, in _trade_error_action
        raise exc  # re-raise unknown exception types per §6.2 (4)
      File "/app/app/chat/executor.py", line 224, in apply
        execute(
            ticker=trade.ticker,
            side=trade.side,
            quantity=trade.quantity,
            user_id=user_id,
        )
    TypeError: execute_trade() missing 1 required positional argument: 'price_cache'

    Root cause (verified by reading `backend/app/portfolio/trade.py:128-167`):
    `app.portfolio.execute_trade()` has the signature
      `async def execute_trade(*, ticker, side, quantity, price_cache, user_id="default")`
    but `backend/app/chat/executor.py:_load_trade_callable()` returns the
    raw function and `apply()` calls it WITHOUT a `price_cache` argument.
    The portfolio trade path used by the UI's POST /api/portfolio/trade
    works fine because the REST route imports the cache from the FastAPI
    app state and passes it explicitly; the chat executor never grew that
    plumbing.

    Consequence: every Playwright test under 07-ai-chat-mock.spec.ts that
    asserts on a chat-driven trade fails. The "portfolio summary" sub-test
    (which has NO trade in the mocked response) passes — confirming the
    chat plumbing itself is fine, only the trade-execution call is broken.

    Artifacts:
      /home/hafnium/finally/test/playwright/test-results/07-ai-chat-mock--Buy-2-MSF-bdad4--action-and-a-positions-row-chromium/test-failed-1.png
      /home/hafnium/finally/test/playwright/test-results/07-ai-chat-mock--Buy-2-MSF-bdad4--action-and-a-positions-row-chromium/trace.zip
      /home/hafnium/finally/test/playwright/test-results/07-ai-chat-mock--buy-9999--a2815-ufficient-cash-error-action-chromium/test-failed-1.png
      /home/hafnium/finally/test/playwright/test-results/07-ai-chat-mock--buy-9999--a2815-ufficient-cash-error-action-chromium/trace.zip
  fix_hint: |
    Two paths to consider, both equally good:
      (a) Have the chat executor resolve the live `price_cache` from
          wherever the rest of the backend keeps it (app.state, a module
          singleton, dependency injection) and pass it explicitly into
          `execute_trade(...)`.
      (b) Add a thin convenience wrapper next to `execute_trade` (e.g.
          `app.portfolio.execute_trade_default()`) that internally pulls
          the global cache and forwards every other kwarg. The chat
          executor then calls that wrapper instead. This keeps the trade
          API unchanged for the REST route while giving the chat path a
          drop-in callable that matches its existing kwarg set.
    Either way, please also add a backend unit test in
    `backend/tests/chat/test_executor.py` that exercises
    `apply()` against a real (or in-memory) portfolio module so the
    integration boundary is covered going forward — the existing chat
    handler tests pass because they stub `trade_fn` and never hit the
    real wiring.
  iteration: 2
  fixed_in_commit: "496a6cb"
  # ITERATION 2 STATUS: FIXED. Resolution implemented across two commits:
  #   2ebdbc9 — `backend/app/api/chat.py` now resolves the live PriceCache via
  #             `get_price_cache(request)` and threads it through
  #             `handle_message(...)`; `backend/app/chat/handler.py` accepts a
  #             `price_cache` kwarg and forwards it to `executor.apply`;
  #             `backend/app/chat/executor.py` calls
  #             `execute_trade(..., price_cache=price_cache)` instead of dropping
  #             the kwarg.
  #   496a6cb — Compatibility shim: when `handle_message` is invoked without a
  #             `price_cache` (legacy callers / tests), it resolves the
  #             application-wide cache so the executor never sees `None`. Adds
  #             2 regression tests covering both the wired and legacy paths.
  # Verification: full Playwright suite (10 tests across 8 spec files) ran
  # green in 11.0s from a freshly-recreated `finally_test_db` volume on the
  # `finally:test` image built from HEAD = commit 496a6cb. The two specs
  # previously broken by B006 — `07-ai-chat-mock 'Buy 2 MSFT'` and
  # `07-ai-chat-mock 'buy 9999 TSLA'` — now pass.
```

---

## Iteration 2 — Phase 3 re-run after B006 fix (chat executor price_cache wiring)

Stack info captured at filing time:
- Docker image `finally:test` rebuilt successfully from commit `496a6cb`
  (`docker build -t finally:test /home/hafnium/finally`). The backend layer
  rebuilt because `backend/app/chat/*.py` and `backend/app/api/chat.py`
  changed; frontend layer cached.
- Stack started via `docker compose -f /home/hafnium/finally/test/docker-compose.test.yml up -d`
  with a freshly-recreated `finally_test_db` volume (pre-flight teardown via
  `test/run-e2e.sh` ran `down -v` before bringing the stack up).
- `/api/health` returned `{"status":"ok","db":"ok","market":"simulator"}`
  after 3 polls (~6s).
- Playwright 1.49 with chromium-1223 from `~/.cache/ms-playwright/`.
- Suite run: `bash /home/hafnium/finally/test/run-e2e.sh` (which wraps
  `npx playwright test --reporter=list`).

Per-spec results (10 tests in 8 spec files):

| Spec file                          | Tests | Pass | Fail |
|------------------------------------|------:|-----:|-----:|
| 01-fresh-start.spec.ts             |   1   |   1  |   0  |
| 02-watchlist-crud.spec.ts          |   1   |   1  |   0  |
| 03-buy-shares.spec.ts              |   1   |   1  |   0  |
| 04-sell-shares.spec.ts             |   1   |   1  |   0  |
| 05-insufficient-cash.spec.ts       |   1   |   1  |   0  |
| 06-portfolio-viz.spec.ts           |   1   |   1  |   0  |
| 07-ai-chat-mock.spec.ts            |   3   |   3  |   0  |
| 08-sse-resilience.spec.ts          |   1   |   1  |   0  |
| **Total**                          | **10**| **10**| **0**|

Total run time: 11.0s.

Result: **SUITE GREEN.** No new bugs filed this iteration. All previously
filed defects (B001, B002, B003, B004, B006) have `fixed_in_commit`
populated; B005 remains an informational note about sandbox configuration
(no application code involved).

Teardown verification: `docker compose ... down -v` ran via the EXIT trap;
`docker volume ls | grep finally_test_db` shows no leftover volume and the
`finally-test` container is gone.

