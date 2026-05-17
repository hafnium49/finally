# Review of `planning/PLAN.md`

**Reviewer:** reviewer agent
**Date:** 2026-05-17
**Scope:** Fresh read of `planning/PLAN.md` against `CLAUDE.md`, `planning/MARKET_DATA_SUMMARY.md`, the existing `backend/app/market/*` implementation, and prior review passes (`plan-review-20260517-171658.md`, `plan-review-codex-20260517-173402.md`).

The goal is fresh signal, not a rehash of prior reviews. Where this report touches an already-known issue, it either (a) sharpens the diagnosis with new evidence or (b) explicitly notes the prior review is still correct and unresolved.

Severity tags: `[BLOCKER]` will derail or fork implementation, `[MAJOR]` material risk to correctness/UX, `[MINOR]` worth fixing, `[NIT]` cosmetic/style.

---

## 1. Cross-Section Contradictions and Gaps (correctness)

### [BLOCKER] §9 vs §10 vs §8: there is no push channel for portfolio / cash / watchlist mutations triggered by the LLM

The plan defines exactly one SSE stream: `GET /api/stream/prices` (§8). But the LLM auto-executes trades and edits the watchlist server-side (§9). After a chat round-trip:

- Cash balance changes
- A new position appears (or quantity changes)
- The watchlist may have new/removed tickers
- A new `portfolio_snapshots` row is written

The frontend has no mechanism described for learning about any of this except via the chat endpoint's response. That works for the chat panel itself, but the *header* (`portfolio total value`, `cash balance` — §10) and the *positions table* and the *watchlist panel* are separate components. The plan never says how they refresh.

Concrete options the plan must pick one of:
1. Return the same `actions` array, plus a *full* `portfolio_snapshot` and `watchlist_snapshot` from `/api/chat`, and have the frontend dispatch updates to all sibling panels.
2. Add a second SSE channel (`/api/stream/portfolio` or `/api/stream/state`) that fans out portfolio/watchlist deltas.
3. Have the frontend refetch `/api/portfolio` and `/api/watchlist` after every chat response.

Without a decision, two agents will pick different options and the UI will silently desync. Recommend (1) for v1 (simplest, no new infra) and (3) as belt-and-suspenders.

The same problem exists for *manual* trades: after `POST /api/portfolio/trade`, the response is undocumented (§8), and again there's no push for the header to update its live total. Right now the only thing that re-renders the header on cash change is... nothing.

### [MAJOR] §6 vs §7 vs §10: holding a position whose ticker is NOT in the watchlist breaks valuation, P&L charts, and tick history

The simulator/Massive sources track "watched tickers" (the union of all watchlists per §6). The plan implies (§7) that `price_ticks` is written for "every ticker currently in any watchlist." But trades and positions are independent: a user can buy NFLX, then remove NFLX from the watchlist.

Consequences:
- `MarketDataSource.remove_ticker("NFLX")` clears the cache entry (current code: `simulator.py:251-255`).
- Portfolio valuation can no longer look up NFLX's price → `total_value` and `unrealized_pnl` are wrong or null.
- The P&L chart and the positions table both go stale silently.
- The `price_ticks` table stops growing for NFLX → main chart history dies.

Fix: the set of tracked tickers is `union(watchlist, positions.ticker)`, not `watchlist` alone. Specify this in §6 ("tracked set"), §7 (tick-history writer source), §8 (watchlist DELETE behavior — refuse, warn, or silently keep tracking the ticker for position support), and §10 (positions table assumes a current price always exists).

This is a real bug-in-waiting because the natural agent implementation is "DELETE watchlist → source.remove_ticker → done."

### [MAJOR] §9 conversation summary: the schema is missing and the storage location is left to implementer choice

Both prior reviews flagged this; **it remains unresolved** and is the single largest spec hole. §9 reads: "stored separately (e.g., a `summary` row in a small `chat_state` table or as JSON in the `users_profile` row)." That's not a decision; it's a fork.

Decide now. Recommended:

```sql
CREATE TABLE chat_state (
  user_id TEXT PRIMARY KEY,
  summary TEXT NOT NULL DEFAULT '',
  summary_message_count INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL
);
```

Add a max-length bound on `summary` (e.g., 2000 chars) — the rolling rewrite is itself an LLM call and there's nothing in the spec preventing the summary from growing every iteration.

### [MAJOR] §6 SSE event shape vs implemented behavior

PLAN.md §6: "Each SSE event contains ticker, price, previous price, timestamp, and change direction" — phrased in the singular, implying one event per ticker change.

Implemented `backend/app/market/stream.py:81-83`: emits a `data:` line carrying *all tickers* in a single dict per tick:

```python
data = {ticker: update.to_dict() for ticker, update in prices.items()}
```

These are incompatible payloads. The frontend agent will reasonably read §6 and build a parser for single-ticker events; the existing backend sends a dict. Either:
- Update §6 to describe the actual dict-of-tickers payload, with a concrete JSON example, or
- Update the backend to emit one event per changed ticker (and rebuild the `_generate_events` loop to track per-ticker version, not just global `_version`).

The first option is cheaper. Either way, the plan must include the actual `data:` payload as JSON in §6 so the frontend can compile against it.

### [MAJOR] §8: half the endpoints have no documented response shape

Prior reviews noted this. Concretely missing schemas (no examples, no field lists):

| Endpoint | What's missing |
|---|---|
| `GET /api/portfolio` | Field list. Does it return `cash`, `cash_balance`, or `balance`? `positions[].avg_cost` vs `average_cost`? `unrealized_pnl` per-position, total, both? `market_value` field? Each ticker's current price? |
| `POST /api/portfolio/trade` | Request body validation rules; response shape (fill_price, cash_after, position_after — same as `actions` entries?); error codes (`insufficient_cash`, `insufficient_shares`, `unknown_ticker`, others?) |
| `GET /api/portfolio/history` | Sample/window granularity? Range parameter? Returns `[{recorded_at, total_value}, ...]` only, or include cash/holdings split? |
| `GET /api/prices/history/{ticker}` | Row shape (`{recorded_at, price}` array? Or `{timestamp, price}` to match SSE?), sample rate, max rows, how empty ticker handled |
| `POST /api/chat` request | Just `{message: string}`? Conversation id? |

Define them now or write three different frontend code paths.

### [MINOR] §8 watchlist shape vs §10 / SSE: redundant `price` field

`GET /api/watchlist` returns `{ticker, price, session_anchor_price, change_pct}` per ticker (§8). The SSE stream also pushes prices. Document: the watchlist endpoint price is the snapshot at request time, used to render before SSE has delivered the first tick. After the first SSE event, the watchlist `price` is stale and the frontend should prefer SSE values. Without this note, agents will either build a sync mechanism (overkill) or argue about which is canonical.

### [MINOR] §7 `chat_messages.actions` JSON shape is defined but never said to be versioned

The action schema (§9) will evolve. The DB row stores raw JSON. When v1 actions are loaded by a v2 chat panel, the panel must tolerate unknown fields. Add a one-liner: "Frontend must ignore unknown `actions[].kind`, `actions[].error`, and any extra fields, treating them as forward-compatible."

---

## 2. Architecture & Design

### [MAJOR] Concurrency: `GBMSimulator` mutates shared numpy state from `step()` while `add_ticker()`/`remove_ticker()` run from another coroutine

§7 only addresses the trade path's `asyncio.Lock`. The simulator has its own concurrency issue not covered anywhere:

- `_run_loop` (`simulator.py:260-270`) calls `self._sim.step()` every 0.5s, which reads `self._tickers`, `self._params`, and `self._cholesky` and writes `self._prices`.
- `SimulatorDataSource.add_ticker` calls `self._sim.add_ticker(ticker)` (line 244), which mutates `_tickers`, `_params`, `_prices`, *and rebuilds `_cholesky`*.

Both run on the same asyncio loop, so they don't preempt mid-statement, but `add_ticker` is `async` and the call to `self._sim.add_ticker(ticker)` is synchronous. So in practice this is safe *today* (no `await` inside `step()` or `add_ticker`). But two concerns:

1. If anyone adds an `await` to `step()` or to `_rebuild_cholesky()` (e.g., to make it cancellable for large `n`), this becomes a race that produces `numpy.linalg.LinAlgError` on Cholesky of a half-built matrix.
2. The Massive client's `add_ticker` path (not shown here but plan describes polling shared sets) needs the same guarantee.

Specify in §6 or §7: "Simulator state mutations (`add_ticker`, `remove_ticker`, `_rebuild_cholesky`) and `step()` must execute on the same event loop with no `await` between read and write of `_tickers` / `_params` / `_cholesky`. If multi-threaded execution is ever introduced, gate these with a `threading.Lock`."

### [MAJOR] `_run_loop` swallows all exceptions and never backs off

```python
async def _run_loop(self) -> None:
    while True:
        try:
            if self._sim:
                prices = self._sim.step()
                for ticker, price in prices.items():
                    self._cache.update(ticker=ticker, price=price)
        except Exception:
            logger.exception("Simulator step failed")
        await asyncio.sleep(self._interval)
```

If `step()` throws every iteration (e.g., a divide-by-zero from a bad seed, or numpy error), this loops at 2 Hz and floods logs forever. Plan should require: exponential backoff on repeated errors, a circuit-breaker that surfaces "data source unhealthy" via `/api/health`, or both.

Same issue will apply to the Massive poller if not yet added. Make this a §6 contract, not a per-implementation choice.

### [MAJOR] No mechanism to invalidate the "session anchor" if process restarts mid-day

§10 + §8: `session_anchor_price` is "the first price the backend observed for that ticker at process start." This means:

- Cold start at 9:30 AM, anchor = $190.
- Backend restarts at 10:30 AM (e.g., container redeploy, OOM kill, dev hot reload), anchor resets to whatever the price was then.

For the simulator, that means the displayed "session change" silently jumps to ~0% mid-session every time the backend cycles. For Massive (real data), this is more confusing because the user expects "change since open" semantics and gets "change since last redeploy" instead.

Either:
- Persist the anchor in a small `session_anchors` table keyed on `(ticker, anchor_date)` with daily rollover, or
- Add a UI tooltip: "Session change resets when the backend restarts."

For a course capstone, the tooltip is fine — but the plan should pick one explicitly.

### [MINOR] Per-user `asyncio.Lock` dict has unbounded growth (theoretical)

§7 says trades go through "a `dict[str, asyncio.Lock]`, lazily populated." With only `user_id="default"` today this is one entry. But the plan claims multi-user readiness. The dict has no eviction policy. Document: "When multi-user support is added, locks must be evicted on user idle to prevent unbounded memory growth." Cheap to write down now.

### [MINOR] `portfolio_snapshots` written both on a 30s timer AND immediately after each trade

§7: "Recorded every 30 seconds by a background task, and immediately after each trade execution."

- A burst of 5 trades in 2 seconds writes 5 rows + the next periodic row → 6 rows in 32 seconds. Fine.
- But the 30s timer and the trade path can race to write at the same `recorded_at`. Schema uses `id` (UUID) as PK, so no collision. Just confirm: no UNIQUE on `(user_id, recorded_at)`. Currently true — leave it.
- For chart smoothness, recommend that the timer skip its tick if a snapshot was written in the last N seconds (e.g., 5s). Not strictly required; flag as polish.

### [MAJOR] Security: §11 auth shim is described in prose but breaks SSE entirely

§11 recommends a "shared-secret header or basic-auth shim on `/api/*`" before exposing publicly. Browser `EventSource` does **not** support custom headers. So:
- Basic auth header → works (browser sends it automatically once cached) but UX is the browser native popup.
- Shared-secret header (e.g., `X-API-Key`) → **does not work for SSE**. EventSource has no way to attach it.

If anyone follows §11 literally and adds an `X-API-Key` middleware, the price stream dies on auth. Document the constraint or recommend basic auth specifically. (Or: pass the secret as a query string, which is technically possible but logs it in access logs.)

---

## 3. LLM Integration Pitfalls

### [MAJOR] §9: no documented behavior when LLM returns malformed structured output

Cerebras + gpt-oss-120b + structured outputs is mostly reliable but not 100%. The plan says "graceful handling of malformed responses" in §12 tests, but §9 itself never says *what* graceful means:

- Return a 502 to the frontend? Show "Sorry, try again" in the chat?
- Retry once? Twice?
- Log the bad response for debugging?
- Persist the user's message anyway?

Pick a policy. Recommend: return a synthetic assistant message `{"message": "I had trouble generating a response. Please try again.", "actions": []}`, log the raw response at WARN, and *do* persist the user message so the conversation history stays linear.

### [MAJOR] §9: the summarization LLM call has no spec

"A lightweight LLM call (or simple truncation if no summary exists yet)" — undefined:

- Same model (`openrouter/openai/gpt-oss-120b`)? A cheaper model? OpenRouter free tier?
- Same `LLM_MOCK=true` behavior? Or do tests bypass summarization?
- What's the prompt? Max output tokens?
- Latency budget? If summarization runs synchronously inside the chat handler when the 11th turn arrives, it adds 1-3s to that specific request.

Specify: "Summarization uses the same model and same `LLM_MOCK` flag; runs inline in the chat handler before the main LLM call; budget 500 output tokens." Also specify: when `LLM_MOCK=true`, the mock summarizer returns a stub like "Previous conversation about portfolio analysis." so summary regen is testable.

### [MAJOR] §9 / §5: `OPENROUTER_API_KEY` marked required but first-launch UX promises chat works out of the box

§5: "Required: OpenRouter API key." §2 First Launch: "An AI chat panel ready to assist." If the user runs `start_mac.sh` without setting the key, what happens? Plan never says. Options:

1. Backend refuses to start. User sees a Docker log error. Bad first impression.
2. Backend starts, chat endpoint returns 503 with a friendly message. Header shows a warning.
3. Backend starts with `LLM_MOCK=true` implicitly when no key is present. Chat works in mock mode.

Pick (2) or (3). Document. Currently a student running the demo with `.env.example` missing → unclear failure.

### [MINOR] §9 `actions[].cash_after` adds coupling without proof of value

The chat panel re-renders history including `cash_after` from past trades. That value goes stale immediately (next trade changes it). On reload, showing "balance after this trade was $8,076.60" alongside "current balance: $4,231" is reasonable but mildly confusing. Either keep it (and document it as historical) or drop it from the persisted shape (compute on the fly from `trades` table). Lean: keep it as historical, label clearly in UI.

### [NIT] §9 system prompt guidance never mentions guardrails

"Be concise and data-driven" — fine. Nothing about: "Don't recommend leveraging beyond cash balance." "Don't recommend the user buy crypto or futures (we don't support them)." "Don't claim to know news beyond your knowledge cutoff." For a fake-money demo it's not critical, but worth a line.

---

## 4. Drift Between PLAN.md and Implemented Code

(Cross-references to `backend/app/market/`.)

### [MAJOR] `PriceCache.version` increments on every `update()` call, not on actual price change

`cache.py:41` — `self._version += 1` runs unconditionally inside `update()`. So if the simulator computes the same rounded price two ticks in a row (rare but possible at low volatility), the version still bumps and SSE pushes. This violates the §6 contract ("only emit when a ticker's cached price has actually changed").

Two options:
- **Make `update()` idempotent**: compare new `round(price, 2)` to existing, only bump version on change.
- **Move the diff check into the SSE generator**: compare a per-ticker version map instead of the global counter.

Prior review flagged this. Still unaddressed in the plan. Add a sentence to §6: "`PriceCache.update()` must compare the new rounded price to the existing entry and only bump the version counter when the value changes. First-time entries always count as a change."

### [MAJOR] SSE keepalive is in the plan, not in the code

`stream.py:69-85` has no `: keepalive\n\n` emission. §6 promises one every ~15s. Either implement it or remove the promise. (Prior reviews flagged.)

Concrete patch shape:

```python
last_keepalive = time.monotonic()
while True:
    if await request.is_disconnected(): break
    now = time.monotonic()
    if now - last_keepalive >= 15:
        yield ": keepalive\n\n"
        last_keepalive = now
    # ... existing version-check + emit ...
    await asyncio.sleep(interval)
```

### [MAJOR] §4 directory tree lists files that don't exist in the repo

`Dockerfile`, `docker-compose.yml`, `.env.example`, `frontend/`, `scripts/`, `test/`, `db/` — none present at HEAD (only `.env` exists). Prior reviews flagged. The fix is one sentence at the top of §4: "*Target* structure. Items marked ✓ are implemented; the rest are deliverables for the indicated agent." Currently the section reads as a factual repo map.

### [MINOR] `backend/CLAUDE.md` says "version property … increments on every update" — true but contradicts §6's intended semantics

Once `update()` is made idempotent (per above), update `backend/CLAUDE.md` line 28 to: "increments only when a ticker's rounded price changes."

### [NIT] `models.py` `to_dict()` includes `change_percent` but §10 / §8 don't reference it

Harmless extra field. Either reference it in §10 ("the SSE event includes per-tick `change_percent` if the frontend wants flash intensity") or remove from `to_dict`.

---

## 5. Testability & E2E Hazards

### [MAJOR] Simulator is non-deterministic; E2E tests that depend on prices will be flaky

§12 lists "prices are streaming" and "AI chat (mocked): send a message, receive a response, trade execution appears inline." The chat-mock + trade test must execute against a *known* price (otherwise the assertion "cash decreased by $X" is unverifiable).

Add a `SIM_SEED` env var that seeds Python's `random` and numpy's RNG when set. E2E test docker-compose injects `SIM_SEED=42`. Spec the contract:

> "When `SIM_SEED` is set to an integer, the simulator's RNGs (`random` and `numpy.random`) are seeded once at process start. Tests rely on this for deterministic price sequences."

Without this, every E2E run is at the mercy of GBM variance.

### [MAJOR] No test for SSE "version bumps only on change" because the current code doesn't do it

§12 says: "version counter advances only on changed prices." Today this test would *fail* against the implementation (it advances on every `update()`). When an agent writes the test, they'll either fix the cache (good) or weaken the test to match current behavior (bad — silent contract drift). Add to §12: "If this test fails, fix the cache, not the test."

### [MAJOR] No tests planned for the §1 trade race condition under realistic conditions

§12 mentions "race-condition test with two simultaneous `await`s." This needs more specificity to be useful:

- Spawn N=50 concurrent trade tasks, each buying 1 share.
- Assert: final cash = initial cash − 50 × fill_price (within rounding), position quantity = 50 (not less, not more).
- Without the lock, this test produces inconsistent results some fraction of runs.

Without N≥10, the asyncio scheduling on a fast machine usually serializes naturally and you get a false-pass.

### [MINOR] `pytest-asyncio` `asyncio_mode = "auto"` + `loop_scope = "function"` is fine for unit tests; LLM mock tests need their own fixture

The chat handler holds onto an `AsyncOpenAI`-style client; reusing it across tests should be considered. Not a contract issue, but flag for the chat-implementation agent.

### [MINOR] No test for "watchlist DELETE while holding a position" (see §2 finding above)

When that ambiguity is resolved, the resolution needs a test: "DELETE NFLX while holding NFLX position → assert price still tracked / portfolio still values correctly."

---

## 6. Scope & Priorities for a Course Capstone

### [MAJOR] Conversation summarization is over-engineered for v1

The summary mechanism (§9) requires an extra LLM call per ~10 turns, a separate storage row, careful prompt design, and a mock for testing. For a capstone demo where most sessions are < 10 turns, this adds risk and surface area for little benefit.

Simpler alternative: truncate to last 20 messages, full stop. Document the limitation: "Beyond ~20 turns the assistant loses earlier context. For a course capstone this is acceptable." Defer rolling summarization to a §13 / future-work section.

If kept, it must get the spec sharpening from §3 above.

### [MAJOR] Massive (Polygon.io) integration adds operational risk for marginal demo value

The simulator already produces visually convincing live data. Massive integration adds:
- A second code path that must be tested with real keys
- Rate-limit handling
- Network failure modes
- Different "unknown ticker" semantics that the plan doesn't fully resolve

For a course capstone, recommend the Massive client become a clearly-marked stretch goal in §6, with the demo always using the simulator. The strategy-pattern architecture is preserved (good engineering), but the second implementation can be a stub that raises `NotImplementedError` until someone needs it. Halves the test surface, eliminates Polygon dependency drift.

### [MINOR] `portfolio_snapshots` "downsample to 5-minute aggregates beyond 24h" is a non-goal for v1

§7 mentions this as a "if needed" footnote. Fine. Just don't implement it. The 1M rows/year math is per-user; with one user, it's never a problem.

### [MINOR] Multi-user "future-proofing" via `user_id` everywhere

The prior review's insight block already noted this. Concretely cheap to keep, but: nothing in the API surface accepts a user identifier. The hardcoded `"default"` in the API layer is a single point that, on the day real multi-user lands, will need to change everywhere. Either drop the `user_id` columns (simplification) or add a single `get_user_id(request) -> str` helper now that hardcodes `"default"` — so the future change is one-file. Recommend the helper.

---

## 7. Frontend / UX Concerns Not Yet Surfaced

### [MAJOR] §10 promises "functional on tablet" but a Bloomberg-style 6-panel layout doesn't gracefully reflow

Saying "responsive but desktop-first … functional on tablet" sets an expectation that's expensive to meet. A treemap + line chart + positions table + chat sidebar all on a tablet portrait viewport is not "functional" without a tabbed/accordion layout. Either:
- Drop tablet support: "Desktop-only, ≥1280px wide."
- Specify the tablet layout: which panels collapse, what becomes a tab, etc.

Otherwise the Frontend Engineer agent will deliver something that "kinda works" at 1024×768 and a reviewer will mark it incomplete.

### [MAJOR] §10 "Trade bar" duplicates the chat trade path with different validation surfaces

The Buy/Sell buttons on the trade bar hit `POST /api/portfolio/trade`. The chat panel triggers trades via `POST /api/chat`. Both go through the same trade-execution module (per §9). But:

- The trade bar has no `actions` array — what does the response look like on `insufficient_cash`? §8 says nothing.
- The trade bar must surface validation errors inline (toast? in the trade bar itself?). §10 doesn't say.
- Should the trade bar be disabled while a chat request is in flight (since the chat might be about to trade)? Probably not, but worth deciding.

Define the manual trade response shape (single trade, mirrors a single `actions[]` entry) and the UI surface for errors.

### [MINOR] §10 "Click a ticker to see a larger detailed chart" — what if the user clicks a ticker they don't own and isn't on the watchlist?

The main chart fetches from `price_ticks`. Per §7, that table only has rows for currently-watchlisted tickers. So clicking a search result (if a search bar exists — not in §10 but trivially demanded) → empty chart. Spec what happens: error message? Auto-add to watchlist? Currently undefined because there's no search UI defined.

### [MINOR] §10 chat panel: no `id` field on assistant messages

Per §7, `chat_messages.id` is a UUID. Per §9, the response shape (`{message, actions}`) omits it. The frontend can't:
- Distinguish a re-rendered history message from a fresh one
- Implement an "edit" or "retry" affordance later

Add `id` (and `created_at`) to the chat response shape, even though no UI uses them in v1.

---

## 8. Documentation Hygiene

### [MAJOR] §13 still reads as an active worklist (prior reviews flagged; unresolved)

Both prior reviews called this out. Not fixed. The "★ Insight" block at the end of §13 still asserts that the chat/trade boundary is underspecified and that SSE-on-tick is the documented model, which contradicts the now-resolved sections above it. A future agent who scrolls to the bottom of PLAN.md sees: "Hey, the chat boundary is ambiguous, fix it." Then re-opens decisions already made.

Recommended structural fix:
- Move §13.1 and §13.2 resolved items into `planning/archive/RESOLVED_NOTES.md`.
- Keep §13 as a short "Open decisions" section with only items that genuinely lack a chosen answer (the conversation-summary storage location, the LLM-key-missing UX, the watchlist-vs-positions tracking question — see §1 of this review).
- Delete the "★ Insight" block; it's now misleading.

### [MAJOR] §9 references `cerebras-inference` skill (prior reviews flagged; unresolved)

Plan tells implementing agents to "use cerebras-inference skill." That works for a Claude Code agent with the right skill installed; it doesn't work for a Codex agent or a human. Both prior reviews flagged. Still unfixed.

Replace with portable instructions:

```
LLM calls use LiteLLM → OpenRouter with:
  model = "openrouter/openai/gpt-oss-120b"
  extra_body = {"provider": {"only": ["cerebras"]}}
  response_format = {"type": "json_schema", "json_schema": {...}}
  timeout = 30
  max_retries = 1
The cerebras-inference skill (Claude Code only) provides a worked example.
```

### [MINOR] §5 mentions `.env.example` but it's not in the repo

The "committed `.env.example`" claim in the §4 directory tree is aspirational. When the deployment agent picks this up, they should ship `.env.example` with the three documented keys and dummy values. Add this to the §11 deliverables list.

### [NIT] §6 "Updates at ~500ms intervals" — be precise about which "updates"

Today: simulator *computes* prices at 500ms intervals; the cache receives all 10 prices in a batch; SSE *would* push every 500ms but per §6 should push-on-change. Three different "intervals." Disambiguate.

### [NIT] §7 "All tables include a `user_id` column" — `price_ticks` does not (correctly; documented later)

Reword: "All tables that hold user-scoped data include a `user_id` column. The exception is `price_ticks`, which is global (see table notes)."

---

## 9. Summary of Top Issues by Severity

**Blockers (must fix before frontend/chat work starts):**
1. No push channel for portfolio/cash/watchlist updates from LLM trades — §1.1 of this review.
2. SSE payload shape in PLAN.md ≠ what the backend emits — §1.4.

**Majors (will cause rework or bugs):**
3. Conversation summary storage undefined (still unresolved from prior reviews) — §1.3.
4. Tracking set for prices must include positions, not just watchlist — §1.2.
5. API response shapes missing for half the endpoints — §1.5.
6. Simulator `_run_loop` exception handling has no backoff — §2.2.
7. `PriceCache.version` bumps on every update (drift from §6) — §4.1.
8. SSE keepalive not implemented (drift from §6) — §4.2.
9. Auth-shim recommendation in §11 breaks SSE — §2.4.
10. LLM-key-missing UX undefined — §3.3.
11. Summarization LLM call underspecified — §3.2.
12. Simulator non-determinism breaks E2E — `SIM_SEED` env var needed — §5.1.
13. Trade-bar response shape undefined — §7.2.
14. §13 still reads as active worklist with contradictory "Insight" — §8.1.
15. `cerebras-inference` skill is non-portable — §8.2.
16. Tablet "functional" promise expensive to keep — §7.1.
17. Conversation summarization probably over-scoped for v1 — §6.1.

**Minors:** see §2.3 (asyncio.Lock dict growth), §2.5 (snapshot races), §3.4 (`cash_after` historical staleness), §4.4 (`backend/CLAUDE.md` drift), §5.4 (test for delete-while-holding), §6.3 (multi-user helper), §7.3 (clicking off-watchlist ticker), §7.4 (chat message `id` field), §8.3 (`.env.example` missing).

**Nits:** see §3.5, §4.5, §8.4, §8.5.

---

## 10. Recommended Next-Step Sequence

If the goal is to unblock parallel agent work without rework:

1. **Spec sweep (1 PR):** Resolve §1.1, §1.2, §1.3, §1.4, §1.5, §3.3, §6.1, §8.1, §8.2 in PLAN.md. These are all documentation-only and unblock the chat and frontend agents.
2. **Backend cache fix (1 PR):** Make `PriceCache.update()` idempotent and add SSE keepalive. Update `backend/CLAUDE.md`. Add the missing test from §5.2.
3. **Database & portfolio module (1 PR):** Schema, lifespan init, trade-execution path with `asyncio.Lock`, snapshot writer. Includes the per-user-lock race test from §5.3.
4. **Chat module (1 PR):** Now possible because the contracts are unambiguous.
5. **Frontend bootstrap (parallel to 3+4):** Static export, layout shell, watchlist + SSE wiring.

Skipping step 1 saves a few hours of documentation work and costs several days of merge-conflict and contract-mismatch debugging downstream.

---

*End of review.*
