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
