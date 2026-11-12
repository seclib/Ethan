# Security Asset Inventory — ETHAN

## Assets

| Asset | Location | Type | Criticality | Owner |
|---|---|---:|---|---|
| User credentials | `users` PostgreSQL table | identity | Critical | API/auth |
| JWT tokens | issued by `interfaces/api/auth.py` | session | Critical | API |
| Refresh/session flows | `interfaces/api/main.py` | session | Critical | API |
| Admin starter account | `deploy/postgres/init.sql`, `003_create_users_table.sql` | identity/config | Critical | security |
| API keys | `core/auth/api_keys.py`, `interfaces/api/routers/api_keys.py` | credential | Critical | API/auth |
| Projects | `core/projects` | user-owned data | High | Core services |
| Conversations/messages | `core/state/chats.py` | user-owned data | High | Core state |
| Knowledge collections/docs | `core/knowledge/*` | user-owned/shared data | High | knowledge |
| Goals/tasks | `core/goals/manager.py` | user-owned execution | High | core runtime |
| API runtime | `interfaces/api/main.py` | gateway | Critical | integration |
| WebSocket bridge | `interfaces/api/routers/realtime.py` | realtime access | High | API |
| WebUI API proxy | `interfaces/webui/src/app/api/[...path]/route.ts` | proxy | High | WebUI |
| WebUI middleware | `interfaces/webui/src/middleware.ts` | route protection | High | WebUI |
| Docker services | `docker-compose*.yml` | infrastructure | High | deployment |
| Provider config | `llm_providers` / `ethan_config` | global configuration | High | providers/config |
| Audit system | `audit_log` and related | integrity/accountability | High | audit |
| Audit history | `CHANGELOG`, `docs/audit*`, ADR/ESR | traceability | Medium | docs maintainers |

## Important notes

- The current repository contains user data state and local generated artifacts, including WebUI build output `.next` in this working copy. They must never enter public release artifacts.
- Source assets are not inherently compromised. Exposed risk comes from deployment, branch pollution and historical secret exposure.
- User-facing features and service output are not separately isolated by a tenant model today.

Status: UNKNOWN / future P0 checks.
