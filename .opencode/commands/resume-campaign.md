---
description: Recover the latest campaign state and identify the next authorized action
---

Resume an ETHAN engineering campaign from durable memory.

Steps:
1. Record Git branch, HEAD, and working tree status.
2. Read `AGENTS.md` and `Obsidian/AGENTS.md`.
3. Read `Obsidian/Operational-Memory/PROJECT_STATE.md`, `DECISIONS.md`, `TASKS.md`, `BLOCKERS.md`.
4. Find the active campaign report (under Obsidian or docs) and identify the last verified state, completed steps, and blockers.
5. Cross-check claims against the actual repository and tests; treat old reports as not proof of current functionality.
6. List the next authorized action(s) only — do not expand scope beyond the campaign authorization.
7. Report any pre-existing modifications that must be preserved.

Do not start implementation unless the user explicitly authorizes it. Do not commit or push.

Campaign: $ARGUMENTS
