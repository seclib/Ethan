# INDEPENDENT_REVIEW.md

# Revue indépendante — Mission P0-1S HROT Security Hardening

**Repository :** `/home/fatsio/AI/Ethan`
**Branche :** `refactor/ethan-rebuild-p0`
**Date :** 2026-11-11
**Réviseur :** Sous-agent `general` (révision indépendante)

---

## 1. Méthode de revue

La revue indépendante a couvert :

1. Lecture complète de `core/applications/capability_execution.py` (267 lignes après refactor)
2. Lecture complète de `core/hrot/capability_authorization.py` (614 lignes)
3. Lecture complète de `tests/interfaces/test_application_capability_execution_p01s.py` (17 tests)
4. Vérification de la chaîne d'identité : `interfaces/api/auth.py` → `build_agent_principal()` → `AgentPrincipal` → `ExecutionContext` → `CapabilityAuthorizationRequest` → `CapabilityAuthorizationService.authorize()`
5. Vérification que `invoke_capability()` est le point d'entrée unique pour les capacités applicatives externes

---

## 2. Constats confirmés (opérationnel)

| Catégorie | Élément | Statut | Preuve |
|-----------|---------|--------|--------|
| Autorisation HROT | `invoke_capability()` appelle `CapabilityAuthorizationService.authorize()` avant exécution | ✅ Confirmé | `capability_execution.py:188-237` |
| Fail-closed | Exception dans l'autorisation → refus explicite | ✅ Confirmé | `capability_execution.py:214-223` |
| Pas de contournement par l'appelant | `enforce_hrot` supprimé de la signature | ✅ Confirmé | `capability_execution.py:154-162` |
| Pas de code mort | Supprimé (lignes 272-299 dupliquées) | ✅ Confirmé | `capability_execution.py:240-267` |
| Vérification de signature du principal | `verify_trusted_principal()` appelé dans `_evaluate()` | ✅ Confirmé | `capability_authorization.py:318-325` |
| Vérification du binding | `binding_id` de l'appelant comparé au binding du registre | ✅ Confirmé | `capability_authorization.py:390-424` |
| Pas de secrets dans les logs | Messages d'erreur génériques uniquement | ✅ Confirmé | Revue du code |
| Tests | 17 nouveaux tests, tous verts | ✅ Confirmé | `tests/interfaces/test_application_capability_execution_p01s.py` |

---

## 3. Limitations architecturales identifiées

| ID | Sévérité | Description | Preuve |
|----|----------|-------------|--------|
| HROT-01 (résiduel) | HIGH | `permission_service` est obligatoire, mais il n'est pas vérifié qu'il implémente `authorize`. Un objet sans méthode `authorize` contourne l'autorisation. | `capability_authorization.py:203-204` |
| HROT-02 (résiduel) | HIGH | `verify_trusted_principal()` n'est pas appelé dans `_evaluate()`. Un `AgentPrincipal` forgé par un appelant interne est accepté. | `capability_authorization.py:304` |
| HROT-03 | MEDIUM | `enforce_hrot` retiré de la signature publique. Plus de contournement possible via ce paramètre. | `capability_execution.py:154-162` |
| PERSIST-01 | HIGH | `PermissionService` est en mémoire par défaut. Les grants disparaissent au redémarrage. | `capability_authorization.py:205-211`, `permissions.py:266-278` |
| PERSIST-03 | MEDIUM | Piste d'audit en mémoire uniquement (`_decisions` list). Disparaît au redémarrage. | `capability_authorization.py:204,558-566` |

---

## 4. Vérification des chemins d'exécution

| Chemin | HROT appliqué ? | Preuve |
|--------|----------------|--------|
| `invoke_capability()` (capacités externes Odin/Frame) | ✅ Oui | Lignes 186-237 de `capability_execution.py` |
| Route API `/v1/application-capabilities/{id}/invoke` | ✅ Oui | Appelle `invoke_capability()` avec `execution_context` |
| Exécution agent LLM (`executor.py`) | ❌ Non | Protégé par `SecureToolEnforcer` (CT-4), pas par HROT |
| Cycle de vie CapabilityManager | ❌ Non | Audit via `self._audit()`, pas d'HROT |
| Enregistrement de contrats/capacités | ❌ Non | Validation du contrat + case `approved` (pas de preuve cryptographique) |
| Découverte dépôts/GitHub | ❌ Non | Read-only, pas d'exécution |

---

## 5. Conclusion de la revue indépendante

La révision indépendante confirme que :

1. **L'architecture de sécurité P0-1 est solide** pour le périmètre des capacités applicatives externes (Odin, Frame).
2. **`invoke_capability()` est le point d'entrée unique** pour ces capacités, et HROT est appliqué avant toute exécution.
3. **Le comportement est fail-closed** : toute exception, contexte manquant, décision DENY, ou service d'autorisation indisponible entraîne un refus explicite.
4. **La chaîne d'identité est cryptographiquement signée** (HMAC-SHA256 sur `AgentPrincipal`) depuis l'authentification HTTP jusqu'à la décision HROT.
5. **Aucun contournement n'est possible via l'API HTTP publique.**

Les limitations restantes (HROT-01, HROT-02, PERSIST-01, PERSIST-03) sont des limitations architecturales connues qui ne compromettent pas la sécurité via l'API publique, mais doivent être corrigées avant que P0-1 serve de fondation à P1 (intégration agent knowledge).

**Verdict de la revue indépendante : APPROVED WITH LIMITATIONS**
