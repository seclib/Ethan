# INDEPENDENT_REVIEW.md

Revue indépendante — Audit F (Mission P0-1R).

Mission P0-1R — Indépendant, lecture seule. Aucune modification de code.

---

## 1. Méthode de revue indépendante

Cette revue a été conduite en analysant le code source sans se fier au rapport d'implémentation précédent. L'approche consiste à :

1. Identifier tous les chemins d'exécution capables d'exécuter une capacité, un outil ou une application externe.
2. Vérifier si chaque chemin passe par `CapabilityAuthorizationService.authorize()`.
3. Chercher des chemins alternatifs qui pourraient contourner l'autorisation HROT.
4. Contester l'hypothèse selon laquelle `invoke_capability()` est le seul point d'entrée pour les capacités externes.
5. Vérifier la chaîne de confiance depuis l'authentification HTTP jusqu'à la décision HROT.

---

## 2. Chemins d'exécution identifiés (revue indépendante)

La revue indépendante confirme l'inventaire du document `EXECUTION_PATH_INVENTORY.md` et identifie **12 chemins d'exécution** répartis en 3 catégories :

### 3.1 Capacités applicatives externes (DTAI) — COUVERTES par HROT

| Chemin | Point d'entrée | HROT ? | Commentaire |
|--------|---------------|--------|-------------|
| Invocation de capacité Odin/Frame | `core/applications/capability_execution.py:154` `invoke_capability()` | **Oui** | Seul chemin d'exécution des contrats de capacité avec implémentation allowlistée (`_TRUSTED_IMPLEMENTATIONS`) |
| Route API d'invocation | `interfaces/api/routers/applications.py:297` | **Oui** (via `invoke_capability`) | RBAC `Permission.EXECUTE` + HROT |

### 3.2 Exécution agent et outils — NON COUVERT par HROT (différent périmètre)

| Chemin | Point d'entrée | HROT ? | Commentaire |
|--------|---------------|--------|-------------|
| Exécution agent LLM | `core/agents/executor.py:192` `execute()` | **Non** | Les skills/knowledge/RAG sont injectés comme données (<data>), pas comme instructions. Les outils passent par `SecureToolEnforcer` (CT-4, P0-2), pas par HROT. |
| Boucle d'outils agent | `core/agents/executor.py:76` `_execute_agent_tool()` | **Non** | `ToolExecutor.execute()` → `SecureToolEnforcer` (PolicyEngine + Capability + ExfilGuard) |
| Cycle de vie CapabilityManager | `core/capability_manager/manager.py` : install/start/stop/test/enable/disable/uninstall | **Non** | Audit via `self._audit()` uniquement, pas d'HROT |
| Backends CapabilityManager | `core/capability_manager/backends.py` | **Non** | `validate_install_actions()` (barrière anti-injection sur actions déclaratives) |
| Découverte dépôts locaux | `core/applications/local_repository_discovery.py` | **Non** | Read-only, pas d'exécution |
| Découverte GitHub | `core/applications/github_organization_discovery.py` | **Non** | Appel API GitHub publique, read-only |
| Registre d'applications (enregistrement) | `core/applications/application_registry.py` : `register()` | **Non** | Validation du contrat, pas d'autorisation d'exécution |
| Contrats de capacités (enregistrement) | `core/applications/capability_contract.py` : `register_application_capability()` | **Non** | Le paramètre `approved` est une case à cocher, pas une preuve d'approbation humaine cryptographiquement liée |
| Cycle de vie applicatif | `core/applications/resilience.py` : `ApplicationLifecycleManager` | **Non** | Machine à états interne |
| Exécution d'agents via AgentManager | `core/agents/manager.py:212` `execute()` | **Non** | Pas d'appel HROT. Vérification `skill_id in agent.skill_ids` uniquement. |

---

## 3. Contestation de l'hypothèse "invoke_capability est le seul point d'entrée"

**Hypothèse :** Toutes les capacités applicatives externes passent par `invoke_capability()`.

**Verdict de la revue indépendante : PARTIELLEMENT VRAI, avec nuances importantes.**

### 3.1 Ce qui est confirmé

Pour les **capacités applicatives avec contrat et implémentation allowlistée** (Odin `odin.runtime-status`, Frame `frame.runtime-status`), `invoke_capability()` est effectivement le **seul** point d'entrée. Il n'existe aucun autre chemin dans le code qui appelle `_odin_runtime_status` ou `_frame_runtime_status` directement.

### 3.2 Ce qui n'est PAS couvert par HROT (mais n'est pas non plus une "capacité applicative" au sens DTAI)

- **Exécution d'outils agent** (via `SecureToolEnforcer`) : ce sont des outils, pas des capacités applicatives DTAI. Le périmètre est différent.
- **Cycle de vie des composants** (via `CapabilityManager`) : ce sont des composants d'infrastructure (Docker, Python package, etc.), pas des capacités applicatives avec contrats.
- **Enregistrement de contrats et de bindings** : c'est de la configuration, pas de l'exécution. L'approbation (`approved=True`) est une case à cocher passée par l'appelant de l'API, pas une preuve d'approbation humaine cryptographiquement vérifiée (sauf si `PermissionService.grant_permission()` est appelé séparément avec une `HumanAuthority` valide).

### 3.3 Contournement potentiel de HROT dans `invoke_capability`

La revue indépendante identifie **un seul vecteur de contournement réaliste** (appelant interne uniquement) :

- **`enforce_hrot: bool = True`** : un appelant interne de `invoke_capability()` peut passer `enforce_hrot=False` pour désactiver l'autorisation HROT. La route API ne le fait pas (toujours True par défaut), mais rien n'empêche un appelant interne du code Python de le faire.

**Verdict : Ce contournement n'est pas accessible via l'API HTTP publique.** Il nécessite un accès au code Python de l'application ETHAN.

---

## 4. Chaîne de confiance — Revue indépendante

La revue indépendante confirme la chaîne d'identité décrite dans `IDENTITY_AND_TRUST_REVIEW.md` :

1. **Authentification HTTP** : `auth_middleware()` vérifie JWT/API Key/Service, peuple `request.state.principal` (AgentPrincipal signé HMAC).
2. **Route API** : construit `ExecutionContext` depuis `request.state.principal`.
3. **`invoke_capability()`** : construit `CapabilityAuthorizationRequest` avec l'`execution_context`, appelle `CapabilityAuthorizationService.authorize()`.
4. **HROT** : 10 étapes, fail-closed, audit en mémoire.

**Point faible confirmé :** `CapabilityAuthorizationService._evaluate()` n'appelle **pas** `verify_trusted_principal()`. Un `AgentPrincipal` forgé par un appelant interne serait accepté. Cette faiblesse n'est exploitable que par un appelant interne (pas via l'API HTTP).

---

## 5. Tableau récapitulatif des chemins d'exécution et de leur statut HROT

| Chemin | Couvert par HROT ? | Alternative d'autorisation | Risque de contournement |
|--------|-------------------|---------------------------|------------------------|
| `invoke_capability()` (capacités externes) | **Oui** | N/A | Faible (appelant interne uniquement via `enforce_hrot=False`) |
| Route API `/application-capabilities/{id}/invoke` | **Oui** (RBAC + HROT) | N/A | Aucun (via HTTP) |
| Exécution agent LLM (`executor.py`) | **Non** | `SecureToolEnforcer` + résolution de ressources explicite | N/A (périmètre différent) |
| Cycle de vie CapabilityManager | **Non** | Audit `self._audit()` | N/A (périmètre différent) |
| Enregistrement de contrats/capacités | **Non** | Validation du contrat + case `approved` | Case à cocher, pas de preuve cryptographique |
| Découverte dépôts/GitHub | **Non** | Read-only | Aucun (pas d'exécution) |

---

## 6. Conclusion de la revue indépendante

La revue indépendante **confirme** l'architecture de sécurité P0-1 pour le périmètre des capacités applicatives externes (Odin, Frame) :

- `invoke_capability()` est le point d'entrée unique pour ces capacités.
- HROT est appliqué avant toute exécution, de manière fail-closed.
- La chaîne d'identité depuis l'authentification HTTP jusqu'à la décision HROt est cryptographiquement signée (HMAC).
- Aucun contournement n'est possible via l'API HTTP publique.

La revue indépendante identifie **trois limites architecturales** (non des vulnérablières exploitables via HTTP) :

1. **`enforce_hrot` contournable par un appelant interne** (code Python).
2. **Pas de `verify_trusted_principal()` dans `_evaluate()`** (un `AgentPrincipal` forgé par un appelant interne est accepté).
3. **HROT ne couvre pas l'exécution agent LLM ni le cycle de vie CapabilityManager** (périmètres différents, protégés par d'autres mécanismes : `SecureToolEnforcer`, résolution de ressources explicite, audit).

Ces limites doivent être documentées et prises en compte avant que P0-1 serve de fondation à l'intégration DAĒNĀ (mission P1).
