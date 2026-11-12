---
description: Review changes, run relevant tests, and capitalize technical knowledge in Obsidian
---

Close an ETHAN task with full validation and knowledge capitalization.

Steps:
1. Review the complete Git diff (staged + unstaged + untracked) and confirm no unauthorized files changed.
2. Run relevant tests and boundary checks; record actual results. Distinguish pre-existing failures from regressions.
3. Verify no secrets, tokens, or personal data were introduced.
4. Update Obsidian Operational-Memory: `PROJECT_STATE.md`, `DECISIONS.md` (only validated decisions), and a dated session note under `Obsidian/.../sessions/YYYY-MM-DD.md` with changes, tests, results, hypotheses, unfinished tasks.
5. Preserve historical records; use wikilinks where appropriate.
6. Clearly label validation status: PROPOSED / IMPLEMENTED / TESTED / RUNTIME_VALIDATED / E2E_VALIDATED / PARTIAL / BLOCKED.
7. Do not commit or push unless explicitly requested. Do not perform destructive Git operations.

Task: $ARGUMENTS
