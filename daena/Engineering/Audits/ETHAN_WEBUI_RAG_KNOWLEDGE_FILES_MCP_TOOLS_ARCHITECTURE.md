# Architecture cible — RAG, Knowledge, Files, MCP, Tools (inspiré Open WebUI)

> **Principe** : Open WebUI = **référence fonctionnelle/UX**. ETHAN Core = **source de vérité unique** (logique métier, persistence, configuration). Le futur WebUI est un *thin client* qui configure via APIs ETHAN — **aucune** registry/RAG/MCP/Memory/Agent/tool local dans la UI. Aucune source de vérité ne doit être dupliquée.
> **Ne modifie aucun fichier.** Nouveau fichier documentaire `docs/plans/`.

---

## Schéma global cible

```
                   ┌──────────────────────────────────────────────────┐
                   │  ETHAN Core / Runtime                             │
                   │  ┌──────────────┐ ┌─────────────┐ ┌────────────┐│
                   │  │ core/llm     │ │ core/rag    │ │ core/      ││
                   │  │ (providers,  │ │ embeddings/ │ │ knowledge/ ││
                   │  │  model_store)│ │ ingestion/  │ │  graphs    ││
                   │  └──────┬───────┘ └─────┬───────┘ └─────┬──────┘│
                   │         │               │               │       │
                   │  ┌──────┴───────┐ ┌─────┴────────┐ ┌────┴──────┐  │
                   │  │ core/tools   │ │ core/facts   │ │ core/     │  │
                   │  │ (registry,   │ │ memory/      │ │ state/    │  │
                   │  │  servers     │ │  vector      │ │ files     │  │
                   │  │  MCP client) │ │  store)      │ │ channels) │  │
                   │  └──────┬───────┘ └─────┬───────┘ └────┬──────┘  │
                   └──┬──────┴───────────────┴──────────────┴───────┘
                      │                REST + SSE                          │
               ┌──────┴──────────────┐─────────────────────────┐
               │ interfaces/api      │  interfaces/cli / desktop│
               │ routers: models,    │  (Atreus consommateur)  │
               │ providers, knowledge,│                         │
               │ files, tools, mcp,  │                         │
               │ retrieval,          │                         │
               └──────┬──────────────┘                         │
                      │ REST + SSE/WebSocket                     │
              ┌───────┴────────────────────────────────────────┐│
              │  ETHAN WebUI (thin client — fork UX Open WebUI)  ││
              │  features/{knowledge,files,tools,providers,...} ││
              │  lib/api/*.ts (clients modulaires + React Query)││
              └──────────────────────────────────────────────────┘
          ┌──────────┬───────────┬──────────┬────────────┐
          ▼          ▼           ▼          ▼            ▼
      WebUI        CLI        Desktop      Mobile      Atreus
    (interface)  (interface)  (interface)  (interface)  (Core consumer)
```

---

## 0. Principe fondamental — Configuration unifiée multi-interfaces

> **Exigence** : un utilisateur doit pouvoir configurer RAG, Knowledge, Files, MCP et Tools depuis **WebUI, CLI ou Desktop** sans créer plusieurs systèmes différents. La configuration appartient à **ETHAN** (Core), jamais à une interface.

### 0.1 Une seule source de vérité de configuration

```
        ┌─────────────────────────────────────────────────────────┐
        │  ETHAN Core — Configuration UNIQUE                      │
        │  core/config/ (schéma + loader + service + store)       │
        │  core/config/secrets.py (clés isolées, jamais en DB)    │
        │  core/state/record_store.py (PG + Redis)                │
        └───────────────┬─────────────────────────────────────────┘
                        │  REST (interfaces/api) + CLI direct
        ┌───────────────┼───────────────────┬─────────────────────┐
        ▼               ▼                   ▼                     ▼
     WebUI           CLI                Desktop               Atreus
   (formulaires)   (ethan config)      (panneaux)          (lecture seule)
```

- **Une seule API de configuration** : `/v1/config/{domain}` (GET/PUT) — pas d'endpoint par interface.
- **Un seul schéma** : `core/config/schema.py` définit les clés RAG/Knowledge/Files/MCP/Tools.
- **Un seul store** : `core/state/record_store.py` (PG + Redis) — pas de config locale dans WebUI/CLI/Desktop.
- **Secrets isolés** : `core/config/secrets.py` (env/Vault) — jamais dans la DB ni dans les réponses API.

### 0.2 Les 4 interfaces = 4 clients du même Core

| Interface | Rôle | Accès config |
|---|---|---|
| **WebUI** | Formulaires visuels (fork UX Open WebUI) | `GET/PUT /v1/config/{domain}` |
| **CLI** | `ethan config get/set {domain}.{key}` | Appel direct `core/config` |
| **Desktop** | Panneaux natifs (Atreus) | `GET/PUT /v1/config/{domain}` |
| **Atreus** | Agents autonomes (lecture config) | `GET /v1/config/{domain}` |

> **Règle** : aucune interface ne stocke de config. Toute modification passe par `core/config` → propagation immédiate à toutes les interfaces (EventBus `CONFIG_UPDATED`).

### 0.3 Exemple — Configurer le RAG depuis les 3 interfaces

```bash
# CLI
ethan config set rag.embeddings.engine ollama
ethan config set rag.chunking.chunk_size 4000
ethan config get rag.top_k
```

```ts
// WebUI (thin client)
await api.put('/v1/config/rag', { embeddings: { engine: 'ollama' }, chunking: { chunk_size: 4000 } });
```

```ts
// Desktop (Atreus)
await ethanClient.config.update('rag', { embeddings: { engine: 'ollama' } });
```

→ **Résultat identique** : la config est écrite dans `core/config` → tous les consommateurs (WebUI, CLI, Desktop, Atreus, ChatPipeline) lisent la même valeur.

### 0.4 Domaines de configuration couverts

| Domaine | Clé config | Endpoint |
|---|---|---|
| RAG | `rag.*` (embeddings, chunking, reranker, hybrid, extraction, web_search) | `/v1/config/rag` |
| Knowledge | `knowledge.*` (collections, access) | `/v1/config/knowledge` |
| Files | `files.*` (storage provider, max_size, extensions) | `/v1/config/files` |
| MCP | `mcp.*` (servers, auth) | `/v1/config/mcp` |
| Tools | `tools.*` (registry, valves, builtins) | `/v1/config/tools` |

### 0.5 Propagation des changements

```
core/config (PUT) → EventBus CONFIG_UPDATED
   ├── WebUI (re-render settings)
   ├── CLI (next command reads new value)
   ├── Desktop (refresh panels)
   ├── Atreus (agents re-read config)
   └── ChatPipeline (RAG/tools re-initialized)
```

---

## 1. RAG

### 1.1 Analyse Open WebUI
- `retrieval/` : pipeline ingestion + vector DB + reranker + web search.
- **15 backends vectoriels** (`retrieval/vector/dbs/`) : Chroma, PGVector, Qdrant (multi), Milvus (multi), Weaviate, Pinecone, OpenSearch, Elasticsearch, Oracle23ai, S3Vector, OpenGauss, pgvector, milvus_multitenancy, qdrant_multitenancy.
- **Loaders documents** (`retrieval/loaders/`) : `external_document`, `external_web`, `youtube`, `mistral`, `datalab_marker`, `mineru`.
- **20+ moteurs de recherche web** (`retrieval/web/`) : Brave, Bing, Google PSE, Exa, Firecrawl, Perplexity, Tavily, DuckDuckGo, Kagi, Mojeek, SearXNG, SerpAPI, Serper, Serpstack, Serply, YaCy, Yandex, You.com, Bocha, Sogou…
- **Rerankers** (`retrieval/models/`) : ColBERT (`jinaai/jina-colbert-v2`), `ExternalReranker`, CrossEncoder (sentence_transformers).
- **Fonctions utils** (`retrieval/utils.py`) : `build_loader_from_config`, `get_embedding_function`, `get_reranking_function`, `query_collection[_with_hybrid_search]`, `generate_*_batch_embeddings` (openai/azure/ollama), `get_sources_from_items`, `filter_accessible_collections`.
- **Config riche** (`/retrieval/config` GET+POST) : `RAG_TEMPLATE, TOP_K, BYPASS_EMBEDDING_AND_RETRIEVAL, RAG_FULL_CONTEXT`, hybride (`ENABLE_RAG_HYBRID_SEARCH, HYBRID_BM25_WEIGHT, RELEVANCE_THRESHOLD, TOP_K_RERANKER`), extraction contenu (`CONTENT_EXTRACTION_ENGINE, PDF_*, DATALAB_MARKER_*, TIKA, DOCLING, DOCUMENT_INTELLIGENCE, MINERU`), embeddings (`RAG_EMBEDDING_ENGINE/MODEL, RAG_OPENAI/OLLAMA/AZURE configs`), chunking (`CHUNK_SIZE, CHUNK_OVERLAP, TEXT_SPLITTER, ENABLE_MARKDOWN_HEADER_TEXT_SPLITTER`), upload (`FILE_MAX_SIZE/MAX_COUNT, ALLOWED_FILE_EXTENSIONS`), intégrations (`GOOGLE_DRIVE, ONEDRIVE`), recherche web (20+ clés).
- **Endpoints ingestion** : `/retrieval/process/file|text|youtube|web|web/search`, `/retrieval/query/doc|collection`, `/retrieval/delete`, `/retrieval/reset/{db,uploads}`.

### 1.2 Analyse ETHAN
- `core/rag/__init__.py` expose `RAGPipeline`, `RAGContext`, `RAGRetrieval`, `RAGEmbeddings`, `DocumentChunk`, `IngestedDocument`.
- `core/rag/ingestion.py` : découpage chunks + embeddings → stockage.
- `core/rag/embeddings.py` : gestion embeddings.
- `core/rag/retrieval.py` : retrieval.
- `core/rag/pipeline.py` : orchestration.
- `core/rag/context.py` : contexte.
- Backends vectorels **déjà présents** via `core/memory/` (Chroma, Qdrant, pg_store).
- `core/knowledge/` graphe.
- Pas de config riche (chunking/embeddings/reranker/web search) exposée via une API unique.

### 1.3 Comparaison
| Aspect | OWUI | ETHAN |
|---|---|---|
| Ingénierie | Pipeline monolithique couplé config | core/rag découpé ingestion/retrieval/context/embeddings |
| Vector DB | **15 backends** prêts à l'emploi | 3 (Chroma/PGVector/Qdrant) |
| Embeddings config | 3 engines (openai/ollama/azure) + sentence-transformers | RAGEmbeddings (moins configurable) |
| Reranker | ColBERT + External + CrossEncoder | absent |
| Recherche web | **20+ moteurs** | absent (→ core/tools) |
| Hybrid search | BM25 + vecteur (HYBRID_BM25_WEIGHT) | absent |
| Chunking | TEXT_SPLITTER, MARKDOWN, CHUNK_SIZE/OVERLAP | minimal |
| Extraction contenu | Marker, MinerU, Tika, Docling, Mistral OCR, Document Intelligence | absent |

### 1.4 Fonctionnalités manquantes dans ETHAN Core → MOVE-TO-CORE (RFC)
1. **Factory vectorielle** (`core/rag/vector/factory.py`) pour absoster 15 backends OWUI (Chroma/PGVector/Qdrant/Milvus/Weavite/Pinecone/Elasticsearch/OpenSearch/Oracle/S3Vector/OpenGauss…).
2. **Reranker** (ColBERT/External/CrossEncoder) → `core/rag/reranker.py`.
3. **Web search** comme Tool Core (`core/tools/web_search.py`).
4. **Hybrid search** (BM25 + vecteur) → `core/rag/retrieval.py`.
5. **Engine de chunking** configurable (splitter/markdown/overlap/size) → `core/rag/ingestion.py`.
6. **Loaders documents** (pdf/docx/youtube/marker/mineru/tika/docling/mistral) → `core/state/files.py` + extraction pipeline Core.
7. **API de configuration RAG unifiée** → `/v1/retrieval/config` (secrets → `core/config/secrets.py`, jamais DB).

### 1.5 Modèle de données
**RAG config** (dans `core/config` + `core/state/record_store`, secrets isolés) :
```json
{
  "rag_template": "prompt", "top_k": 5, "top_k_reranker": 3, "reranker_model": "...",
  "reranker_engine": "sentence_transformers|external|colbert",
  "hybrid_search": {"enabled": true, "bm25_weight": 0.5, "relevance_threshold": 0.1},
  "embeddings": {"engine": "openai|ollama|azure|sentence_transformers", "model": "...",
                 "batch_size": 1, "concurrent_requests": 0, "async": true,
                 "openai": {"url": "", "key_ref": "secret:..."},
                 "ollama": {"url": "host.docker.internal:11434"},
                 "azure": {"url":"","key_ref":"secret:...","version":""}},
  "chunking": {"splitter": "recursive|cross_encoders|markdown|by_length", "chunk_size": 4000,
               "chunk_overlap": 500, "markdown_header_splitter": true},
  "extraction": {"engine": "default|external|tika|docling|mineru|mistral|azure_document_intelligence",
                 "pdf_extract_images": true, "pdf_loader_mode": "single/full", ...}
}
```
**Document/chunk** (déjà `core/rag/ingestion.py` `IngestedDocument`/`DocumentChunk`).

### 1.6 API
- `/v1/retrieval/config` GET — status + config (sans secrets) ; POST — mise à jour → `core/config`.
- `/v1/retrieval/embeddings` GET — config embeddings ; POST — update (secrets isolés).
- `/v1/retrieval/process/file|text|youtube|web|web/search` — ingestion via `core/rag/ingestion.py`.
- `/v1/knowledge/{id}/ingest` — ingestion dans collection.
- `/v1/knowledge/{id}/query` — `RAGPipeline.retrieve` (hybride + reranker).
- `/v1/retrieval/query/doc|collection` — retrieval direct.

### 1.7 Persistence
- Config : `core/config` (schema) + `CoreRecordStore` (PG+Redis). Secrets → `core/config/secrets.py`.
- Vectors : backends Core (`core/memory` Chroma/PGVector/Qdrant) — **un seul** par déploiement.
- Chunks/docs : `core/rag/ingestion.py` persiste dans le vector backend + metadata dans RecordStore.

### 1.8 Permissions
- Admin-only : config RAG (`/v1/retrieval/config` → `require_permission(ADMIN)`).
- Knowledge : contrôle d'accès par collection (`core/knowledge` access).
- Ingestion : rattachée à une collection → hérite de ses ACL.

### 1.9 Interface WebUI
- Fork `settings/[tab]/retrieval` OWUI → page Settings RAG (tabs : Embeddings, Chunking, Reranker, Hybrid, Extraction, Web Search, Integrations).
- `features/knowledge` ingestion UI (process file/text/web/youtube + status).
- Thin client : tout passe par `/v1/retrieval/*` & `/v1/knowledge/{id}/ingest|query`.

### 1.10 Consommateurs
WebUI (config UI + ingestion), CLI (ingest/query), Desktop/Atreus (RAG via ChatPipeline), Agents autonomes (retrieval intégré au pipeline).

---

## 2. Knowledge (collections / graphe)

### 2.1 Analyse Open WebUI
- `models/knowledge.py` : tables `knowledge` (id, user_id, name, description, timestamps) + `knowledge_file`.
- `routers/knowledge.py` : CRUD collection, access update, reindex, files (add/remove/update batch), export, search files, reset.
- Collections = groupes de fichiers indexés dans un vectordb.

### 2.2 Analyse ETHAN
- `core/knowledge/{manager,collections,types}` : `KnowledgeManager`, `KnowledgeCollectionManager`, `KnowledgeNode`/`KnowledgeConnection` (graphe concept/fact/rule/entity/source/document) — **graphe sémantique relationnel**.
- Pas (encore) d'API documents/routers `knowledge.py` exposant collections.

### 2.3 Comparaison
| | OWUI | ETHAN |
|---|---|---|
| Collection | fichiers vectorisés | agrégation documents + graphe |
| Accès | access_grants par collection | knowledge access |
| Réindexation | reindex API | KnowledgeCollectionManager |
| Graphe | ❌ | ✅ KnowledgeNode/Connection (force ETHAN) |

### 2.4 Fonctionnalités manquantes dans ETHAN → MOVE-TO-CORE
1. **Collections de connaissance** (`KnowledgeCollectionManager`) exposées via API.
2. **Documents associés aux collections** (fichiers) → lier `FileStore`+`core/rag/ingestion` à une collection.
3. **Export collection** (`GET /{id}/export`).

### 2.5 Modèle de données
```json
// Collection
{ "id":"uuid", "name":"string", "description":"", "status":"ready|processing",
  "files":[ {file_id} ], "access_grants":[...], "embeddings_config":{...},
  "metadata":{...}, "graph":{nodes:[KnowledgeNode], connections:[...]} }
// KnowledgeNode (core/knowledge types.py)
{ "id", "label", "node_type":"concept|fact|rule|entity|source|document",
  "content", "source", "connections":[...], "metadata", "created_at", "updated_at" }
```

### 2.6 API
- `/v1/knowledge` GET/POST (list/create) — `KnowledgeCollectionManager`.
- `/v1/knowledge/{id}` GET/PUT/DELETE.
- `/v1/knowledge/{id}/files` GET + `file/add|update|remove` POST.
- `/v1/knowledge/{id}/reindex` POST.
- `/v1/knowledge/{id}/access/update` POST — ACL.
- `/v1/knowledge/{id}/graph` GET — nœuds/connexions (graphe).
- `/v1/knowledge/{id}/export` GET.

### 2.7 Persistence
- `core/knowledge/collections.py` → `KnowledgeCollectionManager` (CoreRecordStore PG+Redis) ; graphe `KnowledgeStore`.

### 2.8 Permissions
- Collection-level access (créateur/admin/shared) → `core/auth` Access Grants ; `require_permission`.

### 2.9 Interface WebUI
- `features/knowledge/` + `/dashboard/knowledge` (pages list/create/[id]) réutilisant la UX collection+files+reindex d'OWUI ; graphe UI (nouveau — inspiré UX mais rendu graphe Core).

### 2.10 Consommateurs
WebUI, CLI, Atreus/Desktop (retrieval graphe), Agents (connaissance comme memory).

---

## 3. Files & Storage

### 3.1 Analyse Open WebUI
- `models/files.py` : `File` table (id, user_id, format, name, mime, type, size, data, etag, created_at, updated_at), `FileModel`.
- `routers/files.py` : upload, list, search par contenu, get content/html/{name}, process status, delete all.
- `storage/provider.py` : Storage abstraction **local/S3/GCS/Azure**.
- `configs.py` : `/storage` config, `/file_storage` settings.
- Upload : `FILE_MAX_SIZE, FILE_MAX_COUNT, ALLOWED_FILE_EXTENSIONS, FILE_IMAGE_COMPRESSION_*`.

### 3.2 Analyse ETHAN — EXISTANT
- `core/state/files.py` `FileStore` (filename, content_type, size, user_id, storage_path, metadata) → ✅
- `core/state/record_store.py` CoreRecordStore (PG+Redis).
- Open WebUI **indique** storage providers (S3/GCS/Azure/local) → ETHAN n'a pas de `storage provider.py` Core.

### 3.3 Comparaison
| | OWUI | ETHAN |
|---|---|---|
| Storage abstraction | storage/provider.py (local/S3/GCS/Azure) | FileStore abstrait (storage_dir local) — providers manquants |
| Upload config | FILE_MAX_SIZE/COUNT/EXTENSIONS | minimal |
| Content extraction | retrieval loaders | core/rag ingestion (à brancher) |
| Process status | /{id}/process/status | FileStore (à enrichir) |

### 3.4 Fonctionnalités manquantes dans ETHAN Core → MOVE-TO-CORE
1. **Storage provider abstraction** (`core/file_storage/` ou `core/state/storage.py`) : local + S3/GCS/Azure (clés → `core/config/secrets.py`).
2. **Upload config** (max_size/count/extensions) → `core/config`.
3. **Content extraction / processing status** → brancher `core/rag/ingestion` + FileStore.status.

### 3.5 Modèle de données
```
FileRecord {
  id: uuid, filename, content_type, size, user_id,
  storage_path: "local://...|s3://bucket/key|gs://...", 
  storage_provider: "local|s3|gcs|azure",
  etag, process_status: "uploaded|processing|processed|failed",
  metadata: {pages?, text_content?, thumbnail?},
  created_at, updated_at
}
```
→ aligné sur `core/state/files.py` FileStore (étendre storage_provider/status).

### 3.6 API
- `/v1/files` POST (upload), GET (list/search) — `core/state/files.py` FileStore.
- `/v1/files/{id}` GET, DELETE.
- `/v1/files/{id}/content` GET (html/text/name) ; `/{id}/process/status`.
- `/v1/config/storage` GET/PUT (local/S3/GCS/Azure) — secrets isolés.

### 3.7 Persistence
- Métadonnées `FileStore` → RecordStore (PG+Redis).
- Binaires → backend storage (local filesystem or S3/GCS/Azure via `core/file_storage`).

### 3.8 Permissions
- `require_permission(FILES)` pour upload/delete ; ACL par fichier (access_grants) pour partage.

### 3.9 Interface WebUI
- `/dashboard/documents` + upload UI (drag-drop) ; preview HTML ; file details + status ; settings storage provider.

### 3.10 Consommateurs
WebUI (upload/preview), Knowledge (fichiers de collections), CLI, Atreus/Desktop.

---

## 4. MCP (serveurs d'outils)

### 4.1 Analyse Open WebUI
- `utils/mcp/client.py` `MCPClient` : connecte via `streamablehttp_client`, supporte `OAuthClientProvider`/`TokenStorage`, `list_tool_specs`, `connect/disconnect` — **client MCP complet**.
- `configs.py` `/terminal_servers`, `/tool_servers` (CRUD + verify).
- `ToolServerModel` (id, name, url, ...).
- Intégré dans `tools/builtin.py` → outils exposés au LLM.

### 4.2 Analyse ETHAN — EXISTANT
- `core/tools/servers.py` `ToolServerManager` (register name/url/auth_type/auth_config/enabled/status/lifecycle events) → **gestion d'enregistrement only**.
- `core/tools/executor.py` `ToolExecutor` (call_llm_tool) → **aucune logique MCP nativer**.
- EventBus pour `TOOL_SERVER_REGISTERED`.

### 4.3 Comparaison
| | OWUI | ETHAN |
|---|---|---|
| Client MCP transport | streamable_http + stdio | ❌ (à intégrer) |
| Auth OAuth | OAuthClientProvider + TokenStorage | ❌ |
| Introspection tools | list_tool_specs | ❌ |
| Lifecycle/registry | ToolServerManager | ✅ mais sans client |
| Intégration pipeline | builtin tools | ToolExecutor (à brancher MCP) |

### 4.4 Fonctionnalités manquantes dans ETHAN Core → MOVE-TO-CORE
1. **Client MCP natif** → reporter `open_webui/utils/mcp/client.py` dans `core/tools/mcp_client.py` (streamable_http + stdio + OAuth).
2. **Introspection tool specs** → `core/tools/registry.py` (map MCP tools → `Tool`).
3. **Brancher MCP → ToolExecutor/ToolRegistry** pour exécution par ChatPipeline/Agents.

### 4.5 Modèle de données
```
ToolServer {
  id: uuid, name, url, transport: "http"| "stdio",
  auth_type: "none"|"oauth", auth_config: {client_id, token_url,...},
  enabled, status: "disconnected|connected|error",
  last_connected_at, tools: [{name,description,parameters}],
  metadata, created_at, updated_at
}
```
→ aligné sur `core/tools/servers.py`.

### 4.6 API
- `/v1/tools/servers` GET/POST (list/create).
- `/v1/tools/servers/{id}/toggle` PUT.
- `/v1/tools/servers/{id}/test` POST (connect/health).
- `/v1/tools/servers/{id}/tools` GET (list_tools via client MCP Core).

### 4.7 Persistence
- `core/tools/servers.py` → CoreRecordStore (PG+Redis).

### 4.8 Permissions
- Admin-only serveurs MCP (require ADMIN) — sensibilité élevée.

### 4.9 Interface WebUI
- Fork `ToolServersModal.svelte` → Modal création/listing MCP ; statut realtime (WebSocket EventBus).

### 4.10 Consommateurs
WebUI, CLI, Desktop, Mobile, Atreus, Agents autonomes.

---

## 5. Tools & Functions (appelables)

### 5.1 Analyse Open WebUI
- `models/tools.py` : `Tool` table (id, user_id, name, url, model, specs_url, headers, params, is_active, is_global, access), `ToolMeta`, `ToolValves`.
- `models/functions.py` : **doublon** `Function` table (id, user_id, name, type, content, valves, is_active, is_global) — **concept dupliqué avec tools**.
- `routers/tools.py` : list/load_url/export/import + CRUD + valves (user/dev spec).
- `routers/functions.py` : CRUD + toggle + valves + sync + load_url — **même API que tools**.
- `tools/builtin.py` : get_current_timestamp, web_search, image_generation, code_execution, etc. — outils natifs.
- **Valves** : `valves` (config dev) + `user_valves` (config user) — schéma JSON.

### 5.2 Analyse ETHAN — EXISTANT
- `core/tools/{registry,selector,executor,monitor,functions,servers,types,tracker}`.
- `Tool` (dataclass), `ToolContext`, `ToolResult`, `ToolManager` (registry→selector→executor→monitor→record), `ToolServerManager` (MCP).
- `core/tools/functions.py` existe déjà pour functions natives.

### 5.3 Comparaison
| | OWUI | ETHAN |
|---|---|---|
| Registry | ToolRegistry (DB) | ToolRegistry Core ✅ |
| Custom tools (URL/MCP) | tools + functions (doublon) | tools + servers (MCP) ✅ |
| Builtin tools | builtin.py | functions.py ✅ |
| Valves (config user/dev) | ToolValves (JSON schema) | Tool.parameters (à typer valves) ⚠️ |
| Sélection | filter → pipe → suggest | ToolSelector par capability ✅ |
| Exécution | builtin tools + MCP | ToolExecutor ✅ |
| Export/import | ✅ | ❌ (à ajouter) |
| load_url | ✅ | ToolLoaderCore (MOVE) |
| Monitor/statistiques | — | ToolMonitor ✅ |

### 5.4 Fonctionnalités manquantes dans ETHAN Core → MOVE-TO-CORE / ADAPT
1. **Fusion functions↔tools** → unifier sous `core/tools` ; `functions.py` routers OWUI supprimé (DELETE).
2. **Valves modulaires** (user/dev avec JSON schema) → `Tool.valves_schema` + `Tool.parameters` OWUI.
3. **Export/import** tools → `ToolRegistry.export()/import_()`.
4. **load_url** (import depuis URL) → `ToolRegistry.load_from_url`.
5. **Builtin outils natifs** → `core/tools/builtin.py` (intégrer builtin OWUI : web_search, image_generation, code_interpreter, current_time).

### 5.5 Modèle de données
```
Tool {
  id: uuid, name, type: "builtin"|"custom"|"mcp"|"function",
  description, parameters: {schema, required, valves:{user_schema, dev_schema}},
  url/headers/model/specs_url, is_active, is_global,
  access_grants, meta{icon,category,env}, created_at, updated_at
}
ToolExecution { tool_id, chat_id, messages, result, latency, cost, status, ... }
```
→ aligné sur `core/tools/types.py` `Tool`/`ToolResult` + `core/tools/monitor.py` (execution logging).

### 5.6 API
- `/v1/tools` GET (list), POST (create).
- `/v1/tools/{id}` GET/PUT/DELETE.
- `/v1/tools/{id}/toggle`, `/{id}/access/update`, `/{id}/valves`, `/{id}/valves/spec`, `/{id}/valves/user`.
- `/v1/tools/load/url` POST (import).
- `/v1/tools/export`,`/import` POST/GET.

### 5.7 Persistence
- `core/tools/registry.py` → CoreRecordStore (PG+Redis) ; exécutions → `core/tools/monitor.py` (PG/Redis).

### 5.8 Permissions
- Admin-only : import/export, load_url, toggle global.
- Custom tools : `require_permission(FILES)` ou `TOOLS` ; partage par access_grants.

### 5.9 Interface WebUI
- Fork `workspace/tools` + `ToolForm` + valves modal → `features/tools` ; builtin outils list.

### 5.10 Consommateurs
ChatPipeline (tool selection), Agents, CLI (tools), Atreus/Desktop, WebUI.

---

## 6. Synthèse migration OWUI → ETHAN Core (unification, zéro doublon)

| Domaine OWUI | Module ETHAN Core (source de vérité UNIQUE) | Action |
|---|---|---|
| `retrieval/` (15 DB + 20 web + rerank) | `core/rag/{embeddings,ingestion,retrieval,context}` + `core/tools/web_search` | ADAPT + MOVE-TO-CORE (vector factory RFC, reranker, web search tool) |
| `knowledge.py` collections | `core/knowledge/{manager,collections,types}` | ADAPT (expose collection manager API) |
| `files.py` + `storage/provider.py` | `core/state/files.py` + nouveau `core/file_storage/` | MOVE storage provider → Core ; ADAPT FileStore (status, storage_provider) |
| `utils/mcp/client.py` (client) | `core/tools/mcp_client.py` + `servers.py` | MOVE client → Core ; ADAPT |
| `tools.py` + `functions.py` (DOUBLON) | `core/tools/{registry,selector,executor,functions}` | REPLACE ; DELETE doublon functions.py |
| `tools/builtin.py` | `core/tools/builtin.py` | MOVE builtins → Core |
| `retrieval/config` (RAG config) | `core/config/` + secrets | REPLACE (secrets isolés) |

> ✅ Open WebUI reste **indépendant** (référence) ; ETHAN Core est la **seule source de vérité**. Configuration via WebUI/CLI/Desktop → toujours passée par `interfaces/api` → Core. Aucun des 5 domaines ne doit exister en double.
