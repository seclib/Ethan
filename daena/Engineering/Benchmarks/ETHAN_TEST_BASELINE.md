# ETHAN — Test Baseline

## Commandes exactes et résultats (2026-11-02)

```bash
.venv/bin/pytest -q tests/test_http_service_provisioning.py tests/test_http_service_rotation.py tests/test_http_service_token_lifecycle.py tests/test_http_service_identity.py tests/test_http_service_audit.py tests/core/test_service_identity.py
```
Résultat : **59 passed, 1 warning**

```bash
.venv/bin/pytest -q tests/test_http_trusted_principal.py tests/test_http_trusted_principal_integration.py tests/test_http_user_identity_fallback.py tests/test_http_principal_scope_admin.py tests/test_http_principal_fail_closed.py tests/test_config_persistence.py
```
Résultat : **50+ passed, 14 warnings**

```bash
.venv/bin/pytest -q interfaces/api/tests/
```
Résultat : **1 failed, 313 passed, 1 skipped, 1 warning**

Échec historique :
- `interfaces/api/tests/test_terminal_ws.py::test_terminal_authorized_is_accepted`
Cause : WebSocket Disconnect code 1000 simulation de session exited, indépendant du trusted principal.

## Classification

- Réussis (unit/service HTTP) : ~370.
- Echoué : terminal WS.
- Ignoré : skipped provider test maybe 1.
- Non reproductibles : flaky providers catalog appears in repeated full suite sometimes.

## Tests non exécutés

- UI lighthouse / visual tests (frontend package) non run dans ce lot.

## Règles de vérité

- Les tests de service auth/identity cross PostgreSQL sont réels.
- Les tests JSONL isolés ne constituent pas des preuves multi-instance.
- Les claims HROT/identity restent contractuels.
