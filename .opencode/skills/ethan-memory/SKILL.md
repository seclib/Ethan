---
name: ETHAN Memory Protocol
description: Retrieve and capitalize ETHAN technical memory in Obsidian using the ECLL loop; use at the start of any significant ETHAN task
---

## Purpose

Use the canonical Obsidian knowledge base at `/home/fatsio/AI/Ethan/Obsidian` as persistent engineering memory. Never assume a task starts from zero.

## At task start (RETRIEVE)

Read in order:
1. Root `AGENTS.md`
2. `Obsidian/AGENTS.md`
3. `Obsidian/Operational-Memory/PROJECT_STATE.md`
4. `Obsidian/Operational-Memory/DECISIONS.md`
5. `Obsidian/Operational-Memory/TASKS.md`
6. `Obsidian/Operational-Memory/BLOCKERS.md`

Then targeted search:
- `Obsidian/Knowledge/Architecture/` for models and schemas
- `Obsidian/Knowledge/` for technical docs
- `Obsidian/Archives/` for raw history (treat as evidence of attempts, not current state)
- `_meta/` for migration reports and proofs

## Rules

- Use targeted retrieval; do not load the whole vault.
- Compare docs with actual code and tests; code wins on contradiction.
- Preserve failed/superseded attempts; never rewrite history.
- Distinguish verified facts, hypotheses, and recommendations.
- Never archive secrets, tokens, passwords, or personal data.

## At task close (CAPITALIZE)

- Update `PROJECT_STATE.md` (current state, next task, blockers).
- Update `DECISIONS.md` only for decisions actually validated.
- Create/update a dated session note recording changes, tests, results, hypotheses, unfinished tasks.
- Label validation status: PROPOSED / IMPLEMENTED / TESTED / RUNTIME_VALIDATED / E2E_VALIDATED / PARTIAL / BLOCKED.
- Add Obsidian wikilinks where appropriate.
