# ESR-001 — Capability Model

**Statut** : Implémenté
**Date** : 2026-09-23
**Décision parente** : [ADR-4001](/docs/architecture/adr/ADR-4001-capability-manager.md)
**Code** : [`core/capability_manager/types.py`](/core/capability_manager/types.py),
[`core/capability_manager/builtin.py`](/core/capability_manager/builtin.py)

> ⚠️ Homonymie : ce modèle décrit le cycle de vie des **composants
> optionnels**. Le système de *permissions* agents est documenté dans
> `docs/security/05-capability-system.md` — ce sont deux concepts distincts.

---

## 1. Structure d'une capability

`CapabilitySpec` (dataclass **frozen**, définie par le développeur) :

| Champ | Type | Description |
|---|---|---|
| `id` | `str` | Identifiant unique (`qdrant`, `memory`…) |
| `name` | `str` | Nom affichable |
| `description` | `str` | Description utilisateur |
| `type` | `CapabilityType` | Catégorie de composant |
| `backend` | `str` | `docker` \| `python_package` \| `node_package` \| `executable` \| `builtin` |
| `version` | `str` | Version de référence |
| `requires_confirmation` | `bool` | Plan à confirmer avant exécution |
| `dependencies` | `tuple[Dependency]` | Dépendances système/capability |
| `config_schema` | `tuple[ConfigField]` | Champs de configuration typés |
| `install_actions` | `tuple[dict]` | Actions d'installation (allowlist par backend) |
| `start_actions` / `stop_actions` | `tuple[dict]` | Actions de démarrage/arrêt |
| `uninstall_actions` | `tuple[dict]` | Actions de désinstallation |
| `data_resources` | `tuple[dict]` | Données persistées (kind, name/path, description) |
| `health_checks` | `tuple[HealthCheck]` | Paliers de vérification |

**Invariants** : la spec est immuable en persistance ; le backend valide
les actions à l'enregistrement (`validate_install_actions` — une action
inconnue **refuse l'enregistrement** de la capability) ; `backend` doit
appartenir à `BACKENDS` et le type à `CapabilityType.ALL` (validation
explicite `CapabilitySpec.validate()`, invoquée par
`CapabilityManager.register()`).

## 2. Types

`CapabilityType` : `provider`, `model`, `vector_database`, `runtime`,
`service`, `integration`, `tool`, `embedding`, `reranker`, `stt_tts`,
`mcp_server`, `plugin`, `skill`.

## 3. États (12)

```text
SUPPORTED · NOT_INSTALLED · INSTALLING · INSTALLED · STARTING · RUNNING
STOPPED · UNHEALTHY · CONFIGURATION_REQUIRED · READY · UNINSTALLING · ERROR
```

Machine à états (`CapabilityState.TRANSITIONS`, extraits) :

```text
SUPPORTED              → NOT_INSTALLED, ERROR
NOT_INSTALLED          → INSTALLING
INSTALLING             → INSTALLED, ERROR, NOT_INSTALLED (rollback)
INSTALLED              → STARTING, CONFIGURATION_REQUIRED, UNINSTALLING, ERROR
STARTING               → RUNNING, UNHEALTHY, ERROR, STOPPED
RUNNING                → READY, UNHEALTHY, STOPPED, ERROR
READY                  → RUNNING, UNHEALTHY, STOPPED, ERROR, UNINSTALLING
UNHEALTHY              → STARTING, STOPPED, UNINSTALLING, ERROR, READY
UNINSTALLING           → SUPPORTED, ERROR
ERROR                  → NOT_INSTALLED, SUPPORTED, INSTALLING, UNINSTALLING, ERROR
```

Ensembles utiles : `BUSY = {INSTALLING, STARTING, UNINSTALLING}` (aucune
mutation concurrente) ; `READY_STATES = {READY, RUNNING, STOPPED}`.
Transition illégale → `TransitionError` (→ HTTP 409).

## 4. Métadonnées exposées (status)

`CapabilityRuntimeState` (persisté, domaine `capability_manager` du
CoreRecordStore) : `state`, `enabled`, `config` (write-only, jamais
renvoyé tel quel), `installed_version`, `last_error` (tronqué à 200–300
caractères), `runtime_meta`, `updated_at`.

## 5. Dépendances

`Dependency(id, kind, command, description, optional)` — kinds gérés :
`system` (présence d'un exécutable dans le PATH, ex. `docker`, `python3`),
`capability` (autre composant ETHAN, avec états acceptés). Une dépendance
non `optional` manquante bloque l'installation (état reste `SUPPORTED`,
message explicite).

## 6. Configuration

`ConfigField(name, type, required, default, description, min_value,
max_value, choices)` — types : `string`, `int`, `bool`, `port`.
Validation stricte (`_validate_config`) : champs inconnus refusés, bornes
min/max appliquées, `choices` fermés, scalaires uniquement — voir
[ESR-006](/docs/engineering/esr/ESR-006-security-model.md). Les valeurs
sont substituées dans la spec via `{config.<field>}` (jamais l'inverse).

## 7. Health checks

`HealthCheck(kind, level, …)` :

| Kind | Vérification réelle |
|---|---|
| `tcp` | Connexion TCP à `{config.host}:{config.<port>}` (timeout 2 s) |
| `endpoint` | HTTP GET sur une URL déclarée résolue (timeout 3 s) |
| `exec` | Commande **figée dans la spec** (jamais d'input utilisateur) |
| `builtin` | Composant intégré : process Core vivant (pid) |

Levels : `basic` (présence réseau) < `functional` (API répond correctement).
**READY exige que tous les checks `functional` passent** — un composant
seulement joignable en TCP reste `UNHEALTHY`/`RUNNING`, jamais `READY`.

Résolution de `{config.<field>}` : valeur saisie par l'utilisateur, sinon
le **défaut déclaré** par `config_schema` — un composant qui tourne sur les
défauts n'est jamais jugé « santé refusée » (le check part réellement avec
la valeur effective).

## 8. Cycle de vie

Pipeline détaillé : [ESR-002](/docs/engineering/esr/ESR-002-installation-engine.md).
Catalogue intégré actuel (`builtin.py::registry()`) : `memory` (`builtin`),
`ollama` (`executable`), `qdrant`, `redis`, `searxng` (`docker`),
`chromadb`, `whisper` (`python_package`), `mcp-filesystem`
(`node_package`). Exemple complet de spec : `qdrant()` (5 actions
d'installation, 2 health checks, volume de données, 3 champs de config).