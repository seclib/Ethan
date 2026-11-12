# EXECUTION_PATH_INVENTORY.md

Inventaire exhaustif des chemins d'exécution capables d'exécuter un outil, une capacité, une application, un plugin ou une opération externe dans ETHAN OS.

Mission P0-1R — Indépendant de toute implémentation. Mode lecture seule.

---

## 1. Méthodologie

L'inventaire a été établi par lecture directe des fichiers sources suivants :

- `core/applications/capability_execution.py`
- `interfaces/api/routers/applications.py`
- `core/agents/executor.py`
- `core/agents/manager.py`
- `core/agents/resources.py`
- `core/agents/types.py`
- `core/capability_manager/manager.py`
- `core/capability_manager/backends.py`
- `core/applications/capability_contract.py`
- `core/hrot/capability_authorization.py`
- `core/hrot/durable.py`
- `interfaces/api/auth.py`
- `core/auth/__init__.py`
- `core/auth/principal.py`

Aucun fichier n'a été modifié. Aucune opération de code n'a été exécutée sur le dépôt.

---

## 2. Matrice des chemins d'exécution

| # | Chemin d'exécution | Point d'entrée | Mécanisme d'autorisation | Contexte de confiance | Effets de bord | Résultat de l'audit |
|---|---|---|---|---|---|---|
| A1 | Invocation de capacité applicative (Odin, Frame, autres) | `core/applications/capability_execution.py:154` `invoke_capability()` | HROT via `CapabilityAuthorizationService.authorize()` (étape 189-240) + `PermissionService.evaluate()` | `ExecutionContext` construit depuis `request.state.principal` dans `interfaces/api/routers/applications.py:318-333` | Exécution de l'implémentation allowlistée (`_odin_runtime_status`, `_frame_runtime_status`) via `_TRUSTED_IMPLEMENTATIONS` | **HROT appliqué avant side effect** (fail-closed). Code mort en lignes 272-299 (duplication de 243-270). |
| A2 | Route API d'invocation | `interfaces/api/routers/applications.py:297` `invoke_application_capability` | `require_permission(Permission.EXECUTE)` (RBAC FastAPI) + HROT via `invoke_capability()` | `request.state.principal` (JWT vérifié par `auth_middleware`) | Délègue à `invoke_capability()` | **RBAC + HROT**. Pas de bypass connu sur ce chemin. |
| A3 | Exécution agent LLM (conversation + outils) | `core/agents/executor.py:192` `create_agent_executor()` → `execute()` | `resolve_agent_resources()` (sélection explicite uniquement, pas de ressource globale) + `SecureToolEnforcer` (CT-4 séparation données/instructions) | `execution_context` passé à `AgentManager.execute()` | Construction du prompt système, exécution d'outils via `run_agent_chat()` / `_execute_agent_tool()` | **HROT N'EST PAS APPLIQUÉ** à l'exécution agent LLM. Les outils passent par `SecureToolEnforcer` (P0-2), pas par HROT. Les skills/knowledge/RAG sont injectés comme données (<data>), pas comme instructions. |
| A4 | Exécution d'outils agent (boucle d'outils) | `core/agents/executor.py:76` `_execute_agent_tool()` | `ToolExecutor.execute()` → `SecureToolEnforcer` (PolicyEngine + Capability + ExfilGuard) | `ToolContext(query, user_id=f"agent:{agent_name}", source="agent")` | Exécution de l'outil, effets de bord de l'outil | **SecureToolEnforcer appliqué**. Fail-closed si aucun ToolManager/enforcer. HROT non impliqué ici. |
| A5 | Cycle de vie CapabilityManager (install/start/stop/test/enable/disable/uninstall) | `core/capability_manager/manager.py` : `install()`, `start()`, `stop()`, `test()`, `enable()`, `disable()`, `uninstall()` | Audit via `self._audit()` (événements allow/error). Pas d'appel HROT. | Paramètre `actor` (chaîne, pas d'identité vérifiée) | Installation/démarrage/arrêt de composants Docker/Python/Node/exécutable/builtin | **Pas d'autorisation HROT**. Audit seulement. Pas de contexte d'identité cryptographiquement vérifié. |
| A6 | Backends CapabilityManager (Docker, Python, Node, Executable, Builtin) | `core/capability_manager/backends.py` | `validate_install_actions()` (barrière anti-injection, allowlist d'actions) | Aucun contexte d'identité | Exécution de commandes système (docker compose, pip, etc.) | **Pas d'autorisation HROT**. Barrière anti-injection sur les actions déclaratives uniquement. |
| A7 | Découverte de dépôts locaux | `core/applications/local_repository_discovery.py` : `LocalRepositoryDiscovery.analyze_repository()` | Read-only, pas d'exécution du code découvert | Aucun | Lecture de métadonnées de dépôt Git (branche, HEAD, remote, fichiers) | **Read-only**. Pas d'autorisation requise. Pas d'exécution. |
| A8 | Découverte GitHub | `core/applications/github_organization_discovery.py` : `discover_github_repositories()` | Appel API GitHub publique (read-only) | Aucun | Liste de métadonnées de dépôts GitHub | **Read-only réseau**. Pas d'exécution. |
| A9 | Registre d'applications (enregistrement) | `core/applications/application_registry.py` : `register()` | Aucun appel HROT. Validation du contrat via `ExtensionContractValidator` | Paramètre `actor` (chaîne) | Écriture du registre d'applications, événement d'observabilité | **Pas d'autorisation HROT**. Validation de conformité du manifest uniquement. |
| A10 | Contrats de capacités (enregistrement) | `core/applications/capability_contract.py` : `register_application_capability()` | Aucun appel HROT. Validation du contrat via `ContractValidator` | Paramètre `approved` (booléen, passé par l'appelant) | Enregistrement du contrat de capacité | **Pas d'autorisation HROT**. Le paramètre `approved` est une simple case à cocher passée par l'appelant, pas une preuve d'approbation humaine. |
| A11 | Cycle de vie applicatif (machine à états) | `core/applications/resilience.py` : `ApplicationLifecycleManager` | Transitions d'états légales uniquement | Aucun | Changement d'état du cycle de vie (REGISTERED→VALIDATED→READY→...) | **Pas d'autorisation HROT**. Machine à états interne. |
| A12 | Exécution d'agents via AgentManager | `core/agents/manager.py:212` `execute()` | Aucun appel HROT. Vérification `skill_id in agent.skill_ids` | `execution_context` passé à l'executor | Persistence de l'exécution, changement de statut agent, exécution de la tâche via l'executor | **Pas d'autorisation HROT**. L'executor est injecté par la composition root. HROT n'est pas appelé dans ce chemin. |

---

## 3. Constats d'architecture

### 3.1 Point d'entrée canonique unique

`invoke_capability()` dans `core/applications/capability_execution.py` est l'**unique** chemin d'exécution des capacités applicatives externes (Odin, Frame). La route API `invoke_application_capability` y délègue après avoir construit un `ExecutionContext` depuis `request.state.principal`.

### 3.2 Deux chemins d'exécution distincts

| Chemin | Autorisation | HROT ? |
|--------|-------------|--------|
| Capacités applicatives externes (`invoke_capability`) | `Permission.EXECUTE` (RBAC) + `CapabilityAuthorizationService` (HROT) | **Oui** |
| Exécution agent LLM + outils (`executor.py`) | `resolve_agent_resources` + `SecureToolEnforcer` (CT-4) | **Non** — HROT n'est pas appelé |
| Cycle de vie CapabilityManager | Audit `self._audit()` uniquement | **Non** — pas d'autorisation |

### 3.3 Code mort détecté

Dans `core/applications/capability_execution.py`, les lignes 272-299 sont une **duplication exacte** des lignes 243-270 (validation jsonschema, lookup de l'implémentation, exécution, retour). Ce bloc est **inatteignable** car la fonction retourne déjà à la ligne 269 dans tous les cas (échec HROT → return failed, succès HROT → return après exécution). Cela ne constitue pas une faille de sécurité directe (le code n'est jamais exécuté), mais indique un défaut de qualité et de révision du code.

---

## 4. Conclusion de l'inventaire

- **Tous les chemins d'exécution ont été identifiés.** Aucun chemin caché n'a été découvert.
- **HROT est appliqué uniquement sur le chemin d'invocation de capacité applicative** (`invoke_capability`).
- **HROT n'est PAS appliqué** sur l'exécution agent LLM, le cycle de vie CapabilityManager, ni l'enregistrement de contrats/applications.
- Le chemin d'invocation de capacité est le seul où l'autorisation HROT est pertinente au sens de la mission P0-1 (capacités applicatives externes).
- Le code mort (lignes 272-299) ne crée pas de faille de sécurité mais doit être nettoyé (mission P3).
