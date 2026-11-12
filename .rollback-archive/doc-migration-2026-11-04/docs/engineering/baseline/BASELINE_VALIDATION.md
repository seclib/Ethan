# ETHAN — Baseline Validation

Statut de chaque affirmation majeure : CONFIRMÉ / PARTIEL / NON VÉRIFIÉ / NON IMPLÉMENTÉ.

## 1. Constats vérifiés

| Affirmation | Statut | Preuve |
|---|---|---|
| WebUI accessible sur 3001 après correction config | CONFIRMÉ | health: `curl -s http://localhost:3001` → HTTP 307 redirect; API proxy login → 200 |
| APIs service HROT opérationnelles | CONFIRMÉ | tests `tests/test_http_service_*` et smoke terminal |
| JWT/RBAC trusted principal paths | CONFIRMÉ | `interfaces/api/auth.py`, tests `test_http_*principal*` |
| Service principal persisted in PG | PARTIEL | `core/auth/service_identities.py`, `CoreRecordStore`, service tests avec env `DATABASE_URL` |
| HROT durable store | PARTIEL | `core/hrot/durable.py` = PG + JSONL selon config |
| AgentManager untouched | CONFIRMÉ | scope restrictions respectées par tests cibles |
| `fetch_user_record` DB-gated | PARTIEL | DB access reads from `DATABASE_URL` or `.env`, fallback in test |

## 2. Constats corrigés

- WebUI login ENOTFOUND: caused by missing `.env`, now fixed with two variables and API restart in same network.
- `tests/conftest.py` compatibility for ASGI; re-established.
- target test state isolation through `tests/conftest.py` clear HROT approvals.
- HROT storage atomic behavior validated after DB and async checks.

## 3. Incertitudes restantes

- Aucun E2E UI Playwright login test dans cette baseline.
- L'échec terminal WS reste non expliqué.
- Identification multi-instance depends on env layer and volumes.
- ADR/ESR additions not consolidated.
- WebUI cleanup creates untracked test files; not removed.

## 4. Résultats réconciliés

| Commande | Contexte | Résultat |
|---|---|---|
| `.venv/bin/pytest -q tests/test_http_service_provisioning.py tests/test_http_service_rotation.py tests/test_http_service_token_lifecycle.py tests/test_http_service_identity.py tests/test_http_service_audit.py tests/core/test_service_identity.py` | local avec .env parsed from tests | `48 passed, 1 warning` |
| `.venv/bin/pytest -q interfaces/api/tests/` | sans env DATABASE_URL dans service tests; DB baseline host accessible | `1 failed, 313 passed, 1 skipped, 1 warning` |
| exact WebUI login via port 3001 | runtime compose | `200` on proxy login; redirect 307 at entry |

The counts differ because different test files, mocks and environmental state. Use target service set, then full suite, then terminal test separately rather than treating any single report as universal.

## 5. Priorités corrigées

- P0: terminal WS simulation; why it unexpectedly fails.
- P1: consistent and reproducible config + test isolation.
- P2: HROT PostgreSQL migration + ADR reconciliation.
- P3: documentation ahead-of-implementation gaps.

## 6. ADR/ESR status

- Many ADR/ESR docs refer to decisions in progress; keep as reference.
- No destructive reorganization done.
- Current baseline docs are additive, not authoritative.

## 7. Trois à cinq lots de travail (pas encore commencés)

1. Fix and isolate terminal WebSocket.
2. HROT PostgreSQL authority integration with migration tests.
3. Restore reproducible Docker network and env.
4. Add E2E login tests WebUI.
5. Consolidate ADR indexes after release.

## Verdict : **BASELINE VALIDATED OF SIX LOT DOCUMENTS, UNDER RESERVE**

Confidence: medium-high for targeted service tests, medium for full integration.
