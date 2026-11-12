# Matrice architecturale — Frontière ETHAN ↔ ETHAN WebUI (base Open WebUI)

> **Objectif** : Définir la frontière stricte entre ETHAN (Core/Runtime/API) et le futur ETHAN WebUI dont Open WebUI sert de référence UX.
> **Principe** : **une seule source de vérité par domaine** — toujours dans `core/`. Open WebUI ne fournit que de la **UI/UX/composants/navigation**, jamais de logique métier ni de provider/registry concurrent.
> **Contraine** : `Ne modifie aucun fichier.` Aucun fichier source existant n'est touché.

---

## 0. Principe de non-dualité (frontière immuable)

> Il ne doit **jamais** exister deux implémentations concourantes. Le futur WebUI est un *thin client* qui **consomme** les capacités ETHAN.

| Capability ETHAN | Source de vérité unique | ✅ autorisé dans WebUI | ❌ interdit dans WebUI |
|---|---|---|---|
| Model Registry | `core/llm/model_store.py` | UI liste/toggle/pin | registry modèle local |
| Provider Registry | `core/llm/provider_manager.py` + `providers/` | UI connexions/statut | provider/proxy local |
| RAG pipeline | `core/rag/` | UI ingestion/config | pipeline parsing/indexation local |
| MCP | `core/tools/servers.py` (client Core) | UI serveur list/connect | client MCP natif UI |
| Memory/Facts | `core/memory/` + `core/facts/` | UI query/update/delete | store mémoire local |
| Agents | `core/agents/` + `core/modules/` | UI agent list/execute | gestion agent local |
| Configuration | `core/config/` + `core/config/secrets.py` | UI settings GET/PUT | PersistentConfig local |
| Chat/Conversations | `core/state/chats.py` | UI rendu/stream | persistance chat locale |

---

## 1. Matrice par domaine

Colonnes : **Fonctionnalité | Source de vérité (Core) | API | UI | Persistence | Responsable | Consommateurs | OpenWebUI (référence UX)**

### 1.1 Chat & streaming (SSE/WebSocket)

| Fonctionnalité | Source de vérité | API | UI | Persistence | Responsable | Consommateurs | OpenWebUI référence |
|---|---|---|---|---|---|---|---|
| Orchestration chat (validate modèle+ACL, contexte skills/tools/RAG/memory, génération, events) | `core/chat/pipeline.py` (ChatPipeline) | v1.py `/v1/chat` (POST + SSE stream) + realtime.py | features/assistant/ + chat.service.ts | core/state/chats.py + record_store | core/chat | WebUI, CLI, Desktop, Mobile, Agents | Chat.svelte, controls live, feedback, export, share |
| Message user ↔ réponse streaming | ChatPipeline.run | SSE `/v1/chat` | components/chat, MessageInput, Messages | ChatStore.add_message | core/chat | WebUI | chat.svelte |
| Paramètres live (température/top_p/max_tokens etc) | ChatPipeline (params validés Core) | `/v1/chat` payload | ChatControls.svelte | — (non persisté serveur) | core/chat | WebUI | ChatControls.svelte |
| Bifurcations / réponses alternatives | core/state/chats.py branching | `/v1/chats/{id}/branch` | UI branche | ChatStore branches | core/state | WebUI | Chat.svelte |
| Continue / Regenerate / Edit / Rate | core/chat/pipeline (events) | `/v1/chat/{id}/regenerate\|continue\|edit` | Message actions | ChatStore | core/chat | WebUI | actions inline |
| Export / Share | ChatStore share_id | `/v1/chats/{id}/share\|export` | ShareChatModal | ChatStore share_id + CoreWebUIStore | core/state | WebUI | ShareChatModal.svelte |

### 1.2 Conversations

| Fonctionnalité | Source de vérité | API | UI | Persistence | Responsable | Consommateurs | OpenWebUI référence |
|---|---|---|---|---|---|---|---|
| CRUD conversation | `core/state/chats.py` ChatStore | domains `/v1/chats`, v1 `/v1/chats/{id}` | chat-sidebar.tsx | RecordStore (chats) | core/state | WebUI, CLI | chats.ts |
| Archivage / épinglage / tags / folders | ChatStore fields | `/v1/chats/{id}/archive\|pin`, `/v1/chats/{id}/tags` | chat-sidebar filtres | ChatStore | core/state | WebUI | Folder/TagChatModal |
| Clone conversation | ChatStore | `/v1/chats/{id}/clone` | — | ChatStore | core/state | WebUI | chats clone |
| Import/Export | ChatStore | `/v1/chats/import\|export` | — | ChatStore | core/state | WebUI, CLI | chats import/export |
| Stats d'usage | core/metrics analytics | `/analytics/*` | analytics UI | metrics | core/metrics | admins | analytics.py |

### 1.3 Models

| Fonctionnalité | Source de vérité | API | UI | Persistence | Responsable | Consommateurs | OpenWebUI référence |
|---|---|---|---|---|---|---|---|
| Catalogue modèles (custom cards) | `core/llm/model_store.py` (ModelStore) | routers/models.py `/v1/models` | features/providers + use-models.ts | ModelStore (CoreWebUIStore) | core/llm | WebUI, CLI, API | /workspace/models, models.ts |
| Fiches & profils | ModelStore | `/v1/models/{id}` | UI profil | ModelStore | core/llm | WebUI | models create/edit |
| Sync providers | `core/llm/provider_manager.py` | `/v1/providers/sync` | bouton sync | ModelStore | core/llm | WebUI | models sync |
| Import/Export | ModelStore | `/v1/models/import\|export` | — | ModelStore | core/llm | WebUI | models import/export |
| Suggestions prompts | ModelStore defaults | `/v1/config/models/defaults` | PromptSuggestion | CoreWebUIStore | core/config | WebUI | configs suggestions |

### 1.4 Providers

| Fonctionnalité | Source de vérité | API | UI | Persistence | Responsable | Consommateurs | OpenWebUI référence |
|---|---|---|---|---|---|---|---|
| Registry fournisseurs | provider_factory + provider_manager | routers/providers.py `/v1/providers` | features/providers + ai-providers-section | CoreWebUIStore (providers) | core/llm | WebUI, CLI, API | settings/[tab] connections |
| Connexions (Ollama/OpenAI/OpenRouter/Anthropic/Google/Azure/vLLM/LMStudio/llama.cpp) | `core/llm/providers/*` | `/v1/providers/{id}` | AddConnectionModal | core/llm + secrets | core/llm | WebUI | AddConnectionModal, connections |
| Clés API/Screts | `core/config/secrets.py` (env/Vault) | `/v1/providers/{id}/secrets` (isolé) | champ secret UI | secret manager (Vault/env) | core/config | providers, auth | 🔒 migrer de PersistentConfig |
| Routing & sélection | router.py + routing.yaml + selector.py | `/v1/models/{id}/route` | — | routing.yaml | core/llm | ChatPipeline, Agents | routing |
| Tracker coûts | `core/llm/tracker.py` | `/v1/providers/{id}/usage` | analytics usage | metrics | core/llm/cost | WebUI | analytics tokens |

### 1.5 RAG (ingestion, embeddings, retrieval)

| Fonctionnalité | Source de vérité | API | UI | Persistence | Responsable | Consommateurs | OpenWebUI référence |
|---|---|---|---|---|---|---|---|
| Pipeline ingestion | `core/rag/ingestion.py` | `/v1/knowledge/{id}/ingest` | ingestion UI | core/rag + vector backend | core/rag | ChatPipeline, Knowledge | retrieval process file/text/youtube/web |
| Embeddings | `core/rag/embeddings.py` | `/v1/retrieval/embeddings` | config UI | vector backend | core/rag | ingestion | retrieval embedding |
| Retrieval | `core/rag/retrieval.py` | `/v1/knowledge/{id}/query` | — (interne) | vector backend | core/rag | ChatPipeline | retrieval query doc/collection |
| Contexte RAG | `core/rag/context.py` | — (interne) | — | vector backend | core/rag | ChatPipeline | |
| Backends vectoriels | core/memory backends (Qdrant/pgvector/Chroma) | — (interne) | config UI | vector DB | core/memory | ingestion/retrieval | 15 DBs OWUI → adapter factory Core RFC |
| Recherche web | `core/tools/` (web search tool) | `/v1/retrieval/search/web` | — | — | core/tools | retrieval | 20+ moteurs OWUI → Tool Core |
| Reranker | core/rag + tools | — (interne) | config UI | — | core/rag | retrieval | rerankers colbert/external |

### 1.6 Knowledge (collections / graphe)

| Fonctionnalité | Source de vérité | API | UI | Persistence | Responsable | Consommateurs | OpenWebUI référence |
|---|---|---|---|---|---|---|---|
| Gestion collections | `core/knowledge/collections.py` (KnowledgeCollectionManager) | routers/knowledge.py `/v1/knowledge` | features/knowledge + use-knowledge.ts | CoreWebUIStore + vector backend | core/knowledge | WebUI, ChatPipeline | /workspace/knowledge |
| Nœuds & connexions (graphe) | types.py KnowledgeNode/Connection + manager.py | `/v1/knowledge/{id}/graph` | graphe UI (adapter) | KnowledgeStore | core/knowledge | ChatPipeline, Agents, Memory | (concept ETHAN — enrichir UX OWUI) |
| Réindexation | KnowledgeManager | `/v1/knowledge/{id}/reindex` | bouton UI | vector backend | core/knowledge | WebUI | knowledge reindex |
| Accès/Sharing | KnowledgeManager access | `/v1/knowledge/{id}/access/update` | access UI | CoreWebUIStore | core/knowledge | WebUI | access update |
| Upload fichiers knowledge | FileStore + KnowledgeManager | `/v1/knowledge/{id}/file/{add\|update\|remove}` | file picker UI | FileStore | core/knowledge + state/files | WebUI | knowledge file add/remove |

### 1.7 Files & Storage

| Fonctionnalité | Source de vérité | API | UI | Persistence | Responsable | Consommateurs | OpenWebUI référence |
|---|---|---|---|---|---|---|---|
| Métadonnées fichiers | `core/state/files.py` (FileStore) | domains `/v1/files` | /dashboard/documents | RecordStore (files) + storage backend | core/state | WebUI, Knowledge | files.ts, ContentRenderer |
| Upload & storage (local/S3/GCS/Azure) | FileStore + secrets.py | `/v1/files` (upload), `/v1/config/connections` | upload UI | storage backend | core/state + config | WebUI, Knowledge | storage provider config |
| Traitement (status) | FileStore | `/v1/files/{id}/process/status` | status UI | RecordStore | core/state | WebUI | files process status |
| Contenu / preview | FileStore | `/v1/files/{id}/content` | preview UI | storage backend | core/state | WebUI | files content/html |
| Search contenu | FileStore | `/v1/files/search` | search UI | RecordStore | core/state | WebUI | files search |

### 1.8 MCP (serveurs d'outils)

| Fonctionnalité | Source de vérité | API | UI | Persistence | Responsable | Consommateurs | OpenWebUI référence |
|---|---|---|---|---|---|---|---|
| Client MCP (transport/OAuth/introspection) | `core/tools/servers.py` (MOVE client OWUI→Core) | `/v1/tools/servers/{id}/connect`, `/v1/tools/servers/{id}/tools` | ToolServersModal | ToolServerManager | core/tools | WebUI | utils/mcp/client.py (backend Core) |
| Lifecycle serveurs | ToolServerManager | `/v1/tools/servers` (list/create/toggle) | ToolServersModal | CoreWebUIStore (tool-servers) | core/tools | WebUI | configs tool_servers |
| Statut connexion | ToolServerManager | `/v1/tools/servers/{id}` | status UI | — | core/tools | WebUI | terminal/tool servers config |
| Consommateurs | — | — | — | — | core/tools | WebUI, CLI, Desktop, Mobile, Autonomous agents, MCP servers | — |

### 1.9 Tools & Functions (appelables)

| Fonctionnalité | Source de vérité | API | UI | Persistence | Responsable | Consommateurs | OpenWebUI référence |
|---|---|---|---|---|---|---|---|
| Registry outils | `core/tools/registry.py` (ToolRegistry) | routers/tools.py `/v1/tools` | features/skills + components/tools | CoreWebUIStore (tools) | core/tools | WebUI, ChatPipeline, Agents | workspace/tools |
| Sélection / exécution | selector.py + executor.py | `/v1/tools/{id}/execute` (interne) | — | ToolRegistry | core/tools | ChatPipeline, Agents | |
| Builtin outils | builtin tools | `/v1/tools/{builtin}` | — | — | core/tools | WebUI, pipeline | tools/builtin.py |
| Valves (config user/dev) | Tool.parameters/schema | `/v1/tools/{id}/valves` | valves modal UI | CoreWebUIStore | core/tools | WebUI | Tool valves modale |
| Fonctions callables (unified) | ToolRegistry (fusion functions↔tools) | `/v1/tools` | — | CoreWebUIStore | core/tools | WebUI, pipeline | ⚠️ fusionner functions.py↔tools.py → DELETE doublon |

### 1.10 Memory & Facts

| Fonctionnalité | Source de vérité | API | UI | Persistence | Responsable | Consommateurs | OpenWebUI référence |
|---|---|---|---|---|---|---|---|
| Facts (ingestion/retrieval) | `core/facts/{ingest,retrieval,store,types}` | v1 `/v1/memory/facts` | features/memory | CoreFactsStore | core/facts | ChatPipeline, Memory | memories.ts |
| Memory lifecycle | `core/memory/{manager,consolidation,forgetting,recall}` | `/v1/memory/events\|ingest` | — | backends (chromadb/qdrant/pg) | core/memory | ChatPipeline, Facts | memories.py vector backends |
| Compression/oubli | compression.py, forgetting.py | — (interne) | — | vector backend | core/memory | memory | |
| Rappel contextuel | recall.py | — (interne) | — | — | core/memory | ChatPipeline | |
| Consommateurs | — | — | — | — | core/memory + core/facts | WebUI, ChatPipeline, Agents, Memory capability | memories.ts |

### 1.11 Agents

| Fonctionnalité | Source de vérité | API | UI | Persistence | Responsable | Consommateurs | OpenWebUI référence |
|---|---|---|---|---|---|---|---|
| Registry/état agents | `core/agents/manager.py` + types.py | v1 `/v1/agents` | features/agents + /agents | CoreRecordStore (agents) | core/agents | WebUI, CLI, Autonomy | ⚠️ OWUI n'a pas d'agents → migrer automations→Core |
| Exécution agent | AgentManager.execute | `/v1/agents/{id}/execute` | — | AgentStore | core/agents | Autonomy engine, CLI | automations run |
| Autonomie (curiosity/healing) | `core/autonomy/` | — (interne) | — | — | core/autonomy | orchestrator | automations triggers/actions (ref) |
| Module plugin | `core/modules/` | — (interne) | — | — | core/modules | Agents, Autonomy | functions/pipelines (ref extensible) |
| Consommateurs | — | — | — | — | core/agents + modules | WebUI, CLI, Desktop, Mobile, Autonomous agents | features/agents |

### 1.12 Skills

| Fonctionnalité | Source de vérité | API | UI | Persistence | Responsable | Consommateurs | OpenWebUI référence |
|---|---|---|---|---|---|---|---|
| Registry skills | `core/skills/{registry,store,executor,selector,composer,lab}` | `/v1/skills` | features/skills | SkillStore | core/skills | ChatPipeline, Agents, Planner | workspace/skills |
| Composer/Lab | composer.py, lab.py | — | skills lab UI | SkillStore | core/skills | WebUI | skills create/edit |
| Sélection | selector.py | — (interne) | — | SkillStore | core/skills | ChatPipeline | |

### 1.13 Settings & Configuration

| Fonctionnalité | Source de vérité | API | UI | Persistence | Responsable | Consommateurs | OpenWebUI référence |
|---|---|---|---|---|---|---|---|
| Config système | `core/config/{loader,schema,service,store}` + secrets.py | `/v1/settings` (GET/PUT) + `/v1/config/*` | features/settings + components/settings | CoreWebUIStore + secret manager | core/config | WebUI, CLI, Runtime | settings/[tab] |
| Secrets (clés/provider) | `core/config/secrets.py` (env/Vault) | `/v1/config/secrets` (isolé) | champ secret UI | secret manager | core/config | providers, auth | 🔒 migrer de PersistentConfig DB |
| Import/Export config | core/config store | `/v1/config/import\|export` | — | CoreWebUIStore | core/config | WebUI | configs import/export |
| Bannières/Suggestions | core/config | `/v1/config/banners` | banners UI | CoreWebUIStore | core/config | WebUI | banners, suggestions |
| UI prefs (dark/langue) | core/config | `/v1/settings` | layout switcher | CoreWebUIStore | core/config | WebUI | interface settings |

### 1.14 Users & Groups

| Fonctionnalité | Source de vérité | API | UI | Persistence | Responsable | Consommateurs | OpenWebUI référence |
|---|---|---|---|---|---|---|---|
| Gestion utilisateurs | `core/auth/users.py` (UserManager) | domains `/v1/users` | /settings users tab | CoreRecordStore (users) | core/auth | WebUI, Auth | users.ts |
| Profil/Status | UserManager | `/v1/users/{id}` | profil UI | CoreRecordStore | core/auth | WebUI | user settings |
| Groupes/Rôles | `core/auth/groups.py` (GroupManager) | `/v1/users/groups` | groups UI | CoreRecordStore | core/auth | Auth, Permissions | groups |
| Consommateurs | — | — | — | — | core/auth | WebUI, Auth, Permissions | users.ts |

### 1.15 Authentication

| Fonctionnalité | Source de vérité | API | UI | Persistence | Responsable | Consommateurs | OpenWebUI référence |
|---|---|---|---|---|---|---|---|
| Auth provider JWT | `core/auth/` (oauth.py) | interfaces/api/auth.py `/auth/*` | /auth/login + lib/auth/client.ts | — (cookie HttpOnly) | core/auth | WebUI, CLI, API | utils/auth.py |
| OAuth (Google/Microsoft/GitHub/OIDC/Feishu) | `core/auth/oauth.py` | `/auth/oauth/{provider}/token/exchange` | OAuth buttons UI | OAuthSessionStore | core/auth | Auth | utils/oauth.py (handlers réutilisables) |
| LDAP | `core/auth/ldap.py` | `/auth/admin/config/ldap/*` | ldap config UI | core/config/secrets | core/auth | Auth | ldap config |
| SCIM provisioning | `core/auth/scim.py` | `/scim/*` | — (externe) | CoreRecordStore | core/auth | Identity providers | scim.py |
| API Keys | `core/auth/api_keys.py` | `/auth/api_key` (CRUD) | api key UI | CoreRecordStore (hashed) | core/auth | API, CLI | api_key auths |
| SSO/Session | core/auth | cookie HttpOnly | AuthProvider | — | core/auth | WebUI, CLI | AuthProvider.tsx |

### 1.16 Permissions & Access Control

| Fonctionnalité | Source de vérité | API | UI | Persistence | Responsable | Consommateurs | OpenWebUI référence |
|---|---|---|---|---|---|---|---|
| Permission enum | `core/auth/__init__.py` (Permission) | require_permission(Permission.X) | — | — | core/auth | tous routers | ⚠️ UserPermissions 15 dims → map Permission Core |
| Default permissions | core/auth | `/v1/users/default/permissions` | permissions page UI | CoreRecordStore | core/auth | WebUI | users default perms |
| Access grants (partage) | core/auth/groups.py + access | `/v1/access_grants` | sharing UI | CoreRecordStore (access_grants) | core/auth | WebUI | access_grants table |
| Contrôle par endpoint | require_permission | — | — | Permission | core/auth | routers | |
| Feature flags | core/config | `/v1/features` (via settings) | feature UI toggles | CoreWebUIStore | core/config | WebUI | features permissions |

### 1.17 Événements / Bus / Observabilité

| Fonctionnalité | Source de vérité | API | UI | Persistence | Responsable | Consommateurs | OpenWebUI référence |
|---|---|---|---|---|---|---|---|
| Event bus (timeflux) | `core/bus/`, `core/events/` | `/v1/flux` (list), `/v1/flux/{id}` (get) | features/flux + /logs/flux | — (éphém/Résis) | core/events | WebUI logs, audit | analytics/evaluations |
| Audit | `core/audit/` | — | logs UI | audit | core/audit | Security | |
| Télémétrie | `core/telemetry/` | — | — | — | core/telemetry | Observability | |
| Métriques/Santé | `core/metrics/` | healthcheck, analytics | dashboard santé | metrics | core/metrics | SRE | analytics |

---

## 2. Schéma de flux (frontière claire)

```
              ┌──────────────────────────────────────────────┐
              │            ETHAN Core / Runtime               │
              │   ┌──────────┬──────────┬──────────┐         │
              │   │  core/   │  core/   │ interfaces│         │
              │   │ llm/     │ rag/     │ /api/     │         │
              │   │ chat/    │ knowledge│ routers/  │         │
              │   │ agents/  │ memory/  │  v1.py    │         │
              │   │ tools/   │ state/   │ domains   │         │
              │   │ skills/  │ config/  │ auth      │         │
              │   └──────────┴──────────┴──────────┘         │
              │        SOURCE DE VÉRITÉ UNIQUE                │
              └─────────────────────┬────────────────────────┘
                                    │ REST + SSE/WebSocket (thin gateway)
                                    │
              ┌─────────────────────┴────────────────────────┐
              │          ETHAN WebUI  (thin client)           │
              │  ← Fork Open WebUI (UX/composants/navigation)  │
              │   Next.js  +  lib/api/* (clients modulaires)    │
              └─────────────────────┬────────────────────────┘
                                    │
        ┌─────────────┬─────────────┼─────────────┬─────────────┐
        ▼             ▼             ▼             ▼             ▼
     WebUI          CLI            Desktop        Mobile       Agents autonomes
    (interface)   (interface)    (interface)   (interface)   (consommateur Core)
```

**Règles de la frontière :**
1. Le **WebUI ne possède aucun provider/registry/RAG/Memory/Agent local** — il consomme `core/`.
2. Open WebUI est **référence UX** ; la logique métier est **dans `core/`**.
3. Toute capacité n'existant pas dans `core/` → **RFC → MOVE-TO-CORE**.
4. Aucune source de vérité ne doit être dupliquée (matrice §0).

---

## 3. Synthèse migration OWUI → ETHAN Core

| Capacité OWUI | Module ETHAN Core (source de vérité) | Migration |
|---|---|---|
| Chat.svelte + SSE | core/chat/pipeline.py + ChatStore | UI fork → Next.js ; backend → Core |
| Models/Prompts registry | core/llm/model_store.py | REPLACE OWUI models.py |
| Provider connections | core/llm/providers/* + secrets | REPLACE OWUI configs PersistentConfig |
| retrieval/ (RAG 15 DB) | core/rag/ + vector factory RFC | ADAPT ; OWUI = référence indépendante |
| knowledge collections | core/knowledge/ | ADAPT ; + graphe |
| files storage | core/state/files.py + storage | ADAPT |
| MCP client utils/mcp | core/tools/servers.py (+ MOVE) | MOVE-TO-CORE |
| tools/functions/valves | core/tools/ (fusion) | REPLACE ; DELETE doublon functions |
| memories | core/memory/ + core/facts/ | REPLACE ; unifier |
| automations → agents | core/agents/ + core/modules/ + core/autonomy | REPLACE |
| PersistentConfig → secrets | core/config/secrets.py + core/config/ | REPLACE (secrets isolés) |
| UserPermissions | core/auth Permission enum | ADAPT (mapping) |
| OAuth/LDAP/SCIM | core/auth/{oauth,ldap,scim} | REPLACE |
| analytics/evaluations | core/metrics/analytics + core/learning/evaluations | ADAPT |
| channels | core/state/channels.py | ADAPT |
| calendar/terminals/audio/images/notes | core/scheduler/calendar, builtin tools | ADAPT/MOVE |

---

## 4. Responsabilités (owner Core) récapitulatives

| Owner Core Module | Domaines sous sa responsabilité |
|---|---|
| `core/llm` | Models, Providers, routing, embeddings provider, tracker coûts |
| `core/chat` | Chat pipeline, streaming, messages |
| `core/state` | Conversations, Files, Notes, Channels, record store |
| `core/rag` | Ingestion, embeddings, retrieval, context, vector backends |
| `core/knowledge` | Collections, graphe de connaissance |
| `core/tools` | Registry outils, MCP servers, execution, sélection |
| `core/skills` | Registry/selector/executor skills, composer |
| `core/memory` + `core/facts` | Memory lifecycle, facts, vector stores |
| `core/agents` + `core/modules` + `core/autonomy` | Agents, modules plugins, autonomie |
| `core/auth` | Users, groups, permissions, OAuth/LDAP/SCIM, API keys |
| `core/config` | Settings, configuration, secrets, schema, bootstrap |
| `core/events` + `core/bus` | EventBus, timeflux/événements, audit |
| `core/metrics` + `core/learning` | Analytics, évaluations, télémétrie, santé |

> **Le WebUI n'est responsable que de l'UI/UX/composants/navigation** et consomme les APIs ci-dessus en tant que client fin.
