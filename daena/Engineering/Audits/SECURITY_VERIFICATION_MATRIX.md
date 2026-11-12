# Security Verification Matrix — ETHAN

| Control | Evidence source | Status | Validation method |
|---|---|---|---|
| User login via JWT | `interfaces/api/main.py`, `interfaces/api/auth.py` | VERIFIED | HTTP integration test |
| RBAC permissions | `core/auth/__init__.py`, `interfaces/api/auth.py::require_permission` | VERIFIED | unit tests matrix |
| Admin route gate | `security.py::_require_admin` | VERIFIED | route tests |
| TOTP | `core/auth/totp.py`, security router | VERIFIED | 2FA unit/API tests |
| Session revocation | no visible token version store | PARTIAL / INFERRED | token lifecycle tests |
| WebSocket auth | `interfaces/api/routers/realtime.py` | VULNERABLE | unauthorized connection test |
| API key scopes | `core/auth/api_keys.py::validate_key` | VERIFIED code | API tests |
| API keys ownership | router + manager | PARTIAL | list/revoke tests |
| Resource ownership | `projects/__init__.py`, `state/chats.py` | OPTIONAL | cross-user IDOR tests |
| Audit events | `audit_log` schema and API integration | INFERRED | audit tests |
| Secret redaction | security tests | FIXED / VERIFIED | redaction tests |
| Docker and deployment | `docker-compose*.yml` | VERIFIED config | compose and daemon policy tests |
| Public repo baseline | `.gitignore`, docs, scanner | INCOMPLETE | full-history scan |

## Acceptable evidence

No control is marked `FIXED` if implementation is merely described but not executed successfully.

Verification must include security-relevant and failed tests as data.

## Phase 01 findings

- Git supply-chain scan started but all refs not completed.
- Dependency scan limited; no Dependabot configured.
- CI uses immutable actions not SHA-pinned.
- Docker images use mutable tags.
- Public release requires allowlist-based publish due local artifacts.
- Trivy only warning mode.
