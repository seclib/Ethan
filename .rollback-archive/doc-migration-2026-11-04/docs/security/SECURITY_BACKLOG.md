# ETHAN Security Backlog

## Existing work already present

- Authentication and RBAC.
- TOTP.
- Password reset.
- API-key management.
- Security router.
- Audit and redaction.
- Dockerized runtime.
- CORS restrictions.
- Cookie secure behavior corrected for HTTP/HTTPS.
- Config/secrets separation.
- Provider default atomicity migration.
- Knowledge collection grants partly implemented.

## Open work

### Critical

- WebSocket authentication and scope enforcement.
- Bootstrap one-time finalization and starter password retirement.
- JWT revocation / session version.
- Ownership enforcement across HTTP and tasks.
- API principal binding and API key ownership.
- Deployment and public release hardening.

### High

- Branch and history cleanup references.
- QA and test coverage.
- Frontend mobile cookie validation.
- Docs and runbook synchronization.

### Medium

- Chat and Project ownership constraints.
- Knowledge resource granularity.
- CLI direct DB reduction.
- Admin boundary uniformization.
- Logs and diagnostics hardening.

### Low

- Naming and policy ADR/ESR additions.
- Demo and Pages.

## Dependency notes

- Security Gate must precede WebUI-only changes.
- Bootstrap Security must precede outward production exposure.
- Resource ownership and tests must precede agent support.

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
