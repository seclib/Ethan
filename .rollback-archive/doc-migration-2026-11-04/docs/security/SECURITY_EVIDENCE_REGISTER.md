# Security Evidence Register — ETHAN

## VERIFIED
- Authentication by JWT middleware: `interfaces/api/auth.py::auth_middleware`
- RBAC permission check: `interfaces/api/auth.py::require_permission`
- Admin role gate: `interfaces/api/routers/security.py::_require_admin`
- Admin updates: `interfaces/api/routers/security.py::update_user`
- Admin deletion: `interfaces/api/routers/security.py::delete_user`
- starter account SQL: `deploy/postgres/migrations/003_create_users_table.sql`
- starters in init: `deploy/postgres/init.sql`
- cookie next dynamic secure: `interfaces/webui/src/app/api/[...path]/route.ts::cookieOpts`
- WebSocket no auth observed: `interfaces/api/routers/realtime.py::websocket_endpoint`
- terminal WebSocket auth pattern: `interfaces/api/routers/terminal.py::_authorize_ws`
- rate limiter: `interfaces/api/rate_limit.py`
- resource upload limit: `interfaces/api/routers/projects.py::upload_project_document`
- API key manager: `core/auth/api_keys.py`

## INFERRED
- revocation current function impossible without `token_version`.
- websocket unauthenticated access grants broad NATS subjects.
- API key ownership not fully enforced.
- user supplied `user` can cross ownership.

## UNKNOWN
- full historical secret scan all refs.
- WebSocket protocol encryption and origin policy in VPS.
- all internal event subjects.
- all routes with internal ACLs.
- complete repository history.
- dynamic generated artifacts.
- operational backup restore.

## FIXED / Verified partially
- Docker `ethan-api` restart corrected to `no`.
- WebUI cookie Secure behavior corrected for HTTP/HTTPS.
- login form no autocapitalize/autocorrect hardened.
- logout cookie deletion enriched.
- menus and routes Frame/Odin and locale update.
- E2E unit tests partial because browsers missing.
