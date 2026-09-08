# ETHAN — WebUI Platform Architecture Assessment

**Rôle** : CTO / Principal Architect — évaluation (lecture seule, aucune modification de code).
**Date** : 2026-09-07
**Dépôt** : `~/AI/Ethan` (`origin git@github.com:seclib/Ethan.git`, branche `main`)
**Méthode** : reconnaissance du dépôt — `core/`, `interfaces/`, `plugins/`, `sdk/`, `infrastructure/`, `deploy/`, `scripts/`, `tests/`, `docs/` — inspection des routes API, modèles de domaine, stores, hooks WebUI, configuration, événements, NATS/Redis/PostgreSQL/Qdrant.

---

## 1. Executive Summary

ETHAN est un **runtime cognitif événementiel** (pas une application Web). Conformément à `AGENTS.md`, l'architecture est structurée en quatre couches :

```
Core (intelligence) > Runtime (orchestration) > Services (infra) > Interfaces (WebUI, CLI, API…)
```

Les interfaces **révèlent** ETHAN, elles ne le définissent pas. La source de vérité doit rester `core/` + services.

**Constats de haut niveau :**

1. **Architecture Core-owned respectée.** Le WebUI (Next.js) est un client API pur : proxy `/api/[...path]/route.ts` → `interfaces/api` (FastAPI) → `core/`. Les stores WebUI (`agent.store.ts`, `chat-sidebar.store.ts`, `ui.store.ts`) ne contiennent que de l'état d'interface (UI/UX), pas de logique métier.
2. **Constante évolution.** Le git log montre des séries « Refonte v4 », « Refonte webui v3 », « Backend v3 »… Le dépôt est en **consolidation active** ; beaucoup de composants sont implémentés, d'autres partiellement ou en cours de migration.
3. **Pas de dossier `runtime/`.** Le runtime n'est **pas** un paquet séparé : c'est l'ensemble des services Docker Compose (kernel, modules, api, nats, redis, postgres, pg_backup) plus les code paths Core qui orchestrent (kernel, orchestrator, modules). Documenté dans le README (« no monolithic runtime/ folder »).
4. **Duplication identifiée (config/providers).** `core/config/store.py` (ConfigStore, PG JSONB) coexiste avec `core/state/webui_store.py` (WebUIStore) et `core/state/record_store.py` (CoreRecordStore). Providers : `core/llm/provider_manager.py` est la source de vérité serveur, mais `webui_store` maintient des défauts statiques legacy (`_DEFAULT_PROVIDERS`).
5. **Contrat Core/WebUI est en place.** Mapping Open-WebUI → ETHAN documenté (`docs/architecture/OPENWEBUI_ETHAN_MAPPING.md`), clients API WebUI consomment `/v1/*`.

La cible : **ETHAN reste le runtime intelligent ; le WebUI devient un cockpit complet** (conversations + projets + knowledge + RAG + models + agents + skills + tools + MCP + automation) sans jamais posséder la logique métier.

---

## 2. Current Architecture

### 2.1 Vue des conteneurs (docker-compose.yml)

| Service | Rôle |
|---|---|
| `nats` (ethan-nats) | Event bus NATS (JetStream) |
| `redis` (ethan-redis) | État vivant / cache |
| `postgres` (ethan-postgres) | Persistance (JSONB `core_domain_records`) |
| `api` (ethan-api) | FastAPI gateway (port 8000) |
| `kernel` (ethan-kernel) | `core/kernel.py` CognitiveKernel (orchestrateur d'événements) |
| `modules` (ethan-modules) | Lanceur de modules cognitifs (`core/modules`) |
| `pg_backup` | Sauvegardes PostgreSQL |
| `ui` | Next.js build (port 3001) |

### 2.2 Couches logicielles

| Couche | Dossier | Rôle confirmé |
|---|---|---|
| **Core** | `core/` | LLM + providers, agents, skills, tools/MCP, RAG, knowledge, memory, facts, chat pipeline, planner, goals, scheduler, kernel, bus, state, auth, security, config, approval, audit, telemetry |
| **Interfaces** | `interfaces/` | `api/` (FastAPI), `webui/` (Next.js), `cli/` (shell), `desktop/`, `channels/`, `shell/` |
| **Plugins** | `plugins/` | browser, memory, sandbox, sdk, terminal |
| **SDK** | `sdk/` | SDK Python (event, goals, module, autonomy, learning, metacognition) |
| **Services** | `infrastructure/`, `deploy/`, `install/`, `scripts/` | systemd, postgres, docker, traefik, otel, prometheus, grafana, secrets, env |

### 2.3 État de fonctionnement réel (vérifié)

| Composant | État |
|---|---|
| Chat pipeline (`core/chat/pipeline.py`) | ✅ Streaming, message tree, RAG, tools, skills |
| ProviderManager (`core/llm/provider_manager.py`) | ✅ source de vérité des providers, monté dans l'API |
| RAG strategies (`core/rag/strategies.py`) | ✅ hybrid/semantic/keyword/auto, tests |
| Skills unifiées (`core/skills/store.py`) | ✅ kind prompt/pipeline, gate is_active, tests |
| Agents + resources (`core/agents/resources.py`) | ✅ scoping explicite, résolution dossiers/domaines, tests |
| MCP servers (`core/tools/servers.py`) | ✅ sync tools, secrets masqués, tests |
| Web ingest (`core/knowledge/web_ingest.py`) | ✅ scan → preview → index, robots/SSRF, tests |
| Kernel (`core/kernel.py`) | ✅ orchestrateur d'événements (pas de logique business) |
| Migration sources | ✅ `deploy/postgres/migrations/003_create_users_table.sql` |
| Runtime | ⚠️ orchestré par Docker Compose + Core (pas de dossier `runtime/`) |

---

## 3. Target Architecture

Le WebUI doit évoluer vers un **AI workspace** complet, fonctionnellement inspiré par : **AnythingLLM** (workspace documentaire & agents), **Open WebUI** (UX conversation-centric, modèles, admin), **Odysseus** (structure de mission / multiples agents).

Contrainte absolue : ETHAN reste la source de vérité. Chaque nouvelle page du WebUI doit être une **projection** d'une capacité Core déjà implémentée.

```
┌────────────────────────────────────────────────────────────┐
│  INTERFACES (remplaçables)                                  │
│  WebUI (3001) · CLI · Desktop · API externe                │
└───────────────▲──────────────────────────▲─────────────────┘
                │ HTTP JWT / SSE / WS      │
┌───────────────┴──────────────────────────┴─────────────────┐
│  API Gateway (interfaces/api, FastAPI :8000) — passerelle    │
│  auth (JWT) · RBAC · audit · transformation                  │
└───────────────┬─────────────────────────────────────────────┘
                │ appels Core via singletons injectés
┌───────────────▼─────────────────────────────────────────────┐
│  CORE (source de vérité)                                    │
│  llm · agents · skills · tools/MCP · rag · knowledge · memory│
│  chat · planner · goals · scheduler · state · config · auth │
└───────────────┬─────────────────────────────────────────────┘
                │ NATS JetStream
┌───────────────▼─────────────────────────────────────────────┐
│  KERNEL + MODULES (orchestration) + services Redis/PG       │
└─────────────────────────────────────────────────────────────┘
```

### 3.1 Gaps fonctionnels WebUI → capacités Core

| Capacité cible WebUI | Core/API existant ? | Commentaire |
|---|---|---|
| Chat streaming, messages, tools, modèles | ✅ `core/chat`, `core/llm` | Opérationnel |
| Fournisseurs + modèles | ✅ `providers.py`, `models.py` + ProviderManager | Opérationnel |
| RAG Collections + stratégies | ✅ `core/rag` | Opérationnel |
| Agents avec ressources sélectionnées | ✅ `core/agents` | Opérationnel |
| Skills (prompt/pipeline, activables) | ✅ `core/skills` | Opérationnel |
| MCP servers | ✅ `core/tools/servers.py` | Opérationnel |
| Knowledge + Web Import | ✅ `core/knowledge` | Opérationnel |
| Folders + Domains | ✅ `core/folders`, `core/domains` | Deux concepts distincts (voir §4.2) |
| **Projets** (workspace AnythingLLM/Odysseus) | ❌ **Gap principal** | Pas de domaine `Project` dans le Core (voir §5.3) |
| **Bibliothèque / sources partagées** | ⚠️ partiel (files, gallery) | À consolider |
| **Reminders** | ⚠️ `core/scheduler`, `core/missions` | Riche mais pas présenté ainsi |
| **STT** | ❌ `core/llm/tts.py` = TTS ; pas de STT confirmé | À camper sur TTS d'abord |

---

## 4. Bounded Contexts

### 4.1 Matrice des 22 domaines cibles

| # | Contexte | Propr. Core | Store BD | API owner | Frontend owner | État | Duplication |
|---|---|---|---|---|---|---|---|
| 1 | **Identity** | `core/auth` | PG `users`/`groups` | `domains.py` + `/auth/*` | Login/Register | ✅ | — |
| 2 | **Conversations** | `core/chat` + `core/state/chats.py` | PG | `domains.py` (/v1/chats) | use-chats | ✅ | — |
| 3 | **Projects** | ❌ absent | — | — | — | ❌ | — |
| 4 | **Knowledge** | `core/knowledge` | PG | `v1.py`, capabilities | page Knowledge | ✅ | — |
| 5 | **Documents** | `core/state/files.py` | PG `files` | `domains.py` (/files) | pages files | ✅ | — |
| 6 | **RAG** | `core/rag` | PG + vector | capabilities, web_ingest | RAG view | ✅ | — |
| 7 | **Models** | `core/llm` | PG | `models.py` | page Models | ✅ | 3 classes à clarifier |
| 8 | **Providers** | `core/llm/provider_manager.py` | PG | `providers.py` | page Providers | ✅ | `webui_store._DEFAULT_PROVIDERS` legacy |
| 9 | **Model Routing** | `core/llm/router.py` + routing.yaml | fichier | (direct) | (n.a.) | ⚠️ | — |
| 10 | **Embeddings** | `core/rag/embeddings.py` | — | v1/rag/providers | RAG view | ✅ | — |
| 11 | **Vector DBs** | `core/memory` + `core/rag/vector_store` | Chroma/Qdrant | — | — | ⚠️ | **double backend vecteurs** |
| 12 | **Chunking** | `core/rag/extractors` | — | — | — | ✅ | — |
| 13 | **STT** | ❌ pas confirmé | — | — | — | ❌ | TTS seulement |
| 14 | **Search** | `core/rag/retrieval`, `core/research` | — | research | Deep Research | ⚠️ | RAG-research, pas moteur universel |
| 15 | **Agents** | `core/agents` | PG | `v1.py` | page Agents | ✅ | — |
| 16 | **Skills** | `core/skills` (store unifié) | PG | `v1.py` | page Skills | ✅ | — |
| 17 | **Integrations** | `plugins/` + cookbook | FS/PG | cookbook | page Cookbook | ⚠️ | plugins partiels |
| 18 | **MCP** | `core/tools/servers.py` | PG | capabilities | page MCP | ✅ | resources/prompts non exposés |
| 19 | **Reminders** | `core/scheduler`, `core/missions` | PG | mission | Missions/Calendar | ✅ | pas nommé « Reminders » |
| 20 | **Library** | `core/state/files.py` + gallery | PG | — | Gallery | ⚠️ | notion unifiée absente |
| 21 | **System Config** | `core/config` + `webui_store` + `record_store` | PG JSONB | config.py, state.py | Settings | ⚠️ | **3 stores à unifier** |
| 22 | **UI Preferences** | (frontend) | localStorage | — | — | ✅ | par design |

### 4.2 Deux concepts « organisation » (ne pas confondre)

| Concept | Impl. | API | WebUI | Rôle |
|---|---|---|---|---|
| **Folders** | `core/folders/FolderManager` | `/v1/folders` | page `/folders` | Arborescence libre de ressources (Knowledge, RAG, Skills…) |
| **Domains** | `core/domains/DomainManager` | `/v1/domains` | page `/domains` | Regroupements *sémantiques* (OSINT, Recon, Code) — groupes transverses |

Les deux sont disjoints dans le Core (dossiers = hiérarchie, domaines = étiquettes). **Pas une duplication**, mais un **risque de confusion produit** : distinguer explicitement « Dossiers (arborescence) » de « Domaines (groupes transverses) » dans le WebUI.

---

## 5. Dependency Graph

### 5.1 Dépendances du WebUI (frontend → backend)

```
WebUI (Next.js :3001)
  ├─ /api/[...path]/route.ts (proxy JWT cookie → Bearer)
  │     └─ interfaces/api (FastAPI :8000)
  │            ├─ core/auth (JWT, RBAC) — toutes routes protégées sauf PUBLIC_PATHS
  │            ├─ core/llm (ProviderManager, registry, model_store)
  │            ├─ core/chat (pipeline)
  │            ├─ core/agents · core/skills · core/tools (+servers MCP)
  │            ├─ core/rag · core/knowledge (+web_ingest) · core/facts
  │            ├─ core/folders · core/domains
  │            ├─ core/state (record_store, webui_store) → PG/Redis
  │            └─ core/scheduler · core/missions · core/research …
  └─ services d'infra : NATS (bus), Redis (live), PostgreSQL (persist), Chroma/Qdrant (vecteurs)
```

### 5.2 Dépendances Core internes

| Module | Dépend de | Consommé par |
|---|---|---|
| `core/bus` (nats_bus) | NATS | kernel, modules, events |
| `core/state` | Redis + PostgreSQL | tous les stores de domaine (agents, skills, knowledge, rag…) |
| `core/llm` | providers (HTTP) | chat, agents, skills run, executors |
| `core/rag` | embeddings + vector store | chat (RAG), web_ingest, knowledge |
| `core/kernel` | bus, state, registry, scheduler | ethan-kernel (conteneur) |
| `interfaces/api` | tout `core/*` (singletons injectés au lifespan) | WebUI, CLI, API externe |

### 5.3 **Le gap « Projets »** (recommandation)

Le contexte **Projects** n'existe pas dans le Core. Recommandation : **un Projet est un conteneur de conversation avec portée de connaissance et contexte d'exécution** (combinaison des 4 rôles de la question §5 de l'énoncé) :

- **conversation container** : groupe de chats (associés `project_id`)
- **knowledge scope** : bucket de collections RAG + agent(s) + resources autorisées
- **execution context** : contexte lors des exécutions (planner/missions)
- **UI construct** : simple repr. de synthèse, jamais le propriétaire de la logique

Modèle recommandé (à implémenter dans `core/projects/`, pas dans le frontend) :

```
Project { id, name, description, created_at, updated_at, owner }
  ├── chats[]            (conversations du projet)
  ├── collections[]      (RAG collections admissibles)
  ├── agents[]           (agents autorisés dans le projet)
  ├── domains[]          (domaines transverses liés)
  └── folders[]          (dossiers de ressources liés)
```

**Ne pas introduire de logique métier dans le frontend** : le WebUI affichera un sélecteur de projet et de la navigation, le Core fournira le CRUD et l'association.

---

## 6. Source-of-Truth Matrix

| Ressource | Source de vérité | API d'accès | WebUI | Duplication / défaut |
|---|---|---|---|---|
| Providers LLM | `core/llm/provider_manager.py` | `providers.py` | page Providers | ⚠️ `webui_store._DEFAULT_PROVIDERS` statiques legacy en fallback |
| Modèles | `core/llm/registry` + `model_store` | `models.py` | page Models | 3 classes (`ProviderStore`, `ModelStore`, `Registry`) à consolider |
| Agents | `core/agents` | `v1.py` | page Agents | — |
| Skills | `core/skills/store.py` | `v1.py` | page Skills | — |
| Tools/MCP | `core/tools` + `servers.py` | `capabilities.py` | pages Tools + MCP | — |
| RAG strategies | `core/rag/strategies.py` | capabilities | RAG view | — |
| Knowledge | `core/knowledge` | v1 | page Knowledge | — |
| Folders | `core/folders` | `/v1/folders` | page Folders | — |
| Domains | `core/domains/DomainManager` | `/v1/domains` | page Domains | 2 conceptes distincts de Folders |
| Config système | `core/config` / `webui_store` / `record_store` | config.py, state.py | Settings | **Duplication : 3 stores** |
| Conversations | `core/state/chats.py` + `core/chat` | `domains.py` (/v1/chats) | use-chats | — |
| Users/Groups | `core/auth` | `domains.py` + `/auth/*` | Login/Register | — |
| State | Redis (live) + PG (persistent) | CompositeStateBackend | — | — |

---

## 7. API Inventory

### 7.1 Routeurs montés (`interfaces/api/main.py:562`)

| Router | Préfixe (vue) | Domaine Core | Auth |
|---|---|---|---|
| `v1_router` | `/v1/*` | multidomaine (agents, skills, folders…) | JWT |
| `providers_router` | `/providers` | `core/llm` | JWT |
| `models_router` | `/models` | `core/llm` | JWT |
| `capabilities_router` | `/tools`, pipelines, servers MCP | `core/tools` | JWT |
| `domains_router` | `/users`, `/groups`, `/chats`, `/files` | `core/auth`, `core/state` | JWT (ADMIN) |
| `core_domains_router` | `/v1/domains` | `core/domains` | JWT |
| `folders_router` | `/v1/folders` | `core/folders` | JWT |
| `web_ingest_router` | `/v1/web-ingest/*` | `core/knowledge/web_ingest` | JWT |
| `config_router` | `/v1/settings` | `core/config` / webui_store | JWT |
| `security_router` | `/security` | `core/security` | JWT (ADMIN) |
| `mission_router` | `/missions` | `core/missions` | JWT |
| `cookbook_router`, `email_router`, `research_router`, `realtime_router`, `openwebui_router` | spécialisés | divers | JWT |
| `auth` | `/auth/login, register, me, refresh, logout` | `core/auth` | public (login/register) |

### 7.2 API manquantes pour la cible

| Besoin | Existe ? | À créer (Core d'abord) |
|---|---|---|
| CRUD Projet | ❌ | `core/projects/` + route `/v1/projects` |
| Recherche universelle (conversations+knowledge+agents) | ⚠️ `core/research` partiel | Endpoint unifié `/v1/library/search` |
| STT (audio → texte) | ❌ (TTS seulement) | `core/llm/stt.py` |
| Exécution pipelins skills par agent (intersection tools) | ⚠️ skills `run` seulement | Contexte agent dans pipeline |

---

## 8. Data Model Inventory

| Entité | Store | Colonnes/Schema (vue) | Propriétaire Core |
|---|---|---|---|
| Users | PG `users` | id, username, password_hash, role, active | `core/auth/users.py` |
| Groups | PG `groups` + membres | id, name, members[] | `core/auth/groups.py` |
| Chats | PG (record_store) | id, title, messages[], meta | `core/state/chats.py` |
| Files | PG `files` | id, filename, mime, size, path | `core/state/files.py` |
| Agents | PG `core_domain_records` (domain=agents) | id, name, resources, skill_ids… | `core/agents` |
| Skills | PG records (skills) | id, kind, content/steps, is_active, valves | `core/skills/store.py` |
| MCP servers | PG records (mcp_servers) | id, name, transport, auth(secrets masqués) | `core/tools/servers.py` |
| Collections RAG | PG records | id, name, retrieval_strategy, embedding… | `core/knowledge/collections.py` |
| Settings | PG `ethan_config` (ConfigStore) + webui_store | sections llm/permissions/budget/system | `core/config`, `core/state/webui_store` |
| Folders | PG records | id, name, parent_id, resources | `core/folders` |
| Domains | PG records | id, name, memberships | `core/domains` |
| Facts/Memory | PG + Redis + vecteurs | user_model, facts, experiences | `core/memory`, `core/facts` |

---

## 9. Frontend Architecture (WebUI)

### 9.1 Structure

```
interfaces/webui/src/
├── app/            pages (chat ., agents, analytics, calendar, cookbook, diagnostics,
│                   domains, folders, gallery, groups, inbox, knowledge, logs, mcp,
│                   missions, models, notes, plugins, providers, research, security,
│                   settings, skills, tools, workspace + api/[...path] proxy + (auth)/login|register)
├── components/     features (agents, assistant, domains, folders, flux, goals, knowledge,
│                   memory, mcp, missions, providers, settings, skills, tools) + layout + shared + ui
├── hooks/          use-edge-dock.ts (+ hooks locaux par feature)
├── lib/api/        clients HTTP (agents, analytics, audio, auth-providers, capabilities, chat,
│                   client, cookbook, domains, extensions, files, flux, folders, goals,
│                   groups, knowledge, mcp, memory, missions, models, plugins, providers,
│                   rag, research, security, settings, skills, tools, web-import)
├── store/          agent.store.ts, chat-sidebar.store.ts, model.store.ts, overlay.store.ts, ui.store.ts
├── types/          types TypeScript (dont assistant)
├── locales/        i18n
└── tests/          unit (jest)
```

### 9.2 Principes confirmés

- **Client API pur** : `lib/api/client.ts` — `NEXT_PUBLIC_ETHAN_API_URL` (défaut `/api`), cookie HttpOnly via `credentials: include` ; le proxy `app/api/[...path]/route.ts` convertit cookie JWT → en-tête Bearer.
- **State UI-only** : les stores (Zustand) ne tiennent que de l'état d'interface ; pas de logique métier.
- **Navigation unique** : `components/layout/nav-config.ts` (explicite : « règle anti-fantôme : seules des fonctionnalités réellement existantes »).
- **Page chat dashboard** : `app/page.tsx` — compose ressources via hooks (use-chats, use-active-model, use-active-agent).

### 9.3 Risques frontend

| Risque | Détail |
|---|---|
| Évaporation de l'état | Les stores WebUI sont volatils (pas de persistance Core pour l'UI) — OK car l'UI n'est pas propriétaire |
| Sections fantômes | Uniquement si la page existe sans route Core — à surveiller par relecture nav-config vs routes |
| Localisation | `locales/` présent ; pas validé ici |

---

## 10. Backend Architecture (API + Core)

### 10.1 Pattern d'injection

- `interfaces/api/main.py` construit au lifespan : `ProviderManager` (store PG/Redis), `ChatPipeline` (compose ChatStore + ProviderManager + RAG + SkillStore), `ToolManager`, `SkillStore`, `FolderManager`, `DomainManager`, `WebUIStore`… puis injecte via `set_*_manager` dans chaque router.
- Chaque router est un **passe-plat** : toute la logique reste dans `core/*`.

### 10.2 Auth

- `interfaces/api/auth.py` : JWT HS256, `JWT_SECRET` / `JWT_EXPIRY_HOURS` (env), `PUBLIC_PATHS` + HTTPBearer, middleware `require_permission(Permission.*)`.
- `core/auth/rbac` : Permissions (READ/WRITE/ADMIN/MEMORY…).
- Routes publiques : `/health`, `/metrics`, `/docs`, `/auth/login`, `/auth/register`…

### 10.3 Persistance

- `CoreRecordStore` : document-oriented, PG JSONB `core_domain_records` + cache Redis + fallback in-memory (standalone-friendly).
- `ConfigStore` : PG `ethan_config` + Redis, **sans secrets** (les secrets vivent dans `core/config/secrets.py` — env/Vault/Docker secrets).
- `CompositeStateBackend` : RedisLiveState + PostgresPersistentState.

---

## 11. Security Boundaries

| Contrainte (énoncée §6) | Vérification | Statut |
|---|---|---|
| WebUI ne peut pas bypasser Core | Toutes les routes passent par l'API gateway + auth ; `PUBLIC_PATHS` restreint | ✅ |
| Agents ne peuvent pas bypasser Runtime | Agents scoping via `core/agents/resources.py` + executor ; zero ressources par défaut | ✅ |
| Plugins ne peuvent pas bypasser permissions | `plugins/` chargés par Core ; sandbox présent (`plugins/sandbox`) | ⚠️ à auditer finement |
| API credentials non exposés | JWT secret via env ; jamais loggé ; secrets jamais dans ConfigStore | ✅ |
| Accès fichiers scopé | `core/state/files.py` via `/files` + permissions READ/WRITE | ⚠️ ownership utilisateur à confirmer |
| Intégrations capacités explicites | MCP : sync + `metadata.mcp_server_id` ; secrets masqués (token_set) | ✅ |
| Opérations privilégiées | RBAC `require_permission` sur mutations (ADMIN sur users/groups/security) | ✅ |

---

## 12. Existing Technical Debt

| # | Dette | Impact | Zone |
|---|---|---|---|
| 1 | **3 stores de config** coexistent : `core/config/store.py` (ConfigStore), `core/state/webui_store.py` (WebUIStore), `core/state/record_store.py` (CoreRecordStore) | Incohérence possible (settings dupliqués entre `ethan_config` et records) | Core config/state |
| 2 | **`webui_store._DEFAULT_PROVIDERS` statiques legacy** (ex. `openai`, `huggingface`, `pinecone`) qui peuvent servir de réponse par défaut | Masque la vraie liste du ProviderManager en fallback | Core state → ProviderManager |
| 3 | **ProviderStore / ModelStore / Registry** : 3 classes dans `core/llm` avec rôles à clarifier | Contrats internes flous, risque de double écriture | Core llm |
| 4 | **Double backend de vecteurs** : `core/memory` (chroma/qdrant) vs `core/rag/vector_store` | Deux chemins possibles pour les embeddings | Core */vector |
| 5 | **Routers `domains.py` vs `core_domains.py`** : même nom « domaine » pour deux concepts (users/chats vs regroupements transverses) | Confusion produit + imports ambigus | interfaces/api |
| 6 | `interfaces/cli` (redondant partiellement avec `ethan` shell script) | Surface de commandes maintue | interfaces/cli + scripts |
| 7 | `examples/openjarvis` (submodule) | Référence historique — à distinguer clairement d'ETHAN | examples |
| 8 | Docs : très nombreux fichiers d'audit (−audit, −final, v3…) | Bruit documentaire | docs/ |

---

## 13. Architectural Risks

| Risque | Probabilité | Impact | Mitigation recommandée |
|---|---|---|---|
| Consolidation active casse des contrats WebUI | Haute (git history) | Élevé | Contrats OpenAPI versionnés + tests d'API suffisants ; respecter routes existantes |
| Duplication configurations (3 stores) | Moyenne | Élevé | Unifier via un seul store de records + shim de compat ; supprimer `_DEFAULT_PROVIDERS` fallback |
| Gap « Projets » bloque l'UX workspace | Certaine (absent) | Élevé | Ajouter `core/projects` (petit) puis route ; UI ensuite |
| Double backend vecteurs | Moyenne | Moyen | ADR pour un back of record (Qdrant par défaut ?) |
| Confusion Folders/Domains | Élevée (UX) | Moyen | Libellé & microcopie distincts ; one-pager d'aide |
| Discovery des providers non réels dans le fallback | Moyenne | Moyen | Retirer les défauts statiques ; toujours interroger ProviderManager |

---

## 14. Recommended ADRs

| N° | Sujet | Décision recommandée |
|---|---|---|
| ADR-3001 | Unified Record Store | `core/state/record_store.py` devient le store unique ; `ConfigStore` et `webui_store` deviennent des façades par-dessus |
| ADR-3002 | Providers source of truth | Seul `core/llm/provider_manager.py` est la vérité ; suppression du fallback statique `_DEFAULT_PROVIDERS` |
| ADR-3003 | Projects domain | Nouveau contexte `core/projects` (conversation container + knowledge scope + execution context) |
| ADR-3004 | Vector store de record | Un seul back-end de vecteurs (Qdrant/Chroma selon déploiement), exposé par `core/rag/vector_store` |
| ADR-3005 | Folder vs Domain | Folders = arborescence, Domains = étiquettes transverses ; pas de fusion |
| ADR-3006 | API contracts versionnés | OpenAPI généré + tests de contrat pour chaque route WebUI consommée |

---

## 15. Migration Strategy

Séquencée, sans refactor massif :

1. **Phase A — Stabilité (aucune régression)**
   - ADR-3006 : figer les contrats API consommés par le WebUI (schémas types + tests).
2. **Phase B — Dé-duplication config**
   - ADR-3001/3002 : unifier les stores ; retirer `_DEFAULT_PROVIDERS` ; valider par tests existants (providers, models, settings).
3. **Phase C — Projets (gap principal)**
   - ADR-3003 : implémenter `core/projects` + `/v1/projects` ; pas d'UI avant le Core.
4. **Phase D — Consolidation vecteurs + routage**
   - ADR-3004/3005 : choix du back-vector unique ; clarifier Folders/Domains dans la microcopie WebUI.
5. **Phase E — WebUI workspace**
   - Nouvelles pages Projets/Bibliothèque/Gallery alignées sur les routes Core existantes/ajoutées.

---

## 16. Implementation Sequence (ordre recommandé)

1. ADR-3006 : tests de contrats API (préalable à tout).
2. ADR-3001 + ADR-3002 : unification des stores / suppression du fallback providers.
3. ADR-3003 : `core/projects` (+ tests, + route).
4. ADR-3004 : un seul back-vector.
5. ADR-3005 : clarté produit Folders/Domains.
6. Phase E : WebUI (projets, bibliothèque, gallery) en pur client API.

---

## ARCHITECTURE ASSESSMENT COMPLETE

### Findings (synthèse)

1. Architecture Core-owned solide : WebUI = client API pur, source de vérité dans `core/`, runtime via Docker Compose + Core. ✅
2. 20/22 bounded contexts existent au moins partiellement dans le Core ; **2 absents : Projects, STT**. Le gap principal est **Projects**.
3. No monolithic `runtime/` : la couche runtime = kernel + modules + services (documenté).
4. Duplication nécessitant consolidation : **3 stores de config**, **doubles providers fallback** (`webui_store`), **double backend vecteurs**, **3 classes llm-aligned**.

### Contradictions

- « Domains » signifie deux choses (routeurs `domains.py` vs `core_domains.py`) — même label, deux responsabilités.
- README annonce « runtime services » tandis que `runtime/` n'existe pas comme dossier — cohérent mais à documenter explicitement.
- `webui_store._DEFAULT_PROVIDERS` (legacy) contredit le ProviderManager (actif) en fallback.

### Duplicated systems

| Système | Duplication | Action |
|---|---|---|
| Config | ConfigStore + WebUIStore + CoreRecordStore | Unifier (ADR-3001) |
| Providers | ProviderManager + `_DEFAULT_PROVIDERS` legacy | Supprimer le fallback (ADR-3002) |
| Vecteurs | `core/memory` chroma/qdrant + `core/rag/vector_store` | Back unique (ADR-3004) |
| Modèles | ProviderStore / ModelStore / Registry | Répartition claire (ADR-3002 complément) |

### Blockers (pour la cible workspace)

1. **Aucun domaine Projects** (bloquant pour une UX workspace/AnythingLLM/Odysseus).
2. **Stores config dupliqués** (bloquant pour une Settings fiable).
3. **Fallback providers statiques** (bloquant pour un menu Providers fiable).

### Recommended implementation order

`Contrats API → unification stores → Projects core → back-vector unique → clarté Folders/Domains → WebUI workspace` (voir §16).

---

*Fin du document. Évaluation en lecture seule — aucun code modifié.*
