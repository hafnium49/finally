# LLM_CONTRACT.md — FinAlly Chat / LLM Subsystem (Phase 1 contract)

This document is the canonical contract for the chat / LLM subsystem. It is owned by the **LLM Engineer** and consumed read-only by the **Backend API Engineer** (whose `/api/chat` handler delegates to `handle_message()` and serializes the returned `ChatResponse`) and the **Integration Tester** (whose Playwright tests rely on the deterministic mock-mode responses defined here).

Sources of truth:

- `planning/PLAN.md` §9 — chat / LLM spec (authoritative behavior)
- `planning/SCHEMA.md` §1.7 / §3 — `chat_messages` / `chat_state` tables and the canonical `actions` JSON shape
- `planning/API_CONTRACT.md` §1.4 and §5 — error-code enum and the `/api/chat` wire format (especially the rule that `actions` is always `[]` on the wire, never `null`)

Where any of the above is ambiguous, this file picks the conservative interpretation and flags it inline.

---

## 0. Module layout (informative)

The Phase 2 implementer will create these files under `backend/app/chat/`. Phase 1 only writes this contract; no code goes in yet.

| File | Purpose |
|---|---|
| `__init__.py` | Re-exports `handle_message(...)` and the FastAPI `router`. |
| `schemas.py` | Pydantic v2 models from §1 below. |
| `system_prompt.py` | Holds `SYSTEM_PROMPT_VOICE = "TODO(user)..."` — left stubbed at end of Phase 2. |
| `prompt.py` | `build_system_prompt()` + `build_messages()` — assembles the skeleton from §2. |
| `client.py` | LiteLLM wrapper. Live mode uses the **cerebras-inference skill** (see §5). Dispatches to `mock.py` when `LLM_MOCK=true`. |
| `mock.py` | Deterministic regex-keyed mock responses (§4). |
| `summarizer.py` | Conversation summary rewrite, triggered on overflow (§3). |
| `executor.py` | Applies parsed `LLMResponse` → portfolio + watchlist mutations → resolved `ChatAction[]` (§6). |
| `handler.py` | `handle_message(user_text, user_id="default") -> ChatResponse` — the orchestration glue called by `/api/chat`. |

All LLM calls go through `client.py`; no direct `litellm.completion()` elsewhere.

---

## 1. Pydantic models

These are concrete Pydantic v2 model definitions. The Phase 2 implementer pastes them into `backend/app/chat/schemas.py` verbatim (modulo imports and minor formatting).

```python
"""Pydantic v2 models for the FinAlly chat subsystem.

These models are the source of truth for:
- the structured output we request from the LLM (LLMResponse + nested LLMTrade / LLMWatchlistChange)
- the resolved per-action records persisted to chat_messages.actions and returned on the /api/chat wire (ChatAction)
- the /api/chat response envelope (ChatResponse)
"""

from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Inputs from the LLM (structured output)
# ---------------------------------------------------------------------------

TICKER_REGEX = r"^[A-Z]{1,5}$"


class LLMTrade(BaseModel):
    """A trade the LLM wants the backend to execute on the user's behalf."""

    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(..., description="Uppercase ticker symbol, 1-5 letters.")
    side: Literal["buy", "sell"]
    quantity: float = Field(..., gt=0, description="Positive; fractional shares allowed.")

    @field_validator("ticker", mode="before")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.upper() if isinstance(v, str) else v


class LLMWatchlistChange(BaseModel):
    """A watchlist mutation the LLM wants the backend to apply."""

    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(..., description="Uppercase ticker symbol, 1-5 letters.")
    action: Literal["add", "remove"]

    @field_validator("ticker", mode="before")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.upper() if isinstance(v, str) else v


class LLMResponse(BaseModel):
    """What the LLM emits. This is the `response_format` we hand to LiteLLM."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(..., min_length=1, description="Conversational text shown to the user.")
    trades: list[LLMTrade] = Field(default_factory=list)
    watchlist_changes: list[LLMWatchlistChange] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Resolved actions persisted + returned on the wire
# ---------------------------------------------------------------------------


class _ChatActionBase(BaseModel):
    """Shared base for the discriminated ChatAction union."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["trade", "watchlist"]
    status: Literal["ok", "error"]
    ticker: str


class TradeActionOk(_ChatActionBase):
    kind: Literal["trade"] = "trade"
    status: Literal["ok"] = "ok"
    side: Literal["buy", "sell"]
    quantity: float
    fill_price: float
    cash_after: float


class TradeActionError(_ChatActionBase):
    kind: Literal["trade"] = "trade"
    status: Literal["error"] = "error"
    side: Literal["buy", "sell"]
    quantity: float
    error: Literal[
        "insufficient_cash",
        "insufficient_shares",
        "unknown_ticker",
        "invalid_quantity",
    ]
    error_message: str


class WatchlistActionOk(_ChatActionBase):
    kind: Literal["watchlist"] = "watchlist"
    status: Literal["ok"] = "ok"
    action: Literal["add", "remove"]


class WatchlistActionError(_ChatActionBase):
    kind: Literal["watchlist"] = "watchlist"
    status: Literal["error"] = "error"
    action: Literal["add", "remove"]
    error: Literal[
        "ticker_already_in_watchlist",
        "not_in_watchlist",
        "invalid_ticker",
    ]
    error_message: str


# Discriminated union. Pydantic v2 picks the right variant from (kind, status).
ChatAction = Annotated[
    Union[TradeActionOk, TradeActionError, WatchlistActionOk, WatchlistActionError],
    Field(discriminator=None),  # disambiguated by Literal kind/status combination
]


# ---------------------------------------------------------------------------
# Wire / handler-return envelope
# ---------------------------------------------------------------------------


class ChatResponse(BaseModel):
    """Returned from handle_message(...) and serialized verbatim by /api/chat.

    `actions` is ALWAYS a list (possibly empty) — never None. Both the
    persisted form in chat_messages.actions and the wire form mirror this.
    See API_CONTRACT.md §5.
    """

    model_config = ConfigDict(extra="forbid")

    message: str
    actions: list[ChatAction] = Field(default_factory=list)
```

### 1.1 JSON-schema example payloads

#### `LLMResponse` — minimal (message only)

```json
{
  "message": "Your portfolio is concentrated in tech: AAPL and NVDA together are 62% of total value.",
  "trades": [],
  "watchlist_changes": []
}
```

#### `LLMResponse` — trade + watchlist combo

```json
{
  "message": "Buying 10 AAPL and adding PYPL to your watchlist.",
  "trades": [
    {"ticker": "AAPL", "side": "buy", "quantity": 10}
  ],
  "watchlist_changes": [
    {"ticker": "PYPL", "action": "add"}
  ]
}
```

#### `ChatResponse` — successful execution

```json
{
  "message": "Buying 10 AAPL and adding PYPL to your watchlist.",
  "actions": [
    {
      "kind": "trade",
      "status": "ok",
      "ticker": "AAPL",
      "side": "buy",
      "quantity": 10,
      "fill_price": 192.34,
      "cash_after": 8076.60
    },
    {
      "kind": "watchlist",
      "status": "ok",
      "ticker": "PYPL",
      "action": "add"
    }
  ]
}
```

#### `ChatResponse` — partial failure

```json
{
  "message": "Trying to buy 50 TSLA and 10 AAPL.",
  "actions": [
    {
      "kind": "trade",
      "status": "error",
      "ticker": "TSLA",
      "side": "buy",
      "quantity": 50,
      "error": "insufficient_cash",
      "error_message": "Need $12,400.00 but only $8,076.60 available."
    },
    {
      "kind": "trade",
      "status": "ok",
      "ticker": "AAPL",
      "side": "buy",
      "quantity": 10,
      "fill_price": 192.34,
      "cash_after": 6153.26
    }
  ]
}
```

#### `ChatResponse` — message only, no actions

```json
{
  "message": "Hello — I'm FinAlly, your trading assistant.",
  "actions": []
}
```

> Note the empty array, not `null`. This is the wire invariant from API_CONTRACT.md §5.

---

## 2. System prompt skeleton

`build_system_prompt(portfolio_ctx, summary, verbatim_history)` in `prompt.py` assembles a single string by substituting into the following template **in this exact order**. The double-brace tokens are placeholder slots; they do not appear in the final string.

```
You are FinAlly, an AI trading assistant.

{{SYSTEM_PROMPT_VOICE}}

## Response format
You must respond with valid JSON matching this schema:
{{LLM_RESPONSE_JSON_SCHEMA}}
Trades execute automatically. Watchlist changes apply automatically. Be concise.

## Current portfolio
{{PORTFOLIO_CONTEXT_JSON}}

## Conversation summary (older turns folded)
{{CONVERSATION_SUMMARY}}

## Recent conversation
{{VERBATIM_HISTORY}}
```

### 2.1 Slot definitions

| Slot | Source | Type / Format |
|---|---|---|
| `{{SYSTEM_PROMPT_VOICE}}` | `backend/app/chat/system_prompt.py` constant `SYSTEM_PROMPT_VOICE` | Free-form string. **User-authored.** See §2.2. |
| `{{LLM_RESPONSE_JSON_SCHEMA}}` | `LLMResponse.model_json_schema()` rendered as a compact JSON object | Stable JSON Schema produced by Pydantic; embedded so the LLM sees the shape even when the provider's structured-output mode is ignored or stripped by an intermediary. |
| `{{PORTFOLIO_CONTEXT_JSON}}` | Built in `prompt.py` from `portfolio.get_portfolio()` + `watchlist.list_with_prices()` + `PriceCache` | Compact JSON object with keys `cash_balance`, `total_value`, `unrealized_pnl`, `positions[]`, `watchlist[]`. See §2.3 for the exact shape. |
| `{{CONVERSATION_SUMMARY}}` | `chat_state.summary` for `user_id="default"` | Plain string. Empty (`""`) on a fresh database — in that case the section header still renders, with `(none yet)` as the body. |
| `{{VERBATIM_HISTORY}}` | Last 10 rows of `chat_messages` for the user, oldest first | Role-tagged lines, one per message, formatted `[user] ...` / `[assistant] ...`. The new user turn is appended as the trailing `[user]` line so the model sees it in-context. |

### 2.2 `SYSTEM_PROMPT_VOICE` — user-authored slot

This slot is **user-authored**. The LLM Engineer MUST NOT fill it with default voice text in either Phase 1 or Phase 2.

In Phase 2, `backend/app/chat/system_prompt.py` ships exactly this:

```python
SYSTEM_PROMPT_VOICE = """
TODO(user): 5-10 lines describing how FinAlly should *talk*.
- How proactive? (suggest trades unprompted, or wait to be asked?)
- How risk-averse? (warn before risky trades, or just execute?)
- Tone? (terse trader, friendly explainer, dry institutional?)
- Catchphrases or absolutely-not phrases?
This block is concatenated into the system prompt assembled by build_system_prompt().
""".strip()
```

The orchestrator pauses Phase 3 to surface this file to the user for editing. Tests in `backend/tests/chat/` MUST assert that `SYSTEM_PROMPT_VOICE` still contains the literal substring `TODO(user)` at the end of Phase 2 — this prevents the implementer from accidentally writing the voice themselves.

### 2.3 `{{PORTFOLIO_CONTEXT_JSON}}` shape

The compact JSON object built into the prompt. Fields mirror `/api/portfolio` and `/api/watchlist` so the LLM sees the same world the user sees:

```json
{
  "cash_balance": 8076.60,
  "total_value": 10044.00,
  "unrealized_pnl": 44.00,
  "positions": [
    {"ticker": "AAPL", "quantity": 10, "avg_cost": 192.34, "current_price": 196.74, "unrealized_pnl": 44.00}
  ],
  "watchlist": [
    {"ticker": "AAPL", "price": 196.74, "change_pct": 2.7363},
    {"ticker": "GOOGL", "price": 175.20, "change_pct": -0.1140}
  ]
}
```

`null`s from the upstream APIs are kept as `null`s; the LLM is instructed (via the voice slot, when the user writes it) to treat missing prices as "no tick yet".

### 2.4 `{{VERBATIM_HISTORY}}` formatting

```
[user] Buy 5 AAPL
[assistant] Buying 5 AAPL.
[user] What's my exposure to tech?
[assistant] AAPL + NVDA + GOOGL = 62% of total value.
[user] Reduce that to 40%
```

Trailing newline-terminated. The current turn (the message that triggered this call) is included as the last `[user]` line; the LLM's reply will become the next `[assistant]` line written to `chat_messages` after generation. No timestamps; no IDs; no `actions` rehydration — those live in the resolved `actions` array, not in the prompt, to keep tokens bounded.

---

## 3. Context-window policy

### 3.1 Window

- **Verbatim window:** the most recent **10 messages** (user and assistant combined) from `chat_messages` for the active `user_id`, ordered oldest-first. The new user turn currently being processed counts toward the 10.
- **Older history:** folded into a single string in `chat_state.summary`. Empty (`""`) on a fresh database.

### 3.2 Trigger

Summarization fires **when adding the new user message would push the verbatim window past 10**. Concretely, immediately after the user message is persisted to `chat_messages` (and before the next call), if `count(chat_messages where user_id = ?) > 10`:

1. Select the oldest message in the table for this user (call it `M_old`).
2. Build a summarization prompt (§3.3).
3. Call the LLM; receive a new summary string.
4. Update `chat_state.summary` to the new string and `chat_state.updated_at = now`.
5. **Delete `M_old`** from `chat_messages`. After deletion, the verbatim window holds exactly 10 messages again.

Edge cases:

- If summarization fails (LLM error, timeout), `M_old` is **not** deleted — we keep the row and silently grow the window to 11. The next turn will retry. This keeps a single transient LLM failure from losing conversation state.
- Summarization is a fire-and-forget operation **after** the user's main response has been generated and returned. The user does not wait on it. Concretely, the order in `handle_message()` is:
  1. Generate main response → return `ChatResponse` to the caller.
  2. Persist assistant message.
  3. *Then* run the summarization check / call.

This guarantees the verbatim window the main LLM call saw matches what was written to history at the time of generation, and keeps the user-perceived latency bounded by one LLM round-trip.

### 3.3 Summarization model and prompt

- **Model:** the same model used for the main chat call — `openrouter/openai/gpt-oss-120b` via OpenRouter with Cerebras as the provider. We do not provision a separate "small" model; the per-turn marginal cost is small and gpt-oss-120b on Cerebras is fast enough that an extra call is not user-visible.
- **`response_format`:** none — the summarization call returns a free-form string (we extract the assistant's message content). This is a deliberate departure from the main call's structured output, because a single string is all we need.
- **Prompt:**

  ```
  You are folding old conversation history into a rolling summary.

  Existing summary (may be empty):
  <<<
  {{EXISTING_SUMMARY}}
  >>>

  Newly evicted message ([role] content):
  <<<
  {{EVICTED_MESSAGE}}
  >>>

  Rewrite the existing summary so it incorporates the newly evicted message.
  Keep it under 200 words. Preserve concrete facts (tickers traded, decisions made,
  user preferences expressed). Drop pleasantries and fillers. Output the new summary
  as plain prose with no preamble.
  ```

- `{{EXISTING_SUMMARY}}` is the current `chat_state.summary` (the literal string `(none yet)` is substituted when it is empty, so the model has something to anchor on).
- `{{EVICTED_MESSAGE}}` is `M_old` formatted as `[user] ...` or `[assistant] ...` — same role-tag convention as §2.4. If `M_old` is an assistant row with non-empty `actions`, the action summary is appended as `(actions: 2 trades, 1 watchlist add)` so the summary keeps a trace of what happened.

### 3.4 Token-budget rationale

10 verbatim + ≤200-word summary keeps every chat prompt O(1) in conversation length. With gpt-oss-120b's context limit far exceeding this and Cerebras's fast inference, the per-turn cost is dominated by the prompt itself, not the history. We do not implement token-count-based windowing in v1.

---

## 4. Mock-mode response table

When `LLM_MOCK=true`, `client.py` delegates to `mock.respond(user_text: str) -> LLMResponse`. The function performs case-insensitive regex matching against `user_text.strip()` in the order listed below and returns the first match's response. The default fallback is taken only if no regex matches.

### 4.1 Determinism requirement

For a given `user_text`, `mock.respond()` MUST produce **byte-identical** `LLMResponse` JSON across calls. The Integration Tester's Playwright assertions depend on this. Concretely:

- No timestamps, no random IDs, no clock reads in the mock output.
- Float quantities are formatted without trailing-zero noise (e.g., `5.0` and `5` parse identically through Pydantic; the **serialized form** the LLM Engineer cares about is whatever `LLMResponse(...).model_dump_json()` produces — that is deterministic for fixed inputs in Pydantic v2).
- The mock does NOT consult portfolio state, the price cache, or the database. It only depends on `user_text`.

### 4.2 Regex table

All patterns are matched case-insensitively (Python `re.IGNORECASE`) against `user_text.strip()`. Captures referenced by index:

| # | Regex | Captures | LLMResponse JSON (the value of `LLMResponse.model_dump()`) |
|---|---|---|---|
| 1 | `^buy\s+(\d+(?:\.\d+)?)\s+([A-Za-z]{1,5})\b` | `(1)` quantity, `(2)` ticker | `{"message": "Buying {Q} {TICKER}.", "trades": [{"ticker": "{TICKER}", "side": "buy", "quantity": {Q_FLOAT}}], "watchlist_changes": []}` |
| 2 | `^sell\s+(\d+(?:\.\d+)?)\s+([A-Za-z]{1,5})\b` | `(1)` quantity, `(2)` ticker | `{"message": "Selling {Q} {TICKER}.", "trades": [{"ticker": "{TICKER}", "side": "sell", "quantity": {Q_FLOAT}}], "watchlist_changes": []}` |
| 3 | `^add\s+([A-Za-z]{1,5})\s+(?:to\s+)?(?:my\s+)?watchlist\b` | `(1)` ticker | `{"message": "Adding {TICKER} to your watchlist.", "trades": [], "watchlist_changes": [{"ticker": "{TICKER}", "action": "add"}]}` |
| 4 | `^remove\s+([A-Za-z]{1,5})\b` | `(1)` ticker | `{"message": "Removing {TICKER} from your watchlist.", "trades": [], "watchlist_changes": [{"ticker": "{TICKER}", "action": "remove"}]}` |
| 5 | `(what'?s?\|tell me about)\s+my\s+portfolio` | — | `{"message": "Mock portfolio summary: you have positions; check the dashboard for details.", "trades": [], "watchlist_changes": []}` |
| 6 | `^(hi\|hello\|hey)\b` | — | `{"message": "Hello — I'm FinAlly (mock mode). I can buy/sell, manage your watchlist, or summarize your portfolio.", "trades": [], "watchlist_changes": []}` |
| 7 | (default — no match) | — | `{"message": "Mock mode: I received your message but only recognize buy/sell/add/remove/portfolio in mock mode.", "trades": [], "watchlist_changes": []}` |

Substitution rules:

- `{TICKER}` is the captured ticker uppercased.
- `{Q}` is the captured quantity exactly as the user typed it (e.g., `5` stays `5`, `5.5` stays `5.5`). This drives the `message` text only.
- `{Q_FLOAT}` is the captured quantity coerced to `float` (e.g., `5` → `5.0`, `5.5` → `5.5`). This is the JSON value Pydantic will see for `LLMTrade.quantity`.

### 4.3 Example pairings

| User text | Mock `LLMResponse.message` | Mock trades / watchlist_changes |
|---|---|---|
| `"Buy 10 AAPL"` | `"Buying 10 AAPL."` | `trades=[{ticker:"AAPL",side:"buy",quantity:10.0}]` |
| `"sell 2.5 nvda"` | `"Selling 2.5 NVDA."` | `trades=[{ticker:"NVDA",side:"sell",quantity:2.5}]` |
| `"Add PYPL to watchlist"` | `"Adding PYPL to your watchlist."` | `watchlist_changes=[{ticker:"PYPL",action:"add"}]` |
| `"Add PYPL to my watchlist"` | `"Adding PYPL to your watchlist."` | identical to above |
| `"Remove META"` | `"Removing META from your watchlist."` | `watchlist_changes=[{ticker:"META",action:"remove"}]` |
| `"What's my portfolio?"` | mock portfolio summary string | (none) |
| `"hello"` | mock greeting string | (none) |
| `"explain technical analysis"` | default fallback string | (none) |

### 4.4 What the Integration Tester can assume

- Sending `"Buy 10 AAPL"` produces a `ChatResponse` whose `actions[0]` is a `TradeActionOk` for AAPL buy 10 (assuming the user has enough cash — the mock LLM emits the trade, the executor runs the real trade path, and if cash is insufficient the action becomes a `TradeActionError`).
- Sending `"hello"` produces a `ChatResponse` with `actions == []`.
- The exact `message` strings above are stable across mock-mode runs. Tests may assert substring matches like `"Buying 10 AAPL"` in the chat panel.

---

## 5. Live-mode call wiring

> **Phase 2 instruction:** Before writing `client.py`, invoke the **cerebras-inference skill** in the Phase 2 session and follow its examples. The skill knows the exact LiteLLM call shape, provider-pinning syntax, and structured-output incantation for OpenRouter + Cerebras + gpt-oss-120b. This contract specifies the *behavior*; the skill specifies the *call*.

### 5.1 Library and model

- **Library.** LiteLLM (`litellm.completion(...)`), via OpenRouter.
- **Model.** `openrouter/openai/gpt-oss-120b`.
- **Provider routing.** Pin to Cerebras inference. The cerebras-inference skill specifies the exact `extra_body={"provider": {...}}` or equivalent payload OpenRouter expects to force Cerebras.
- **Auth.** `OPENROUTER_API_KEY` from environment (loaded by FastAPI from `.env` at the project root). LiteLLM picks it up automatically when set.

### 5.2 Structured output

- Pass `response_format=LLMResponse` (LiteLLM's Pydantic-class response-format support) so the provider returns JSON matching the `LLMResponse` schema.
- Parse the returned `choices[0].message.content` (a JSON string) into `LLMResponse` via `LLMResponse.model_validate_json(...)`.
- If parsing fails (provider returned malformed JSON despite structured output), `client.complete()` raises a `LLMResponseError`. `handler.handle_message()` catches it and returns a fallback `ChatResponse(message="Sorry, I couldn't process that response. Please try again.", actions=[])` — the user gets a graceful error and the request still returns 200 (see API_CONTRACT.md §5).

### 5.3 Environment validation at startup

- Wired in `backend/app/main.py`'s lifespan startup hook (owned by the Backend API Engineer; this contract specifies the *requirement* the API Engineer wires up).
- If `LLM_MOCK != "true"` and `OPENROUTER_API_KEY` is missing or empty, the startup hook **raises**, preventing the server from accepting traffic. This is a hard fail by design — a server that boots without an LLM key but accepts `/api/chat` traffic just produces 500s and confuses the user.
- If `LLM_MOCK == "true"`, no key check; the mock dispatcher does not call OpenRouter.
- `client.py` exposes a tiny `assert_ready()` function the lifespan hook calls. Keeping the check inside `client.py` keeps the env-var dependency localized.

### 5.4 Request shape (informative)

The exact call is what the cerebras-inference skill produces; the conceptual shape is:

```python
response = litellm.completion(
    model="openrouter/openai/gpt-oss-120b",
    messages=[
        {"role": "system", "content": system_prompt},  # from prompt.build_system_prompt()
        {"role": "user", "content": user_text},
    ],
    response_format=LLMResponse,
    extra_body={"provider": {"order": ["Cerebras"]}},  # exact key per the skill
    temperature=0.2,  # low but not zero: still useful chat variation, low trade-action noise
    max_tokens=1024,
)
```

`temperature` and `max_tokens` are starting points; the LLM Engineer may tune in Phase 2 based on observed behavior, but the cerebras-inference skill's defaults take precedence if they conflict.

---

## 6. Executor error packaging

`executor.apply(llm_response, user_id="default") -> list[ChatAction]` applies the LLM's requested mutations and returns the resolved actions list. The list is then attached to the `ChatResponse` and persisted as the `chat_messages.actions` JSON for the assistant row.

### 6.1 Ordering

Trades are applied first, in the order they appear in `llm_response.trades`. Watchlist changes are applied second, in the order they appear in `llm_response.watchlist_changes`. The returned `actions` list preserves this order: all trade actions, then all watchlist actions. This is the order API_CONTRACT.md §5 documents.

### 6.2 Trade error packaging

For each `LLMTrade` in `llm_response.trades`:

1. Call `portfolio.execute_trade(ticker, side, quantity, user_id)` (the same code path `POST /api/portfolio/trade` uses; acquires the per-user `asyncio.Lock`, validates, computes fill at the latest `PriceCache` value, writes DB).
2. On success: append a `TradeActionOk` with `fill_price` and `cash_after` from the trade-path return value.
3. On the following exceptions, append a `TradeActionError` (do NOT re-raise):

   | Exception | `error` code | `error_message` template |
   |---|---|---|
   | `InsufficientCashError(need, have)` | `insufficient_cash` | `f"Need ${need:,.2f} but only ${have:,.2f} available."` |
   | `InsufficientSharesError(ticker, have, want)` | `insufficient_shares` | `f"You hold {have} shares of {ticker}, can't sell {want}."` |
   | `UnknownTickerError(ticker)` | `unknown_ticker` | `f"{ticker} not recognized."` |
   | `InvalidQuantityError(quantity)` | `invalid_quantity` | `f"Quantity must be positive; got {quantity}."` |

4. Any other exception: **re-raise**. It becomes a 500 from `/api/chat` (per API_CONTRACT.md §1.3). The executor does not swallow unknown failures — they indicate a backend bug that should be visible, not silently logged as a user-facing error.

> The four-error set above is the universe of "expected failure" trade exceptions. The first three are the canonical error codes from API_CONTRACT.md §1.4. `invalid_quantity` is a new code introduced here for the chat path — see §8 for the flag to the orchestrator. The HTTP trade endpoint rejects negative / zero quantities at Pydantic validation (422 `validation_error`), so this code only surfaces inside `actions[]`.

### 6.3 Watchlist error packaging

For each `LLMWatchlistChange` in `llm_response.watchlist_changes`:

1. Call `watchlist.add(ticker, user_id)` or `watchlist.remove(ticker, user_id)`.
2. On success: append a `WatchlistActionOk`.
3. On the following exceptions, append a `WatchlistActionError`:

   | Exception | `error` code | `error_message` template | When |
   |---|---|---|---|
   | `TickerAlreadyInWatchlistError(ticker)` | `ticker_already_in_watchlist` | `f"{ticker} is already in your watchlist."` | LLM emits `add` for a ticker already present. |
   | `NotInWatchlistError(ticker)` | `not_in_watchlist` | `f"{ticker} is not in your watchlist."` | LLM emits `remove` for a ticker not present. |
   | `InvalidTickerError(ticker)` | `invalid_ticker` | `f"{ticker} is not a valid ticker symbol."` | LLM emits a ticker that fails the `^[A-Z]{1,5}$` regex post-uppercasing (rare — Pydantic validation should catch it, but a defensive net). |

4. Any other exception: re-raise (same 500 rule as trades).

### 6.4 The LLM's `message` is immutable post-generation

`handle_message()` does NOT edit `llm_response.message` after executor runs, even when one or more actions failed. The LLM's prose was written before validation ran and cannot know which actions failed. The frontend renders failures inline by reading `actions[]` — that is the contract surface for "what actually happened."

This means a user can see a confusing pair like:

> **FinAlly:** "Buying 50 TSLA and 10 AAPL."
> *(action card: TSLA buy 50 failed — insufficient cash)*
> *(action card: AAPL buy 10 — filled at $192.34)*

That is the intended UX and is documented in PLAN.md §9 "Trade Execution & Validation".

### 6.5 Persisting `actions`

After the executor returns, `handler.handle_message()`:

1. Writes the user message row to `chat_messages` (role=`user`, actions=`NULL`).
2. Writes the assistant message row to `chat_messages` (role=`assistant`, actions = `json.dumps([action.model_dump() for action in actions])`).
3. **Storage form:** when `actions` is empty, the column stores the literal string `'[]'` (not `NULL`). This means `json.loads(row.actions)` always yields a list when `role = 'assistant'`. The API layer's normalization on read (`NULL` → `[]`, `[]` → `[]`) still applies and remains a defensive net.
4. Returns the `ChatResponse(message=llm_response.message, actions=actions)`.

This satisfies API_CONTRACT.md §5's invariant that the wire form is always `[]`, never `null`, on assistant turns.

---

## 7. End-to-end flow

```
HTTP POST /api/chat  {"message": "Buy 10 AAPL"}
        │
        ▼
  api/chat.py  ──validates body (max 4000 chars)──►  handle_message(user_text, user_id="default")
                                                              │
                                                              │ 1. Load portfolio context (cash, positions, watchlist) ◄── reads portfolio + watchlist + PriceCache
                                                              │ 2. Load chat_state.summary + last 10 messages from chat_messages
                                                              │ 3. system_prompt = build_system_prompt(portfolio_ctx, summary, verbatim_history, new user_text)
                                                              │
                                                              │ 4. if LLM_MOCK == "true":
                                                              │       llm_response = mock.respond(user_text)
                                                              │    else:
                                                              │       llm_response = client.complete(system_prompt, user_text)   ◄── LiteLLM → OpenRouter → Cerebras → gpt-oss-120b
                                                              │       (response_format=LLMResponse → parsed via Pydantic)
                                                              │
                                                              │ 5. actions = executor.apply(llm_response, user_id)                ◄── calls portfolio.execute_trade + watchlist.add/remove
                                                              │      • trades first, then watchlist_changes
                                                              │      • per-call exceptions → ChatAction(status="error")
                                                              │      • unknown exceptions → re-raise (becomes 500)
                                                              │
                                                              │ 6. Persist:
                                                              │      chat_messages (role=user,    content=user_text,             actions=NULL)
                                                              │      chat_messages (role=assistant, content=llm_response.message, actions=json.dumps(actions))
                                                              │
                                                              │ 7. Return ChatResponse(message=llm_response.message, actions=actions)
                                                              │
                                                              │ 8. (fire-and-forget after return)  if chat_messages count > 10:
                                                              │       summarizer.fold_oldest(user_id)       ◄── second LLM call, free-form string
                                                              │
        ◄──────────────────────────────────────────────────────┘
  api/chat.py  ──serializes ChatResponse──►  HTTP 200  {"message": "...", "actions": [...]}
```

Notes:

- Step 8 runs **after** the response has been returned to the caller so the user does not wait on summarization. Implementation in Phase 2 may use `BackgroundTasks` from FastAPI or a small `asyncio.create_task` shim; either is acceptable so long as the user-perceived latency stays at one LLM round-trip.
- The lock acquired in step 5 (per-user `asyncio.Lock` in the trade path) is held only during `execute_trade()`, not across the whole chat handler. Concurrent `/api/portfolio/trade` calls are still serialized correctly against chat-triggered trades because both go through `portfolio.execute_trade()`.
- The same `handle_message()` function is called by `/api/chat`; there is no other entry point. Future surfaces (e.g. a CLI) would import it directly.

---

## 8. Open ambiguities / flags for the orchestrator

These are items where this contract chose conservatively but the orchestrator may want to re-affirm before Phase 2 dispatch:

1. **New error code `invalid_quantity` inside `actions[]`.** API_CONTRACT.md §1.4 enumerates the chat-path `error` codes as `insufficient_cash`, `insufficient_shares`, `unknown_ticker`. This contract adds `invalid_quantity` for the case where the LLM emits a non-positive quantity that escapes Pydantic validation (defensive net). If the orchestrator wants strict alignment with API_CONTRACT.md §1.4, drop the code and let Pydantic's `quantity: float = Field(..., gt=0)` reject the trade entirely at the structured-output parse step. Decision: keep the code, flag here.
2. **New watchlist error codes `ticker_already_in_watchlist`, `not_in_watchlist`, `invalid_ticker` inside `actions[]`.** API_CONTRACT.md §1.4 enumerates these for the *HTTP* error-envelope path but does not explicitly extend them to `actions[]` entries. This contract reuses the same machine codes for symmetry (one renderer for both surfaces). If the orchestrator prefers chat-only failure modes to use a smaller universe, narrow this set. Decision: reuse the existing codes.
3. **Storage form for empty `actions`.** SCHEMA.md §3 permits either `NULL` or `'[]'` and defers to the LLM Engineer. This contract picks `'[]'` for assistant rows with no actions so `json.loads(row.actions)` is uniform for `role='assistant'`. User rows still use `NULL` (per SCHEMA.md §1.7). The API layer's read-side normalization (`NULL` → `[]`) is retained as a defensive net.
4. **Summarization model = main chat model.** Using gpt-oss-120b for summarization is heavier than necessary but avoids provisioning a second model. The orchestrator may want to swap to a cheaper / smaller model later; the swap is local to `summarizer.py`.
5. **Mock-mode `"hello"` is matched.** API_CONTRACT.md does not specify mock greeting behavior. Added because Playwright tests benefit from a no-side-effect "warm-up" message that exercises the chat path without touching portfolio state. Flag here in case the Integration Tester wants a different default.
6. **`mock.respond()` ignores portfolio state.** Even for `"what's my portfolio"`, the mock emits a fixed string rather than rendering live portfolio numbers. This keeps E2E assertions byte-stable; the cost is the mock-mode "portfolio summary" is not actually a summary. Flag in case the Integration Tester wants a richer mock that injects portfolio totals.

---

## 9. Phase 2 implementer checklist (informative)

When Phase 2 starts, the LLM Engineer should:

- [ ] Paste the `schemas.py` from §1 into `backend/app/chat/schemas.py`.
- [ ] Invoke the **cerebras-inference skill** to scaffold `client.py` (LiteLLM + OpenRouter + Cerebras + gpt-oss-120b + `response_format=LLMResponse`).
- [ ] Write `backend/app/chat/system_prompt.py` as the literal `TODO(user)` block from §2.2.
- [ ] Write `prompt.py` per §2.
- [ ] Write `mock.py` implementing the §4 regex table.
- [ ] Write `summarizer.py` per §3.
- [ ] Write `executor.py` per §6.
- [ ] Write `handler.py` per §7 (`handle_message()` orchestration).
- [ ] Add a `router` in `__init__.py` that the Backend API Engineer mounts in `main.py`; the route delegates to `handle_message()`.
- [ ] Unit tests in `backend/tests/chat/` for: schemas (validation), prompt (assembly + JSON-schema slot), mock (every row in §4.2 + determinism check), summarizer (overflow trigger, retry-on-error), executor (every error code in §6.2 and §6.3, ordering), handler (end-to-end mock + persistence).
- [ ] Test that `SYSTEM_PROMPT_VOICE` still contains `TODO(user)` at the end of Phase 2.
