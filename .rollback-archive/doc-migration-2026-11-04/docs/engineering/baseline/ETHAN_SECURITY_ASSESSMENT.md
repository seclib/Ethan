# ETHAN — Security Assessment

## 1. Statut

- Identités HUMAN / API_KEY / SERVICE / AGENT / SYSTEM defined in `core/auth/principal`.
- JWT par Bearer/cookie was introduced and principal build persisted where PostgreSQL configured.
- RBAC central via `core/auth/rbac`.
- TRUST-SERVICE and HROT additive gates as of 2.5.
- Audit and approvals present.
- Terminal WS is pending red-team/fail closed issue.

## 2. Risques observés

- JSONL HROT fallback remains possible in local mode.
- `fetch_user_record` falls back to JWT role only if the persistent user record is missing, which was narrowed after 2.4 but remains a compatibility compromise.
- Shared database secrets (`DATABASE_URL`) may be plaintext in `.env`; this has been excluded from reporting.
- WebUI depends on Docker DNS name `api`.

## 3. Garanties démontrées

- HUMAN JWT build now requires persistent active record or callback in test.
- API keys are server-owned from `CoreRecordStore`.
- service JWT keys are dedicated.
- HROT durable stores have fail-closed semantics.
- principal checks for admin use persistent RBAC roles when available.
- middleware is fail-closed for expired and invalid tokens.

## 4. Échec historique

- The terminal websocket test failure is not caused by security guards but by mock simulation.
- not treated as security regression.

## 5. Recommandations

- merge all admin gates to principal-based RBAC rather than only token payload role.
- require PostgreSQL HROT in production.
- add HROT transactional audit outbox later.
- avoid reliance on `.env` secrets interpolation manually.

