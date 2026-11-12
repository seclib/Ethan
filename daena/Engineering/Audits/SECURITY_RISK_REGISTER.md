# Security Risk Register — ETHAN

| ID | Risk | Classification | Severity | Priority | Owner | Validation |
|---|---|---|---|---|---|---|
| R1 | Starter admin credentials predictable | VERIFIED | Critical | 1 | security | login enabled without rotation |
| R2 | Unauthenticated WebSocket exposing NATS subjects | VERIFIED | critical | 1 | api/WebUI | `realtime.py` inspection |
| R3 | No centralized token revocation | INFERRED | high | 2 | auth | middleware lookup |
| R4 | Optional resource ownership | INFERRED | high | 2 | core state | project/chat managers |
| R5 | API key ownership not fully enforced | PARTIALLY VERIFIED | high | 2 | API/auth | routes + manager |
| R6 | Global agent/tool context and cross-user leakage | INFERRED | high | 2 | core orchestration | execution inspection |
| R7 | Public repository history and untracked artifacts | partially verified | medium | 3 | DevSecOps | git status + ignore |
| R8 | Default password values documented or suggested | VERIFIED | high | 2 | docs | docs references |
| R9 | Security browser fixture and mobile validation | UNKNOWN | medium | 4 | WebUI | unavailable Playwright browser binary in environment |
| R10 | Network direct API identity and CORS bypass | INFERRED | high | 2 | API | auth/cors config |

## Notes

- Classification `UNKNOWN` means not yet audited at implementation proof level.
- No risk is remediated by inventory alone.

## Phase 01 findings

- Git supply-chain scan started but all refs not completed.
- Dependency scan limited; no Dependabot configured.
- CI uses immutable actions not SHA-pinned.
- Docker images use mutable tags.
- Public release requires allowlist-based publish due local artifacts.
- Trivy only warning mode.

## Reconciliation append 
### Highest priority
1. full historical all-refs Gitleaks
2. API key principal derivation
3. WebSocket auth and topic scopes
4. token version
5. ownership
6. bootstrap state
