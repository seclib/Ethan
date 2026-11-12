# DTAI_ASSESSMENT.md

État réel du système DTAI (Dynamic Tool & Application Integration) d'ETHAN. Mission d'investigation uniquement : aucune modification de code. Distinction opérationnel / partiel / absent, avec preuves (chemins, lignes, flux).

---

## 1. Vue d'ensemble architecturale

ETHAN implémente une séparation stricte : le **Core** possède toute la logique métier, le **Runtime** orchestre, et les **interfaces** (WebUI, CLI, Desktop, API) ne font que révéler et contrôler via HTTP. Les routers API sont des **passerelles minces** sans logique métier : elles injectent un manager Core et délèguent.

Le socle DTAI repose sur deux registres distincts mais convergents :

| Registre | Fichier Core | Rôle |
|----------|-------------|------|
| **Application Integration Registry** | `core/applications/application_registry.py` | Enregistrement des applications indépendantes avec manifest, conformité, cycle de vie |
| **Capability Registry** | `core/applications/capabilities.py` | Définition versionnée de capacités ETHAN (statut draft/active/deprecated/retired, permissions, sensibilité) |
| **Capability Manager** | `core/capability_manager/manager.py` | Cycle de vie des composants optionnels (détect → install → start → stop → test → enable → disable → uninstall) |

---

## 2. Socle commun générique (opérationnel)

### 2.1 Modèle de manifest
- `core/applications/models.py` (710 lignes). `ApplicationIdentity` (app_id, instance_id, name, version, contract_version, publisher, manifest_version), `ApplicationCapability`, `ApplicationDependency`, `InterfaceDescriptor` (kind cli/http/desktop/api/operator/web/grpc/websocket), `ApplicationProvenance`, `ApplicationManifest`. Contract version `1.0.0` uniquement. JSON Schema embarqué. `from_mapping`/`to_dict`/`from_yaml`/`from_json`.
- **Statut** : opérationnel.

### 2.2 Validateur de contrat
- `core/applications/validator.py` (`ContractValidator`) : valide un mapping YAML/JSON, un fichier ou une chaîne. Détecte les secrets (patterns API keys, tokens, mots de passe). Retourne `ValidationResult` (valid/invalid/incomplete/incompatible).
- **Statut** : opérationnel.

### 2.3 Découverte
- `core/applications/discovery.py` (`ApplicationDiscoveryService`) : lecture seule, récursive, scan `.yaml/.yml/.json` jusqu'à `max_depth`. Détection conflits (`duplicate_app_id`, `duplicate_instance_id`). Retourne `DiscoveryReport`. États de capacité : `DECLARED → VERIFIED → AVAILABLE → AUTHORIZED`.
- **Statut** : opérationnel.

### 2.4 Catalogue
- `core/applications/catalog.py` (`ApplicationCatalog`, racines `CatalogSource` builtin/local_example/github). `refresh()` exécute la découverte et filtre les manifests valides. `find(app_id)`, `entries()`.
- **Statut** : opérationnel.

### 2.5 Registre d'intégration
- `core/applications/application_registry.py` (`ApplicationIntegrationRegistry`, verrou `fcntl`). `register(manifest, contract, actor, emit_event)` → `ApplicationRecord` (état `REGISTERED`, conformité évaluée). `get`/`list`/`update_manifest`/`mark_available`/`withdraw`/`health_check`. États : `REGISTERED/VALIDATED/AVAILABLE/UNAVAILABLE/WITHDRAWN`.
- **Statut** : opérationnel.

### 2.6 Cycle de vie applicatif
- `core/applications/resilience.py` : `LifecycleState` (REGISTERED → VALIDATED → READY → STARTING → RUNNING → DEGRADED → STOPPING → STOPPED → FAILED → UNKNOWN). Machine à états avec transitions légales. `ResilientExecutor` (timeout, retry borné, circuit breaker, idempotency, guard par clé d'opération).
- **Statut** : opérationnel.

### 2.7 Permissions / HROT
- `core/applications/permissions.py` (`PermissionService`) : rien n'est implicitement accordé. `HumanAuthority` (proof de Root of Trust Humain), `PermissionScope` (app_id, instance_id, capability, resource, action, context_constraints), `PermissionGrant` (HROT-signé, expirations, révocation). Vérification cryptographique via `HrotApprovalProof`/`HrotApprovalContext` en mode production. `manifest_fingerprint(manifest)` : SHA-256 canonique pour détecter les modifications post-autorisation.
- **Statut** : opérationnel.

### 2.8 Répertoire de manifests durables
- `core/applications/manifest_repository.py` (`ApplicationManifestRepository`, stockage SQLite via `ApplicationStateStore`). `create`/`update` (version incrémentée)/`get_current`/`get`/`by_id`/`list`. **`delete()` lève `NotImplementedError`** (pas de suppression silencieuse, politique de retrait par policy).
- **Statut** : opérationnel (sauf suppression).

### 2.9 Catalogue d'intégration
- `core/applications/integration_catalog.py` (`IntegrationCatalogService`) : projection lecture seule depuis découverte + registre + repository. États : `discovered/validated/registered/installed/available/running/authorized`. Racines configurables via `ETHAN_LOCAL_REPOSITORY_ROOT` / `ETHAN_LOCAL_REPOSITORY_ROOTS`.
- **Statut** : opérationnel (lecture seule).

### 2.10 Découverte dépôts locaux
- `core/applications/local_repository_discovery.py` (`LocalRepositoryDiscovery`) : scan read-only des dépôts Git locaux. `analyze_repository()` extrait branche, HEAD, remote (normalisé owner/repo), statut working tree, fichiers détectés (README, Dockerfile, compose, package.json, pyproject.toml, Cargo.toml), types estimés, classification (`DISCOVERED`/`INVALID`/`COMPATIBLE`). Exclusion de répertoires (`.git`, `node_modules`, `.venv`). **Ne jamais exécuter le code découvert.**
- **Statut** : opérationnel.

### 2.11 Découverte GitHub
- `core/applications/github_organization_discovery.py` : appel API GitHub publique (pagination, token optionnel via `GITHUB_TOKEN`). Retourne `GitHubRepositoryMetadata`. Read-only, rien n'est exécuté.
- **Statut** : opérationnel (réseau requis).

### 2.12 Contrats de capacités applicatives
- `core/applications/capability_contract.py` (`ApplicationCapabilityContract` : capability_id, contract_version 1.0.0, application_id, name, description, category information/analysis/automation/knowledge/system, invocation_interface, input/output_schema JSON Schema, required_permissions, runtime_requirements, execution_constraints, timeout_seconds 1-300, activation_required).
- `register_application_capability(registry, contract, approved)` : rejette si doublon avec définition différente.
- **Statut** : opérationnel.

### 2.13 Exécution de capacités
- `core/applications/capability_execution.py` : `TRUSTED_IMPLEMENTATION_ALIASES = {"odin.runtime-status", "frame.runtime-status"}`. `bind_capability_implementation` (nécessite approbation explicite), `activate_capability_binding`, `invoke_capability` (valide contrat, binding, activation, input_schema jsonschema, appelle l'implémentation allowlistée avec timeout, retourne `CapabilityExecutionResult`).
- **Statut** : opérationnel pour Odin et Frame uniquement.

### 2.14 Registre de capacités ETHAN
- `core/applications/capabilities.py` (`CapabilityRegistry`, `CapabilityDefinition` avec capability_id, name, description, category, version, status DRAFT/ACTIVE/DEPRECATED/RETIRED, sensitivity LOW/MEDIUM/HIGH/CRITICAL, permissions, constraints, dependencies, metadata). Méthodes : register/get/list/search/activate/deprecate/retire/history/permission_mapping.
- **Statut** : opérationnel.

---

## 3. Cycle de vie des composants optionnels (Capability Manager)

### 3.1 Spec déclarative
- `core/capability_manager/types.py` (`CapabilitySpec` : id, name, description, type, version, backend docker/python_package/node_package/executable/builtin, install/uninstall/start/stop_actions déclaratives figées, data_resources, dependencies, config_schema typé, health_checks endpoint/tcp/exec/builtin, requirements os/arch/ram/disk, requires_confirmation, provenance).
- États : `SUPPORTED/NOT_INSTALLED/INSTALLING/INSTALLED/STARTING/RUNNING/STOPPED/UNHEALTHY/CONFIGURATION_REQUIRED/READY/UNINSTALLING/ERROR`.

### 3.2 Backends
- `core/capability_manager/backends.py` : 5 backends (Docker, PythonPackage, NodePackage, Executable, Builtin). `validate_install_actions()` : barrière anti-injection (allowlist d'actions par backend). Aucune chaîne utilisateur ne rejoint une argv.

### 3.3 Manager
- `core/capability_manager/manager.py` (`CapabilityManager`, 1150+ lignes) : `register`/`detect`/`plan_install`/`plan_uninstall`/`install`/`configure`/`start`/`stop`/`test`/`enable`/`disable`/`uninstall`/`get_operation`/`list_operations`/`cancel_operation`/`status`/`status_all`/`logs`. Opérations persistées dans `CoreRecordStore` (domaine `capability_operations`), réconciliées au redémarrage (24h de rétention, 50 max).
- **Statut** : opérationnel.

---

## 4. Endpoints HTTP (routers montés dans main.py)

### 4.1 Applications (`interfaces/api/routers/applications.py`, préfixe `/v1`, tag `applications`)
- `GET /v1/applications` (READ) : entrées catalogue découvertes.
- `GET /v1/applications/registered` (READ) : registres d'intégration.
- `GET /v1/application-capabilities` (READ, `application_id` optionnel) : contrats de capacités.
- `POST /v1/application-capabilities/validate` (READ, body `contract`) : validation.
- `POST /v1/application-capabilities` (PLUGINS, `approved=true` requis) : création contrat.
- `GET /v1/applications/{app_id}` (READ) : manifeste.
- `POST /v1/applications/refresh` (PLUGINS) : rafraîchissement catalogue.
- `GET /v1/applications/{app_id}/runtime` (READ) : état (Odin/Frame uniquement).
- `POST /v1/applications/{app_id}/start` (PLUGINS), `POST /v1/applications/{app_id}/stop` (PLUGINS).
- `POST /v1/application-capabilities/{capability_id}/bind` (PLUGINS, `approved`, `implementation_alias`, `activated`).
- `POST /v1/application-capabilities/{capability_id}/activate` (PLUGINS, `activated`).
- `POST /v1/application-capabilities/{capability_id}/invoke` (EXECUTE, body `application_id`, `input`).

### 4.2 Application Manifests (`application_manifests.py`)
- `GET /v1/application-manifests` (READ, `app_id`/`instance_id` optionnels) : `{"manifests": [...]}`.

### 4.3 Application Integration Catalog (`application_integration_catalog.py`)
- `GET /v1/application-integration/catalog` (READ) : catalogue complet avec items, sources, états.

### 4.4 GitHub Discovery (`github_discovery.py`)
- `GET /v1/github/organizations/{organization}/repositories` (READ).
- `GET /v1/github/users/{username}/repositories` (READ).

### 4.5 Local Repositories (`local_repositories.py`)
- `GET /v1/local-repositories` (READ) : liste des analyses.
- `GET/POST /v1/local-repositories/{path:path}/compatibility` (READ) : valid, status, errors, registered.
- `POST /v1/local-repositories/{path:path}/register` (PLUGINS, `approved=true`) : enregistrement d'un dépôt local.

### 4.6 Component Lifecycle (`component_lifecycle.py`, déprécié)
- CRUD opérations, détect, install/configure/start/stop/test/enable/disable/uninstall par capability_id.

### 4.7 Plugins, Skills, Connections, Domains
- `/v1/plugins`, `/v1/skills`, `/connections`, `/domains` : passerelles vers les managers Core.

---

## 5. Cas d'application concrets

| Composant | Odin | Frame | Quantar | TradingAgents |
|-----------|------|-------|---------|---------------|
| Manifest dans `examples/` | ✅ | ✅ | ✅ | ❌ (proposition test uniquement) |
| Registre d'application | ✅ `register_odin_pilot` | ✅ `register_frame_pilot` | ✅ `register_quantar_pilot` | ❌ |
| Plugin cycle de vie | ✅ `OdinService` (819 lignes) | ✅ `FrameService` (hérite ComposeService) | ✅ `QuantarService` + `QuantarTaskService` | ❌ |
| Contrat d'exécution allowlisté | ✅ `odin.runtime-status` | ✅ `frame.runtime-status` | ❌ | ❌ |
| Endpoints runtime/start/stop | ✅ | ✅ | ❌ (pas dans les routers examinés) | ❌ |
| Exécution réelle de tâches | N/A (daemon) | N/A (daemon) | ⚠️ in-process si `tradingagents` installé, Docker one-shot sinon | ❌ |
| Dépendance externe | Docker + dépôt Odin | Docker + bun + dépôt Frame | Docker + image `quantar-runtime:latest`, OU `tradingagents` Python | `tradingagents` Python + dépôt externe |
| Intervention manuelle | Cloner dépôt, Docker | Cloner dépôt, bun, Docker | Installer `tradingagents` OU build image Docker | Tout est à créer |

### 5.1 Odin — détail
- `core/plugins/odin.py` (`OdinService`, 819 lignes) : port 4173, santé HTTP `http://127.0.0.1:4173/`, redaction secrets dans les logs, contrôleur externe optionnel. **Ne hérite pas de `ComposeService`** → duplication ~700 lignes avec `core/plugins/compose_service.py`.
- `core/applications/odin_integration.py` : `ODIN_CONTROL_CAPABILITIES` (6 capacités de contrôle).
- Endpoints opérationnels si Docker + dépôt Odin présents.
- Pas d'installation automatisée du dépôt Odin, pas de mise à jour, pas d'intégration dans le CapabilityManager générique.

### 5.2 Frame — détail
- `core/plugins/frame.py` (`FrameService(ComposeService)`, port 5190, project name "frame"). Dépendance `bun`.
- Endpoints opérationnels si Docker + bun + dépôt Frame présents.
- Pas d'installation automatisée, pas de mise à jour.

### 5.3 Quantar — détail
- `core/applications/quantar_service.py` (`QuantarTaskService`, 1034 lignes) : `QuantarTask` (status PREPARED/QUEUED/STARTING/RUNNING/COMPLETED/FAILED/CANCELLED/...), `run_task()` (exécute `TradingAgentsGraph.propagate(ticker, analysis_date)` in-process si `tradingagents` importable), `run_task_in_container()` (Docker one-shot `docker compose run --rm quantar-task`), `cancel_task()`/`reconcile_tasks()`/`request_recovery()`.
- `TRADINGAGENTS_AVAILABLE = false` par défaut (pas de `tradingagents` installé dans l'environnement).
- **Aucun contrat d'exécution Quantar** dans `TRUSTED_IMPLEMENTATION_ALIASES`. **Aucun endpoint HTTP dédié** pour créer/exécuter/lister les tâches Quantar dans les routers examinés.

### 5.4 TradingAgents — détail
- Absent du dépôt ETHAN. Proposition de manifest uniquement dans `tests/core/test_dta1a_tradingagents_manifest.py` (67 lignes, `app_id: tradingagents`, capacités `research-analysis` / `research-report-generation`, interface CLI `python main.py`, provenance `/home/fatsio/AI/TradingAgents`).
- Aucun registre, aucun plugin, aucun endpoint, aucun code d'intégration ETHAN.

---

## 6. Ce qui est réellement opérationnel

### 6.1 Sans dépendance externe
| Composant | État | Preuve |
|-----------|------|--------|
| Modèle de manifest + validateur | ✅ | `models.py` + `validator.py` + tests |
| Découverte de manifests | ✅ | `discovery.py` + `catalog.py` |
| Registre d'applications | ✅ | `application_registry.py` (en mémoire, persistance optionnelle) |
| Cycle de vie applicatif (machine à états) | ✅ | `resilience.py` |
| Permissions / HROT | ✅ | `permissions.py` |
| Répertoire de manifests durables | ✅ (sauf delete) | `manifest_repository.py` |
| Catalogue d'intégration | ✅ (lecture seule) | `integration_catalog.py` |
| Découverte locale de dépôts Git | ✅ | `local_repository_discovery.py` |
| Découverte GitHub | ✅ (réseau requis) | `github_organization_discovery.py` |
| Contrats de capacités applicatives | ✅ | `capability_contract.py` |
| Exécution de contrats (odin/frame) | ✅ (si binding créé) | `capability_execution.py` |
| Registre de capacités ETHAN | ✅ | `capabilities.py` |
| Capability Manager (composants optionnels) | ✅ | `manager.py` + `backends.py` + `types.py` |
| Endpoints applications / local-repositories / github-discovery | ✅ | `applications.py` / `local_repositories.py` / `github_discovery.py` |
| Endpoints component lifecycle (déprécié) / plugins / skills / connections | ✅ | `component_lifecycle.py` / `plugins.py` / `skills.py` / `connections.py` |

### 6.2 Avec dépendance externe (Docker, dépôt application, tradingagents)
| Composant | État | Condition |
|-----------|------|-----------|
| Odin cycle de vie Docker | ⚠️ | `examples/odin/compose.yaml` présent + Docker |
| Frame cycle de vie Docker | ⚠️ | `examples/frame/compose.yaml` présent + Docker + bun |
| Quantar cycle de vie Docker | ⚠️ | Image `quantar-runtime:latest` + compose |
| Quantar exécution in-process | ⚠️ | `tradingagents` installé (pas le cas par défaut) |
| TradingAgents | ❌ | Aucun code d'intégration ETHAN |

---

## 7. Lifecycle complet : découverte → suppression

### 7.1 Découverte
1. `LocalRepositoryDiscovery.discover()` ou `ApplicationDiscoveryService.discover()` scanne le filesystem.
2. `ContractValidator.validate_manifest_data()` valide le manifest.
3. `ApplicationCatalog.refresh()` constitue le catalogue des manifests valides.
4. `IntegrationCatalogService.build()` projette découverte + registre + repository.

### 7.2 Analyse / Validation
- `ContractValidator.validate()` → `ValidationResult` (valid/invalid/incomplete/incompatible).
- Détection de conflits (duplicate app_id / instance_id).
- Analyse de dépôt (remote Git, branche, fichiers détectés, classification).

### 7.3 Enregistrement (registration)
1. `ApplicationIntegrationRegistry.register(manifest)` → `ApplicationRecord` (état REGISTERED, conformité évaluée).
2. `ApplicationCapabilityContract.from_mapping()` + `register_application_capability()` (nécessite `approved=true`).
3. Optionnel : `ApplicationManifestRepository.create()` pour stockage durable séparé.

### 7.4 Installation / Démarrage
**Composants gérés par CapabilityManager :**
1. `plan_install()` → plan d'étapes (vérification, install, start, santé).
2. `install()` → opération persistée, tâche async, transitions `INSTALLING → INSTALLED → STARTING → RUNNING → READY`.
3. `start()` / `stop()` / `test()` / `enable()` / `disable()`.
4. `uninstall()` → `SUPPORTED`, données conservées sauf `delete_data=true`.

**Applications Docker (Odin/Frame/Quantar) :**
1. `get_status()` vérifie l'état réel.
2. `install()` / `start()` / `stop()` / `uninstall()` via `ComposeService` ou `OdinService`.
3. Pas d'intégration avec `CapabilityManager` — cycle de vie isolé.

### 7.5 Mise à jour
- `ApplicationIntegrationRegistry.update_manifest(app_id, instance_id, manifest)` : met à jour le manifest, réévalue la conformité, passe en `VALIDATED`.
- `ApplicationManifestRepository.update()` : nouvelle version du manifest durable.
- **Pas de mécanisme de mise à jour du code source de l'application** (pas de git pull automatisé).

### 7.6 Suppression
- `ApplicationIntegrationRegistry.withdraw(app_id, instance_id, reason)` : état `WITHDRAWN`, `available=False`.
- `ApplicationManifestRepository.delete()` → **`NotImplementedError`**.
- `CapabilityManager.uninstall(capability_id, delete_data)` : supprime le composant, optionnellement les données.

---

## 8. Exposition des capacités aux agents

1. **Capability Registry** (`core/applications/capabilities.py`) : définitions avec `permission_set()` et `permission_mapping()`. Un agent peut vérifier qu'il a la permission requise avant d'invoquer une capacité.
2. **Application Capability Contracts** (`capability_contract.py` + `capability_execution.py`) : contrats avec `input_schema`/`output_schema` (JSON Schema), `required_permissions`, `timeout_seconds`. L'invocation passe par `invoke_capability()` qui valide le schéma d'entrée, exécute l'implémentation allowlistée, valide le schéma de sortie.
3. **Skills** (`core/skills/`) : `SkillStore`, `SkillLab` (sandbox Docker), exécution via `ChatPipeline`. Mécanisme distinct des capacités d'application.
4. **Connections** (`core/integrations/connections/`) : connexions OAuth/password vers providers externes, opérations déclarées.
5. **Tools** (router `capabilities.py`) : outils personnalisés, pipelines, serveurs d'outils MCP.

---

## 9. Permissions et isolation

### 9.1 Permissions API
`core.auth.Permission` : `READ`, `WRITE`, `EXECUTE`, `SETTINGS`, `ADMIN`, `PLUGINS`. Chaque endpoint déclare sa permission via `require_permission(Permission.X)`.

### 9.2 Permissions applicatives (HROT)
`core/applications/permissions.py` : modèle granulaire. `PermissionScope(app_id, instance_id, capability, resource, action, context_constraints)`. `PermissionGrant` nécessite `HumanAuthority` vérifiée. En mode production, vérification cryptographique via `HrotApprovalProof`. La requérante ne peut pas approuver sa propre permission. `manifest_fingerprint` lié à la grant — toute modification du manifeste invalide l'autorisation (`MANIFEST_CHANGED`).

### 9.3 Isolation des connexions
`connections.py` : l'utilisateur est déduit du JWT (`request.state.user`). Un utilisateur ne peut opérer que sur ses propres connexions. Les tokens ne sont jamais retournés.

### 9.4 Confinement Docker
`ComposeService._validate_confinement()` : le fichier compose doit être exactement `<repo>/compose.yaml`. `OdinService` a une allowlist stricte des chemins. Commandes docker compose dans une allowlist figée (`up -d`, `down`, `stop`, `restart`, `ps`, `config`, `logs --tail=N`).

### 9.5 Barrière anti-injection (Capability Manager)
`validate_install_actions()` rejette toute action non déclarée dans l'allowlist du backend. Les valeurs utilisateur sont validées contre `ConfigField` typé (string/int/bool/port avec min/max/choices) et ne parviennent jamais à une argv.

---

## 10. Observabilité

### 10.1 Événements d'intégration
`core/applications/observability.py` (`EventCollector`, `IntegrationEvent`, `OBSERVABILITY_SCHEMA_VERSION`) : `ApplicationIntegrationRegistry` enregistre des événements (registration, etc.) avec `event_id`, `schema_version`, `app_id`, `instance_id`, `timestamp`, `event_type`, `operation`, `status`, `provenance`, `evidence_refs`, `origin`.

### 10.2 Audit
`CapabilityManager` utilise `AuditStore` (`core/audit/`) et `EventBus` (`core/bus/`). Chaque mutation (install, configure, start, stop, uninstall, enable, disable) est auditée avec décision allow/erreur.

### 10.3 Opérations persistées
`_operations` dans `CoreRecordStore` (domaine `capability_operations`). Rétention 24h, 50 opérations max. Réconciliation au démarrage via `recover_operations()`. Une opération `RUNNING` interrompue passe en `TIMEOUT`.

### 10.4 Santé et logs
- `CapabilityManager.logs()` : logs réels (Docker) ou `available=False`.
- `OdinService.get_logs()` : `docker logs --tail=N` avec redaction des secrets.
- `QuantarTaskService` : logs par tâche, `get_logs(task_id, tail)`, `reconcile_tasks()` pour reprise après crash.

---

## 11. Interfaces WebUI associées
Les routers API sont consommés par les interfaces, mais aucune logique métier ne réside dans les interfaces. Interfaces identifiées : WebUI (consomme `/v1/applications`, `/v1/local-repositories`, `/v1/components`, `/v1/plugins`, `/v1/skills`, `/connections`), Open WebUI adapter (`interfaces/api/routers/openwebui.py`), Odin AI (`interfaces/api/routers/odin_ai.py`), Frame (`interfaces/api/routers/frame.py`). Aucune interface WebUI spécifique n'implémente de logique DTAI.

---

## 12. Duplications identifiées

1. **`core/plugins/odin.py` vs `core/plugins/compose_service.py`** : ~700 lignes dupliquées (start, stop, restart, install, uninstall, get_status, get_logs, _build_status_dict, _run_docker). `OdinService` ne hérite pas de `ComposeService` contrairement à `FrameService` et `QuantarService`.
2. **Manifests odin/frame/quantar** : même digest SHA-256 (`17f4307a...`) sur les trois — valeur non récalculée, probablement un placeholder.
3. **`skills.py` vs `skills_import.py`** : duplication des endpoints `/skills/export` et `/skills/import` (deux routers pour la même fonctionnalité).
4. **`ApplicationIntegrationRegistry` vs `ApplicationRegistry` vs `IntegrationRegistry`** : alias multiples pour la même classe.
5. **`ApplicationDiscoveryService`** : ~12 alias (`CapabilityDiscoveryService`, `ManifestDiscoveryService`, `ApplicationDiscovery`, etc.).

---

## 13. Ce qui manque pour un processus DTAI reproductible

| Domaine | Manquant | Impact |
|---------|----------|--------|
| Installation automatisée | Pas de git clone automatisé des dépôts d'application | L'opérateur doit manuellement placer les dépôts dans `examples/` |
| Mise à jour des applications | Pas de mécanisme `git pull` / mise à jour de version | Impossible de maintenir une application à jour via l'API |
| Bindings de capacité persistants | Stockés en attribut dynamique du registry | Perdus au redémarrage de l'API |
| TradingAgents | Aucun code d'intégration ETHAN | Cas d'application inexistant |
| Quantar endpoints HTTP | Pas de router dédié pour créer/exécuter/lister les tâches | Moteur Quantar existant mais non exposé via les routers DTAI |
| Suppression de manifest | `NotImplementedError` | Impossible de purger un manifest durable |
| Intégration Odin/Frame dans CapabilityManager | Cycle de vie isolé dans `OdinService`/`FrameService` | Deux chemins de cycle de vie parallèles |
| WebUI DTAI dédiée | Aucune interface spécifique identifiée | Les interfaces consomment l'API générique sans vue spécialisée |
| Tests E2E | Pas de test E2E complet (découverte → enregistrement → installation → démarrage → arrêt → suppression) avec Docker réel | Maturité opérationnelle non prouvée en bout en bout |

---

## 14. Tests existants
- `tests/core/test_dta1a_tradingagents_manifest.py` : proposition de manifest TradingAgents (test uniquement).
- `tests/core/test_quantar_real_task_runtime.py` : simule TradingAgents avec des faux modules (prouve la logique, pas l'exécution réelle).
- Pas de test E2E découverte → enregistrement → installation → démarrage → arrêt → suppression avec Docker réel.

Fin de l'évaluation DTAI.
