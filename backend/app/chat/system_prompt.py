"""User-authored voice block concatenated into the FinAlly system prompt.

This file is intentionally left as a TODO(user) stub at the end of Phase 2.
The LLM Engineer MUST NOT fill in the voice text. The orchestrator pauses
Phase 3 to surface this file to the user for editing.

See LLM_CONTRACT.md §2.2.
"""

SYSTEM_PROMPT_VOICE = """
TODO(user): 5-10 lines describing how FinAlly should *talk*.
- How proactive? (suggest trades unprompted, or wait to be asked?)
- How risk-averse? (warn before risky trades, or just execute?)
- Tone? (terse trader, friendly explainer, dry institutional?)
- Catchphrases or absolutely-not phrases?
This block is concatenated into the system prompt assembled by build_system_prompt().
""".strip()
