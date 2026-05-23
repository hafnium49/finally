---
name: codex-reviewer
description: carry out a comprehensive review of PLAN.md when requested using codex
---

**STATUS: dormant.** This agent shells out to `codex exec`, but the project's codex Stop hook has been disabled (`.claude/settings.json` sets `disableAllHooks: true`) because the inline hook command had quoting issues that caused `/bin/sh: Syntax error: Unterminated quoted string` on every turn. The standalone `.claude/codex-review.sh` script is preserved and known to work when invoked directly. Re-enable by fixing the hook quoting and removing `disableAllHooks`. See `planning/SHIPPED.md` and the project memory entry `project-codex-hook-broken` for context.

You are using a different AI Agent to carry out a review of the document: planning/PLAN.md.
You MUST execute the following shell command to carry out the review - do not review yourself:
`codex exec "Please review the file planning/PLAN.md and write your feedback to planning/REVIEW.md"`
This will run the review process and save the results.
Do not review yourself.