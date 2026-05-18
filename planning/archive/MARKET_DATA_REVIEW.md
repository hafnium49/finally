# Market Data Backend — Code Review

**Reviewer:** Claude (Opus 4.7, 1M context)
**Date:** 2026-05-17
**Scope:** `backend/app/market/` (8 modules) and `backend/tests/market/` (6 test modules)
**Reference docs:** `planning/PLAN.md` §6 / §8 / §12, `MARKET_INTERFACE.md`, `MARKET_SIMULATOR.md`, `MASSIVE_API.md`

---

## TL;DR

The shipped market-data subsystem is a clean, well-factored implementation of the strategy pattern that PLAN.md asks for. All 73 unit/integration tests pass, ruff is clean, overall coverage is **91%**, and the simulator's GBM math, correlation handling, and async lifecycle are all correct.

However, the review surfaced **2 real bugs that will bite in production**, **3 deviations from PLAN.md**, and several smaller nits worth fixing before the SSE consumer (frontend) and trade-execution path are wired in. The most consequential items:

| # | Severity | Issue |
|---|----------|-------|
| 1 | **High** | `stream.create_stream_router()` uses a **module-level `APIRouter` singleton** — calling it twice double-registers `/api/stream/prices` and the second call's `price_cache` is ignored (closures over the first). Confirmed by probe. |
| 2 | **High** | `PriceCache.update()` bumps `_version` on every call, not on actual change. With Massive on a 15s poll cycle, identical prices still cause SSE pushes. Contradicts PLAN.md §6 "push-on-change, not push-on-tick." Confirmed by probe. |
| 3 | **Medium** | SSE generator **never emits the periodic `: keepalive\n\n` comment** required by PLAN.md §6. `MARKET_INTERFACE.md` itself flags this as a known gap. |
| 4 | **Medium** | `MassiveDataSource.start()` does **not** uppercase/strip tickers, but `add_ticker` / `remove_ticker` do. Mixed-case input via `start()` becomes unremovable. Confirmed by probe. |
| 5 | **Medium** | `stream.py` has only **33% test coverage** — no tests exercise the SSE generator at all. The two high-severity bugs above slipped through because of this gap. |

---

## How the review was done

1. Read every source file under `backend/app/market/` and every test under `backend/tests/market/`.
2. Cross-referenced behavior against PLAN.md §6/§8/§12 and the three planning docs (`MARKET_INTERFACE.md`, `MARKET_SIMULATOR.md`, `MASSIVE_API.md`).
3. Ran the full suite: `uv run pytest --cov=app --cov-report=term-missing` → **73 passed, 91% coverage**.
4. Ran lint: `uv run ruff check app/ tests/` → **clean**. Formatter (`ruff format --check`) flags 3 test files (cosmetic line-wraps only).
5. Wrote small Python probes to confirm or refute suspected behaviors (router singleton, version-bump on no-op, Massive case-normalization).

---

## Test results

```
============================= 73 passed in 2.08s ==============================

Name                           Stmts   Miss  Cover   Missing
------------------------------------------------------------
app/market/__init__.py             6      0   100%
app/market/cache.py               39      0   100%
app/market/factory.py             15      0   100%
app/market/interface.py           13      0   100%
app/market/massive_client.py      67      4    94%   85-87, 125
app/market/models.py              26      0   100%
app/market/seed_prices.py          8      0   100%
app/market/simulator.py          139      3    98%   149, 268-269
app/market/stream.py              36     24    33%   26-48, 62-87
------------------------------------------------------------
TOTAL                            349     31    91%
```

- Coverage uncovered lines correspond exactly to: the SSE generator body (`stream.py:26-87`), the `_poll_loop` while-true (`massive_client.py:85-87`), and the `RESTClient` real wrapper (`massive_client.py:125`). All deliberate gaps except `stream.py`, which is a real coverage hole.
- `ruff check` clean. `ruff format --check` flags only line-wrap reflow in three test files (`test_models.py`, `test_simulator.py`, `test_simulator_source.py`) — cosmetic, not semantic.

---

## Strengths

**Architecture matches PLAN.md cleanly.**

- The `MarketDataSource` ABC has zero implementation imports — importing `interface.py` doesn't pull NumPy or `massive`. This is genuinely useful for testing and for downstream code that only needs the type.
- The strategy pattern is honored everywhere: callers of the cache don't know whether the simulator or Massive is writing.
- The factory's `.strip()` on `MASSIVE_API_KEY` is the right kind of paranoia — a stray space in `.env` would otherwise route users to a confusing `401` from Massive instead of the simulator.

**`PriceUpdate` is a textbook frozen dataclass.**

- `frozen=True, slots=True` for immutability and memory efficiency.
- Computed properties (`change`, `change_percent`, `direction`) derived from the two stored prices, so they can't go out of sync.
- `to_dict()` shape is consistent and stable for JSON serialization.
- 100% test coverage with assertions on every property.

**GBM simulator math is correct.**

- The classical `S(t+dt) = S(t) * exp((mu - 0.5*sigma^2)*dt + sigma*sqrt(dt)*Z)` formulation, with `dt` derived from a real "trading-year-in-seconds" constant. The `MARKET_SIMULATOR.md` parameter-justification math is verifiable from the code.
- Cholesky decomposition only rebuilt when tickers change; `step()` itself is a matrix multiply, not a re-decomposition.
- TSLA special-case is intentional and documented.
- `_cholesky is None` correctly handled for `n <= 1`.
- Random shocks logged at `DEBUG`, magnitudes ∈ [2%, 5%], sign ∈ {-1, +1}, probability ~0.001/tick — matches the design doc.

**`PriceCache` thread-safety reasoning is right.**

- `threading.Lock` is the correct primitive given that Massive's sync `RESTClient` runs in `asyncio.to_thread(...)`; an `asyncio.Lock` would not protect that path. (`MARKET_INTERFACE.md` explains the choice well.)
- All read/write methods acquire the lock; the lock is held only for dict ops (microseconds).

**Async lifecycle is solid.**

- `SimulatorDataSource.stop()` cancels the task and `await`s it under `try/except asyncio.CancelledError` — idempotent and exception-safe.
- `_run_loop` has a top-level `try/except Exception` around `step()` so a NumPy hiccup can't kill the simulator.
- `start()` seeds the cache *before* spawning the loop, so SSE clients connecting in the first 500 ms see data immediately. There's a test for this.
- `MassiveDataSource.start()` does an **immediate first poll** before scheduling the loop — same property for the Massive code path.

**Test suite is thoughtful.**

- `test_simulator.py` exercises the math (positivity over 10K steps), boundary conditions (n=0, n=1 for Cholesky), and the public ticker-management API.
- `test_simulator_source.py` covers `start/stop/add/remove`, idempotent stop, custom intervals, exception resilience.
- `test_massive.py` uses focused mocks (`MagicMock` snapshots) and verifies the malformed-snapshot skip, the ms→s timestamp conversion, the empty-tickers short-circuit, and the cancellation path.
- `test_factory.py` covers all four environment-variable branches (unset, empty, whitespace, set).

---

## Bugs (must fix)

### B1 — `stream.create_stream_router` shares a module-level `APIRouter` across calls (High)

`backend/app/market/stream.py:17`:

```python
router = APIRouter(prefix="/api/stream", tags=["streaming"])


def create_stream_router(price_cache: PriceCache) -> APIRouter:
    @router.get("/prices")
    async def stream_prices(request: Request) -> StreamingResponse:
        ...
    return router
```

The `router` is created at module import. Every call to `create_stream_router(cache)` decorates `/prices` on the **same** singleton. Probe:

```
First router routes: [('/api/stream/prices', {'GET'}), ('/api/stream/prices', {'GET'})]
Same router instance?: True
Second router routes count: 2
```

Two failure modes:

1. **Double registration.** Tests, multi-app setups, or the FastAPI lifespan being re-entered (e.g., during `uvicorn --reload`) will end up with `N` copies of `/api/stream/prices`. FastAPI dispatches the first match, but routing tables get cluttered.
2. **Closure captures the first `price_cache`.** A second `create_stream_router(other_cache)` returns the same router, whose handler still references the **original** cache from the first call. Silently wrong if production ever swaps caches or if tests instantiate per-test caches.

**Fix:** Create a fresh `APIRouter` inside the factory:

```python
def create_stream_router(price_cache: PriceCache) -> APIRouter:
    router = APIRouter(prefix="/api/stream", tags=["streaming"])

    @router.get("/prices")
    async def stream_prices(request: Request) -> StreamingResponse:
        return StreamingResponse(
            _generate_events(price_cache, request),
            media_type="text/event-stream",
            headers={...},
        )

    return router
```

Drop the module-level `router = ...` line.

---

### B2 — `PriceCache.update()` bumps the version even when the rounded price hasn't changed (High)

`backend/app/market/cache.py:23-42`. Probe:

```
Identical price (190.00 -> 190.00): version went 1 -> 2
Sub-cent (190.001 -> 190.002, both round to 190.00): version 1 -> 2
```

PLAN.md §6 ("SSE Streaming") and `MARKET_INTERFACE.md` ("The `version` counter — what it's for") both promise:

> The SSE generator caches the last version it sent and only emits a new event when `cache.version` advances. … Slow upstream sources (Massive on free tier: one update every 15 s) don't cause 30 redundant SSE pushes between real updates.

But the current implementation bumps `_version` unconditionally inside `update()`. Concrete consequences:

- **Massive case:** If `last_trade.price` is identical between two polls (overnight, halted stock, low-volume name), the version still bumps and SSE fires. Client-side flash animations fire on a no-op update.
- **Simulator case:** Most ticks produce a sub-cent move that *might* round to the same value (especially for low-volatility names like JPM/V at small `dt`). Each one causes a redundant SSE frame and a misleading flash.

This is also what makes `stream.py`'s SSE-on-version-change logic functionally identical to push-on-tick. The push-on-change optimization PLAN.md asks for is **not present** end-to-end.

**Fix:** Skip the version bump when the new rounded price equals the previous:

```python
def update(self, ticker: str, price: float, timestamp: float | None = None) -> PriceUpdate:
    with self._lock:
        ts = time.time() if timestamp is None else timestamp
        prev = self._prices.get(ticker)
        new_price = round(price, 2)
        previous_price = prev.price if prev else new_price

        update = PriceUpdate(
            ticker=ticker,
            price=new_price,
            previous_price=previous_price,
            timestamp=ts,
        )
        self._prices[ticker] = update
        if prev is None or prev.price != new_price:
            self._version += 1
        return update
```

Add tests:
- `test_no_version_bump_on_identical_price`
- `test_version_bumps_on_change`
- `test_first_update_bumps_version` (the prev-is-None case)

Note the related minor fix in the same method: `ts = timestamp or time.time()` should be `ts = time.time() if timestamp is None else timestamp`. A literal `timestamp=0.0` is falsy and gets silently replaced. Tested: confirmed.

---

### B3 — SSE keepalive comment is missing (Medium)

`backend/app/market/stream.py`. PLAN.md §6 mandates `: keepalive\n\n` every ~15 s to keep idle SSE connections open through proxies. The shipped generator only yields when the version changes — if Massive's poll fails or the cache is idle for >30 s, intermediaries (nginx, Cloudflare, App Runner) will close the connection.

`MARKET_INTERFACE.md` already calls this out as "Gap to fix: keepalive comments." Just hasn't been closed.

**Fix:** Track time-since-last-yield and emit a comment on overflow:

```python
async def _generate_events(price_cache, request, interval=0.5, keepalive_seconds=15.0):
    yield "retry: 1000\n\n"
    last_version = -1
    last_yield_at = time.monotonic()
    try:
        while True:
            if await request.is_disconnected():
                break

            current = price_cache.version
            now = time.monotonic()

            if current != last_version:
                last_version = current
                prices = price_cache.get_all()
                if prices:
                    payload = json.dumps({t: u.to_dict() for t, u in prices.items()})
                    yield f"data: {payload}\n\n"
                    last_yield_at = now
            elif now - last_yield_at >= keepalive_seconds:
                yield ": keepalive\n\n"
                last_yield_at = now

            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        ...
```

Add a unit test that runs the generator against a fake `Request` with no version advances and asserts a keepalive line appears within `keepalive_seconds + interval`.

---

### B4 — `MassiveDataSource` case-normalization is inconsistent between `start()` and `add/remove_ticker` (Medium)

`backend/app/market/massive_client.py`:

- `start(tickers)` at line 43: `self._tickers = list(tickers)` — preserves caller's case.
- `add_ticker(ticker)` at line 67: `ticker = ticker.upper().strip()`
- `remove_ticker(ticker)` at line 73: `ticker = ticker.upper().strip()`

Probe confirms the consequence:

```
After add_ticker("aapl"):  _tickers = ['AAPL']
start(["aapl"]) + remove_ticker("aapl"):  _tickers afterwards = ['aapl']  # not removed!
```

If any caller (frontend, LLM, tests, future REST endpoint) ever passes a lowercase ticker to `start()`, that ticker will become **unremovable** because `remove_ticker` uppercases the argument first. The same trap applies to `add_ticker` adding a duplicate after a mixed-case `start()`.

**Fix:** Normalize once at the entry point — either in `start()`:

```python
async def start(self, tickers: list[str]) -> None:
    ...
    self._tickers = [t.upper().strip() for t in tickers]
```

…or push the normalization into a helper used by all three methods. Add a regression test.

Side observation: the simulator does **not** normalize at all (`SimulatorDataSource._sim` will happily track both `"AAPL"` and `"aapl"` as distinct keys). For consistency, decide whether normalization is a `MarketDataSource` contract or a per-implementation detail and document it — currently the two implementations disagree.

---

### B5 — `_fetch_snapshots` shares the live `_tickers` list with the worker thread (Low)

`backend/app/market/massive_client.py:123-128`:

```python
def _fetch_snapshots(self) -> list:
    return self._client.get_snapshot_all(
        market_type=SnapshotMarketType.STOCKS,
        tickers=self._tickers,
    )
```

`_fetch_snapshots` runs on a worker thread via `asyncio.to_thread(...)`. Meanwhile `add_ticker` / `remove_ticker` can mutate `self._tickers` on the event-loop thread. CPython's GIL makes `list.append` / list-comp atomic, so this is unlikely to crash — but the *batch identity* shifts mid-call. A caller observing "I added X then waited for the next poll" can't reason about whether X was included.

**Fix:** Snapshot once before the thread call:

```python
async def _poll_once(self) -> None:
    if not self._tickers or not self._client:
        return
    tickers = list(self._tickers)
    try:
        snapshots = await asyncio.to_thread(self._fetch_snapshots, tickers)
        ...

def _fetch_snapshots(self, tickers: list[str]) -> list:
    return self._client.get_snapshot_all(market_type=SnapshotMarketType.STOCKS, tickers=tickers)
```

This is low priority — current behavior is "eventually consistent" rather than buggy — but it's a five-line cleanup.

---

## Deviations from PLAN.md

### D1 — `stream.py` is missing the keepalive (covered above, B3)

### D2 — Unknown-ticker seed-price range disagrees with PLAN.md

`PLAN.md` §6 says:

> When a ticker not in the seed list is added to the watchlist (by the user or LLM), the simulator auto-generates a plausible seed price (random in a sensible range, e.g., $20–$400)…

`simulator.py:151` uses `random.uniform(50.0, 300.0)`. `MARKET_SIMULATOR.md` documents 50–300 too. Either the implementation or PLAN.md needs to win — pick one and align both docs. The narrower range is arguably better (a $20 seed price would draw too much attention given the per-tick GBM scale), but PLAN.md is the contract.

### D3 — Push-on-change is not actually push-on-change (covered above, B2)

### D4 — Direction of "flat" is computed from unrounded comparison, but rounded prices are stored

Not a bug today (since both inputs are rounded before storage), but worth noting: `PriceUpdate.direction` compares `self.price` and `self.previous_price`. Because the cache always rounds both to 2 dp before constructing the `PriceUpdate`, a sub-cent move that rounds equal will produce `direction == "flat"` — exactly what we want once B2 is fixed. After B2 the version won't bump on flats, so the SSE won't fire on them, which is correct behavior.

---

## Test-coverage gaps

**`stream.py` 33% — the SSE generator itself is untested.**

This is the most significant testing gap. The push-on-change behavior, the disconnect handling, the cancellation path, and (once added) the keepalive cadence all need tests. A pattern that works without a real HTTP server:

```python
async def _drive(gen, steps):
    out = []
    for _ in range(steps):
        try:
            out.append(await asyncio.wait_for(gen.__anext__(), timeout=0.5))
        except StopAsyncIteration:
            break
    return out


async def test_sse_yields_on_version_change():
    cache = PriceCache()
    cache.update("AAPL", 190.0)
    request = MagicMock()
    request.is_disconnected = AsyncMock(return_value=False)

    gen = _generate_events(cache, request, interval=0.01)
    chunks = await _drive(gen, steps=2)         # retry directive + initial frame
    assert any('"AAPL"' in c for c in chunks)
```

Worth adding:
- yields only when version advances
- emits the keepalive comment after the configured idle window
- exits the loop on `is_disconnected() == True`
- handles `CancelledError` cleanly

**`MassiveDataSource._poll_loop` not exercised.**

The while-true poller body (lines 85-87) is uncovered. The current tests exercise `_poll_once()` directly, which is fine for the fetch logic but misses the loop's interaction with `asyncio.sleep` and cancellation. A test that starts a source with `poll_interval=0.05` and observes ≥2 polls would close the gap.

**No race-condition / concurrent-access test.**

PLAN.md §7 (and the §13 review notes) call out the importance of preventing concurrent-trade races. The cache currently uses `threading.Lock` correctly, but there's no test that fires concurrent `cache.update()` from two threads to prove it. Worth at least a smoke test:

```python
def test_cache_thread_safety():
    import threading
    cache = PriceCache()
    def hammer():
        for i in range(1000):
            cache.update("AAPL", 100.0 + i * 0.01)
    threads = [threading.Thread(target=hammer) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert cache.version == 4000  # (or 1+actual-changes after B2)
    assert cache.get("AAPL") is not None
```

**No interface-conformance test.**

`MarketDataSource` is an ABC, but nothing pins down that `SimulatorDataSource` and `MassiveDataSource` actually implement the same surface. PLAN.md §12 explicitly asks for "both implementations conform to the abstract interface." A parametrized test that instantiates each and verifies `start/stop/add_ticker/remove_ticker/get_tickers` works against an empty input would catch any future drift.

---

## Smaller observations

**`models.py:21` — `round(price - previous_price, 4)` for `change` while prices are 2-dp.**
The 4-dp rounding on a value already rounded to 2 dp is wasted precision; 2 dp would be consistent with the stored prices. Same for `change_percent` at 4 dp — fine, but it's reflexively defensive given that the inputs are already 2-dp. Not a bug.

**`cache.py:30` — `timestamp or time.time()`.**
Replace with `time.time() if timestamp is None else timestamp`. Tested and confirmed: `update("AAPL", 100, timestamp=0.0)` silently substitutes `time.time()`. In practice no caller passes 0.0 (Massive uses `ms/1000.0` and the simulator uses `time.time()`), but the bug is real and the fix is one line.

**`stream.py` docstring drift.**
> "Sends all prices every `interval` seconds."

Misleading — it only yields when the version changes. Update the docstring to "Wakes every `interval` seconds and yields the full price map *if* the cache has advanced; otherwise sleeps. Emits a keepalive comment after `keepalive_seconds` of idle."

**`stream.py:38` — return-type annotation is `StreamingResponse`, not `AsyncGenerator`.**
Already correct (per the summary's "issue #3"). Reads cleanly.

**`simulator.py:151` — `dict(DEFAULT_PARAMS)` copy is correct.**
Prevents the mutable default from being shared across tickers. Good defensive code; worth a comment so future contributors don't "simplify" it.

**`__init__.py` re-exports.**
Matches `MARKET_INTERFACE.md`'s "Public Imports" exactly. `MarketDataSource` is exported so consumers can type-annotate against the ABC. Good.

**`market_data_demo.py`.**
Self-contained, well-structured Rich dashboard. The demo correctly uses `cache.version` polling (and *does* skip redundant ticks at the demo level) — interesting that the demo gets push-on-change right via its own check even though the cache doesn't.

**`MASSIVE_API.md` line reference drift.**
The doc mentions `massive_client.py:97`, `:103`, `:118` for `asyncio.to_thread`, ms-conversion, and the bare `try/except`. Current code: 97, 103, 118 — still accurate. Worth checking on each future edit.

**Optional formatter fix.**
`uv run ruff format` will rewrite the three flagged test files (line-wraps only). Worth committing once to baseline.

---

## Suggested action plan

In rough priority order. Each item is small (≤30 LOC except B3 which adds a test as well).

1. **Fix `stream.create_stream_router`** to create a per-call `APIRouter` (B1). Add a test that calls it twice with two caches and asserts routes are independent.
2. **Make `PriceCache.update` push-on-change** (B2). Skip the version bump when `round(price, 2) == prev.price`. Add three tests.
3. **Add SSE keepalive** (B3). Add a configurable `keepalive_seconds` and emit `: keepalive\n\n` on idle. Add a test.
4. **Normalize `MassiveDataSource` ticker case in `start()`** (B4). Decide on a normalization contract and document it (probably "yes, both implementations uppercase+strip"). Add a regression test.
5. **Tighten `PriceCache.update` timestamp handling** (`timestamp or time.time()` → `is None` check). One-liner.
6. **Backfill `stream.py` tests** to ≥80% line coverage. This is what would have caught B1/B3 in the first place.
7. **Resolve the $20–$400 vs $50–$300 deviation** (D2) — pick one and update PLAN.md or the simulator.
8. **Snapshot `_tickers` before the `to_thread` call** (B5). Five-line cleanup.
9. **Add an ABC-conformance test** that runs both data sources through `start/add/remove/stop`.
10. **Reformat the three flagged test files** with `ruff format`. Cosmetic.

None of these change the public API. After (1)–(4) the subsystem matches the contract in PLAN.md §6 end-to-end; the rest are quality improvements.

---

## Verdict

The market-data layer is **well-designed and largely well-implemented**, with a clean abstraction, correct GBM math, and a thoughtful test suite for the modules that have tests. The SSE / change-detection path — the part downstream consumers actually integrate against — has two important bugs and a coverage gap that need closing before the frontend and chat-trade flows depend on push-on-change semantics. None of the issues are architectural; all are localized and fixable in a single short PR.
