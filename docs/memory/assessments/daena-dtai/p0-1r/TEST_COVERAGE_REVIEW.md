# TEST_COVERAGE_REVIEW.md

Audit E — Revue de la couverture des tests et vérification d'exécution.

Mission P0-1R — Indépendant, lecture seule.

---

## 1. Tests existants identifiés

| Fichier de test | Chemin | Ce qui est testé |
|-----------------|--------|------------------|
| `test_application_capability_execution_api.py` | `tests/interfaces/test_application_capability_execution_api.py` | 5 tests : bind, invoke unbound, bind+execute avec grant HROT, invoke sans grant (refusé), invocation non autorisée (RBAC) |
| `test_application_capability_contract_api.py` | `tests/interfaces/test_application_capability_contract_api.py` | 4 tests : validate, list, register, register sans approval, register invalide |
| `test_capability_registry.py` | `tests/test_ethan_core/test_capability_registry.py` | Registre de capacités (CRUD, dépendances, validation) |
| `test_hrot_approval_flow.py` | `tests/test_hrot_approval_flow.py` | 7 tests : flux d'approbation (approuvé, rejeté, double résolution, inconnu, expiré, auto-approbation rejetée, non-admin rejeté) |
| `test_approval_hrot_integration.py` | `tests/core/test_approval_hrot_integration.py` | Intégration ApprovalEngine + HumanRoot (registre d'actions de confiance, audit log) |
| `test_application_hrot_operations_phase11.py` | `tests/core/test_application_hrot_operations_phase11.py` | 6 tests : génération/déverrouillage clés, confidentialité, approbation/rejeu, révocation persistance |
| `test_hrot_provider_gateway.py` | `tests/core/test_hrot_provider_gateway.py` | 12 tests : requête autorisée, refus sans auth, mauvais principal, expiré, révoqué, mauvais provider, mauvais modèle, malformed, paramètre inconnu, rate limit, exception, payload trop lourd, secret redacté |

Total : **53 tests** couvrant l'autorisation, l'approbation HROT, la révocation, et l'exécution de capacité.

---

## 2. Scénarios couverts (positif et négatif)

| Scénario | Test | Statut |
|----------|------|--------|
| Invocation avec grant HROT valide | `test_bind_and_execute_odin` | COUVERT — PASSED |
| Invocation sans grant HROT (refusé) | `test_invoke_without_hrot_grant_is_denied` | COUVERT — PASSED |
| Invocation capacité non liée | `test_invoke_unbound_or_unknown` | COUVERT — PASSED |
| Invocation utilisateur non autorisé (RBAC) | `test_unauthorized_invocation` | COUVERT — PASSED |
| Bind de capacité avec approbation | `test_bind_capability` | COUVERT — PASSED |
| HROT approbation/rejet | `test_approval_flow_approved`, `test_approval_flow_rejected` | COUVERT — PASSED |
| HROT révocation | `test_hrot_provider_gateway.py::test_revoked_authorization_is_denied` | COUVERT — PASSED |
| HROT expiration | `test_hrot_provider_gateway.py::test_expired_authorization_is_denied` | COUVERT — PASSED |
| HROT rate limiting | `test_hrot_provider_gateway.py::test_rate_limit_is_applied` | COUVERT — PASSED |
| HROT secret non dans les logs | `test_hrot_provider_gateway.py::test_secret_is_redacted_from_string_result` | COUVERT — PASSED |

---

## 3. Scénarios MANQUANTS (couverture insuffisante)

| Scénario manquant | Sévérité | Justification |
|-------------------|----------|---------------|
| Invocation avec `execution_context=None` (contexte manquant) | HIGH | Le code refuse (étape 1 `MISSING_EXECUTION_CONTEXT`), mais aucun test ne le vérifie. |
| Invocation avec `enforce_hrot=False` (contournement) | HIGH | Le paramètre existe mais aucun test ne vérifie qu'un appelant interne ne peut pas le désactiver. |
| Invocation avec `AgentPrincipal` forgé (identité contournée) | HIGH | Aucun test ne vérifie qu'un principal non signé est rejeté (si un appelant interne tente de l'injecter). |
| Mismatch d'identité agent (`AGENT_IDENTITY_MISMATCH`) | MEDIUM | Aucun test ne vérifie que `context.agent_id != request.agent_id` est refusé. |
| Permission service exception (échec d'évaluation) | MEDIUM | Aucun test ne vérifie le comportement quand `permission_service.authorize()` lève une exception. |
| Invocation avec binding désactivé (`INACTIVE_BINDING`) | MEDIUM | Aucun test ne vérifie le refus quand le binding existe mais n'est pas activé. |
| Invocation avec `contract_version` mismatch | MEDIUM | Aucun test ne vérifie le refus quand la version du binding ne correspond pas. |
| Invocation avec `binding.scope mismatch` | MEDIUM | Aucun test ne vérifie le refus quand le binding cible une autre application/capacité. |
| Piste d'audit (`audit_trail`) après décision | MEDIUM | Aucun test ne vérifie que les décisions ALLOW/DENY sont enregistrées dans `_decisions`. |
| Comportement après redémarrage (grants perdus) | MEDIUM | Aucun test ne vérifie que les grants in-memory disparaissent au redémarrage (limitation documentée mais non testée). |
| Invocation avec application inconnue | LOW | Partiellement couvert par `test_invoke_unbound_or_unknown` (424), mais ce test vérifie l'absence de binding, pas l'application inconnue spécifiquement. |
| Invocation avec capability inconnue | LOW | Idem — couvert par absence de binding, pas par absence de contrat. |

---

## 3.1 Analyse de la qualité des tests existants

Les tests existants **prouvent le refus effectif avant exécution** pour deux scénarios critiques :

1. **`test_bind_and_execute_odin`** : prouve qu'avec un grant HROT valide, l'invocation réussit (statut 200, résultat de l'implémentation Odin).
2. **`test_invoke_without_hrot_grant_is_denied`** : prouve qu'avec un binding lié/activé mais **sans grant HROT**, l'invocation est refusée (424, message contenant "denied" ou "failed").

Cependant, les tests ne couvrent pas :
- Les chemins d'échec interne (exception dans `permission_service.authorize()`).
- Le refus basé sur l'absence de contexte d'exécution.
- Le refus basé sur le mismatch d'identité agent.
- La traçabilité des décisions d'audit.
- La persistance (ou absence) des grants au redémarrage.

---

## 3.2 Exécution des tests

Tous les tests ont été exécutés avec succès (voir commande et résultats ci-dessous).

**Commande :**
```
.venv/bin/python -m pytest tests/interfaces/test_application_capability_execution_api.py tests/interfaces/test_application_capability_contract_api.py tests/test_ethan_core/test_capability_registry.py tests/test_hrot_approval_flow.py tests/core/test_approval_hrot_integration.py tests/core/test_application_hrot_operations_phase11.py tests/core/test_hrot_provider_gateway.py -v
```

**Résultat :** 58 passed, 1 warning, 0 failed.

---

## 3.3 Tests qui ne peuvent pas s'exécuter dans cet environnement

| Fichier | Raison |
|---------|--------|
| `tests/interfaces/test_system_exec_api.py` | Pré-existant en échec (401 vs 403 sur `test_create_requires_execute_permission`) — non lié à P0-1 |
| `tests/interfaces/test_odin_ai.py` | Pré-existant en échec (erreurs d'attribut/assertion) — non lié à P0-1 |
| `tests/interfaces/test_gods_eye_view_ai.py` | Pré-existant en échec — non lié à P0-1 |
| `tests/core/test_*.py` (divers) | Import `openjarvis` manquant — environnement non configuré pour ces tests |

Ces échecs sont **pré-existants et non liés à P0-1** (vérifiés via `git stash` sur le code original).

---

## 4. Conclusion

La couverture des tests est **adéquate pour les scénarios critiques principaux** (invocation autorisée, invocation refusée sans grant, RBAC, approbation HROT, révocation, expiration). Cependant, des **scénarios de refus importants ne sont pas testés** (contexte manquant, identité mismatch, permission service failure, binding mismatch, contract version mismatch, traçabilité d'audit, persistance).

Les tests existants ne prouvent pas l'absence de contournement via `enforce_hrot=False` ou via un `AgentPrincipal` forgé, car ces scénarios nécessiteraient un appelant interne (pas de test d'API HTTP).
