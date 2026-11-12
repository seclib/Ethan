# REMEDIATION_PLAN.md

Plan de remédiation — Audit P0-1R HROT.

Mission P0-1R — Indépendant, lecture seule. Ce plan décrit les corrections recommandées ; aucune implémentation n'est effectuée dans le cadre de cette mission.

---

## 1. Faiblesses identifiées et plan de remédiation

| ID | Faiblesse | Sévérité | Plan de remédiation | Priorité | Bloquant P0-1 ? |
|----|-----------|----------|---------------------|----------|-----------------|
| HROT-01 | `permission_service` peut être None → étape HROT policy (grant) sautée. Sans permission_service, seul le RBAC du principal est vérifié, pas les grants HROT explicites. | HIGH | Rendre `permission_service` obligatoire dans `CapabilityAuthorizationService.__init__` (retirer la fallback `PermissionService(production_mode=False)`), ou lever une erreur explicite si absent. Dans `invoke_capability()`, vérifier que `registry.permission_service` est présent avant d'appeler `authorize()`, sinon refuser avec `AUTHORIZATION_EVALUATION_ERROR`. | Haute | Non (fail-closed par défaut, mais couverture incomplète) |
| HROT-02 | Aucun appel à `verify_trusted_principal()` dans `_evaluate()`. Un `AgentPrincipal` forgé par un appelant interne est accepté. | HIGH | Appeler `verify_trusted_principal(context.principal)` à l'étape 1 (après `_coerce_execution_context`). Si la vérification échoue, DENY `INVALID_PRINCIPAL_SIGNATURE`. Cela garantit que seul un principal signé par le middleware d'authentification est accepté. | Haute | Non (contournement uniquement par appelant interne) |
| HROT-03 | `enforce_hrot: bool = True` contournable par un appelant interne de `invoke_capability()`. | MEDIUM | Retirer le paramètre `enforce_hrot` de la signature publique (le rendre toujours True), ou le renommer en paramètre privé/internal. La route API ne le passe jamais (toujours True par défaut). | Moyenne | Non (non accessible via HTTP) |
| HROT-04 | `execution_context` peut être None → refusé (fail-closed correct). | LOW (conception) | Aucun remédiation nécessaire : le refus est le comportement correct. Documenter que `execution_context` est obligatoire. | Basse | Non |
| HROT-05 | Échec de `_record()` silencieusement ignoré → décision d'autorisation non tracée en mémoire. | MEDIUM | Lever ou logger une erreur si `_record()` échoue, afin que l'absence de traçabilité soit visible. Ou passer `audit=False` si l'audit en mémoire n'est pas requis. | Moyenne | Non |
| HROT-06 | Code mort (lignes 272-299 dupliquant 243-270 de `capability_execution.py`). | LOW | Supprimer le bloc dupliqué (lignes 272-299). | Basse | Non |
| PERSIST-01 | `PermissionService` en mémoire par défaut — grants perdus au redémarrage. | HIGH | Documenter que `PermissionService` requiert un `store` (ApplicationStateStore) pour la persistance. Dans la composition root (`interfaces/api/main.py`), injecter un store configuré. Sans store, documenter que les grants HROT sont volatils. | Haute | Non (fail-closed au redémarrage) |
| PERSIST-02 | Aucun lien automatique entre `DurableHrotStore` (approbations durables) et `PermissionService` (grants). | MEDIUM | Documenter que les deux systèmes sont indépendants. Si une intégration est souhaitée, créer un adaptateur qui lit les approbations `APPROVED` de `DurableHrotStore` et crée les grants correspondants dans `PermissionService`. | Moyenne | Non |
| PERSIST-03 | Piste d'autorisation (`_decisions`) en mémoire uniquement — disparait au redémarrage. | MEDIUM | Documenter que les décisions d'autorisation sont volatiles. Pour une piste d'audit durable, persister via `EventCollector` ou `ApplicationStateStore`. | Moyenne | Non |
| PERSIST-04 | Pas d'envoi des décisions HROT vers `EventCollector`. | LOW | Documenter que les décisions HROT ne sont pas envoyées à l'observabilité événementielle. Ajouter un appel à `event_collector.record()` dans `invoke_capability()` si nécessaire. | Basse | Non |
| PERSIST-05 | Pas de secrets dans les décisions d'audit | CONFORME | Aucun remédiation nécessaire. | — | Non |

---

## 2. Ordre de remédiation recommandé

1. **HROT-01** (Haute) : Rendre `permission_service` obligatoire. C'est la plus grave car elle permet l'exécution sans vérification de grant HROT si le service est absent.
2. **HROT-02** (Haute) : Ajouter `verify_trusted_principal()` dans `_evaluate()`. Empêche la falsification d'identité par un appelant interne.
3. **HROT-03** (Moyenne) : Retirer `enforce_hrot` de la signature publique. Élimine le risque de contournement par appelant interne.
4. **PERSIST-01** (Haute) : Configurer un `store` sur `PermissionService` dans la composition root, ou documenter explicitement la volatilité des grants.
5. **HROT-05** (Moyenne) : Gérer l'échec de `_record()` (logger ou lever).
6. **HROT-06** (Basse) : Supprimer le code mort.
7. **PERSIST-02, PERSIST-03, PERSIST-04** (Moyenne/Basse) : Améliorations d'observabilité et de persistance, non bloquantes.

---

## 3. Impact sur P1 (DAĒNĀ agent knowledge integration)

P1 prévoit que les agents puissent récupérer des connaissances autorisées pendant leur exécution, sous contrôle de l'autorisation P0. Les remédiations HROT-01 et HROT-02 sont **prérequises** avant P1 car :

- Sans `permission_service` obligatoire (HROT-01), un agent pourrait exécuter une capacité sans grant HROT valide.
- Sans `verify_trusted_principal()` (HROT-02), un agent avec un contexte forgé pourrait obtenir des capacités non autorisées.

Ces remédiations doivent être implémentées et validées avant de débuter P1-1.

---

## 4. Critères d'acceptation de la remédiation

- [ ] `CapabilityAuthorizationService.__init__` requiert un `permission_service` non None, ou lève une erreur si absent.
- [ ] `_evaluate()` appelle `verify_trusted_principal(context.principal)` et refuse si la signature est invalide.
- [ ] `invoke_capability()` n'a plus de paramètre `enforce_hrot` public (ou il est toujours True).
- [ ] `invoke_capability()` vérifie que `registry.permission_service` est présent avant d'appeler `authorize()`.
- [ ] `_record()` logge ou lève en cas d'échec d'enregistrement de la décision.
- [ ] Le code mort (lignes 272-299) est supprimé.
- [ ] Tous les tests existants (58) passent après remédiation.
- [ ] Aucun nouveau test ne régress e.

---

## 5. Risques de la remédiation

- **Rupture de compatibilité** : retirer `enforce_hrot` de la signature publique pourrait casser des appelants internes qui l'utilisent. Vérifier qu'aucun code interne ne l'utilise avec `False`.
- **Dépendance au store** : configurer un `store` sur `PermissionService` ajoute une dépendance à l'infrastructure de persistance (ApplicationStateStore). Vérifier qu'elle est disponible dans la composition root.
- **Performance** : `verify_trusted_principal()` ajoute une opération HMAC à chaque autorisation. Impact négligeable (opération cryptographique rapide).
