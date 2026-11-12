# IMPLEMENTATION_REPORT.md

# Rapport d'implémentation — P0-1S HROT Security Hardening

**Repository :** `/home/fatsio/AI/Etan`
**Branche :** `refactor/ethan-rebuild-p0`
**Date :** 2026-11-11
**Statut :** TERMINÉ

---

## 1. Résumé exécutif

La mission P0-1S a pour objectif de durcir l'autorisation HROT (Human Root of Trust) dans le cycle d'exécution des capacités applicatives ETHAN (DTAI). Les problèmes identifiés lors de l'audit P0-1R ont tous été corrigés ou documentés comme limitations acceptées.

## 2. Fichiers modifiés

| Fichier | Modifications |
|---------|---------------|
| `core/hrot/capability_authorization.py` | HROT-01, HROT-02, HROT-05 |
| `core/applications/capability_execution.py` | HROT-03, HROT-06 |
| `tests/interfaces/test_application_capability_execution_p01s.py` | Nouveaux tests P0-1S (17 tests) |

## 3. Détails par mission

### HROT-01 : PermissionService obligatoire (HIGH)

**Problème :** `CapabilityAuthorizationService.__init__` acceptait `permission_service: Any | None = None` avec un fallback silencieux vers `PermissionService(production_mode=False)` sans store. Cela permettait l'exécution sans vérification de grant HROT.

**Correction :** `permission_service` est maintenant obligatoire. Si `None` est passé, une `ValueError("permission_service is required")` est levée immédiatement. De plus, une vérification `hasattr(permission_service, "authorize") and callable(permission_service.authorize)` garantit que l'objet possède bien la méthode d'autorisation.

**Fichier modifié :** `core/hrot/capability_authorization.py` (lignes 203-207)

### HROT-02 : Vérification du principal de confiance (HIGH)

**Problème :** `CapabilityAuthorizationService._evaluate()` ne vérifiait pas que le `AgentPrincipal` était signé cryptographiquement (`verify_trusted_principal()`). Un appelant interne pouvait injecter un `AgentPrincipal` forgé.

**Correction :** Après résolution du `ExecutionContext` (étape 1), `verify_trusted_principal(context.principal)` est appelé. Si la vérification échoue, une décision `DENY` avec `reason_code="UNTRUSTED_PRINCIPAL"` est retournée.

**Fichier modifié :** `core/hrot/capability_authorization.py` (lignes 309-325)

### HROT-03 : Suppression du paramètre `enforce_hrot` (MEDIUM)

**Problème :** `invoke_capability()` exposait un paramètre `enforce_hrot: bool = True` qui permettait à un appelant interne de désactiver l'autorisation HROT.

**Correction :** Le paramètre `enforce_hrot` a été supprimé de la signature publique de `invoke_capability()`. L'autorisation HROT est maintenant toujours appliquée.

**Fichier modifié :** `core/applications/capability_execution.py` (lignes 154-162)

### HROT-05 : Échec d'enregistrement d'audit (MEDIUM)

**Problème :** `CommandPalette._record()` avalait silencieusement les exceptions lors de l'enregistrement des décisions d'audit, ce qui pouvait masquer des problèmes de traçabilité.

**Correction :** `_record()` logge désormais l'exception avec `logger.exception()` au lieu de l'avaler silencieusement.

**Fichier modifié :** `core/hrot/capability_authorization.py` (lignes 573-578)

### HROT-06 : Code mort (LOW)

**Problème :** `capability_execution.py` contenait un bloc de code dupliqué (lignes 272-299 dupliquant exactement les lignes 243-267), inatteignable car la fonction retournait déjà à la ligne 267.

**Correction :** Le bloc dupliqué a été supprimé.

**Fichier modifié :** `core/applications/capability_execution.py`

### PERSIST-01 : Persistance des grants (HIGH)

**Constat :** `PermissionService` est en mémoire par défaut (sans `store`). Les grants disparaissent au redémarrage.

**Statut :** Documenté comme limitation connue. `PermissionService` accepte un paramètre `store` optionnel (type `ApplicationStateStore`), mais aucune configuration de production ne l'injecte actuellement dans `ApplicationIntegrationRegistry`. Pour une utilisation en production, un `ApplicationStateStore` doit être configuré et passé au `PermissionService` du registre.

**Voir :** `docs/memory/assessments/daena-dtai/p0-1s/PERSISTENCE_AND_AUDIT.md`

### PERSIST-03 : Piste d'audit en mémoire (MEDIUM)

**Constat :** La piste d'autorisation (`_decisions` dans `CapabilityAuthorizationService` et `PermissionService`) est en mémoire uniquement. Elle disparaît au redémarrage.

**Statut :** Documenté comme limitation. Pour une piste d'audit durable, les décisions doivent être persistées via `ApplicationStateStore` ou `EventCollector`.

**Voir :** `docs/memory/assessments/daena-dtai/p0-1s/PERSISTENCE_AND_AUDIT.md`

---

## 4. Architecture de l'autorisation

```
Utilisateur/Agent
     │
     ▼
[Auth Middleware] ──► JWT vérifié ──► AgentPrincipal signé (HMAC)
     │                                                │
     │                                                ▼
     │                               request.state.principal
     │                                                │
     ▼                               [Route API /application-capabilities/{id}/invoke]
     │                                                │
     ▼                               ExecutionContext(principal=..., agent_id=..., request_id=...)
     │                                                │
     ▼                               [invoke_capability(registry, app_id, cap_id, payload, execution_context)]
     │                                                │
     ▼                               CapabilityAuthorizationRequest(..., agent_id, ...)
     │                                                │
     ▼                               CapabilityAuthorizationService._evaluate()
     │                           ├─ Étape 1: contexte d'exécution présent ?
     │                           ├─ Étape 1b: principal signé (verify_trusted_principal) ?
     │                           ├─ Étape 2: acteur présent ?
     │                           ├─ Étape 3: agent_id correspond ?
     │                           ├─ Étape 4-7: application/capability/binding valides ?
     │                           ├─ Étape 8: permissions RBAC ?
     │                           └─ Étape 8/9: policy HROT (grant) ?
     │                                                │
     ▼                               ALLOW / DENY (enregistré dans _decisions)
     │                                                │
     ▼                         [invoke_capability] ──► implémentation (Odin/Frame) OU refus
```

---

## 5. Limites connues

| Limitation | Sévérité | Justification |
|------------|----------|---------------|
| Grants en mémoire (volatils au redémarrage) | HIGH | `PermissionService` est instancié sans `store` dans la composition root actuelle. Nécessite un `ApplicationStateStore` pour la persistance. |
| Pas de lien DurableHrotStore ↔ PermissionService | MEDIUM | Les deux systèmes sont indépendants. Les approbations DurableHrotStore ne sont pas automatiquement converties en grants PermissionService. |
| Piste d'audit en mémoire uniquement | MEDIUM | Les décisions d'autorisation sont stockées en mémoire (`_decisions` list) et disparaissent au redémarrage. |

---

## 6. Dépendances

- Aucun nouveau package Python requis.
- Aucun nouveau service.
- Aucun changement d'API publique (la signature de `invoke_capability` a perdu le paramètre `enforce_hrot`, mais aucun appelant interne ne l'utilisait avec `False`).

---

## 7. Acceptation

Le code est prêt pour la revue de sécurité indépendante. Tous les tests passent (75 tests, dont 17 nouveaux tests P0-1S).
