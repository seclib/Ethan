# Analyse & Plan de Migration — Open WebUI → ETHAN WebUI

> **Objet** : Déterminer si Open WebUI peut devenir la base directe d'ETHAN WebUI, et produire un **tableau de migration détaillé**.
> **Stratégie visée** : `Open WebUI → fork → ETHAN WebUI → ETHAN API → ETHAN Core/Runtime`.
> **Contrainte** : L'instance Open WebUI Docker reste **indépendante** (référence UX/fonctionnelle). Aucun fichier source existant n'est modifié par cette analyse.
> **Principe ETHAN (AGENTS.md)** : toute capacité intelligente **doit** exister dans `core/` ou `runtime/` avant d'être exposée par une interface. La WebUI est un *thin client*.

---

## 0. Synthèse exécutive

| Axe | Open WebUI | ETHAN Core | Verdict |
|---|---|---|---|
| **Nature** | Application Web complète (backend + UI monolithiques, logique métier dans le backend mais tightly-coupled à la UI) | Runtime IA modulaire (Core/Runtime) + interfaces thin clients | OWUI = référence UX ; ETHAN = source de vérité |
| **Backend** | FastAPI monolithique, SQLAlchemy/SQLite+PG, logique dans routers + models + utils | Core Python modulaire, EventBus, RecordStore abstrait, gestion d'événements | ETHAN est **mieux structuré** (clean separation) |
| **Frontend** | Svelte 5 (SvelteKit), components tightly couplés au backend OWUI | Next.js (React), clients API modulaires + React Query hooks (thin) | OWUI **meilleure UX mature** ; ETHAN **meilleure architecture client** |
| **Providers LLM** | Connections persistantes (Ollama, OpenAI, OpenRouter, Anthropic, Google, Azure, vLLM, LMStudio, llama.cpp) via valves | `core/llm/` providers homogènes (anthropic, gemini, llamacpp, lmstudio, ollama, openai, openai_compatible, vllm), routing.yaml, selector | **OWUI =+ maturité UI** ; **ETHAN = architecture plus propre** |
| **RAG** | Pipeline ingestion + 15 vectordbs + 20 moteurs recherche web + 3 rerankers + rerank | `core/rag/` (embeddings/ingestion/retrieval/pipeline/context) + `core/knowledge` graphe + backends vectoriels (Qdrant/PG/Chroma) | **OWUI = couverture prête à l'emploi** ; **ETHAN = pipeline plus modulaire mais moins complet** |
| **MCP** | `utils/mcp/client.py` (streamable_http, OAuth), ToolServers modal | `core/tools/servers.py` ToolServerManager (record store, lifecycle) | **OWUI = client MCP complet** ; **ETHAN = gestion d'enregistrement** |
| **Agents** | **Pas d'agents natifs** (functions/pipelines = tools) ; `automations` = règles déclenchées | `core/agents/` (AgentManager, états, exécutions), `core/modules/` plugin system | **ETHAN dominant** |
| **Permissions** | UserPermissions granulaires (workspace/sharing/chat/features/settings) | `Permission` enum (READ/WRITE/ADMIN/CHAT/AGENTS/MEMORY/PLUGINS/SETTINGS/FILES/EXECUTE) | **OWUI = granularité UX** ; **ETHAN = plus simple mais suffisante** |

### Recommandation capitale
Open WebUI **peut** devenir une *base UX inspirante* mais **ne peut pas** devenir la *base directe* (fork) sans **remettre en cause la source de vérité ETHAN Core**. Forker le backend OWUI injecterait de la logique métier **hors Core**, violant AGENTS.md. La voie correcte :

- **Fork du frontend OWUI** (SvelteKit ou migré Next.js) comme **référence UX** → composants/pages.
- **Backend OWUI remplacé** par **ETHAN Core/Runtime + interfaces/api** (API gateway thin).
- Chaque capacité OWUI est **réappariée** à une capacité Core existante ou à un nouveau module Core (RFC).
- Open WebUI reste **indépendant** pour la comparaison.

---

## 1. Cartographie des modules

### 1.1 Open WebUI — ce qui existe

| Couche | Éléments clés |
|---|---|
| **Backend routers** (`backend/open_webui/routers/`) | analytics, audio, auths, automations, calendar, channels, chats, configs, evaluations, files, folders, functions, images, knowledge, memories, models, notes, ollama, openai, pipelines, prompts, retrieval, scim, skills, tasks, terminals, tools, users, utils |
| **Models DB** (`models/`) | Chat/ChatMessage, Channel/Member/File/Webhook, File, Folder, Function, Knowledge/KnowledgeFile, Memory, Model, Note, Prompt(+history), Skill, Tool, User, Group, Automation/AutomationRun, Calendar/Event, Tag, AccessGrant, OAuthSession, SharedChat |
| **RAG** (`retrieval/`) | vector/dbs (chroma, pgvector, qdrant, milvus, weaviate, pinecone, opensearch, elasticsearch, oracle, s3vector, opengauss…), loaders (youtube, mistral, marker, mineru, tavily, external_web), web/ (20+ moteurs), models/ (colbert, external reranker), embeddings |
| **MCP** | `utils/mcp/client.py` — `MCPClient` (streamable_http, OAuth, list_tool_specs) |
| **Fonctions/Outils** | `functions.py`/`tools.py` (valves, is_global, is_active), builtin, tool servers |
| **Auth** (`utils/auth.py`) | JWT HttpOnly, OAuth (Google/Microsoft/GitHub/OIDC/Feishu), LDAP, API keys, SCIM |
| **Permissions** | `models/users.py` + `routers/users.py` → UserPermissions (Workspace/Sharing/AccessGrants/Chat/Features/Settings) |
| **Config** | `config.py` — `PersistentConfig` (DB-backed), environnements, banners, suggestions |
| **Frontend** | SvelteKit, stores/index.ts, routes/(app)/admin + workspace + home/c/notes/calendar/channels/automations/playground |
| **Streaming** | SSE via `/chat` (socket fallback) |
| **Déploiement** | docker-compose.yml, image `ghcr.io/open-webui/open-webui:main` |

### 1.2 ETHAN — ce qui existe

| Couche | Éléments clés |
|---|---|
| **Core modules** (`core/`) | agents, chat(**pipeline**), llm(**providers, model_store, router, selector, tracker**), knowledge(**graphe, collections**), rag(**embeddings, ingestion, pipeline, retrieval, context**), memory(**chromadb/qdrant/pg backends, consolidation, forgetting, recall**), facts, skills(**composer, store, executor**), tools(**registry, selector, executor, servers/MCP**), planner(**DAG, goal_manager, checkpoint**), missions, goals, auth(**users, groups, ldap, oauth, scim, api_keys**), scheduler(**automations, calendar**), state(**chats, files, notes, channels, record_store**), config(**loader, schema, service, store, secrets**), events, bus, capabilities, cognition, metacognition, safety(circuit_breaker), security, modules(plugins), registry, deployment |
| **Interfaces API** | `interfaces/api/routers/` — v1.py (agents/goals/missions/memory/skills/knowledge/flux/settings/chat/tools), domains.py (chats/files/users/groups/channels/notes), config.py, providers.py, models.py, state.py, realtime.py, message.py, capabilities.py, internal.py |
| **Interfaces WebUI** | Next.js — app/(dashboard)/{agents,assistant,documents,knowledge,logs,memory,missions,models,planner,plugins,prompts,providers,settings,skills,terminal,tools,goals} ; features (assistant/agents/flux/goals/knowledge/memory/missions/plugins/providers/settings/skills) ; lib/api/* (client, chat, models, providers, knowledge, skills, tools, memory, agents, missions, goals, plugins, prompts, flux, settings) |
| **SDK** | sdk/python + sdk/typescript (event, goals, agents, autonomy, metacognition, learning, module, memory) |
| **Streaming** | `core/events/` EventBus + SSE/WebSocket (`interfaces/api/main.py` realtime) |
| **Déploiement** | docker-compose.{yml,dev,prod,cluster,openwebui}.yml, deploy/Dockerfile.{api,kernel,ui,module} |

---

## 2. Tableau de migration détaillé par domaine

Chaque domaine répond aux **10 dimensions** demandées.

> **Légende migration** : `KEEP` (réutilisable tel quel), `ADAPT` (à recâpler sur Core), `REPLACE` (remplacé par Core), `DELETE` (supprimé), `MOVE-TO-CORE` (logique métier à déplacer vers Core avant d'être exposée).

---

### 2.1 Chat & streaming

| # | Dimension | Open WebUI | ETHAN | Comparaison / Action |
|---|---|---|---|---|
| 1 | **Ce qu'OWUI possède** | `routers/chats.py` SSE streaming, `Chat.svelte` UI multi-modèle live, paramètres système/température/top_p/modify en temps réel, system prompt, épinglage/archivage/tags/folders, partage, feedback, export, mode temporaire, continue/regenerate/rate/edit/call/multiple-models | — | Référence UX complète |
| 2 | **Ce qu'ETHAN possède** | — | `core/chat/pipeline.py` (ChatPipeline : validate modèle+ACL, charge arbre conversation, résout contexte skills/tools/RAG/memory, génère via ProviderManager, persiste, émet events), `core/state/chats.py` ChatStore (arbres branches messages) | Architecture propre mais UX minimaliste |
| 3 | **OWUI fait mieux** | Streaming SSE + UI ultra-réactive, contrôles live params, feedback inline, export, partage | ETHAN : pipeline orchestré + EventBus + ACL, mais UI moins riche | UI/UX OWUI = référence |
| 4 | **ETHAN fait mieux** | Logique métier backend couplée à la DB et à l'UI ; pas de séparation Runtime | Pipeline Core pur (pas d'API/HTTP), gestion d'arbre, branches, events persistés, circuit_breaker safety | Architecture Core = supérieure |
| 5 | **Réutilisable** | UX des contrôles live, design du Chat.svelte, suggestions, feedback inline, mode temporaire | ChatPipeline, ChatStore, EventBus, SSE realtime (`interfaces/api/main.py`) |
| 6 | **À adapter** | Frontend Chat.svelte → Next.js (features/assistant) ; SSE → `api/fetch` + `features/assistant/services/chat.service.ts` | ChatPipeline persisté dans le store, branching, events |
| 7 | **À remplacer** | Logique stream/validate dans routers/chats.py → migrer vers ChatPipeline + `/v1/chat` ETHAN | — |
| 8 | **À supprimer** | Duplication éventuelle de `chats.py` si ETHAN expose `/v1/chat` | Nettoyer backend OWUI forké |
| 9 | **API nécessaires** | `/v1/chat` (POST message, SSE stream), `/v1/chats/{id}` (arbre), `/v1/chats/{id}/branch`, `/v1/chats/{id}/share`, `/v1/chat/title/suggestions` | GET/POST `/v1/chat`, GET `/v1/chats/{id}` |
| 10 | **Données ETHAN** | chat_id, messages (role, content, parent_id, metadata provider/model/skills/tools/knowledge/files), title, archived, pinned, share_id, folder_id, feedback, summary | ChatStore + RecordStore core |

---

### 2.2 Conversations (threads, branches, partage, dossiers)

| # | Dimension | Open WebUI | ETHAN | Action |
|---|---|---|---|---|
| 1 | **OWUI possède** | `chats` table (title, chat JSON, share_id, archived, pinned, meta, folder_id, tasks, summary), `chat_messages` table, tags, folders, shared_chats, access_grants, import/export, clone | — | |
| 2 | **ETHAN possède** | — | `core/state/chats.py` ChatStore (id,title,user_id,folder_id,archived,pinned,share_id,messages,metadata,created/updated_at), `core/state/record_store.py`, messages arborés (`add_message parent_id`) | |
| 3 | **OWUI fait mieux** | Partage public + access_grants granulaire, tags/folders, import/export, clone, statistiques d'usage | ETHAN : modèle arborescent (branches) | |
| 4 | **ETHAN fait mieux** | Chat JSON monolithique | Arbre de messages native (branches), EventBus `chat.created` | |
| 5 | **Réutilisable** | UX tags/folders, partage, import/export | ChatStore, branching, record_store | |
| 6 | **À adapter** | Import/export → adapter au format ETHAN ; tags/folders UI → Next.js | Ajouter tags dans ChatStore, export API | |
| 7 | **À remplacer** | Persistance OWUI chats → migrer vers ChatStore | — | |
| 8 | **À supprimer** | `shared_chats` table si redondant avec share_id CORE | | |
| 9 | **API nécessaires** | `/v1/chats` (list, new), `/v1/chats/{id}` (get/update), `/v1/chats/{id}/archive|pin|clone|share`, `/v1/chats/{id}/tags`, `/v1/chats/search` | déjà dans v1.py + domains.py | |
| 10 | **Données ETHAN** | conversations, messages, branches, tags, folders, share_id, access_grants | ChatStore + RecordStore |

---

### 2.3 Models

| # | Dimension | Open WebUI | ETHAN | Action |
|---|---|---|---|---|
| 1 | **OWUI possède** | `models` table (base/format/human_name/params/eval), `routers/models.py` (list/base/create/export/import/sync/model/toggle/update/access/delete), connexions providers, profils évaluation, suggestions | — | |
| 2 | **ETHAN possède** | — | `core/llm/model_store.py` (ModelStore, custom cards persistants), `core/llm/manager.py`, `core/llm/registry.py`, `core/llm/types.py`, `interfaces/api/routers/models.py` + `providers.py` | |
| 3 | **OWUI fait mieux** | UI connexions/providers en 1 page, sync auto des modèles, export/import, profils évaluation, suggestions | ETHAN : ModelStore persistant | |
| 4 | **ETHAN fait mieux** | Stockage des modèles dans DB locale | Architecture provider/registry/selector modulaire et testable | |
| 5 | **Réutilisable** | UX liste modèles + toggle + accès ; connexions UI ; suggestion engine | ModelStore, registry, selector | |
| 6 | **À adapter** | UI → pages models/providers Next.js ; fetch `/models` + `/providers` API ETHAN | aligner types `ModelInfo`/`ModelInfo` avec `@/types/index` | |
| 7 | **À remplacer** | Logique models.py OWUI → `core/llm/model_store.py` + router | — | |
| 8 | **À supprimer** | `models.py` DB schema OWUI si remplacé par Core | | |
| 9 | **API nécessaires** | `/v1/models` (list), `/v1/models/{id}` (get/toggle/update), `/v1/models/sync` | `interfaces/api/routers/models.py` | |
| 10 | **Données ETHAN** | model_id, provider_id, name, description, base/format, params, access (public/user/group), pin, meta | ModelStore |

---

### 2.4 Providers

| # | Dimension | Open WebUI | ETHAN | Action |
|---|---|---|---|---|
| 1 | **OWUI possède** | `configs.py` (connections : Ollama/OpenAI/OpenRouter/Anthropic/Google/Azure/vLLM/LMStudio/llama.cpp + OpenRouter/OpenAI-Compatible), `router/ollama.py`+`openai.py` proxies, clés API persistantes (PersistentConfig), valvages | — | |
| 2 | **ETHAN possède** | — | `core/llm/provider_factory.py`, `provider_manager.py`, `providers/{base,anthropic,gemini,llamacpp,lmstudio,ollama,openai,openai_compatible,vllm}.py`, `routing.yaml`, `selector.py`, `tracker.py`, `store.py` | |
| 3 | **OWUI fait mieux** | UI "Add Connection" modale, OpenRouter + OpenAI-Compatible UI riche, proxy /ollama /openai transparents | `routing.yaml` + selector (plus fin) | |
| 4 | **ETHAN fait mieux** | Secrets dans PersistentConfig (risque) ; couplings | `core/config/secrets.py` + `core/config/loader.py` (secrets isolés), providers homogènes | |
| 5 | **Réutilisable** | UX AddConnectionModal, liste des providers + statuts | ProviderManager, factory, providers | |
| 6 | **À adapter** | UI providers → pages providers Next.js ; fetch `/v1/providers` | adapter `ModelInfo.provider` field | |
| 7 | **À remplacer** | proxy /ollama, /openai routers → delegués à ProviderManager Core | | |
| 8 | **À supprimer** | routers/ollama.py, routers/openai.py (proxy) si Core expose providers | | |
| 9 | **API nécessaires** | `/v1/providers` (list), `/v1/providers/default`, `/v1/providers/{id}` | router models.py+providers.py | |
| 10 | **Données ETHAN** | provider_id, type, name, env vars/clés, base_url, default models, enabled, status, meta | core/llm + config/secrets |

---

### 2.5 RAG (ingestion, embeddings, retrieval)

| # | Dimension | Open Web UI | ETHAN | Action |
|---|---|---|---|---|
| 1 | **OWUI possède** | `retrieval/` : 15 vectordbs (chroma, pgvector, qdrant, milvus, weaviate, pinecone, opensearch, elasticsearch, oracle, s3vector, opengauss…), loaders (youtube, mistral, marker, mineru, external_web, tavily), 20+ moteurs recherche web, rerankers (colbert, external), `/retrieval/process/file|text|youtube|web|web/search`, `/retrieval/query/doc|collection`, config embeddings + top_k + top_k_fetch + reranker | — | |
| 2 | **ETHAN possède** | — | `core/rag/{embeddings,ingestion,pipeline,retrieval,context}.py` (DocumentChunk/IngestedDocument), `core/knowledge/{manager,collections,types}` (graphe KnowledgeNode/Connection), backends vectorels Qdrant/PG/Chroma (core/memory) | |
| 3 | **OWUI fait mieux** | Couverture "prête à l'emploi" : 15 DBs + 20 moteurs web + rerankers + loaders documents | ETHAN : ingestion modulaire + graphe connaissance | |
| 4 | **ETHAN fait mieux** | RAG tightly-couplé aux routers OWUI | Pipeline RAG découpé ingestion↔retrieval↔context ↔ embeddings, graphe de connaissance | |
| 5 | **Réutilisable** | Résoudre la *diversité* des backends → ETHAN gagne ; UX de l'admin RAG | core/rag pipeline, embeddings, core/knowledge graphe | |
| 6 | **À adapter** | Config RAG UI → fetch `/v1/knowledge/{id}/collections` + retrieval params ; reranker selection UI | connecter 15 backends via un adapter factory Core (RFC) | |
| 7 | **À remplacer** | Logique retrieval.py OWUI → RAGPipeline Core | | |
| 8 | **À supprimer** | duplication `retrieval/` si déléguée à Core; garder uniquement *référence backend* OWUI indépendant | | |
| 9 | **API nécessaires** | `/v1/knowledge/{id}/ingest`, `/v1/knowledge/{id}/query`, `/v1/retrieval/process`, `/v1/retrieval/embeddings`, `/v1/retrieval/search/web` | core/rag + core/knowledge + interfaces/api/routers/knowledge.py | |
| 10 | **Données ETHAN** | collection_id, document_id, chunks(embeddings), sources (url/file/youtube/web), reranker top_k | core/rag Ingestion + core/knowledge collection manager |

---

### 2.6 Knowledge (collections/documents)

| # | Dimension | Open Web UI | ETHAN | Action |
|---|---|---|---|---|
| 1 | **OWUI possède** | `knowledge.py` + `KnowledgeFiles` : CRUD collection (reindex, métadonnées, accès), add/remove/update file batch, export, search files, reset | — | |
| 2 | **ETHAN possède** | — | `core/knowledge/{manager,collections,types}` : KnowledgeManager, KnowledgeCollectionManager, KnowledgeNode/Connection (graphe concept/fact/rule/entity/source/document) | |
| 3 | **OWUI fait mieux** | UI collection + files + accès + réindexation simple | ETHAN : graphe relationnel de connaissance | |
| 4 | **ETHAN fait mieux** | Connaissance "documents vectoriels" uniquement | Graphe sémantique (connexions, strength, types), collection manager | |
| 5 | **Réutilisable** | UX collection list + files + reindex ; search | KnowledgeCollectionManager, graphe KnowledgeNode | |
| 6 | **À adapter** | UI knowledge → fetch `/v1/knowledge` ; fusionner collection RAG + graphe → adapter UI pour expose le graphe | unifié Collection = documents + graphe | |
| 7 | **À remplacer** | `knowledge.py` OWUI → KnowledgeManager Core | | |
| 8 | **À supprimer** | `KnowledgeFiles` redondant si Core expose knowledge | | |
| 9 | **API nécessaires** | `/v1/knowledge` (list), `/v1/knowledge/{id}` (get/update), `/v1/knowledge/{id}/files`, `/v1/knowledge/{id}/reindex`, `/v1/knowledge/{id}/graph` | interfaces/api/routers/knowledge.py | |
| 10 | **Données ETHAN** | collection_id, name, description, files[], status, access, embeddings config, graph nodes/connections | core/knowledge |

---

### 2.7 Files (upload, stockage, retrieval)

| # | Dimension | Open Web UI | ETHAN | Action |
|---|---|---|---|---|
| 1 | **OWUI possède** | `files.py` : upload, storage local/S3/GCS/Azure, traitement (process status), content search/retrieve (content/html/{name}), delete all | — | |
| 2 | **ETHAN possède** | — | `core/state/files.py` FileStore (filename, content_type, size, user_id, storage_path, metadata) | |
| 3 | **OWUI fait mieux** | Storage providers multiples (S3/GCS/Azure), extraction contenu, search par contenu, preview HTML | ETHAN : métadonnées FileStore | |
| 4 | **ETHAN fait mieux** | Storage couplé au storage_provider OWUI | FileStore abstrait, EventBus `file.registered` | |
| 5 | **Réutilisable** | Storage provider abstraction (local/S3/GCS/Azure config) ; UX upload/preview | FileStore, record_store | |
| 6 | **À adapter** | fetch `/v1/files` + `/v1/knowledge/{id}/files` ; storage provider config → ETHAN secrets (RFC) | connecter STORAGE_PROVIDER OWUI → core/state/files + core/config/secrets | |
| 7 | **À remplacer** | logique storage OWUI → FileStore Core | | |
| 8 | **À supprimer** | `storage/provider.py` OWUI si Core expose storage | | |
| 9 | **API nécessaires** | `/v1/files` (upload/list), `/v1/files/{id}` (get/content), `/v1/files/{id}/process/status`, `/v1/files/{id} delete` | interfaces/api/routers/files.py ? (ou domains) | |
| 10 | **Données ETHAN** | file_id, filename, content_type, size, user_id, storage_path, metadata, process status, content | core/state/files |

---

### 2.8 MCP (serveurs d'outils)

| # | Dimension | Open Web UI | ETHAN | Action |
|---|---|---|---|---|
| 1 | **OWUI possède** | `utils/mcp/client.py` : MCPClient (streamable_http, OAuthClientProvider, TokenStorage, list_tool_specs, `connect`), config ToolServers dans settings, `configs.py` `/terminal_servers` `/tool_servers` | — | |
| 2 | **ETHAN possède** | — | `core/tools/servers.py` ToolServerManager (register name/url/auth_type/auth_config/enabled/status/lifecycle events) | |
| 3 | **OWUI fait mieux** | Client MCP **complet** (auth OAuth, transport, tool introspection) | ETHAN : enregistrement/config only (pas de client MCP d'exécution) | |
| 4 | **ETHAN fait mieux** | Client MCP dans utils (techniquement) | Gestion d'enregistrement + lifecycle + events persistés | |
| 5 | **Réutilisable** | Client MCP (`utils/mcp/client.py`) **backend Core** — réintégrer dans core/tools | ToolServerManager Core | |
| 6 | **À adapter** | fetch `/v1/tools/servers` ; ToolServersModal UI → Next.js (features/tools) | connecter ToolServerManager au ToolManager pour exécution MCP | |
| 7 | **À remplacer** | UI ToolServersModal → `core/tools/server.py` | | |
| 8 | **À supprimer** | client MCP exposé côté OWUI frontend | | |
| 9 | **API nécessaires** | `/v1/tools/servers` (list/create), `/v1/tools/servers/{id}/connect`, `/v1/tools/servers/{id}/tools` (list_tools) | core/tools/servers.py + interfaces/api/routers/tools.py | |
| 10 | **Données ETHAN** | server_id, name, url, auth_type, auth_config, enabled, status, last_connected_at, tools[] | core/tools/servers (ToolServerManager) |

---

### 2.9 Tools / fonctions appelables

| # | Dimension | Open Web UI | ETHAN | Action |
|---|---|---|---|---|
| 1 | **OWUI possède** | `tools.py` + `functions.py` : tools/fonctions custom avec **valves** (params utilisateur/dev), is_active, is_global, access; builtin tools, load_url, export/import; `tools/builtin.py` outils natifs | — | |
| 2 | **ETHAN possède** | — | `core/tools/{registry,selector,executor,monitor,functions,servers,types,tracker}` : Tool, ToolContext, ToolResult, ToolManager, outils natifs | |
| 3 | **OWUI fait mieux** | Système **valves** (config utilisateur vs dev) riche, load_url, export/import, builtin outils natifs | ETHAN : Tool + ToolContext/ToolResult typé, monitor, sélection par capability | |
| 4 | **ETHAN fait mieux** | Outils tightly couplés aux routers OWUI | ToolManager (registry→selector→executor→monitor), capability-based selection | |
| 5 | **Réutilisable** | UX valves modal, load_url, export/import, builtin ; outils natifs | ToolManager, Tool/ToolContext/ToolResult, builtin | |
| 6 | **À adapter** | UI tools → fetch `/v1/tools` ; valves UI → adapter au `parameters`/config ETHAN | unifié ToolRegistry + valves → Tool.parameters | |
| 7 | **À remplacer** | `functions.py` OWUI (concept duplicate de tools) → unifié ToolManager Core | fusionner functions+pipelines → tools Core | |
| 8 | **À supprimer** | `functions.py` routers si remplacé par Core tools ; pipelines (déjà → pipelines = custom) | | |
| 9 | **API nécessaires** | `/v1/tools` (list), `/v1/tools/{id}` (get/update), `/v1/tools/{id}/valves`, `/v1/tools/load/url`, `/v1/tools/export/import` | core/tools + interfaces/api/routers/tools.py | |
| 10 | **Données ETHAN** | tool_id, name, description, type (builtin/custom/mcp), parameters/schema, valves(user/dev), is_active, is_global, access | core/tools |

---

### 2.10 Memory (facts, rappel contextuel)

| # | Dimension | Open Web UI | ETHAN | Action |
|---|---|---|---|---|
| 1 | **OWUI possède** | `memories.py` : memories table (id, user_id, content, created/updated_at), Qdrant/Chroma vector, add/query/reset/update/delete, `/memories/{id}/update`, reset user, query via router | — | |
| 2 | **ETHAN possède** | — | `core/memory/` (manager, chromadb/qdrant/pg backends, vector_store, consolidation, forgetting, recall, user_model), `core/facts/` (ingest, retrieval, store, types) — facts memory + events, CoreWebUIStore intègre facts | |
| 3 | **OWUI fait mieux** | UX simple add/query/reset, intégration vectorielle prête | ETHAN : gestion avancée du cycle de vie (consolidation, forgetting, recall, compression) | |
| 4 | **ETHAN fait mieux** | Souvenirs "contenu libre" seulement | Système facts (ingest/retrieval store) + memory lifecycle + compression + forgetting politique | |
| 5 | **Réutilisable** | UX memory page (query/update/delete) ; backend vector | core/memory manager, core/facts | |
| 6 | **À adapter** | UI memory → fetch `/v1/memory/facts` + `/v1/memory/events` ; unifier "memories" OWUI ↔ "facts" ETHAN | adapter MemoryModel → core/facts Fact | |
| 7 | **À remplacer** | `memories.py` OWUI → core/facts + core/memory | | |
| 8 | **À supprimer** | `memories.py` DB si Core expose | | |
| 9 | **API nécessaires** | `/v1/memory/facts` (list/search/get/create/delete), `/v1/memory/events`, `/v1/memory/ingest`, `/v1/memory/{id}/update` | v1.py déjà défini + core/facts | |
| 10 | **Données ETHAN** | fact_id, content, user_id, embedding, source, created/updated_at, scope, type | core/facts + core/memory |

---

### 2.11 Agents

| # | Dimension | Open Web UI | ETHAN | Action |
|---|---|---|---|---|
| 1 | **OWUI possède** | **Pas d'agents natifs**. `functions`/`pipelines` (serverless) + `automations` (rules/triggers/actions avec terminals) jouent le rôle autonome | — | |
| 2 | **ETHAN possède** | — | `core/agents/{base,manager,types}` : AgentManager, Agent (id/name/description/capabilities/status/model/provider/memory_scope/skill_ids), AgentExecution, états IDLE/RUNNING/PAUSED/ERROR/STOPPED ; `core/modules/` plugin system (capability, memory, autonomy, executive, planner) ; `core/autonomy/{engine,controller,curiosity,healing}` | |
| 3 | **OWUI fait mieux** | UI automations/rules (triggers/actions calendaires) | — | |
| 4 | **ETHAN fait mieux** | Aucun agent autonome | AgentManager + module system + autonomie (curiosity, healing, scheduler) | **ETHAN dominant** |
| 5 | **Réutilisable** | UI automations (trigger/action composer) | AgentManager, Agent types, core/modules | |
| 6 | **À adapter** | UI agents → fetch `/v1/agents` ; automations UI → adapter à `core/scheduler/automations` + `core/autonomy` | créer agent endpoints si besoin | |
| 7 | **À remplacer** | `automations.py` OWUI → `core/scheduler/automations` + `core/autonomy` Core ; pipelines → Agents Core | | |
| 8 | **À supprimer** | duplication `automations` OWUI | | |
| 9 | **API nécessaires** | `/v1/agents` (list/create/get/update/delete), `/v1/agents/{id}/execute`, `/v1/agents/{id}/executions`, `/v1/agents/{id}/skills` | v1.py déjà défini (agents) ; core/modules | |
| 10 | **Données ETHAN** | agent_id, name, description, capabilities, status, model, provider, memory_scope, skill_ids, metadata | core/agents + core/modules |

---

### 2.12 Settings (config globale & secrets)

| # | Dimension | Open Web UI | ETHAN | Action |
|---|---|---|---|---|
| 1 | **OWUI possède** | `config.py` : `PersistentConfig` (DB-backed), `DEFAULT_CONFIG`, env vars (OLLAMA_BASE_URL, ENABLE_OAUTH_SIGNUP, JWT_EXPIRES_IN, STORAGE_PROVIDER…), `routers/configs.py` (import/export, connections, tool/terminal servers, code_execution, models defaults, suggestions, banners), tabs UI (General/Interface/Audio/Images/Retrieval/Connections/Functions/Models/CodeExecution/UI/Users/Pipelines) | — | |
| 2 | **ETHAN possède** | — | `core/config/{loader,schema,service,store,secrets}` + `core/config/bootstrap` ; secrets isolés (`core/config/secrets.py`) ; `interfaces/api/routers/config.py` | |
| 3 | **OWUI fait mieux** | UI settings riche + import/export + PersistentConfig | ETHAN : secrets isolés (bonne pratique) | |
| 4 | **ETHAN fait mieux** | Secrets PersistantsConfig (violation `.clinerules/secret.md`) ; config monolithique | Architecture secrets isolés + config schema validée + bootstrap | |
| 5 | **Réutilisable** | UX settings tabbed UI, import/export | core/config service + secrets | |
| 6 | **À adapter** | UI settings → fetch `/v1/settings` (GET/PUT) + `/v1/config/*` ; secrets → ETHAN secret manager | adapter PersistentConfig OWUI → CoreWebUIStore | |
| 7 | **À remplacer** | `config.py` OWUI → core/config | | |
| 8 | **À supprimer** | config OWUI si Core expose | | |
| 9 | **API nécessaires** | `/v1/settings` (GET/PUT), `/v1/config/import`, `/v1/config/export`, `/v1/config/connections`, `/v1/config/tool_servers`, `/v1/config/terminal_servers`, `/v1/config/code_execution`, `/v1/config/models/defaults` | v1.py `/v1/settings` + routers/config.py | |
| 10 | **Données ETHAN** | system config (provider defaults, retrieval params, UI prefs, banners, secrets) | core/config + CoreWebUIStore |

---

### 2.13 Users (gestion des comptes)

| # | Dimension | Open Web UI | ETHAN | Action |
|---|---|---|---|---|
| 1 | **OWUI possède** | `users.py` : User(DB id, email, name, role admin/user/pending, last_active_at, profile), `routers/users.py` (list/all/search/groups/permissions, default permissions, settings, status), groups, API keys | — | |
| 2 | **ETHAN possède** | — | `core/auth/users.py` UserManager (id, username, email, role, password_hash, active, profile, metadata) ; `core/auth/groups.py` GroupManager | |
| 3 | **OWUI fait mieux** | UI users admin, permissions granulaires, status last_active | ETHAN : UserManager + GroupManager | |
| 4 | **ETHAN fait mieux** | User monolithique dans DB | UserManager événementiel (USER_CREATED event) | |
| 5 | **Réutilisable** | UX users admin, permissions page | UserManager, GroupManager | |
| 6 | **À adapter** | UI users → fetch `/v1/users` ; default permissions → map to ETHAN Permission | aligner role/schema | |
| 7 | **À remplacer** | `users.py` OWUI → UserManager Core | | |
| 8 | **À supprimer** | duplication users OWUI | | |
| 9 | **API nécessaires** | `/v1/users` (list), `/v1/users/all`, `/v1/users/search`, `/v1/users/groups`, `/v1/users/{id}` (get/update/delete), `/v1/users/default/permissions` | interfaces/api/routers/users (ou domains) | |
| 10 | **Données ETHAN** | user_id, username, email, name, role, active, last_active_at, profile, metadata, password_hash | core/auth/users + core/state/record_store |

---

### 2.14 Authentication

| # | Dimension | Open Web UI | ETHAN | Action |
|---|---|---|---|---|
| 1 | **OWUI possède** | OAuth (Google/Microsoft/GitHub/OIDC/Feishu), LDAP, SCIM, JWT HttpOnly cookie (`utils/auth.py`), API keys (PersistentConfig), SSO, `routers/auths.py` (signin/signup/update/password/ldap/oauth/exchange), `utils/oauth.py` | — | |
| 2 | **ETHAN possède** | — | `core/auth/{api_keys,groups,ldap,oauth,scim,users,permissions}` ; `interfaces/api/auth.py` ; JWT HttpOnly cookie (`core/api/...` ou via oauth.py) ; `oauth.py` | |
| 3 | **OWUI fait mieux** | UX OAuth + LDAP config + scim provisioning UI complète, tokens | ETHAN : JWT HttpOnly, API keys isolés | |
| 4 | **ETHAN fait mieux** | OAuth tightly-couplé auth.py ; config LDAP dans PersistentConfig | Auth découpé (oauth/ldap/scim/api_keys), permissions centralisées | |
| 5 | **Réutilisable** | OAuth flow handlers (auth providers) ; UX signin/signup | core/auth/oauth.py, core/auth/ldap.py, core/auth/scim.py | |
| 6 | **À adapter** | JWT cookie + HttpOnly → ETHAN auth ; OAuth providers config → core/config/secrets | unifier session/token storage | |
| 7 | **À remplacer** | `utils/auth.py`, `utils/oauth.py` OWUI → core/auth/* Core | | |
| 8 | **À supprimer** | auth.py/oauth.py OWUI si Core expose | | |
| 9 | **API nécessaires** | `/auth/signin`, `/auth/signup`, `/auth/logout`, `/auth/update/profile|password|timezone`, `/auth/oauth/{provider}`, `/auth/oauth/{provider}/token/exchange`, `/auth/api_key` (CRUD), `/auth/admin/config`, `/auth/admin/config/ldap/*` | interfaces/api/auth.py | |
| 10 | **Données ETHAN** | user_id, email, password_hash, JWT token/id_token, OAuth tokens, OAuth sessions, refresh tokens, API keys (hashed), LDAP config | core/auth/* + core/config/secrets |

---

### 2.15 Permissions (contrôle d'accès)

| # | Dimension | Open Web UI | ETHAN | Action |
|---|---|---|---|---|
| 1 | **OWUI possède** | `UserPermissions` : Workspace (models/knowledge/prompts/tools/skills + import/export), Sharing (public_*), AccessGrants, Chat (controls/valves/system_prompt/params/file_upload/web_upload/delete/share/export/stt/tts/call/multiple_models/temporary…), Features (api_keys/notes/channels/folders/direct_tool_servers/web_search/image_generation/code_interpreter/memories/automations), Settings (interface) ; rôles admin/user/pending ; groupes ; access_grants table | — | |
| 2 | **ETHAN possède** | — | `core/auth/__init__.py` Permission enum (READ/WRITE/ADMIN/CHAT/AGENTS/MEMORY/PLUGINS/SETTINGS/FILES/EXECUTE) ; `core/auth/groups.py` ; `interfaces/api/auth.py` require_permission | |
| 3 | **OWUI fait mieux** | Granularité UX par feature (Workspace/Chat/Features) | ETHAN : permissions par endpoint | |
| 4 | **ETHAN fait mieux** | Permissions dans DB PersistentConfig | Permission enum centralisé, require_permission par endpoint | |
| 5 | **Réutilisable** | UX permissions page (workspace/sharing/chat/features/settings toggles) | Permission enum | |
| 6 | **À adapter** | OWUI UserPermissions → ETHAN Permission (mapping workspace→READ/WRITE, chat→CHAT, etc.) | enrichir Permission si besoin (RAG, KNOWLEDGE) | |
| 7 | **À remplacer** | `UserPermissions` OWUI → Permission enum Core | | |
| 8 | **À supprimer** | duplication permissions OWUI | | |
| 9 | **API nécessaires** | `/v1/users/permissions`, `/v1/users/default/permissions`, `/v1/access_grants` | interfaces/api/auth.py + core/auth | |
| 10 | **Données ETHAN** | user_id, role, workspace/sharing/chat/features/settings permission flags, groups, access_grants (resource→user/group partagé) | core/auth/groups + core/state/record_store |

---

## 3. Tableau récapitulatif de migration (vue d'ensemble)

| Domaine | Module OWUI (référence) | Module ETHAN Core | Verbe de migration | Priorité |
|---|---|---|---|---|
| Chat | routers/chats.py, Chat.svelte | core/chat/pipeline.py, core/state/chats.py | ADAPT UI / REPLACE backend | P0 |
| Conversations | chats/chat_messages/tags/folders | core/state/chats.py (ChatStore) | ADAPT (branches/tags/folders) | P1 |
| Models | models.py | core/llm/model_store.py | ADAPT (keep ModelStore) | P1 |
| Providers | configs.py, ollama/openai router | core/llm/{provider_manager,providers} | REPLACE (secrets→core/config) | P1 |
| RAG | retrieval/* (15 DB + 20 web) | core/rag/* + core/knowledge | ADAPT (unify) ; MOVE vector backends to Core RPC | P1-P2 |
| Knowledge | knowledge.py | core/knowledge/{manager,collections,types} | ADAPT (graphe + collection) | P2 |
| Files | files.py | core/state/files.py | ADAPT | P1 |
| MCP | utils/mcp/client.py | core/tools/servers.py | MOVE client→Core, ADAPT UI | P1 |
| Tools | tools.py / functions.py | core/tools/{manager,registry,executor} | REPLACE (fusion functions→tools) | P1 |
| Memory | memories.py | core/memory + core/facts | REPLACE (unify memories↔facts) | P2 |
| Agents | (absent — automations) | core/agents + core/modules + core/autonomy | REPLACE automations→agents | P2 |
| Settings | config.py PersistentConfig | core/config/{loader,schema,service,secrets} | REPLACE (secrets isolés) | P0-P1 |
| Users | users.py | core/auth/users.py UserManager | REPLACE | P0 |
| Auth | auths.py, oauth.py | core/auth/{oauth,ldap,scim,api_keys} | REPLACE | P0 |
| Permissions | UserPermissions | core/auth Permission enum | ADAPT (mapping) | P1 |

---

## 4. Points critiques de l'architecture (décisions)

1. **Backend OWUI = référence, non base directe.** Fork du *frontend* OWUI (UX) mais le *backend* OWUI est remplacé par ETHAN Core. Forker le backend OWUI injecterait la logique métier hors Core → violation AGENTS.md.
2. **Secrets** : Open WebUI stocke secrets dans `PersistentConfig` (DB) — violation `.clinerules/secret.md`. ETHAN isole via `core/config/secrets.py` (env/Vault). Migration = migrer secrets vers secret manager ETHAN.
3. **MCP client** : le client MCP OWUI (`utils/mcp/client.py`) est la partie la plus complète. **Rapporter dans `core/tools`** (MOVE-TO-CORE) avant d'être exposée par `core/tools/servers.py` + API.
4. **Vector backends** : OWUI a 15 backends RAG. ETHAN n'a que Qdrant/PG/Chroma (via core/memory). Créer un `core/rag/vector/factory.py` pour absorber la diversité OWUI (surcouche Core, OWUI reste référence indépendant).
5. **Unification Tools/Functions** : OWUI a un doublon `functions.py` ↔ `tools.py`. Migration = réunifier vers `core/tools` ETHAN, supprimer `functions.py`.
6. **Memory** : OWUI `memories` ↔ ETHAN `facts`+`memory`. Unifier sous `core/facts` + `core/memory`.
7. **Agents** : OWUI n'a pas d'agents natifs. ETHAN `core/agents` + `core/modules` + `core/autonomy` domine → migrer `automations` OWUI vers Core.
8. **Permissions** : OWUI `UserPermissions` (15 dimensions UX) ↔ ETHAN `Permission` enum (10). Mapping OWUI→ETHAN ; garder granularité UX côté WebUI (thin), source de vérité Core.

---

## 5. Feuille de route de migration (par phase)

| Phase | Domaines | Actions clés | Livrable |
|---|---|---|---|
| **P0** | Settings, Users, Auth, Chat (core existant) | Migrer PersistentConfig → core/config/secrets ; UserManager ; JWT HttpOnly ; ChatPipeline + SSE realtime | WebUI login + chat fonctionnel |
| **P1** | Models, Providers, Files, Tools, MCP, Permissions | ModelStore ; providers Core ; FileStore ; ToolManager (fusion functions) ; MCP client→Core ; UI modulaire | WebUI Models/Providers/Tools/MCP pleinement Core-backed |
| **P2** | RAG, Knowledge, Memory, Agents, Connaissances | core/rag vector factory (15 backends) ; Knowledge graphe+collection ; Memory unify facts+memory ; automations→agents Core | WebUI RAG/Knowledge/Memory/Agents |
| **P3** | Audio, Images, Channels, Notes, Calendar, Automations (UI) | Délégués Core ; UI thin | WebUI complète parity OWUI |

---

## 6. Conclusion — Open WebUI peut-il devenir la base directe ?

**Oui comme référence UX/fonctionnelle, NON comme base code directe (backend).**

- Open WebUI possède une **UX mature et complète** (streaming, contrôles live, gestion RAG, connexions providers, permissions granulaires) — une **mine d'or UX** pour le fork frontend.
- Open WebUI possède une **logique métier monolithique** (routers + utils + config) qui, si forkée, **violerait la source de vérité ETHAN Core** définie par AGENTS.md.
- ETHAN Core possède **déjà un socle équivalent ou supérieur** (ChatPipeline, LLM providers, Memory lifecycle, Knowledge graphe, Agents, ToolManager, Auth).
- **Stratégie gagnante** : `fork frontend OWUI (UX) → ETHAN WebUI (Next.js thin) → ETHAN API (thin gateway) → ETHAN Core/Runtime`. Le backend OWUI reste **indépendant** comme référence ; chaque capability est réappariée à un module Core (tableau §3).

> **Recommandation finale** : Ne pas fork le *backend* OWUI. Forker le *frontend* comme inspiration UX, puis recâpler chaque capacité à `core/*`. Open WebUI continue de tourner comme banc d'essai comparatif.
