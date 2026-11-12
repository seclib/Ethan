# État des lieux — Analyse initiale du repository

> **Date** : 2026-08-17
> **Auteur** : Agent d'exécution ETHAN
> **Statut** : Analyse initiale — aucune modification de code

---

## 1. Synthèse de l'architecture cible

L'architecture cible est définie par les documents de `docs/plans/` :

```
Open WebUI → fork → ETHAN WebUI → ETHAN API → ETHAN Core / Runtime
```

**Principes fondamentaux** :
1. **ETHAN est la source de vérité** — Core/Runtime possèdent la logique métier, la persistance, la configuration.
2. **WebUI est une interface** — thin client, jamais de logique métier dupliquée.
3. **Open WebUI = référence UX** — on récupère la richesse de l'interface, pas l'implémentation.
4. **Migration réversible** — 20 étapes, rollback possible à chaque étape, aucune suppression irréversible sans validation.
5. **Zéro doublon** — pas de registry/RAG/MCP/Memory/Agent/tool local dans l'UI.

**Domaines couverts par les plans** :
- Modèles & Providers (`ETHAN_WEBUI_MODELS_PROVIDERS_ARCHITECTURE.md`)
- RAG, Knowledge, Files, MCP, Tools (`ETHAN_WEBUI_RAG_KNOWLEDGE_FILES_MCP_TOOLS_ARCHITECTURE.md`)
- Settings (`ETHAN_WEBUI_SETTINGS_ARCHITECTURE.md`)
- Matrice architecturale (`ETHAN_WEBUI_ARCHITECTURE_MATRIX.md`)
- Stratégie de migration (`ETHAN_WEBUI_MIGRATION_STRATEGY.md`)

---

## 2. Synthèse de l'état actuel

### 2.1 Backend — `core/` (riche et structuré)

| Module | Contenu | État |
|---|---|---|
| `core/llm/` | `provider_manager.py`, `model_store.py`, `provider_factory.py`, `router.py`, `selector.py`, `registry.py`, `tracker.py`, `client.py`, `images.py`, `tts.py`, `providers/` | ✅ Existant |
| `core/rag/` | `pipeline.py`, `ingestion.py`, `retrieval.py`, `embeddings.py`, `context.py` | ✅ Existant |
| `core/tools/` | `registry.py`, `selector.py`, `executor.py`, `monitor.py`, `functions.py`, `servers.py`, `manager.py`, `types.py` | ✅ Existant |
| `core/knowledge/` | `manager.py`, `collections.py`, `types.py` | ✅ Existant |
| `core/state/` | `chats.py`, `files.py`, `channels.py`, `notes.py`, `record_store.py`, `webui_store.py`, `composite_backend.py`, `postgres_state.py`, `redis_state.py` | ✅ Existant |
| `core/auth/` | `users.py`, `groups.py`, `api_keys.py`, `oauth.py`, `ldap.py`, `scim.py` | ✅ Existant |
| `core/agents/` | `manager.py`, `base.py`, `types.py` | ✅ Existant |
| `core/config/` | `schema.py`, `service.py`, `store.py`, `loader.py`, `secrets.py`, `prompts.py` | ✅ Existant |
| `core/` (autres) | `bus/`, `events/`, `planner/`, `missions/`, `goals/`, `skills/`, `memory/`, `facts/`, `orchestrator/`, `scheduler/`, `safety/`, `security/`, `telemetry/`, `metrics/`, `audit/`, `approval/`, `autonomy/`, `cognition/`, `metacognition/`, `learning/`, `capabilities/`, `deployment/`, `ethan_types/`, `modules/`, `registry/`, `context/`, `cost/`, `executive/` | ✅ Existant |

### 2.2 API — `interfaces/api/` (FastAPI, riche)

| Router | Endpoints | État |
|---|---|---|
| `v1.py` | agents, goals, missions, memory/facts, skills, knowledge, knowledge/collections, rag/documents, rag/retrieve, rag/context, flux, settings, chat/completions, chat/history, plugins | ✅ Existant |
| `config.py` | GET/PUT/PATCH/DELETE `/config/{domain}`, import/export/validate | ✅ Existant |
| `domains.py` | chats, files, users, groups | ✅ Existant |
| `providers.py` | CRUD providers, test, default, models | ✅ Existant |
| `models.py` | CRUD models, search, toggle | ✅ Existant |
| `message.py` | POST /message, /intent, /health | ✅ Existant |
| `realtime.py` | WebSocket /ws | ✅ Existant |
| `state.py` | /state, /version | ✅ Existant |
| `capabilities.py` | automations, calendar | ✅ Existant |
| `internal.py` | audit, budget, facts | ✅ Existant |

### 2.3 Frontend — `interfaces/webui/` (Next.js 15 + React 19)

**Stack** : Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, Zustand, TanStack Query, shadcn/ui, framer-motion, lucide-react.

**Features** (dans `src/features/`) :
- `assistant/` — chat avec streaming SSE
- `agents/`, `goals/`, `missions/` — agents, objectifs, missions
- `knowledge/`, `memory/`, `skills/` — connaissance, mémoire, compétences
- `providers/`, `models/` — providers et modèles
- `settings/`, `plugins/`, `flux/` — paramètres, plugins, logs

**Pages** (dans `src/app/`) :
- `(auth)/` — login, register
- `(dashboard)/` — dashboard principal avec sidebar

**Lib** (`src/lib/`) : `api/` (clients modulaires), `auth/`, `core/`, `types/`, `components/`.

### 2.4 Infrastructure

- **Docker** : `deploy/Dockerfile.{api,kernel,module,pg_backup,python-base,ui}`, `docker-compose*.yml` (cluster, dev, observability, openwebui, ports, prod)
- **Observabilité** : `infrastructure/{alloy,grafana,jaeger,loki,otel,prometheus,promtail,posthog}`
- **Déploiement** : `infrastructure/{docker,kubernetes,launchd,systemd,traefik,vault,secrets}`
- **CI/CD** : `.pre-commit-config.yaml`, `Makefile`, `pyproject.toml`

---

## 3. Écarts entre l'état actuel et l'architecture cible

### 3.1 Constat majeur : l'ancienne WebUI Next.js est DÉJÀ largement implémentée

Le `ETHAN_WEBUI_MASTER_PLAN.md` indique :
- **P0** (Core infrastructure & chat) : ✅ COMPLETE
- **P1** (Workspace) : ✅ COMPLETE
- **P2** (Memory, Planner, Terminal, Settings, Plugins) : ✅ COMPLETE
- **P3** (Desktop, Voice, Mobile, Agents autonomes) : PLANNED

Cela **contredit partiellement** la stratégie de migration qui suppose de créer une nouvelle WebUI à partir d'un fork Open WebUI.

### 3.2 Contradiction résolue — Décision validée (2026-08-17)

| Document | Position |
|---|---|
| `ETHAN_WEBUI_MIGRATION_STRATEGY.md` | Fork Open WebUI → nouvelle WebUI (20 étapes) |
| `ETHAN_WEBUI_MASTER_PLAN.md` | WebUI Next.js existante, P0-P2 COMPLETE |

**Décision validée par l'utilisateur** : **Option (b) + (c) — Hybride**.
- **Conserver** la WebUI Next.js existante comme base (réutilise le travail P0-P2 déjà fait).
- **Enrichir** avec les concepts UX d'Open WebUI (chat, sidebar, model selector, settings) sans fork.
- **Ne pas** abandonner la WebUI Next.js existante.

**Conséquences** :
- La stratégie de migration `ETHAN_WEBUI_MIGRATION_STRATEGY.md` est **adaptée** : au lieu d'un fork Open WebUI, on enrichit la WebUI existante.
- Les 20 étapes restent valables mais l'étape 1 (fork) devient « audit UX Open WebUI → port des composants ».
- Le principe « ETHAN = source de vérité, WebUI = interface » reste inchangé.

### 3.3 Écarts fonctionnels identifiés

| Domaine | État actuel | Cible | Écart |
|---|---|---|---|
| **Auth** | JWT HttpOnly cookie | OAuth, LDAP, SCIM, API keys | Partiel (core/auth existe, UI à vérifier) |
| **Models** | CRUD + sélection | Gestion avancée (pinning, presets) | Partiel |
| **Providers** | CRUD + test + default | Gestion avancée (multi-URL, fallback) | Partiel |
| **Conversations** | CRUD + messages | Partage, recherche, archivage | Partiel |
| **Files** | Upload + liste | Preview, extraction, statut | Partiel |
| **Knowledge** | Collections + documents | Graphe, export, ACL | Partiel |
| **RAG** | Ingestion + retrieval | Hybride, reranking, web search | Partiel |
| **MCP** | Serveurs (listing) | Client MCP complet (streamable_http, OAuth) | **Manquant** |
| **Tools** | Registry + exécution | Valves, export/import, builtins | Partiel |
| **Memory** | Faits + événements | Gestion avancée | Partiel |
| **Settings** | GET/PUT config | 13 onglets admin + user settings | **Manquant** |
| **Permissions** | RBAC de base | Permissions granulaires par domaine | Partiel |

---

## 4. Phases d'implémentation identifiées

### Phase A — Consolidation (fondations)
- [ ] Résoudre la contradiction WebUI existante vs fork Open WebUI
- [ ] Vérifier que les tests passent (`pytest`, `npm test`)
- [ ] Vérifier que le build passe (`npm run build`, `uv build`)
- [ ] Vérifier que Docker build passe

### Phase B — Alignement MOVE-TO-CORE
- [ ] MCP client → `core/tools/mcp_client.py`
- [ ] Web search → `core/tools/web_search.py`
- [ ] Reranker → `core/rag/reranker.py`
- [ ] Storage providers → `core/file_storage/`
- [ ] Fusion tools/functions

### Phase C — Richesses UX (inspiré Open WebUI)
- [ ] Settings UI (13 onglets)
- [ ] Composants chat avancés
- [ ] Thèmes

### Phase D — Production
- [ ] CI/CD
- [ ] Tests e2e
- [ ] Monitoring

---

## 5. Dépendances entre phases

```
Phase A (fondations)
   ↓
Phase B (MOVE-TO-CORE) ──→ Phase C (UX)
   ↓                              ↓
Phase D (production) ←────────────┘
```

- **Phase A** doit précéder tout le reste (stabilité).
- **Phase B** doit précéder **Phase C** (l'UI consomme l'API Core).
- **Phase D** est la dernière (tout doit être stable).

---

## 6. Première phase exécutable

**Phase A — Consolidation** est la première phase exécutable.

### Objectif
Vérifier que le repository est dans un état sain avant toute modification.

### Fichiers concernés
- `pyproject.toml` (dépendances Python)
- `interfaces/webui/package.json` (dépendances frontend)
- `docker-compose*.yml` (services Docker)
- `Makefile` (commandes de build/test)

### Actions
1. Lancer `pytest` → vérifier que les tests passent
2. Lancer `npm run validate` (typecheck + lint + test) → vérifier que le frontend compile
3. Lancer `docker compose build` → vérifier que les images se construisent
4. Documenter les résultats

### Critères de sortie
- [ ] Tous les tests passent
- [ ] Le build frontend passe
- [ ] Le build Docker passe
- [ ] Les résultats sont documentés

---

## 7. Décisions prises et en attente

### Décisions prises

1. **Contradiction WebUI — RÉSOLUE (2026-08-17)** : Option **(b) + (c) — Hybride** validée par l'utilisateur.
   - Conserver la WebUI Next.js existante comme base.
   - Enrichir avec les concepts UX d'Open WebUI (chat, sidebar, model selector, settings) sans fork.
   - La stratégie `ETHAN_WEBUI_MIGRATION_STRATEGY.md` est adaptée : l'étape 1 (fork) devient « audit UX Open WebUI → port des composants ».

### Décisions validées (2026-08-17)

2. **Périmètre de la Phase A — VALIDÉ** : La consolidation (vérification tests/build/Docker) est bien la priorité.
   - Lancer `pytest` et `npm run validate` (typecheck + lint + test).
   - Lancer `npm run build` et `uv build`.
   - Lancer `docker compose build`.
   - Documenter les résultats dans `docs/plans/execution/`.

3. **Priorisation des domaines — VALIDÉE** : Après la Phase A, l'ordre est :
   - **1. MCP** — ajouter le client MCP complet (streamable_http, OAuth) → `core/tools/mcp_client.py`.
   - **2. Settings** — 13 onglets admin + user settings → `core/config` + UI.
   - **3. RAG** — hybride, reranking, web search → `core/rag`.
   - Ensuite : Files, Tools, Knowledge, Memory, Auth, Models, Providers, Conversations, Permissions.
</write_to_file>
<task_progress>
- [x] Lister les documents de docs/plans/
- [x] Inspecter interfaces/ (api routers + webui src)
- [x] Inspecter core/ (llm, rag, tools, knowledge, state, auth, agents)
- [x] Inspecter infrastructure/, deploy/, tests/, fichiers racine
- [x] Lire MASTER_PLAN (P0-P2 COMPLETE)
- [x] Lire V2_ARCHITECTURE
- [x] Inspecter les routers API (v1, config, domains, providers, models, message, realtime, state, capabilities, internal)
- [x] Inspecter les routes v1 restantes (knowledge, tools, plugins, flux) + package.json
- [x] Produire la synthèse de l'architecture cible
- [x] Produire la synthèse de l'état actuel
- [x] Identifier les écarts
- [x] Identifier les phases et dépendances
- [x] Identifier la première phase exécutable et les fichiers concernés
- [x] Créer le rapport d'analyse dans docs/plans/execution/00-ETAT-DES-LIEUX.md
</task_progress>
</write_to_file>