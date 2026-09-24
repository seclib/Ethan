# ETHAN — Architecture Cible Officielle

**Statut** : Référence opposable (ce document fait autorité)
**Date** : 2026-09-24
**Auteur** : CTO / Enterprise Architect
**Méthode** : audit du dépôt au commit `676403a3` (lecture de code, pas de supposition)
**Portée** : Core, API, interfaces (WebUI/CLI/Desktop), services, données, sécurité

> **Principe directeur** — ETHAN Core est la source unique de vérité.
> L'API est une passerelle. La WebUI est une projection. Aucune interface ne
> recrée une capacité déjà présente dans Core (Première Loi, `AGENTS.md`).

---

## 0. Gouvernance documentaire (préalable)

`docs/architecture/` contient **31 documents**, dont plusieurs propositions
concurrentes non tranchées (`proposed.md`, `ETHAN_WEBUI_TARGET_ARCHITECTURE.md`,
`webui-platform-architecture-assessment.md`, `api-core-boundary-refactoring.md`,
`consolidation-plan.md`, `migration-report.md`…). C'est un risque en soi : sans
hiérarchie, chaque nouvelle demande produit un 32ᵉ document.

**Règle adoptée à compter de cette date :**

| Niveau | Document | Rôle |
|---|---|---|
| 1 | **`ARCHITECTURE-CIBLE.md`** (ce document) | Fait autorité : périmètre, frontières, statuts |
| 2 | `adr/ADR-*.md` | Une décision = un ADR, avec preuve d'implémentation |
| 3 | `engineering/esr/ESR-*.md` | Spécifications d'exécution (mécanismes) |
| 4 | `C4-*.md`, `current.md` | Vues descriptives de l'existant (non décisionnelles) |
| 5 | Tout autre document | **Historique** : conservé pour trace, ne fait plus foi |

Toute décision nouvelle doit soit modifier un ADR existant, soit en créer un
(numérotation par domaine : `3xxx` données/domaines, `4xxx` capacités/plateforme).

### Écart dépôt ↔ doctrine (aucun impact runtime)

`AGENTS.md` cite une source de vérité `core/ runtime/ services/`. Le dépôt réel
est `core/ interfaces/ plugins/ deploy/` : **il n'existe ni `runtime/` ni
`services/`**. Le « Runtime » est en pratique `core/modules/` (modules cognitifs
NATS, lancés par `python -m core.modules`) et `core/kernel.py`, dans `core/`.
Décision : **D-00** (§4).

---

## 1. Architecture cible

```text
┌───────────────────────────────────────────────────────────────────────┐
│ INTERFACES (révèlent ETHAN, ne le définissent pas)                    │
│   WebUI (Next.js)   CLI (interfaces/cli)   Desktop   Channels/Shell   │
└───────────────┬───────────────────────────────────────────────────────┘
                │  HTTP/SSE + contrats versionnés /v1  (JWT, RBAC)
┌───────────────▼───────────────────────────────────────────────────────┐
│ API — passerelle mince (interfaces/api)                               │
│   • routers/<domaine>.py : mapping REST → Core, aucune règle métier    │
│   • auth_middleware : JWT/cookie → request.state.user + permissions    │
│   • injection des managers Core (set_*_manager), pas d'état métier     │
└───────────────┬───────────────────────────────────────────────────────┘
                │  appels directs Python (managers) + Event Bus
┌───────────────▼───────────────────────────────────────────────────────┐
│ CORE — source de vérité (core/)                                       │
│   Domaines : projects · chat/conversations · llm (providers, models,  │
│   capabilities) · agents · knowledge · rag · memory · skills · tools  │
│   (MCP) · integrations · plugins · folders · domains · missions ·     │
│   goals                                                               │
│   Transverse : state (record_store), config, auth, security, safety,  │
│   telemetry/metrics, capability_manager (composants), bus, scheduler, │
│   modules (Runtime cognitif), kernel, planner, orchestrator           │
└───────────────┬───────────────────────────────────────────────────────┘
                │  clients (NATS, asyncpg, redis, HTTP providers)
┌───────────────▼───────────────────────────────────────────────────────┐
│ SERVICES (deploy/, docker-compose.yml — 8 conteneurs)                 │
│   nats · redis · postgres · pg_backup · api · kernel · modules · ui    │
└───────────────────────────────────────────────────────────────────────┘
```

### 1.1 Matrice domaine → source de vérité → état audité

| Domaine | Source de vérité (Core) | Surface API | État audité (2026-09-24) |
|---|---|---|---|
| **Projects** | `core/projects/__init__.py` — `ProjectManager` (481 l.) | `routers/projects.py` (passerelle fine) | ✅ Implémenté (ADR-3003 à requalifier) |
| **Conversations** | `core/state/chats.py` (`ChatStore`) + `core/chat/` (session, pipeline, compaction, modes) | `routers/message.py`, `/v1/chat` (dans `v1.py`) | ⚠ Nommage dispersé, pas de domaine `conversations` → **D-02** |
| **Providers** | `core/llm/provider_manager.py` | `routers/providers.py` (CRUD, test, default, capabilities) | ✅ Implémenté (ADR-3002 à requalifier) |
| **Models** | `core/llm/model_store.py`, `registry.py`, `selector.py` | `routers/models.py` | ✅ Implémenté |
| **Capabilities (modèle)** | `core/llm/types.py` : `ProviderCapability`, `TaskType`, `LLMRequirements` | `routers/providers.py` (`/capabilities`) | ✅ Implémenté ; aucune notion « Profile » → **D-05** |
| **Agents** | `core/agents/` | `v1.py` | ✅ Implémenté |
| **Knowledge / RAG** | `core/knowledge/manager.py` + `core/rag/` (pipeline unique) | `routers/knowledge_imports.py`, `web_ingest.py` | ✅ Pipeline unique ; **pas de watcher** → **D-07** |
| **Components** | `core/capability_manager/` (detect→install→configure→test→enable→disable→uninstall) | `routers/component_lifecycle.py` (argv-only) | ✅ Implémenté (ADR-4001..4004) |
| **Skills** | `core/skills/manager.py` | `v1.py` | ✅ Implémenté |
| **Plugins** | `core/plugins/` (validator, registry, catalog) + `plugins/` (sdk) | `routers/plugins*`, CLI | ✅ Implémenté |
| **MCP** | `core/tools/mcp_client.py`, `servers.py`, `manager.py` | `v1.py`, `tools` | ✅ Client MCP dans le Core |
| **Integrations** | `core/integrations/` (credentials isolés, jamais exposés) | `routers/integrations.py`, `connections.py` | ✅ Implémenté + règle secrets |
| **AuthN** | `core/auth/` (users, api_keys, ldap, oauth, scim, totp, password_reset) | `interfaces/api/auth.py` | ✅ Implémenté |
| **AuthZ** | `core/auth/groups.py` + `Permission` | `require_permission(...)` par route | ✅ Implémenté |
| **Persistence** | `core/state/record_store.py` (`CoreRecordStore`) | — | ⚠ 2 chemins résiduels (`ethan_config`, `CoreWebUIStore`) → **G-01/G-02** |
| **Configuration** | `core/config/` (service, schema, secrets, prompts) | `routers/config.py` | ⚠ `config/store.py` écrit encore `ethan_config` (ADR-3001) |
| **Installation** | `core/capability_manager/` + `scripts/cmd-*.sh` + `Makefile` | `./ethan`, `make bootstrap` | ✅ Implémenté |
| **Observabilité** | `core/telemetry/`, `core/metrics/`, `core/diagnostics/` | `routers/diagnostics.py` | ✅ Implémenté |
| **Sécurité** | `core/security/` (policy, validation, prompt_guard, anti-exfiltration) + `core/safety/` | `routers/security.py` | ✅ Implémenté |
| **Extensibilité** | `core/plugins/` + `plugins/` + `core/skills/` + `capability_manager` | CLI/API | ✅ Implémenté |

**Lecture CTO** : sur les 20 décisions demandées, **17 sont déjà implémentées
conformément à la cible**. Les 3 écarts restants sont identifiés nommément
(§4 G-01/G-02, ADR-3001/3004) ; aucun ne remet en cause l'architecture.

---

## 2. Diagrammes de dépendances

### 2.1 Graphe d'imports autorisés (contrats vérifiables)

Ce graphe est **déjà vérifié automatiquement** par `lint-imports`
(configuration `pyproject.toml`) — état mesuré : **5 kept / 0 broken**.

```text
interfaces/*  ────────►  core/*            (RÈGLE 4 : jamais de legacy)
                              ▲
plugins/*     ────────────────┘            (RÈGLE 5 : jamais core.llm)
core/agents/* ──► core/*  (hors core/agents/* entre eux)   (RÈGLE 2)
core/bus/*    ──► core/bus + types seuls   (RÈGLE 3 : pas d'impl. LLM/skills)
core/kernel*  ──► ne dépend d'aucun plugin (RÈGLE 1)
```

| Règle | Interdiction | Justification |
|---|---|---|
| R1 | `core.kernel`/périmètre kernel → `plugins.*` | Le noyau ne dépend d'aucune extension |
| R2 | `core.agents.*` entre eux | Agents indépendants (ADR-001) |
| R3 | `core.bus` → implémentations LLM/skills | Bus = transport, pas d'intelligence |
| R4 | `interfaces.*` → legacy | Les interfaces ne consomment que le Core |
| R5 | `plugins.*` → `core.llm` | Les plugins ne couplent pas le moteur LLM |

### 2.2 Flux d'une requête de chat (chemin nominal)

```text
WebUI (composer)
  └─► POST /v1/chat {messages, project_id?, model?}      [JWT + RBAC]
        └─► API : auth_middleware → user_id/roles
              └─► Core : ChatStore (persistance) + core/chat/pipeline.py
                    ├─► ProjectManager.resolve_context(project_id)
                    │      → instructions, agent, provider/model par défaut
                    ├─► Memory/KAG : core/memory + core/rag/retrieval.py
                    │      → contexte assemblé (jamais de second pipeline)
                    ├─► core/llm/router.py + selector.py
                    │      → choix provider/modèle selon ProviderCapability
                    └─► Provider LLM (HTTP) ── streaming ──┘
        └─► Event Bus (NATS) : événements de cycle de vie (chat.*, llm.*)
              └─► modules cognitifs (core/modules) : mémoire, learning, autonomy
```

**Frontières** : la WebUI ne choisit pas le provider (elle affiche le défaut du
projet et peut le surcharger explicitement) ; elle ne construit pas le contexte ;
elle ne parle jamais à un provider LLM directement.

### 2.3 Flux d'installation d'un composant (optionnel)

```text
WebUI (dialogue « Composant »)
  └─► POST /v1/components/{id}/install      [permission ADMIN/SETTINGS/EXECUTE]
        └─► API component_lifecycle.py : passerelle mince (argv-only)
              └─► Core capability_manager.manager
                    ├─ détect → install → configure → test → enable
                    ├─ backends : docker / local (script.sh + install.sh, JSON Schema)
                    ├─ état persisté dans CoreRecordStore (source de vérité)
                    └─ events (NATS) : component.*
```

**Interdits** (déjà respectés, à préserver) : la WebUI ne lance **jamais**
`docker`/`ollama` ni un shell ; aucune chaîne utilisateur n'atteint un argv
(validation par `ConfigField`/JSON Schema dans le Core).

### 2.4 Flux de persistance

```text
manager Core (projects, folders, domains, agents, skills, missions, …)
  └─► CoreRecordStore (core/state/record_store.py)
        ├─ PostgreSQL : table générique `core_domain_records`
        │    (domain, record_id, record JSONB, created_at, updated_at)
        ├─ Redis : cache d'état live (jamais source de vérité)
        └─ fallback in-memory (dev/test uniquement)
Configuration providers : table `llm_providers` (config JSONB, SANS secrets)
Secrets : core/config/secrets.py (env/Vault/Docker secrets) — jamais en base
```

---

## 3. ADR / ESR — inventaire et requalification

### 3.1 ADR existants : statut documentaire vs statut **audité**

| ADR | Sujet | Statut doc | **Statut audité (preuve)** |
|---|---|---|---|
| ADR-3001 | Store de records unifié (`ConfigStore`+`WebUIStore` → `CoreRecordStore`) | Proposition | ❌ **Non implémenté** : `core/config/store.py` lit/écrit encore la table `ethan_config` ; `CoreWebUIStore` subsiste |
| ADR-3002 | Providers : `ProviderManager` seule source de vérité | Proposition | ✅ **Implémenté** : aucun `_DEFAULT_PROVIDERS` dans `core/` ni `interfaces/` |
| ADR-3003 | Domaine `Projects` | Proposition | ✅ **Implémenté** : `core/projects/` (`ProjectManager`, gestion documents/événements) + `routers/projects.py` |
| ADR-3004 | Back-end de vecteurs unique | Proposition | ❌ **Non tranché** : `core/memory/chromadb_backend.py` **et** `qdrant_backend.py` coexistent avec `core/rag/vector_store.py` |
| ADR-3005 | Folders vs Domains : pas de fusion | Proposition | 🟡 **Partiel** : helpers identiques mutualisés (`core/attachments.py`) ; divergence fail-closed/permissive documentée (`docs/hardening.md` §3.1) |
| ADR-3006 | Contrats API versionnés (OpenAPI + tests de contrat) | Proposition | 🟡 **Partiel** : `tests/cli/ethan/regression/test_api_contracts.py` + `APIResponseValidator` existent, non généralisés |
| ADR-4001 | Capability Manager centralisé dans le Core | Implémenté | ✅ Confirmé (`core/capability_manager/`) |
| ADR-4002 | Installation à la demande (supported ≠ installed ≠ running ≠ ready) | Implémenté | ✅ Confirmé (`types.py` machine à états) |
| ADR-4003 | `uninstall` ≠ delete data (double confirmation) | Implémenté | ✅ Confirmé (`_check_dependent_enabled`, `confirm_delete_data`) |
| ADR-4004 | Core = source de vérité de l'état des composants | Implémenté | ✅ Confirmé (`detect`, `_load_state`/`_save_state`) |

**Action CTO** : les 6 ADR en « Proposition » portent désormais une ligne
« État audité 2026-09-24 » (§3.2). Aucun ADR n'est supprimé.

### 3.2 ADR à créer (écarts réels, non couverts)

| ADR proposé | Sujet | Déclencheur |
|---|---|---|
| **ADR-3007** | Domaine `Conversations` : un seul modèle de conversation (`core/chat` + `ChatStore`), nommage et surface API unifiés | Le nommage « chat/conversation/message » est dispersé entre `core/chat/`, `core/state/chats.py`, `v1.py`, `routers/message.py` (D-02) |
| **ADR-3008** | Découpage du router monolithe `v1.py` (2031 l., 96 routes) en routeurs par domaine | Maintenabilité ; aucune logique métier à déplacer (déjà délégué), seulement de la structure |
| **ADR-3009** | `core/security/*` : périmètre et reconnaissance du domaine (policy, validation, prompt_guard, anti-exfiltration) | Domaine transverse non formalisé dans un ADR alors qu'il porte des invariants de sécurité |
| **ADR-3010** | MCP : ownership Core (`core/tools/mcp_client.py` + `servers.py`) et frontière WebUI (affichage/ACL uniquement) | MCP est implémenté sans décision tracée ; risque de réimplémentation côté UI |

### 3.3 ESR existants (mécanismes)

`docs/engineering/esr/` : ESR-001 (modèle de capacité), ESR-002 (moteur
d'installation), ESR-003 (provisioning Docker), ESR-004 (provisioning local),
ESR-005 (Capability Manager dans la WebUI), ESR-006 (modèle de sécurité).
**Ces ESR couvrent les mécanismes d'installation/composants** : à réutiliser,
ne pas recréer.

---

## 4. Décisions prises

### 4.1 Les décisions d'architecture (statut validé par audit)

| # | Décision | Statut | Preuve / référence |
|---|---|---|---|
| 1 | **Séparation WebUI/Core** : la WebUI ne contient aucune logique métier, ne persiste aucun état métier, n'exécute rien | ✅ Appliqué | `routers/*.py` = passerelles ; `v1.py` n'a plus de `MemoryStore` (setters injectés depuis `interfaces/api/main.py`) |
| 2 | **Projects** : espace de travail persistant (instructions, fichiers, conversations, contexte, provider/modèle + agent par défaut, knowledge) | ✅ Implémenté | `core/projects/__init__.py` : `instructions`, `folder_ids`, `knowledge_ids`, `collection_ids`, `skill_ids`, `tool_ids`, `agent_id`, `provider_id`, `model`, `resolve_context()`, documents RAG |
| 3 | **Conversations** : historique propre, héritant du contexte du Project | 🟡 Partiel | `core/state/chats.py` + `core/chat/pipeline.py` ; rattachement `project_id` à uniformiser → ADR-3007 |
| 4 | **Providers** = service/runtime fournissant des modèles | ✅ Implémenté | `core/llm/provider_manager.py` + 13 providers (`ollama`, `openai`, `anthropic`, `vllm`, `llamacpp`, `lmstudio`, `openrouter`, `azure`, `gemini`, `openai_compatible`…) |
| 5 | **Models** = modèle utilisable, rattaché à un provider | ✅ Implémenté | `core/llm/model_store.py`, `ModelInfo` (`context_length`, `pricing`, `quality_score`, `is_local`, `is_private`) |
| 6 | **Capability** = capacité normalisée du provider/modèle | ✅ Implémenté | `core/llm/types.py` : `ProviderCapability` (llm, vision, embedding, speech_to_text, transcription) + `ModelInfo.capabilities` (chat, code, reasoning…) avec garde anti-sélection croisée |
| 7 | **Usage/Profile** = catégorie d'usage **uniquement si réellement supportée** | ❌ Non supporté → refusé | Seuls existent `TaskType` et `UsageStats` (tokens). Aucun « profile » : **ne pas inventer** → D-05 |
| 8 | **Agents** : spécialisés, indépendants, communicants par événements | ✅ Implémenté | `core/agents/` + ADR-001 + RÈGLE 2 |
| 9 | **Knowledge/RAG** : pipeline unique, **aucun second pipeline parallèle** | ✅ Implémenté | `core/rag/{ingestion,pipeline,retrieval,vector_store,embeddings,extractors}.py` ; `ProjectManager` **délègue** l'ingestion |
| 10 | **Components** : toute opération privilégiée passe par le Core | ✅ Implémenté | `core/capability_manager/` + `component_lifecycle.py` (argv-only, jamais de shell, RBAC) |
| 11 | **Skills** : registre + exécution dans le Core | ✅ Implémenté | `core/skills/` (manager, registry, executor, validation, lab, composer, selector) |
| 12 | **Plugins** : manifest + sandbox + validation Core | ✅ Implémenté | `core/plugins/{validator,registry,catalog,types}` + `plugins/` (sdk) |
| 13 | **MCP** : client et serveurs d'outils possédés par le Core | ✅ Implémenté, décision à tracer | `core/tools/{mcp_client,servers,manager}.py` → ADR-3010 |
| 14 | **Integrations** : Core-owned ; credentials **jamais** exposés | ✅ Implémenté | `core/integrations/` (domaine `integration-credentials` ; réponses publiques = `credential_keys` uniquement) |
| 15 | **Authentication** : Core-owned (users, sessions, 2FA, OAuth/LDAP/SCIM) | ✅ Implémenté | `core/auth/` + `interfaces/api/auth.py` |
| 16 | **Authorization** : RBAC par permissions, appliqué à chaque route | ✅ Implémenté | `core/auth.Permission` + `require_permission(...)` |
| 17 | **Persistence** : document-store unifié (JSONB) + Redis cache + secrets hors base | 🟡 Partiel | `CoreRecordStore` + table `core_domain_records` ✅ ; **résidus** `ethan_config` + `CoreWebUIStore` → G-01/G-02 |
| 18 | **Configuration** : `core/config/` (schéma + service), secrets via `secrets.py` | ✅ Implémenté | `core/config/{service,schema,jsonschema,secrets,prompts}.py` |
| 19 | **Installation/dépendances** : une seule voie (`./ethan`, `make bootstrap`) | ✅ Implémenté | `scripts/cmd-*.sh`, cible `bootstrap` du `Makefile`, `install/install.sh` déprécié |
| 20 | **Observabilité** : télémétrie, métriques, diagnostics Core | ✅ Implémenté | `core/telemetry/`, `core/metrics/`, `core/diagnostics/` |
| 21 | **Sécurité** : policy, validation, prompt-guard, anti-exfiltration, circuit breaker | ✅ Implémenté | `core/security/` (+ `data/`), `core/safety/circuit_breaker.py` |
| 22 | **Extensibilité** : plugins + skills + capabilities, sans modifier le noyau | ✅ Implémenté | `plugins/` + `core/plugins/` + `core/skills/` + `capability_manager` |

### 4.2 Décisions additionnelles tranchées dans ce document

| ID | Décision | Motif |
|---|---|---|
| **D-00** | La doctrine `runtime/` + `services/` de `AGENTS.md` est **réinterprétée** : Runtime = `core/modules/` + `core/kernel.py` ; Services = `deploy/` + `docker-compose.yml`. Aucun déplacement de code | La frontière réelle est fonctionnelle et **déjà vérifiée** par `lint-imports` ; créer des dossiers par symétrie documentaire coûterait cher sans bénéfice |
| **D-01** | **Aucun secret** dans le code, les logs, les événements ou les records : uniquement `core/config/secrets.py` (env/Vault/Docker secrets) | Règle projet ; appliquée par Providers (`llm_providers` sans clés) et Integrations (`integration-credentials`) |
| **D-02** | Vocabulaire produit officiel : **« Conversation »**, implémenté par `core/chat/` + `ChatStore` ; l'API expose `/v1/conversations` avec alias de compatibilité | Un seul modèle de conversation, évite le double historique `/chats` vs `/v1/chat` |
| **D-03** | Les **associations** (Projet ↔ folders/knowledge/collections/skills/tools/agents) sont **des identifiants**, jamais des copies | `ProjectManager` ; évite la duplication de ressources |
| **D-04** | Un projet **« General (Default) »** est une **entité virtuelle** (`_general_project`, jamais persistée), toujours disponible | Zéro friction à la première utilisation (UX « simple by default ») |
| **D-05** | **Pas de notion « Profile/Usage »** tant que le Core ne la porte pas | `TaskType` + `UsageStats` suffisent ; ne pas créer de concept UI-only |
| **D-06** | **Isolation progressive** : toute installation/opération privilégiée passe par `capability_manager` (machine à états + JSON Schema) ; jamais de shell, seulement des `argv` | Sécurité (ESR-002/003/004) |
| **D-07** | L'ingestion repose sur le **pipeline RAG unique** + jobs (`KnowledgeImportManager`) ; **aucun document watcher n'existe** | Audit : ni classe `*Watcher` dans `core/`, ni service `watcher` au compose → **prémisse du brief corrigée** ; un watcher éventuel serait un déclencheur *du* pipeline, jamais un second pipeline |

### 4.3 Écarts ouverts (Gaps) — seuls chantiers justifiés

| ID | Écart constaté | Impact | Traitement |
|---|---|---|---|
| **G-01** | `core/config/store.py` lit/écrit encore la table `ethan_config` | Configuration écrite à deux endroits → valeurs divergentes possibles entre onglets Settings et managers | ADR-3001 à implémenter : `ConfigStore` devient façade sur `CoreRecordStore`, migration `ethan_config` → `core_domain_records` |
| **G-02** | `CoreWebUIStore` (`core/state/webui_store.py`) subsiste et est injecté dans `v1.py` / `interfaces/api/main.py` | Dernier chemin de vérité parallèle côté records WebUI | Suppression progressive, domaine par domaine (ADR-3001/3002) |
| **G-03** | `core/memory/{chromadb_backend,qdrant_backend}.py` + `core/rag/vector_store.py` coexistent | Risque de double écriture d'index | ADR-3004 : trancher le backend de vecteurs unique |
| **G-04** | `interfaces/api/routers/v1.py` : 2031 lignes, 96 routes | Maintenabilité, revues difficiles (pas de logique métier en cause) | ADR-3008 : découpage par domaine, sans changer les URLs — **partie doublons résolue (V1.5)** : les 5 paires (GET+POST `/users`, GET `/diagnostics{,/metrics}`, GET `/v1/tools`) supprimées, contrat à zéro doublon |
| **G-05** | ADR-3005 : divergence `FolderManager` (fail-closed) / `DomainManager` (permissif) | Relations « fantômes » possibles côté domains | RFC produit → aligner Domain sur fail-closed (`docs/hardening.md` §3.1) |
| **G-06** | Contrats API non généralisés (ADR-3006) | Régressions silencieuses côté WebUI | ✅ **Traité (V1)** — `tests/test_api_contract_p0.py` : 6 contrats figés (92 routes P0, RBAC 401 sans token sauf `/health*`, **zéro doublon** — les 5 doublons G-04/ADR-3008 ont été supprimés le 24/09/2026, couverture OpenAPI, santé publique, plafond `response_model`) |
| **G-07** | 31 documents d'architecture, plusieurs propositions non tranchées | Décisions ambiguës, doublons de débat | §0 de ce document (hiérarchie) + requalification des ADR |
| **G-08** | `docs/hardening.md` : `example_usage.py` (`SafetyValidator` disparu) et `tests/test_web_search.py` (module non committé) | Bruit CI sur clone vierge | ✅ **Traité (V1)** — `64c9b546` modules web + `92d0c396` `core/network` committés, `e648454b` exemple safety réécrit, `9fe0f638` import mort `ContentFilter` retiré |
| **G-09** | Ruff structurellement rouge : 1130 erreurs `ruff check` + 432 fichiers à reformater → job « Lint & Static Analysis » de la CI en échec depuis 3 pushes (jobs aval jamais exécutés) | CI rouge permanente masque tests/builds | ✅ **Traité (V1.5)** — CI pinnée `ruff==0.15.1` / `import-linter==2.13`, puis big-bang `ruff check --fix` + `ruff format` sur worktree détaché (`5ee65c47`..`cc74225e`, 992 fichiers) : **0 erreur `ruff check` / 0 écart `ruff format`** ; effectué sans committer le WIP local (ports ciblés vérifiés par la suite complète) |

---

## 5. Décisions volontairement différées

| ID | Sujet | Pourquoi différer | Critère de déclenchement | Propriétaire |
|---|---|---|---|---|
| **DEF-01** | Fusion complète `ConfigStore`/`WebUIStore` → `CoreRecordStore` (ADR-3001) | Migration de données + double écriture transitoire ; à faire **après** gel des contrats config | Dès qu'un ADR-3001 révisé est approuvé ; migration `ethan_config` avec rollback | Architecture + Data |
| **DEF-02** | Backend de vecteurs unique (ADR-3004) | Choix produit coûteux : `pgvector` (déjà disponible) vs Qdrant/Chroma ; impact sur le mode dev | Après mesure réelle des besoins (latence/mémoire) et décision d'exploitation | Architecture + SRE |
| **DEF-03** | Politique unique Folders/Domains (ADR-3005) | Décision **produit**, pas technique (fail-closed peut être perçu comme rigide) | Validation produit de l'alignement fail-closed | Produit |
| **DEF-04** | Notion « Profile/Usage » (D-05) | Aucun besoin Core démontré ; risque de concept UI-only | Si un besoin réel apparaît (ex. routage par persona), alors ADR dédié **avec modèle Core** | Produit + Core |
| **DEF-05** | Document watcher (surveillance de dossier → ingestion) | N'existe pas ; le besoin n'est pas établi. Il serait un simple **déclencheur** du pipeline unique | Si un cas d'usage réel est validé (dossier surveillé, drive monté) | Core |
| **DEF-06** | Découpage de `v1.py` (ADR-3008) | Refactoring sans valeur fonctionnelle immédiate ; à faire en tâche de fond, sans changer les URLs | Avant toute nouvelle grosse fonctionnalité sous `/v1` | Core/API |
| **DEF-07** | Génération des types TypeScript depuis OpenAPI (ADR-3006) | Nécessite contrats stabilisés d'abord | Après gel des contrats des domaines P0 | API + WebUI |
| **DEF-08** | Temps réel (SSE/WebSocket alimenté par NATS) | `routers/realtime.py` existe ; généralisation à trancher | Après le chat unifié (ADR-3007) | Runtime + WebUI |
| **DEF-09** | Archivage des docs d'architecture obsolètes (G-07) | Déplacer/supprimer des docs peut casser des liens | Lors de la prochaine revue trimestrielle | Documentation |

**Règle** : une décision différée n'est pas une décision implicite. Tant qu'elle
n'est pas tranchée, **le comportement actuel fait foi** et aucune interface ne
doit anticiper le futur (pas de champ « profile » pré-créé, pas de watcher
fantôme).

---

## 6. Contraintes architecturales (invariants vérifiables)

| ID | Contrainte | Vérification |
|---|---|---|
| **C-01** | Aucune logique métier dans `interfaces/**` : pas de CRUD en mémoire, pas de règle de domaine, pas d'appel direct à un provider LLM, à Docker ou au système | Revue + tests API ; `v1.py` n'a plus de `MemoryStore` |
| **C-02** | Toute donnée métier passe par un manager Core + `CoreRecordStore` | Revue ; grep `MemoryStore`/dict global dans `interfaces/` |
| **C-03** | Aucun secret en clair : ni code, ni logs, ni events, ni records, ni Git | `core/config/secrets.py` ; `credential_keys` uniquement côté API |
| **C-04** | Les 5 règles d'import (`lint-imports`) restent **0 broken** | `lint-imports` (CI) |
| **C-05** | Aucun second pipeline RAG | Un seul `core/rag/pipeline.py` ; tout nouvel ingest (watcher, connecteur) **appelle** ce pipeline |
| **C-06** | Les interfaces restent **remplaçables** : ETHAN fonctionne sans WebUI (CLI, API) | `./ethan status`, CLI, tests headless |
| **C-07** | Aucune opération privilégiée hors `capability_manager` (argv-only, pas de shell) | Revue `component_lifecycle.py` + tests |
| **C-08** | Les permissions sont déclarées par domaine et vérifiées **côté API** | `require_permission(...)` systématique sur les mutations |
| **C-09** | Les associations inter-domaines sont des **identifiants**, jamais des copies | Revue des managers (`projects`, `folders`, `domains`) |
| **C-10** | Toute décision structurante = un ADR, référencé par ce document | §0 (gouvernance) |

---

## 7. Contrats API nécessaires

### 7.1 Conventions obligatoires (toutes interfaces)

| Aspect | Convention |
|---|---|
| Versionnement | Préfixe `/v1` ; une rupture = `/v2` (jamais de modification de forme sous `/v1`) |
| AuthN | `Authorization: Bearer <JWT>` ou cookie ; `auth_middleware` remplit `request.state.user` |
| AuthZ | `require_permission(Permission.X)` sur toute mutation ; 403 explicite |
| Erreurs | `{"detail": "..."}` ; 404 = ressource inconnue, 422 = règle métier violée, 413/415 = upload, 503 = manager non initialisé |
| Énumérations | `list[dict]` typé par `response_model` Pydantic (jamais de dict libre sans schéma) |
| Streaming | SSE (`text/event-stream`) pour le chat ; pas de WebSocket tant que DEF-08 n'est pas tranché |
| Idempotence | `PUT`/`DELETE` idempotents ; `POST` créateur retourne 201 + l'objet créé |
| Pagination | `limit`/`offset` + total lorsque la collection peut croître (à défaut, documenter l'absence) |

### 7.2 Contrats par domaine — état et priorité

| Domaine | Contrat | Routes clés | État |
|---|---|---|---|
| **Projects** | `/v1/projects` | `GET /`, `POST /`, `GET/PUT/DELETE /{id}`, `GET /default`, `GET /{id}/context`, `GET|POST|DELETE /{id}/documents` | ✅ Exposé, à figer |
| **Conversations** | `/v1/conversations` (alias `/v1/chat`) | liste, création, messages, streaming | 🟡 À unifier (ADR-3007) |
| **Providers** | `/v1/providers` | CRUD, `/{id}/models`, `/{id}/test`, `/{id}/default`, `/{id}/capabilities`, `/vision`, `/transcribe` | ✅ Exposé, à figer |
| **Models** | `/v1/models` | liste, `/{id}`, `/{id}/toggle`, `/search` | ✅ Exposé, à figer |
| **Agents / Missions / Goals** | `/v1/*` | CRUD | ✅ Exposé, à figer |
| **Knowledge / RAG** | `/v1/knowledge/*`, `/v1/knowledge-imports` | collections, documents, jobs d'import | ✅ Exposé |
| **Skills / Tools / MCP** | `/v1/skills`, `/v1/tools`, serveurs MCP | CRUD + exécution | ✅ Exposé |
| **Integrations** | `/v1/integrations`, `/v1/connections` | CRUD, health, connect/disconnect (jamais de credentials en réponse) | ✅ Exposé |
| **Components** | `/v1/components/*` | `detect`, `install`, `configure`, `test`, `enable`, `disable`, `uninstall` (`confirm_delete_data`) | ✅ Exposé |
| **Auth** | `/auth/*` | login, 2FA, reset, register | ✅ Exposé |
| **Config** | `/v1/config`, `/v1/settings` | lecture/écriture de configuration | 🟡 Sera impacté par ADR-3001 |
| **Observabilité** | `/v1/diagnostics`, `/health`, `/health/detailed` | santé, diagnostics | ✅ Exposé |

### 7.3 Exigences de contrat

1. **Un contrat par domaine** : documenté (OpenAPI) + **test de contrat**
   (`APIResponseValidator`, généralisé — G-06).
2. **Types partagés** : la WebUI consomme des types générés depuis OpenAPI
   (`DEF-07`) ; pas de duplication de modèle de données côté TypeScript.
3. **Compatibilité** : tout champ ajouté est optionnel ; toute suppression passe
   par `/v2`.
4. **Frontière stricte** : aucune route n'expose une structure interne du store
   (ex. pas de fuite du format `core_domain_records`).

---

## 8. Modèle de données cible

### 8.1 Principes

1. **Document-oriented** : les entités Core vivent en JSONB dans une table
   générique (`core_domain_records`) — pas de nouveau schéma relationnel par
   domaine (ADR-3001).
2. **Identifiants, pas de copies** : une association entre domaines = un `id`.
3. **Aucun secret** en base : uniquement des **références** (le secret vit dans
   env/Vault/Docker secrets via `core/config/secrets.py`).
4. **Redis = état live**, jamais source de vérité ; PostgreSQL = durable.
5. **Isolation** : toute donnée est scopée par `user_id` (ou projet) là où
   c'est requis ; le filtrage est fait par le **Core**, jamais par l'UI.

### 8.2 Tables PostgreSQL (état réel audité)

| Table | Rôle | Contenu |
|---|---|---|
| `core_domain_records` | **Store unique** des entités Core | `domain`, `record_id`, `record JSONB`, `created_at`, `updated_at` (PK `domain, record_id`) |
| `llm_providers` | Configuration des providers LLM | `provider_id`, `config JSONB` (type, base_url, default_model, display_name, enabled…), `enabled`, `is_default` — **jamais de clé API** |
| `users` (+ 2FA, reset) | Identités | migrations `003`, `006`, `007` |
| `schema_migrations` | Versionnage | une ligne par migration appliquée |
| `ethan_config` | **Vestige à migrer** (G-01) | `domain_name`, `config` — cible : `core_domain_records` |

### 8.3 Domaines persistés recensés (extrait audité)

`agents` · `agent-executions` · `skills` · `missions` · `goals` · `knowledge` ·
`knowledge-collections` · `rag-documents` · `documents` · `rag-config` ·
`folders` · `folder-memberships` · `domains` · `domain-memberships` ·
`projects` · `chats` · `chat-messages` · `chat_session` · `channels` ·
`channel-messages` · `files` · `files_content` · `notes` · `reminders` ·
`calendar-events` · `automations` · `evaluations` · `analytics` · `cookbook-installed` ·
`integrations` · `integration-credentials` · `connections` · `connection-tokens` ·
`api-keys`. 

*Tous partagent le même schéma générique : la structure métier vit dans le JSONB
et reste de la responsabilité du manager propriétaire.*

### 8.4 Invariants de données

| Invariant | Règle |
|---|---|
| **I-01** | Un record est possédé par **un** domaine et un `record_id` unique dans ce domaine |
| **I-02** | Les mutations publient un événement sur le bus (`EventType.*`) |
| **I-03** | Suppression d'un projet ≠ suppression des ressources référencées (documents supprimés explicitement, vector store nettoyé via le pipeline) |
| **I-04** | `uninstall` d'un composant ≠ suppression des données (`confirm_delete_data` obligatoire — ADR-4003) |
| **I-05** | Les credentials d'intégration ne sortent **jamais** du domaine `integration-credentials` |
| **I-06** | Aucune donnée métier ne vit dans l'interface (ni fichier, ni base locale WebUI) |

### 8.5 Cible de migration du socle données

```text
Aujourd'hui                                    Cible (ADR-3001)
────────────────────────────────────────       ────────────────────────────────
CoreRecordStore (core_domain_records)  ✅      inchangé (store unique)
ConfigStore  → table ethan_config      ⚠     →  ConfigStore = façade sur CoreRecordStore
WebUIStore   → records settings/…      ⚠     →  supprimé ; domaines migrés
llm_providers (config providers)       ✅      inchangé (sans secrets)
Redis (cache)                          ✅      inchangé (jamais source de vérité)
```

---

## 9. Stratégie de migration

### 9.1 Principes

1. **Strangler, pas big bang** : on branche domaine par domaine sur le
   Core/`CoreRecordStore`, en laissant les anciens chemins fonctionner jusqu'à
   bascule vérifiée.
2. **Contrat d'abord** : geler le contrat `/v1` d'un domaine **avant** de
   toucher son implémentation (sinon la WebUI casse).
3. **Façade puis suppression** : `ConfigStore`/`WebUIStore` deviennent des
   façades (même API, nouveau stockage) avant toute suppression de code.
4. **Double écriture temporaire explicite** : si nécessaire, elle est
   **bornée dans le temps** et instrumentée (journalisée), jamais silencieuse.
5. **Un critère de sortie par étape** : pas d'étape « terminée » sans test.
6. **Zéro régression interface** : ETHAN doit rester utilisable (WebUI ou CLI) à
   chaque commit ; `./ethan status` = 8/8 healthy.

### 9.2 Plan par écart (état → action → risque → rollback)

| Écart | Action | Risque | Rollback |
|---|---|---|---|
| **G-01** `ethan_config` | ADR-3001 : `ConfigStore` façade sur `CoreRecordStore` ; migration des lignes `ethan_config` → `core_domain_records` (domaine `settings`) | Faible : lecture/écriture config | Migration réversible : table `ethan_config` **conservée** jusqu'à validation ; restauration par `pg_dump` |
| **G-02** `CoreWebUIStore` | Supprimer les usages un par un (`v1.py`, `main.py`), vérifier chaque domaine (settings, providers, chats) | Moyen : domaine oublié ⇒ régression fonctionnelle | Garder la classe jusqu'à zéro usage ; suppression finale en un commit isolé |
| **G-03** vecteurs | ADR-3004 : choisir (recommandation : **`pgvector`** via `core_domain_records`/table dédiée, déjà dans la stack) puis migrer l'index | Moyen/élevé : réindexation | Conserver l'index existant en lecture seule pendant la bascule ; double lecture comparée avant bascule |
| **G-04** `v1.py` | ADR-3008 : extraire par domaine dans `routers/`, **URLs inchangées** ; tests de contrat avant/après | Faible (refactoring pur) | `git revert` du commit de découpage (aucun changement de comportement attendu) |
| **G-05** Folders/Domains | RFC produit → aligner `DomainManager` sur fail-closed | Faible techniquement, **visible produit** | Conserver le comportement permissif derrière un réglage si refus client |
| **G-06** contrats API | ✅ fait (V1) : `tests/test_api_contract_p0.py` fige la surface P0 (snapshot de routes + invariants) ; généralisation domaine par domaine à poursuivre | Faible | Tests ajoutés uniquement (aucun impact runtime) |
| **G-07** docs | Appliquer §0 (hiérarchie) ; marquer les propositions comme historiques | Nul | Réversible (simple en-tête) |
| **G-08** code mort / tests | ✅ fait (V1) : `example_usage.py` réécrit (`e648454b`) ; modules web + `core/network` committés (`64c9b546`, `92d0c396`) ; import mort `ContentFilter` retiré (`9fe0f638`) | Faible | Commit isolé |

### 9.3 Séquencement recommandé

| Vague | Contenu | Prérequis | Critère de sortie |
|---|---|---|---|
| **V1 — Solder le socle** | G-08 (nettoyage), G-06 (contrats des domaines P0) | — | ✅ **Atteint (V1.5)** : clone vierge à `cc74225e` → `lint-imports` 5 kept/0 broken, `ruff check` **0** + `ruff format --check` **0** (ruff pinné), collecte 0 erreur, sous-ensemble CI 26/26, suite complète **1092 passed / 7 skipped / 0 failed** (les 46 échecs préexistants corrigés) ; CI globale **verte** |
| **V2 — Unifier la persistance** | G-01 (ADR-3001), G-02 discipline | V1 | Une seule source config ; `CoreWebUIStore` sans nouvel usage |
| **V3 — Unifier Conversations** | ADR-3007 (modèle unique, `/v1/conversations` + alias) | V2 | Un seul modèle de conversation, E2E chat vert |
| **V4 — Décider les vecteurs** | ADR-3004 (mesures puis bascule) | V2 | Un seul backend d'index, réindexation validée |
| **V5 — Structure API** | G-04 (découpage `v1.py`) | V3 | URLs identiques, tests de contrat verts |
| **V6 — Politique produit** | G-05 (folders/domains), DEF-04/05 si besoin | V3 | Décision produit tracée par ADR |

---

## 10. Risques et rollback

### 10.1 Registre des risques

| ID | Risque | Prob. | Impact | Mitigation | Détection |
|---|---|---|---|---|---|
| R-01 | **La WebUI recrée du métier** (nouveau `MemoryStore`, calcul local, appel direct Ollama/Docker) | Moyenne | Élevé | C-01/C-02/C-07 ; revue obligatoire sur tout `interfaces/**` ; test de contrat | grep `MemoryStore`/`fetch('http://localhost:11434')` en CI ; revue |
| R-02 | **Deux sources de config** subsistent (G-01) | Élevée (existant) | Moyen | V2 : façade unique + migration ; journalisation des accès | Valeur divergente entre onglet Settings et manager |
| R-03 | **Double écriture d'index vectoriel** (G-03) | Moyenne | Élevé | Décision ADR-3004 avant toute nouvelle indexation | Incohérence de résultats de recherche |
| R-04 | **Rupture de contrat API** lors de l'unification Conversations | Moyenne | Élevé | Alias `/v1/chat` conservés ; tests de contrat avant/après | Tests E2E WebUI |
| R-05 | **Régression « ETHAN fonctionne sans WebUI »** | Faible | Élevé | C-06 : CLI + API testés à chaque vague ; boot headless | `./ethan status`, CLI `plugin list`, tests headless |
| R-06 | **Dette documentaire** (31 docs) génère des décisions contradictoires | Élevée (existant) | Moyen | §0 : hiérarchie + requalification des ADR | Revue trimestrielle (DEF-09) |
| R-07 | **Refactoring `v1.py`** casse une route peu testée | Moyenne | Moyen | Découpage mécanique + tests de contrat exhaustifs du périmètre | Tests de contrat (G-06) |
| R-08 | **Secrets** réintroduits par une nouvelle intégration | Faible | Critique | C-03 + revue systématique ; tests « aucune valeur de credential en réponse » | grep secrets en CI (règle projet) |
| R-09 | **Migration `ethan_config`** perte de configuration | Faible | Élevé | Table source conservée + `pg_dump` avant migration | Tests de non-régression config |

### 10.2 Stratégie de rollback

| Niveau | Moyen | Périmètre |
|---|---|---|
| **Commit** | `git revert <sha>` | Refactoring (G-04), nettoyages (G-08), docs (G-07) |
| **Données** | `pg_dump`/restauration ciblée ; table source conservée | G-01 (`ethan_config`), G-03 (index) |
| **Fonctionnel** | Façade conservée (ancien chemin actif) jusqu'à validation | G-02 (`CoreWebUIStore`), Conversations (ADR-3007) |
| **Plateforme** | `./ethan down` + `docker compose up -d` sur image N-1 | Régression runtime |
| **Abandon d'une vague** | Critère explicite : si le critère de sortie n'est pas atteint après 2 itérations, la vague est suspendue et l'écart re-documenté | Toutes |

### 10.3 Critères d'acceptation de l'architecture cible

1. Un seul store de records (`CoreRecordStore`) ; zéro table de configuration parallèle.
2. Un seul pipeline RAG ; un seul backend d'index vectoriel.
3. Un seul modèle de conversation.
4. `interfaces/**` sans logique métier ni état métier durable.
5. `lint-imports` : 5 règles, **0 broken** ; CI verte sur clone vierge.
6. ETHAN opérationnel sans WebUI (CLI + API).
7. Aucun secret hors `core/config/secrets.py`.
8. Chaque décision structurante tracée par un ADR référencé ici.

---

## Annexes

### A. Commandes de vérification (état actuel)

```bash
./ethan doctor                 # 71 PASS / 0 WARNING (mesuré)
./ethan status                 # 8/8 services healthy
.venv/bin/lint-imports         # 5 kept / 0 broken (clone vierge)
.venv/bin/python -m pytest tests/ interfaces/api/tests/ -q
make -n bootstrap              # séquence preflight → pull → up → wait → status
```

### B. Historique du document

| Date | Version | Changement |
|---|---|---|
| 2026-09-24 | 1.0 | Création : audit `676403a3`, architecture cible, requalification des ADR, écarts G-01..G-08, décisions D-00..D-07, vagues V1..V6 |
| 2026-09-24 | 1.1 | Vague V1 exécutée : G-08 clos (`64c9b546`, `92d0c396`, `e648454b`, `9fe0f638`), G-06 contrat P0 livré (`cfe60b31`+`a0844b2f`, 6 tests), G-09 identifié (ruff/CI rouge préexistant) |
| 2026-09-24 | 1.2 | V1.5 : **G-09 clos** (pin CI ruff `0.15.1` + big-bang `--fix`/`format`, 992 fichiers, 0 erreur), **doublons G-04/ADR-3008 supprimés** (contrat à zéro doublon), **46 échecs préexistants corrigés** (ports ciblés du WIP : CLI/knowledge/boot/technology/ssrf), imports legacy `ethan.*` éliminés — SHAs `5ee65c47`..`cc74225e` |

### C. Documents de référence

- ADR : `docs/architecture/adr/` (3001-3006, 4001-4004)
- ESR : `docs/engineering/esr/` (ESR-001 … ESR-006)
- Hardening : `docs/hardening.md` (§3.1 folders/domains, §3.2 dette packaging)
- Boot : `docs/boot-from-scratch.md`, `docs/sre-runbook.md`
- Vues descriptives : `docs/architecture/C4-*.md`










