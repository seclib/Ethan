# DAENA_ARCHITECTURE.md

Architecture actuelle constatée de DAĒNĀ, des systèmes connexes (Knowledge, RAG, Engineering Memory, Agents, DTAI) et de leurs dépendances. Basée sur la lecture réelle des sources, sans hypothèse non étayée.

---

## 1. Vue d'ensemble des couches

```
Utilisateur
   │
   ▼
┌─────────────────────────────────────┐
│  Interfaces (WebUI Next.js / CLI)   │  ← passent par l'API, pas de logique métier
│  (Interpreteur : HTTP / Fetch)      │     (règle ETHAN : Core + Runtime + Services)
└──────────────────┬──────────────────┘
                   │ HTTP / JSON
                   ▼
┌─────────────────────────────────────┐
│   API Gateway (FastAPI / v1.py)     │  ← routers minces, injection de managers
│  interfaces/api/main.py             │     lifespan : NATS, managers Core
└──────────────────┬──────────────────┘
                   │
    ┌──────────────┼──────────────┐
    ▼              ▼              ▼
┌────────┐   ┌────────┐   ┌─────────────┐
│ Core   │   │ Runtime│   │ Services    │
│ agents │   │  orch. │   │  engineering│
│ knowledge│ │        │   │  memory     │
│ rag      │ │        │   │  vault      │
│ search   │ │        │   │  capabilities│
│ memory   │ │        │   │  applications│
└────────┘   └────────┘   └─────────────┘
    │                       │
    ▼                       ▼
CoreRecordStore        Obsidian / daena/
(PostgreSQL / JSON)      (fichiers markdown, YAML)
```

---

## 2. Composants et responsabilités réelles

### 2.1 Interfaces (WebUI)
- `interfaces/webui/src/components/features/observatory/` : 8 espaces (Overview, Vault, Graph, Canvas, Timeline, Search, Engineering, AI Insights). Chaque espace appelle des endpoints `/v1/memory/*` ou `/v1/search` via TanStack Query (`useQuery`/`useMutation`). Aucun dossier `hooks/` dédié ; pas de logique métier.
- `interfaces/webui/src/lib/api/` : couche d'appel HTTP (`apiFetch`, `knowledge.ts`, `memory.ts`, `search.ts`, `rag.ts`, `web-import.ts`, `web-research.ts`, `library.ts`).
- Règle ETHAN (AGENTS.md WebUI) : les interfaces n'implémentent pas la logique métier, ne stockent pas l'état métier, ne définissent pas providers/agents/mémoire/RAG.

### 2.2 API Gateway
- `interfaces/api/main.py` : point d'entrée FastAPI. Lifespan (l. 203-239) établit NATS, instancie tous les managers Core (`KnowledgeManager`, `RAGPipeline`, `SearchManager`, `EngineeringMemoryService`, `CapabilityManager`, `ApplicationIntegrationRegistry`, etc.) et les injecte dans les routers via des setters globaux (injection module-level).
- Router `v1` (préfixe `/v1`) monté. Router `knowledge.py` et `engineering_memory.py` définis mais **non montés** (orphelins, dupliqués dans v1.py).
- Auth : JWT cookie `ethan_token` ou header Bearer, API keys, service identities. `require_permission(Permission.X)` sur les endpoints.

### 2.3 Core — Knowledge
- `core/knowledge/manager.py` (`KnowledgeManager`) : propriétaire des nœuds (`KnowledgeNode`, `KnowledgeConnection`, types CONCEPT/FACT/RULE/ENTITY/SOURCE/DOCUMENT). CRUD, search full-text, `connect`, `ingest_into_rag` (porte vers RAG, nécessite un `RAGPipeline` explicite).
- `core/knowledge/collections.py` (`KnowledgeCollectionManager`) : collections RAG, arborescence (`parent_id`), contrôle d'accès (owner/admin/grants user-groupe read/write), `retrieve_multi` (un passage RAG scoped), `build_context_multi`, `reindex_collection`.
- Persistance : `CoreRecordStore` (domaines `knowledge`, `knowledge-collections`, `rag-documents`, `rag-config`, `agents`, `capability_operations`).

### 2.4 Core — RAG
- `core/rag/pipeline.py` (`RAGPipeline`) : `ingest`, `retrieve`, `build_context` (max_context_chars=8000), `build_messages`. `attach_llm_client` pour les embeddings réels (sinon mode textuel-fallback, vecteurs nuls dim 8).
- `core/rag/ingestion.py` : `RAGIngestion` (stratégies character/sentence/paragraph, validation dimensionnelle).
- `core/rag/retrieval.py` : `RAGRetrieval` (auto/keyword/semantic/hybrid, cosinus en mémoire ou index externe ChromaDB/Qdrant, RRF hybride).
- `core/rag/context.py` : `RAGContext` (assemblage borné avec sources).
- `core/rag/strategies.py` : 4 stratégies, pas de reranking.

### 2.5 Core — Search
- `core/search/__init__.py` (`SearchManager`, 4 types : web/knowledge/library/conversation). Délègue à `KnowledgeManager`, `ChatStore`, `RAGPipeline`. Ne duplique pas leur logique.

### 2.6 Core — Engineering Memory
- `core/engineering_memory/service.py` (`EngineeringMemoryService`) : `record`/`collect_event`, `get`, `search` (filtres), `component_history`, `verify_integrity`. Écrit via `ObsidianPersistence` (fichiers YAML dans le vault Obsidian), journal d'audit ndjson.
- `core/engineering_memory/vault.py` (`VaultService`) : read-only par construction (tree, read, search, backlinks, graph, resolve_wikilink), écriture managée (write, Archives immuables).
- `core/engineering_memory/models.py` : `MemoryRecord` (RecordType : COMPONENT/DECISION/ENGINEERING_EVENT/INCIDENT/REPAIR/VERIFICATION/DEPENDENCY/TEST_RESULT/TECHNICAL_DEBT/EVIDENCE/AGENT_REPORT).
- `core/engineering_memory/adapters.py` : adaptateur non bloquant pour que `AgentManager` et `KnowledgeManager` écrivent des événements (câblé via `set_engineering_memory_integration`, accepte `None`).

### 2.7 Core — Agents
- `core/agents/types.py` : `Agent` (déclare knowledge_ids, knowledge_collection_ids, skill_ids, tool_ids, folder_ids, domain_ids, memory_scope, owner_id, agent_type).
- `core/agents/manager.py` : `create`/`execute`/CRUD. `execute` est le point d'entrée unique.
- `core/agents/executor.py` : résout les ressources via `core/agents/resources.py`, compile le system prompt (skills, knowledge, RAG via `build_context_multi`, tools, capabilities), sépare données/instructions (CT-4, `prompt_guard.py`), boucle d'outils bornée `MAX_TOOL_ROUNDS=3`, `SecureToolEnforcer` (fail-closed).
- `core/agents/resources.py` : `resolve_agent_resources`. Règle : aucune ressource globale sans sélection explicite. Déduplication, ghosts.

### 2.8 Core — Mémoire cognitive (non branchée aux agents)
- `core/memory/manager.py` (`MemoryManager`, 8 types), `core/memory/retrieval.py` (`RetrievalEngine`). Embeddings TODO (vecteurs vides), aucun appel dans `executor.py`.

### 2.9 Core — Planner
- `core/planner/planner.py` : décomposition par patterns (3 patterns codés en dur) + `CapabilityRegistry.find`. Pas de consultation Knowledge/RAG/mémoire.
- `core/planner/decomposer.py` : stratégie LLM en TODO, règles (docker build, deploy, test, build+deploy).

### 2.10 Core — DTAI (Dynamic Tool & Application Integration)
- `core/applications/models.py` : schéma manifest canonique (ApplicationManifest, contract 1.0.0).
- `core/applications/validator.py` : `ContractValidator`.
- `core/applications/discovery.py` : `ApplicationDiscoveryService` (scan récursif, états DECLARED→...→AUTHORIZED).
- `core/applications/application_registry.py` : `ApplicationIntegrationRegistry` (enregistrement, états REGISTERED/VALIDATED/AVAILABLE/UNAVAILABLE/WITHDRAWN).
- `core/applications/resilience.py` : machine à états de cycle de vie, `ResilientExecutor`.
- `core/applications/permissions.py` : `PermissionService` (HROT, `HumanAuthority`, `PermissionScope`, `manifest_fingerprint`).
- `core/applications/manifest_repository.py` : stockage SQLite durable (`delete()` = NotImplementedError).
- `core/applications/capability_contract.py` + `capability_execution.py` : contrats de capacités, `invoke_capability` (TRUSTED_IMPLEMENTATION_ALIASES = odin.runtime-status, frame.runtime-status).
- `core/applications/capabilities.py` : `CapabilityRegistry` (définitions versionnées).
- `core/capability_manager/` : `CapabilityManager` + 5 backends (Docker, Python, Node, Executable, Builtin), `validate_install_actions` (barrière anti-injection).
- Plugins : `core/plugins/compose_service.py` (générique), `core/plugins/odin.py` (duplication ~700 lignes, ne hérite pas), `core/plugins/frame.py` (héritage propre), `core/plugins/quantar.py`.

### 2.11 Cas d'application concrets
- **Odin** : manifest `examples/odin/`, registre `register_odin_pilot`, plugin `OdinService` (port 4173, Docker compose), contrat `odin.runtime-status`, endpoints `/v1/applications/{app_id}/runtime,/start,/stop`.
- **Frame** : manifest `examples/frame/`, registre `register_frame_pilot`, plugin `FrameService(ComposeService)` (port 5190, bun), contrat `frame.runtime-status`.
- **Quantar** : manifest `examples/quantar/`, registre `register_quantar_pilot`, `QuantarService` (compose) + `QuantarTaskService` (moteur tâches TradingAgents, in-process ou Docker one-shot). **Aucun contrat d'exécution, aucun endpoint HTTP dédié dans les routers examinés.**
- **TradingAgents** : absent du dépôt ETHAN (proposition de manifest uniquement dans `tests/core/test_dta1a_tradingagents_manifest.py`).

---

## 3. Dépendances entre composants

```
KnowledgeManager ──► CoreRecordStore (domaine knowledge)
KnowledgeCollectionManager ──► CoreRecordStore (domaine knowledge-collections)
RAGPipeline ──► CoreRecordStore (domaine rag-documents, rag-config)
      │
      └──► (optionnel) Vector store externe ChromaDB / Qdrant
AgentManager ──► CoreRecordStore (domaine agents)
      │
      └──► create_agent_executor ──► resolve_agent_resources
                                       ├─ KnowledgeManager.get (nœuds spécifiques)
                                       ├─ KnowledgeCollectionManager.build_context_multi (collections RAG)
                                       ├─ Skills / Tools / Folders / Domains
                                       └─ compilation system prompt (données <data> avec provenance)
EngineeringMemoryService ──► ObsidianPersistence (fichiers YAML vault) + audit ndjson
      │
      └──► EngineeringMemoryIntegration (adaptateur non bloquant, appelé par AgentManager/KnowledgeManager)
VaultService ──► lecture seule du vault Obsidian (daena/ + Obsidian/)
SearchManager ──► délègue à KnowledgeManager / ChatStore / RAGPipeline (pas de duplication)
ApplicationIntegrationRegistry ──► CoreRecordStore + ApplicationManifestRepository (SQLite)
CapabilityManager ──► CoreRecordStore (domaine capability_operations, 24h/50 max)
```

---

## 4. Flux de données principaux

### 4.1 Flux Knowledge (écriture nœud)
```
Interface (POST /v1/knowledge) → v1.py create_knowledge → KnowledgeManager.create → CoreRecordStore.save(domaine knowledge) → EventBus.publish(KNOWLEDGE_CREATED) → EngineeringMemoryIntegration.record_knowledge_operation (non bloquant)
```

### 4.2 Flux RAG (ingestion)
```
Interface (POST /v1/rag/documents) → v1.py ingest_rag_document → RAGPipeline.ingest (chunking + embedding + index vecteur) → CoreRecordStore.save(domaine rag-documents) → enregistrement dans RAGRetrieval
```

### 4.3 Flux Agent (exécution avec contexte Knowledge/RAG)
```
AgentManager.execute(agent_id, task) → create_agent_executor.execute
   ├─ resolve_agent_resources → knowledge_ids / knowledge_collection_ids / skill_ids / tool_ids / folder_ids / domain_ids
   ├─ compilation system prompt :
   │   ├─ KnowledgeManager.get (nœuds) → <data source="knowledge:...">
   │   ├─ KnowledgeCollectionManager.build_context_multi (collections RAG) → <data source="rag:..."> [{i}] title (source)
   │   ├─ Skills → <data source="skill:...">
   │   └─ Tools → protocole <tool name="...">
   ├─ sanitize_external_content + wrap_data_block (CT-4, séparation données/instructions)
   └─ run_agent_chat (LLM, max 3 tool rounds, SecureToolEnforcer fail-closed)
```

### 4.4 Flux Vault (DAĒNĀ)
```
Interface (GET /v1/memory/vault/tree) → engineering_memory router → VaultService.tree() → lecture du vault Obsidian (daena/ + Obsidian/) → arbre JSON
```

### 4.5 Flux Search unifié
```
Interface (GET /v1/search?q=&type=&limit=) → search.py → SearchManager.search → délègue KnowledgeManager / RAGPipeline / ChatStore / web_search_fn → résultats unifiés
```

---

## 5. Limites architecturales constatées

1. **Aucun mécanisme commun d'accès Knowledge pour les agents** : chaque agent reçoit ses ressources via sélection explicite (`knowledge_ids`, `knowledge_collection_ids`), injectées dans le system prompt. Pas de retrieval autonome à la volée.
2. **Mémoire cognitive non branchée** : `core/memory/` (MemoryManager, RetrievalEngine) n'est pas appelée dans le flux d'exécution agent.
3. **Pas de citation formelle** : la provenance est dans le prompt (`<data source="...">`, `[i] title (source)`), pas extraite de la réponse LLM.
4. **Pas de comptage de tokens** : `max_context_chars=8000` (caractères), `ModelInfo.context_length=4096` (déclaratif, inutilisé pour la troncation).
5. **HROT non intégré à l'exécution agent** : `CapabilityAuthorizationService` existe mais n'est pas appelé dans `executor.py`.
6. **Routeurs orphelins** : `knowledge.py` et `engineering_memory.py` définis mais non montés dans `main.py`.
7. **Duplication OdinService vs ComposeService** (~700 lignes).
8. **TradingAgents absent** (proposition de manifest uniquement).
9. **Pas d'indexation DTAI dans DAĒNĀ** (pas de contrat explicite entre les deux systèmes).
10. **Suppression de manifest durable bloquée** (`NotImplementedError`).

---

## 6. Preuves de validation (références)

- `core/agents/executor.py` : lignes 240-457 (flux agent, injection contexte, CT-4, boucle outils).
- `core/agents/resources.py` : lignes 1-248 (résolution ressources, règle absolue).
- `core/knowledge/manager.py` : lignes 37-233 (KnowledgeManager).
- `core/knowledge/collections.py` : lignes 61-655 (collections, retrieval multi, build_context).
- `core/rag/pipeline.py` : lignes 83-380 (RAGPipeline, config, stats).
- `core/rag/retrieval.py` : lignes 125-364 (RAGRetrieval, stratégies, RRF, cosinus).
- `core/engineering_memory/service.py` : lignes 1-108 (EngineeringMemoryService).
- `core/engineering_memory/vault.py` : lignes 1-385 (VaultService, read-only, écriture managée).
- `core/engineering_memory/adapters.py` : lignes 50-231 (intégration non bloquante).
- `core/applications/capability_execution.py` : contrats d'exécution, TRUSTED_IMPLEMENTATION_ALIASES.
- `core/capability_manager/manager.py` : cycle de vie des composants optionnels.
- `interfaces/webui/src/components/features/observatory/` : 8 espaces, appels API réels.
- `tests/test_agent_knowledge_scoping.py`, `tests/test_agent_resources.py` : tests réels couvrant l'injection de contexte.

Fin de l'architecture actuelle.
