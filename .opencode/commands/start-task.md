---
description: Retrieve context and prepare a technically grounded task plan for ETHAN
---

You are working on ETHAN OS. Follow the ETHAN ECLL protocol.

Before planning:
1. Record Git branch and HEAD; check working tree status.
2. Read `AGENTS.md`, then `Obsidian/AGENTS.md`.
3. Read `Obsidian/Operational-Memory/PROJECT_STATE.md`, `DECISIONS.md`, `TASKS.md`, `BLOCKERS.md`.
4. Retrieve relevant architecture docs, ADRs/ESRs/ASRs, prior investigations, incidents, and runbooks under `Obsidian/` using targeted search — do not load the whole vault.
5. Compare historical docs with actual source code and runtime evidence.

Then produce a concise task plan:
- Objective and scope
- Files likely to change (and confirm they are authorized)
- Existing implementations to reuse (avoid duplicates)
- Risks and blockers
- Verification steps (tests, boundary checks)
- What must be recorded in Obsidian at close

Do not modify code during this step. Preserve all pre-existing Git modifications. Never reset/clean/stash.

Task: $ARGUMENTS
