---
description: Investigate a problem using source code, tests, and historical knowledge
---

Investigate the reported issue methodically (ECLL: RETRIEVE → ANALYZE → COMPARE → PLAN → EXECUTE → EVALUATE → CAPITALIZE).

Steps:
1. Capture Git state (branch, HEAD, status) without modifying anything.
2. Search the codebase (src/, core/, runtime/, services/) for relevant symbols and call sites.
3. Check existing tests related to the area.
4. Search Obsidian (Operational-Memory, Knowledge, Archives) for prior attempts, incidents, and runbooks.
5. Reproduce or gather evidence (logs, runtime) when feasible; never claim validation not performed.
6. Distinguish verified facts, hypotheses, and recommendations.
7. Propose the smallest fix consistent with ETHAN architecture (Core-first; no duplicate managers/registries; HROT authority).
8. Identify regression tests needed.

Do not alter application behavior unless explicitly authorized. Preserve pre-existing modifications.

Issue: $ARGUMENTS
