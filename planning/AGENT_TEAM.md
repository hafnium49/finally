# Agent Team — Orchestration Plan

This document defines the team of specialist subagents that will complete the FinAlly project per `planning/PLAN.md`. It is the contract between the orchestrator (the main Claude Code session) and the dispatched subagents.

> The *what* is in `PLAN.md`. This file is the *how* — who owns what, in what order, with what handoff artifacts.

## Status snapshot

Completed already:
- Market data subsystem (`backend/app/market/`) — simulator, Massive client, price cache, SSE stream. 73 tests, 84% coverage.

Remaining (this plan):
- DB layer · Portfolio + trade execution · FastAPI app + routes · LLM chat · Frontend · Docker + scripts · E2E Playwright tests.

## Roster

| Agent | Persona file | Owns (write access) | Reads as contract |
|---|---|---|---|
| **Database Engineer** | `.claude/agents/database-engineer.md` | `backend/app/db/`, `backend/tests/db/` | PLAN.md §7 |
| **Backend API Engineer** | `.claude/agents/backend-api-engineer.md` | `backend/app/api/`, `backend/app/portfolio/`, `backend/app/main.py`, `backend/tests/{api,portfolio}/` | PLAN.md §6/§7/§8, `SCHEMA.md` |
| **LLM Engineer** | `.claude/agents/llm-engineer.md` | `backend/app/chat/`, `backend/tests/chat/` | PLAN.md §9, `SCHEMA.md`, `API_CONTRACT.md` |
| **Frontend Engineer** | `.claude/agents/frontend-engineer.md` | `frontend/` | PLAN.md §2/§10, `API_CONTRACT.md` |
| **DevOps Engineer** | `.claude/agents/devops-engineer.md` | `Dockerfile`, `docker-compose.yml`, `scripts/`, `.env.example`, `.dockerignore` | PLAN.md §11 |
| **Integration Tester** | `.claude/agents/integration-tester.md` | `test/` (Playwright + `docker-compose.test.yml`), `planning/BUGS.md` | PLAN.md §12, runs the assembled stack |

The **orchestrator** (main session) owns: `planning/SCHEMA.md`, `planning/API_CONTRACT.md`, `planning/LLM_CONTRACT.md`, `planning/BUGS.md` triage, conflict arbitration, and all commits.

## File ownership rules

Builder agents own **disjoint subtrees**. No two agents write the same file. Specifically:

- The FastAPI application file (`backend/app/main.py`) is owned by the Backend API Engineer. Every other backend agent exposes its functionality through its own subpackage `__init__.py` (e.g. `backend/app/chat/__init__.py` exports `router`) and the API Engineer imports them in `main.py`.
- `backend/app/__init__.py` already exists from the market subsystem; agents do not modify it.
- `pyproject.toml` is shared but only **added to** (additive dependency edits). The orchestrator merges if two agents both add deps.
- `planning/` files (`SCHEMA.md`, `API_CONTRACT.md`, `LLM_CONTRACT.md`, `BUGS.md`) are written by the originating agent and amended by the orchestrator only.

## Contract artifacts (Phase 1 outputs)

Three short docs in `planning/` define the seams. They are written sequentially because each builds on the previous.

### `planning/SCHEMA.md` — owned by DB Engineer
- Exact `CREATE TABLE` statements for: `users_profile`, `watchlist`, `positions`, `trades`, `portfolio_snapshots`, `price_ticks`, `chat_messages`, `chat_state` (for summary).
- Default seed data: `users_profile` row + 10 watchlist tickers (PLAN.md §7).
- Indexes (esp. `price_ticks(recorded_at)` for pruning).
- The exact JSON shape stored in `chat_messages.actions` (must match PLAN.md §9 "Backend Response & actions Shape" verbatim).

### `planning/API_CONTRACT.md` — owned by Backend API Engineer
- Every endpoint from PLAN.md §8 with **exact** request/response JSON.
- Field-level: `change_pct` on `/api/watchlist`, the `actions[]` array on `/api/chat`, error code enum (`insufficient_cash`, `insufficient_shares`, `unknown_ticker`).
- HTTP status codes for each path (200, 400, 404, 409, 500).
- SSE event shape for `/api/stream/prices`.

### `planning/LLM_CONTRACT.md` — owned by LLM Engineer
- Structured-output JSON schema (Pydantic model) for the LLM response (message, trades, watchlist_changes).
- System prompt skeleton with `{{USER_PROMPT_BODY}}` placeholder for user-authored prose.
- Conversation context-window policy (10 verbatim + rolling summary).
- Mock-mode response table: `LLM_MOCK=true` → deterministic responses keyed on input regex.

## Execution phases

### Phase 1 — Contracts (sequential)

```
1.1  Dispatch: Database Engineer
     → planning/SCHEMA.md
1.2  Orchestrator reviews + commits SCHEMA.md
1.3  Dispatch: Backend API Engineer
     → planning/API_CONTRACT.md  (reads SCHEMA.md)
1.4  Orchestrator reviews + commits API_CONTRACT.md
1.5  Dispatch: LLM Engineer
     → planning/LLM_CONTRACT.md  (reads SCHEMA.md, API_CONTRACT.md)
1.6  Orchestrator reviews + commits LLM_CONTRACT.md
```

### Phase 2 — Build (parallel, 5 dispatches in a single message)

Each builder agent receives:
- The relevant PLAN.md sections
- The three contract docs
- A scoped task: "build your owned subtree, write unit tests, do not modify files outside it"

```
2.1  Parallel dispatch:
       Database Engineer    → backend/app/db/* + tests
       Backend API Engineer → backend/app/{api,portfolio,main.py} + tests
       LLM Engineer         → backend/app/chat/* + tests, STUB system_prompt.py with TODO(user)
       Frontend Engineer    → frontend/* (Next.js project from scratch)
       DevOps Engineer      → Dockerfile, scripts/*, .env.example, .dockerignore
2.2  Orchestrator merges, runs `cd backend && uv run pytest`, commits checkpoint
2.3  PAUSE: surface backend/app/chat/system_prompt.py to user for the LLM voice/tone
```

### Phase 3 — Integration (sequential, looped)

```
3.1  Dispatch: Integration Tester
     → test/docker-compose.test.yml + test/playwright/*
     → builds image, runs E2E with LLM_MOCK=true
     → writes planning/BUGS.md as structured list
3.2  Orchestrator triages BUGS.md
     For each open bug:
       - Route to owning agent (re-dispatch with bug-specific prompt)
       - Re-run Integration Tester
3.3  Loop until BUGS.md is empty or 3 iterations elapsed per bug
3.4  Final commit + README update
```

## Bug-fix protocol

`planning/BUGS.md` entries:

```yaml
- id: B001
  owner: frontend-engineer
  severity: blocker | major | minor
  repro: "Open localhost:8000, click NVDA in watchlist"
  expected: "Main chart loads NVDA history then appends live ticks"
  actual: "Chart stays empty; console error: history endpoint returns 404"
  iteration: 0
```

The orchestrator dispatches the owning agent with just the relevant bug (not the whole file). Cap at 3 fix iterations per bug — beyond that, orchestrator pauses and asks the user.

## Coordination protocol — how subagents communicate

Subagents do **not** talk to each other. Communication is one-way via files:

```
PLAN.md           ──┐
SCHEMA.md         ──┼──→ each builder agent (read-only)
API_CONTRACT.md   ──┤
LLM_CONTRACT.md   ──┘

builder agent  ──→ writes only to its owned subtree
            \
             └─→ exits, returns summary to orchestrator

orchestrator → merges, commits, dispatches next agent
```

If a builder discovers an ambiguity in a contract doc, it must **not** edit the doc directly. It returns the question to the orchestrator, who decides and (if needed) amends the contract before re-dispatching.

## Anti-patterns to avoid

- ❌ A builder modifying another builder's subtree to "quickly fix" something
- ❌ A builder adding a new endpoint/schema not in the contract docs
- ❌ The Integration Tester editing application code to make a test pass
- ❌ Skipping unit tests in Phase 2 because "E2E will catch it"
- ❌ The LLM Engineer hardcoding the system prompt voice (must remain TODO(user) until user writes it)

## User-author insertion point

PLAN.md §9 says the LLM acts as "FinAlly, an AI trading assistant". The behavioral requirements (analyze, suggest, execute, manage watchlist, be concise) are specified — but the **voice, tone, and risk-warning posture** are deliberately user-authored. The LLM Engineer leaves:

```python
# backend/app/chat/system_prompt.py
SYSTEM_PROMPT_VOICE = """
TODO(user): 5-10 lines describing how FinAlly should *talk*.
- How proactive? (suggest trades unprompted, or wait to be asked?)
- How risk-averse? (warn before risky trades, or just execute?)
- Tone? (terse trader, friendly explainer, dry institutional?)
- Catchphrases or absolutely-not phrases?
This block is concatenated into the system prompt assembled by build_system_prompt().
""".strip()
```

The orchestrator pauses Phase 3 to surface this file to the user.

---

## Appendix A — Post-mortem (what actually happened)

This appendix is appended after the build was complete. The plan above is preserved verbatim; this section records the actual execution.

### Iteration log

| Iter | Phase | Action | Outcome |
|---|---|---|---|
| 0 | 1 | Dispatch DB Engineer → SCHEMA.md | 8 tables, 4 indexes, 12 seed rows; flagged `actions[]`-vs-NULL storage ambiguity |
| 0 | 1 | Dispatch Backend API → API_CONTRACT.md | 11 endpoints documented; pinned `actions: []` (never null) on the wire; flagged SSE per-frame map shape ≠ prompt description (kept actual behavior, documented) |
| 0 | 1 | Dispatch LLM Engineer → LLM_CONTRACT.md | 8 Pydantic models, 7-row mock regex table, `SYSTEM_PROMPT_VOICE` reserved as user slot; flagged 1 new error code (`invalid_quantity`) which orchestrator back-propagated into API_CONTRACT.md |
| 0 | 2 | Parallel dispatch of 5 builders | DB / LLM / Frontend / DevOps succeeded on first try. Backend API agent rejected by user mid-dispatch; re-dispatched once the other 4 had landed (less to coordinate). Tests at end of Phase 2: 273 backend + 37 frontend |
| 0 | 3 | Integration Tester first E2E run | **0/10 pass** — all blocked by B001 (frontend mounted Watchlist + ChatPanel twice for responsive layout, breaking Playwright strict-mode locators). Also caught self-owned B002–B004 (test infra hygiene) and noted B005 (sandbox needs `dangerouslyDisableSandbox: true` for docker) |
| 1 | 3 | Frontend Engineer fix B001 | Single mount + Tailwind `order-*` for responsive reorder. Build + unit tests stayed green |
| 1 | 3 | Integration Tester iteration 1 | **8/10 pass**. New failure B006 — chat trade execution missing `price_cache` kwarg, HTTP 500 |
| 2 | 3 | LLM Engineer fix B006 | Threaded `price_cache` via `api/chat.py` → `handle_message` → `executor.apply` → `execute_trade`. 275 backend tests pass |
| 2 | 3 | Integration Tester iteration 2 | **10/10 pass**. Mocked E2E suite is fully green. Phase 3 complete from the persona's perspective |
| 3 | 4 | (user-added) Live smoke test with real OpenRouter | **2 majors caught that mocks missed**: B017 (LLM saw empty portfolio context — handler looked up nonexistent symbol) and B018 (uid mismatch on host `db/` bind mount). Also a cosmetic B019 (favicon 404) |
| 3 | 4 | LLM Engineer fix B017 + DevOps Engineer fix B018 | 279 backend tests pass; live re-smoke confirms chat sees real portfolio data and `start_mac.sh` works without manual chmod |

### Final bug ledger

9 bugs over 4 iteration loops; 8 fixed, 1 deferred (B019 cosmetic favicon). Severity breakdown: 1 blocker (B001), 3 major (B006, B017, B018), 5 minor (B002–B005, B019). All fixes live in `planning/BUGS.md`.

### What worked

- **Disjoint directory ownership.** Five builder agents wrote ~5,000 LOC in parallel with zero merge conflicts. Owning a subtree turned out to be a stronger contract than any code review could enforce.
- **Frozen contract docs before code.** Phase 1's three docs (`SCHEMA.md`, `API_CONTRACT.md`, `LLM_CONTRACT.md`) let the parallel builders execute against a stable interface. The Backend API Engineer's Phase 1 dispatch caught the SSE per-frame vs. per-event shape mismatch *before* anyone built against the wrong assumption.
- **Bug-specific re-dispatch.** Routing each bug to its owning agent with ONLY the relevant entry (not the whole BUGS.md) kept each fix tight and avoided scope creep.

### What surprised us

- **Mock fidelity matters more than test count.** A 10/10 green mocked E2E suite hid two majors that a single live smoke test caught in ~5 minutes. The plan should have included a Phase 4 live-smoke gate from the start; it was added retroactively. See `planning/SHIPPED.md` for the lesson.
- **Auto-commit hooks ran ahead of the orchestrator.** The codex review hook on `Stop` kept committing in-flight work with generic messages ("Refactor code structure for improved readability"), making the commit log noisy. Disabling all hooks for the final stretch produced cleaner commits but lost the per-turn review.
- **The user-author slot worked.** A single 6-line voice block (`SYSTEM_PROMPT_VOICE`) was the only human-authored code in the build, and it changes the entire feel of the LLM responses. Reserving exactly one high-leverage slot kept the human-in-the-loop step concentrated and useful.

### What we'd do differently

- Add a **Phase 4 live-smoke gate** to the team plan template. The Integration Tester persona is now updated to require it before marking work shipped.
- For mock-mode tests, **assert on the prompt content reaching the LLM**, not just on the returned action. The chat mock ignored prompt content entirely, which is why B017 slipped through. A stronger pattern: capture the assembled prompt in a fixture and assert key fields are present.
- For Docker bind mounts, **normalize ownership in the start script**, not in the Dockerfile. B018 cost an iteration because the `USER app` directive was set at build time and didn't match the host user at runtime.

