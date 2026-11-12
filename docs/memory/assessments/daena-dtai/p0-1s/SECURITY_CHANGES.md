# SECURITY_CHANGES.md

# Modifications de sécurité — P0-1S HROT Security Hardening

**Repository :** `/home/fatsio/AI/Ethan`
**Branche :** `refactor/ethan-rebuild-p0`
**Date :** 2026-11-11

---

## 1. Vue d'ensemble

Ce document résume les changements de sécurité apportés dans le cadre de la mission P0-1S (HROT Security Hardening). L'objectif est de renforcer l'autorisation des capacités applicatives externes (DTAI) dans ETHAN Core.

---

## 2. Modifications par fichier

### core/hrot/capability_authorization.py

#### HROT-01 : PermissionService obligatoire

**Avant :** `permission_service` était optionnel (`Any | None = None`). Si `None`, un `PermissionService(production_mode=False)` était créé silencieusement en mémoire, sans store, permettant l'exécution sans vérification de grant HROT.

**Après :** `permission_service` est obligatoire. Si `None`, une `ValueError("permission_service is required")` est levée. De plus, une vérification `hasattr(permission_service, "authorize") and callable(permission_service.authorize)` garantit que l'objet possède bien la méthode d'autorisation.

**Impact :** Empêche l'exécution sans vérification de grant HROT due à un `permission_service` manquant ou invalide.

#### HROT-02 : Vérification du principal de confiance

**Avant :** `CapabilityAuthorizationService._evaluate()` ne vérifiait pas que le `AgentPrincipal` était signé cryptographiquement. Un appelant interne pouvait injecter un `AgentPrincipal` forgé avec des permissions arbitraires.

**Après :** Après résolution du `ExecutionContext` (étape 1), `verify_trusted_principal(context.principal)` est appelé. Si la vérification échoue (signature HMAC invalide ou absente), une décision `DENY` avec `reason_code="UNTRUSTED_PRINCIPAL"` est retournée.

**Impact :** Empêche un appelant interne d'injecter un `AgentPrincipal` forgé avec des permissions élevées.

#### HROT-05 : Échec d'enregistrement d'audit

**Avant :** `_record()` avalait silencieusement les exceptions (`except Exception: pass`), masquant les échecs d'enregistrement de la piste d'audit.

**Après :** `_record()` logge l'exception avec `logger.exception("Failed to record authorization decision: %s", exc)` avant de retourner la décision. La décision est toujours retournée, mais l'échec d'enregistrement est visible dans les logs.

**Impact :** Améliore la traçabilité et la détectabilité des problèmes d'audit.

---

### core/applications/capability_execution.py

#### HROT-03 : Suppression du paramètre `enforce_hrot`

**Avant :** `invoke_capability()` exposait un paramètre `enforce_hrot: bool = True` qui permettait à un appelant interne de désactiver l'autorisation HROT.

**Après :** Le paramètre `enforce_hrot` a été supprimé de la signature publique. L'autorisation HROT est maintenant toujours appliquée pour chaque invocation de capacité externe.

**Impact :** Élimine un vecteur de contournement par un appelant interne.

#### HROT-06 : Suppression du code mort

**Avant :** `capability_execution.py` contenait un bloc de code dupliqué (lignes 272-299 dupliquant exactement les lignes 243-267), inatteignable car la fonction retournait déjà à la ligne 267.

**Après :** Le bloc dupliqué a été supprimé. Le fichier est passé de 299 à 267 lignes.

**Impact :** Améliore la lisibilité et la maintenabilité. Aucun impact fonctionnel.

---

## 3. Archi­tecture de l'autorisation après modification

```
Appelant (API/CLI/Interne)
     │
     ▼
[Auth Middleware] ──► JWT vérifié ──► AgentPrincipal signé (HMAC-SHA256)
     │                                                │
     │                                                ▼
     │                               request.state.principal
     │                                                │
     ▼                               [Route API invoke_capability]
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

## 7. Tests de sécurité

17 nouveaux tests ont été ajoutés dans `tests/interfaces/test_application_capability_execution_p01s.py` :

| Test | Ce qui est vérifié |
|------|-------------------|
| `test_authorization_service_requires_permission_service` | `CapabilityAuthorizationService` lève `ValueError` si `permission_service` est `None` |
| `test_authorization_service_accepts_permission_service` | `CapabilityAuthorizationService` accepte un `PermissionService` valide |
| `test_authorization_rejects_forged_principal` | Un `AgentPrincipal` forgé (non signé) est refusé |
| `test_authorization_accepts_signed_principal` | Un `AgentPrincipal` signé passe la vérification de signature |
| `test_authorization_rejects_missing_principal` | Un contexte sans `agent_id` est refusé |
| `test_authorization_rejects_binding_mismatch` | Un `binding_id` différent du binding du registre est refusé |
| `test_authorization_rejects_agent_identity_mismatch` | Un `agent_id` différent du `context.agent_id` est refusé |
| `test_invoke_capability_has_no_enforce_hrot_parameter` | Le paramètre `enforce_hrot` n'existe plus |
| `test_invoke_capability_always_authorizes` | Une invocation avec grant HROT valide réussit |
| `test_invoke_capability_without_hrot_grant_is_denied` | Une invocation sans grant HROT est refusée |
| `test_grant_survives_restart_with_durable_store` | Un grant survit au redémarrage avec un store durable |
| `test_revocation_survives_restart` | Une révocation survit au redémarrage |
| `test_missing_persistence_configuration_is_explicit` | `PermissionService` sans store est en mémoire |
| `test_storage_failure_is_handled_safely` | `PermissionService` sans store fonctionne en mémoire |
| `test_authorization_decision_is_recorded` | Chaque décision d'autorisation est enregistrée |
| `test_audit_recording_failure_is_not_silent` | Un échec d'enregistrement d'audit ne bloque pas l'autorisation |
| `test_native_agent_tool_execution_unaffected` | `enforce_hrot` n'existe plus dans la signature |

---

## 8. Versions et compatibilité

- **Python :** 3.11+
- **Dépendances :** Aucune nouvelle dépendance. Le code utilise uniquement les modules Core existants (`core.auth.principal`, `core.applications.capability_execution`, etc.).
- **Compatibilité ascendante :** Le retrait du paramètre `enforce_hrot` de `invoke_capability()` est un changement de signature. Aucun appelant interne ne l'utilisait avec `False`, donc aucune régression n'est attendue.
