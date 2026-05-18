# Review of planning/PLAN.md

## Findings

### High: Section 13 leaves resolved and stale review notes in the active implementation contract

`planning/PLAN.md:557-620` is still framed as a working list that should be triaged before implementation, but nearly every item is marked resolved in the same section. The final "Insight" block also says the chat/trade boundary and SSE behavior are still underspecified (`planning/PLAN.md:617-620`), even though sections 6 and 9 now define those contracts.

This is risky because future agents may treat section 13 as current guidance and reopen decisions already made earlier in the document. Move resolved notes into `planning/archive/`, or replace section 13 with a short "Resolved Decisions" appendix that no longer says implementation is blocked.

### Medium: Conversation summary persistence is required but not defined in the schema

Section 9 requires a rolling summary for messages older than the last 10 and says it must survive across requests (`planning/PLAN.md:337-343`). The database schema only defines `chat_messages` (`planning/PLAN.md:267-273`), and the summary storage is left as an example choice: either a `chat_state` table or JSON in `users_profile` (`planning/PLAN.md:341`).

That ambiguity will split backend implementations. Pick one storage contract, for example:

```sql
chat_state (
  user_id TEXT PRIMARY KEY,
  summary TEXT NOT NULL DEFAULT '',
  updated_at TEXT NOT NULL
)
```

Then add it to section 7 and the LLM tests in section 12.

### Medium: The LLM instructions depend on a non-portable agent skill

The plan tells implementers to use a `cerebras-inference` skill (`planning/PLAN.md:318` and `planning/PLAN.md:329`). In this workspace, that appears to exist only as `.claude/skills/cerebras/SKILL.md`; it is not a generally available project dependency or Codex skill.

The shared plan should not require an agent-local skill to implement core product behavior. Replace that instruction with concrete requirements: LiteLLM dependency, model string, OpenRouter provider configuration, structured output schema, timeout/retry behavior, and fallback/mock behavior. If the Claude skill remains useful, mention it as optional agent-specific guidance.

### Medium: The plan reads as current repo structure, but major listed bootstrap files are absent

The directory tree lists `frontend/`, `scripts/`, `test/`, `db/`, `Dockerfile`, `docker-compose.yml`, and `.env.example` as present project structure (`planning/PLAN.md:89-116`). A repo scan currently finds only `.env` among those top-level bootstrap artifacts.

This is fine if section 4 is the target structure, but the plan currently reads like a factual repository map. Label these as planned deliverables or add a "Current state vs. target state" note so agents do not assume missing scaffolding already exists.

### Medium: SSE semantics in the plan do not match the current market code

The plan requires version bumps only on actual price changes and periodic keepalive comments (`planning/PLAN.md:186-197`). The current `PriceCache.update()` increments `_version` on every call regardless of whether the rounded price changed (`backend/app/market/cache.py:21-41`), and `_generate_events()` only yields when the version changes, with no idle keepalive path (`backend/app/market/stream.py:75-85`).

If the plan is the target contract, section 6 or section 12 should call this out as known implementation work. Otherwise, future agents may assume the existing backend already satisfies the contract and write frontend/test logic around behavior that is not implemented yet.

### Low: Core API response shapes are still too loose for parallel frontend/backend work

Section 8 lists endpoints but only defines detailed response shapes for chat actions and partial watchlist fields (`planning/PLAN.md:282-312`). The frontend needs stable contracts for `GET /api/portfolio`, `POST /api/portfolio/trade`, `GET /api/portfolio/history`, and price history rows.

Add compact JSON examples or typed schemas for those endpoints. This is especially important for portfolio fields such as `total_value`, `cash_balance`, `unrealized_pnl`, `positions[].market_value`, and error codes from manual trade validation.

## Open Questions

- Should `OPENROUTER_API_KEY` be truly required on first launch, or should the app start with chat disabled or `LLM_MOCK=true` when the key is absent? The first-launch UX promises an AI chat panel ready to assist (`planning/PLAN.md:15-20`), while section 5 marks the key as required (`planning/PLAN.md:135-152`).
- Should root runtime data stay in `db/`, while backend schema code also lives in `backend/app/db/`? The plan explains the distinction, but the name collision will still be a source of mistakes.

## Summary

The product direction is coherent and the major contracts are much stronger than the archived review suggests. The main remaining issue is document hygiene: `PLAN.md` mixes target architecture, current repo assumptions, and resolved review history. Cleaning that up before more agents implement against it will prevent avoidable divergence.

No tests were run for this documentation review.
