# Security Roadmap — ETHAN

## Phase 0 — Baseline

- Asset inventory
- trust boundaries
- risk register
- verification matrix
- public release allowlist/denylist
- security charter

## Phase 1 — Authentication and sessions

- enforce session/token version
- reconcile WebSocket tokens
- make starter bootstrap lifecycle explicit
- revoke all sessions after critical changes

## Phase 2 — Resource authorization

- Pass user identity into all resources
- enforce ownership on every CRUD and execution path
- migrate persistence boundaries to real owner columns
- grow RBAC and permission matrix

## Phase 3 — Bootstrap and account security

- additive bootstrap state
- required rotation
- one-time token flow
- recompute legacy detection
- safe default account handling
- admin runbook

## Phase 4 — Realtime and API security

- WebSocket authentication
- topic scope
- subscription policy
- API key bindings
- rate limits
- audit coverage

## Phase 5 — Agent and tool isolation

- execution principal
- task scope
- tool scope
- workflow privilege reduction
- cross-user guards
- workspace security

## Phase 6 — Release and deployment

- actions pinning
- secret scanning
- public GitHub Pages isolation
- secret history review
- production exposure defaults

## Approach

Small, independent, testable phases.

ADR and ESR documents are introduced only after a verified design.

No destructive migration or general auth rewrite at this stage.
