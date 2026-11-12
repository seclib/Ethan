# Phase 01 — Runtime State Matrix

| State | Meaning verified? |
|---|---|
| declared | yes (discovery) |
| registered | yes (registry) |
| validated | yes (registry compliance) |
| available | yes as persisted state only; not runtime proof |
| unavailable | yes as persisted state only |
| lifecycle states | yes as managed state |
| docker started/healthy | service can report status, but not rechecked end-to-end |

## Important
Do not merge `available` with runtime execution. Use service health status and compose container state as separate proof.
