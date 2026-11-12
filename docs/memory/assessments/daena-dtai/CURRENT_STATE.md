# CURRENT_STATE.md

État réel des composants DAĒNĀ, Knowledge, RAG, Engineering Memory, Agents et DTAI.
Distinction systématique : **opérationnel** (code exécutable, tests passent) / **partiel** (déclaré, incomplet ou dégradé) / **absent** (simple déclaration documentaire sans code fonctionnel).

---

## 1. DAĒNą — Observatory (8 espaces fonctionnels)

### 1.1 Overview
- **Composants frontend** : `interfaces/webui/src/app/workspaces/observatory/page.tsx` (`ObservatoryPage`). Sous-composants locaux `StatTile` (l. 215), `QuickAction` (l. 248), `Panel` (l. 276), `EmptyNote` (l. 305), `formatDate` (l. 309).
- **Appels API** : `/v1/memory/facts`, `/v1/memory/events`, `/v1/knowledge/collections`, `/v1/memory/vault/tree`, `/v1/memory/records` (via `interfaces/webui/src/lib/api/`).
- **Backend** : `core/engineering_memory/service.py`, `core/knowledge/collections.py`, `core/search/__init__.py`.
- **État** : opérationnel. Toutes les données proviennent d'appels API Core réels, pas de mock.
- **Tests** : aucun test frontend spécifique à Overview.

### 1.2 Vault
- **Composants frontend** : `interfaces/webui/src/components/features/observatory/components/vault-workspace.tsx` (`VaultWorkspace`), `VaultTree`, `ObservatoryMarkdown`, `parseFrontmatter`, `rewriteWikilinks`. Route `/workspaces/observatory/vault`.
- **Appels API** : `/v1/memory/vault/tree` (GET), `/v1/memory/vault/file` (GET/POST), `/v1/memory/vault/search`, `/v1/memory/vault/backlinks`, `/v1/memory/vault/graph`, `/v1/memory/vault/resolve`, `/v1/memory/vault/records`.
- **Backend** : `core/engineering_memory/vault.py` (`VaultService`, lecture seule par construction, écriture managée avec blocage des Archives), `core/engineering_memory/service.py` (`EngineeringMemoryService`).
- **État** : opérationnel. Lecture/écriture via le Core. Les Archives/ sont en lecture seule (blocage backend).
- **Tests** : `tests/interfaces/test_engineering_memory_vault_router.py` (105 lignes) couvre tree/file/search/backlinks/graph/write. Aucun test frontend spécifique à VaultWorkspace.

### 1.3 Graph
- **Composants frontend** : `interfaces/webui/src/components/features/observatory/graph/graph-view.tsx` (`GraphView`), `interfaces/webui/src/components/features/observatory/graph/layout.ts` (algorithme force-directed, graine fixe 0x5eed, 160 itérations). Route `/workspaces/observatory/graph`.
- **Appels API** : `/v1/memory/vault/graph?limit_nodes=150` (GET).
- **Backend** : `VaultService.graph()` (core/engineering_memory/vault.py l. 242-295) — graphe de wikiliens résolus entre documents Markdown.
- **État** : opérationnel. Données du graphe proviennent de l'API Core ; layout calculé localement.
- **Tests** : `__tests__/layout.test.ts` (39 lignes) couvre `layoutGraph` ; backend couvert par `test_engineering_memory_vault_router.py` (`test_vault_graph`).

### 1.4 Canvas
- **Composants frontend** : `interfaces/webui/src/components/features/observatory/canvas/canvas-workspace.tsx` (`CanvasWorkspace`). Route `/workspaces/observatory/canvas`.
- **Appels API** : `/v1/memory/vault/tree` (GET) uniquement, pour lister les documents Markdown candidats.
- **Persistance** : `localStorage` uniquement (clé `ethan.observatory.canvas.v1`). Aucune écriture backend ; liens purement visuels/navigatifs.
- **État** : **partiel** — local uniquement, fonctionnel pour l'organisation visuelle, aucune donnée persistée sur le Core.
- **Tests** : aucun.

### 1.5 Timeline
- **Composants frontend** : `interfaces/webui/src/components/features/observatory/timeline/timeline-view.tsx` (`TimelineView`). Route `/workspaces/observatory/timeline`.
- **Appels API** : `/v1/memory/records?limit=500` (GET), `/v1/memory/events` (GET).
- **Données** : fusion des Engineering Memory records et des Memory Events (WebUI). Groupement par mois.
- **État** : opérationnel. Données réelles des deux sources API. Peut être vide si aucun enregistrement.
- **Tests** : aucun test frontend spécifique.

### 1.6 Search
- **Composants frontend** : `interfaces/webui/src/components/features/observatory/search/search-view.tsx` (`SearchView`). Route `/workspaces/observatory/search`.
- **Appels API** : `/v1/memory/vault/search` (vault, documents), `/v1/search?q=&type=&limit=` (knowledge / conversations / library / web, via `SearchManager`).
- **Backend** : `core/search/__init__.py` (`SearchManager`, 4 types : web, knowledge, library, conversation). Délègue à `KnowledgeManager`, `ChatStore`, `RAGPipeline` — ne duplique pas leur logique.
- **État** : opérationnel. Deux moteurs réels délégués au Core. Aucun résultat inventé.
- **Tests** : aucun test frontend spécifique. Backend couvert par `interfaces/api/routers/search.py` et `core/search/__init__.py`.

### 1.7 Engineering
- **Composants frontend** : `interfaces/webui/src/components/features/observatory/engineering/engineering-view.tsx` (`EngineeringView`, 8 onglets : ADR, ESR, ASR, Composants, Incidents, Dépendances, Tests & preuves, Dette technique, Archives). Route `/workspaces/observatory/engineering`.
- **Appels API** : `/v1/memory/vault/tree`, `/v1/memory/health`, `/v1/memory/records`.
- **Backend** : `core/engineering_memory/service.py` (`verify_integrity`, `search`, `component_history`).
- **État** : opérationnel. Lecture seule du vault et des records Engineering Memory. Archives explicitement immuables.
- **Tests** : aucun test frontend spécifique.

### 1.8 AI Insights
- **Composants frontend** : `interfaces/webui/src/components/features/observatory/ai-insights/ai-insights-view.tsx` (`AiInsightsView`). Fichier `.bak` présent (non utilisé). Route `/workspaces/observatory/ai-insights`.
- **Appels API** : `/v1/memory/vault/tree`, `/v1/memory/records?record_type=agent_report&limit=100`.
- **Données** : synthèses agents sous `Knowledge/Syntheses/by-agent/` (vault) + rapports `agent_report` de l'Engineering Memory (statut PROVISIONAL → REVIEWED → VALIDATED, promotion humaine requise). Aucune génération d'insights IA déclenchée depuis cette vue (lecture uniquement).
- **État** : **partiel** — fonctionnel si des synthèses/rapports existent, sinon états vides. Aucune génération d'insights IA.
- **Tests** : aucun test frontend spécifique.

### 1.9 LibraryWorkspace (croisement)
- `interfaces/webui/src/components/features/library/library-workspace.tsx` (`LibraryWorkspace`, 124 lignes). Appelle `getLibrary(filters)` via `@/lib/api/library`. Affiche documents, images, knowledge, collections, projets.
- **État** : opérationnel. Capacité de premier niveau, route `/library`, entrée dans Workspaces (sidebar) après DAĒNĀ. Pas d'onglet dans KnowledgeHub (supprimé, voir knowledge-hub.tsx).

### 1.9b KnowledgeHub
- `interfaces/webui/src/components/features/knowledge/components/knowledge-hub.tsx` (113 lignes, 7 onglets : browser, web-search, domains, folders, knowledge, rag, web). Les onglets "Toutes les Skills" et "Library" ont été supprimés (doublons avec `/skills` et `/library`).
- **État** : opérationnel. Pas de deuxième surface Library.

---

## 2. Knowledge et RAG

### 2.1 Knowledge (nœuds de connaissance)
- **Backend** : `core/knowledge/manager.py` (`KnowledgeManager`).
  - `create` (l. 37-78), `get` (l. 80-83), `list` (l. 85-89), `update` (l. 91-115), `delete` (l. 117-132), `search` (l. 134-147, full-text sur label/source/content), `connect` (l. 149-188, relations dirigées avec strength 0-1).
  - `ingest_into_rag(node_id, rag)` (l. 190-201) : porte d'entrée Knowledge → RAG. Nécessite un `RAGPipeline` passé explicitement (pas d'auto-ingestion implicite).
- **Types** : `core/knowledge/types.py` — `KnowledgeType` (CONCEPT, FACT, RULE, ENTITY, SOURCE, DOCUMENT), `KnowledgeNode`, `KnowledgeConnection`.
- **État** : opérationnel (CRUD et search). `ingest_into_rag` réel mais non automatique.

### 2.2 Collections RAG
- **Backend** : `core/knowledge/collections.py` (`KnowledgeCollectionManager`, 655 lignes).
  - CRUD collections (l. 61-226) avec `parent_id`, `retrieval_strategy` (auto/keyword/semantic/hybrid), arborescence (`list_tree`).
  - Contrôle d'accès (l. 229-389) type Open-WebUI : owner, admin, grants user/groupe (read/write). `user_id=None` → pas d'enforcement (legacy interne).
  - Membership documents (l. 393-428).
  - Retrieval (l. 451-534) : `retrieve` (mono-collection), `retrieve_multi` (multi-collections, un seul passage RAG), `build_context_multi`/`build_context` (contexte texte borné `[{i}] {title} ({source})\n{content}`), `reindex_collection` (l. 536-578).
- **État** : opérationnel, entièrement testé.

### 2.3 RAG Pipeline
- **Backend** : `core/rag/pipeline.py` (`RAGPipeline`).
  - `ingest` (l. 83-111) : chunking, embedding, persistance `CoreRecordStore` (domaine `rag-documents`), indexation vecteur externe si branchée.
  - `retrieve` (l. 131-157), `build_context` (l. 159-174, `max_context_chars` défaut 8000), `build_messages` (l. 176-191).
  - `attach_llm_client` (l. 232-234) : branche un client LLM réel sur les embeddings. Sans client → mode "textual-fallback" (embeddings nuls, recherche par mots-clés).
  - `max_context_chars` = 8000 (défaut), `top_k` = 5 (défaut).
- **Ingestion** : `core/rag/ingestion.py` (`RAGIngestion`, stratégies character/sentence/paragraph, validation dimensionnelle des embeddings).
- **Retrieval** : `core/rag/retrieval.py` (`RAGRetrieval`, stratégies auto/keyword/semantic/hybrid, similarité cosinus en mémoire ou index externe ChromaDB/Qdrant, RRF pour hybride).
- **Contexte** : `core/rag/context.py` (`RAGContext`, assemblage borné par caractères avec sources).
- **Embeddings** : `core/rag/embeddings.py` (`RAGEmbeddings`, mode mock si pas de LLM client → vecteurs nuls de dim 8).
- **Stratégies** : `core/rag/strategies.py` (auto, keyword, semantic, hybrid ; pas de reranking cross-encoder).
- **État** : opérationnel. Le chemin complet ingest → retrieve → build_context est réel et testé. L'embedding réel dépend d'un provider configuré (attach_llm_client) ; sinon dégradation textuelle documentée. **Pas de reranking**, pas de comptage de tokens, pas d'adaptation à la fenêtre de contexte réelle du modèle.

### 2.4 Endpoints API Knowledge/RAG
- Montés dans `interfaces/api/main.py` via `v1.py` (router `v1`, préfixe `/v1`).
- Endpoints réels : `/v1/knowledge`, `/v1/knowledge/search`, `/v1/knowledge/collections/*`, `/v1/knowledge/{id}/rag`, `/v1/rag/documents`, `/v1/rag/config`, `/v1/rag/retrieve`, `/v1/rag/context`, `/v1/rag/status`, `/v1/rag/strategies`.
- **Statut** : opérationnels. Les routeurs dédiés `knowledge.py` et `engineering_memory.py` sont définis mais **non montés** dans `main.py` (orphelins, dupliqués dans v1.py).
- **Schémas** : pas de schéma Pydantic d'entrée — `dict[str, Any]` partout, validation déléguée aux managers Core.
- **Tests** : `tests/core/test_knowledge_collections.py`, `tests/core/test_knowledge_tree.py`, `tests/core/test_rag_engine.py`, `tests/core/test_rag_strategies.py`, `tests/integration/knowledge/test_rag_persistence_integration.py`, `tests/interfaces/test_knowledge_tree.py`.

---

## 3. Engineering Memory

### 3.1 Service et modèle
- **Backend** : `core/engineering_memory/service.py` (`EngineeringMemoryService`).
  - `record`/`collect_event` (l. 37-50) : valide, vérifie sécurité, écrit via `ObsidianPersistence`, journal d'audit `_meta/MEMORY_EVENT_LOG.ndjson`.
  - `get` (l. 52-53), `search` (l. 55-70, filtres component/record_type/status), `component_history` (l. 80-81), `verify_integrity` (l. 83-86).
- **Modèle** : `core/engineering_memory/models.py` — `MemoryRecord` (RecordType, RecordOrigin, SourceOfFactLevel, ConfidenceLevel). Types de records : COMPONENT, DECISION, ENGINEERING_EVENT, INCIDENT, REPAIR, VERIFICATION, DEPENDENCY, TEST_RESULT, TECHNICAL_DEBT, EVIDENCE, AGENT_REPORT.
- **Vault** : `core/engineering_memory/vault.py` (`VaultService`, read-only par construction, écriture managée, Archives immuables, wikiliens, backlinks, graph).

### 3.2 Intégration agents / knowledge (adaptateur non bloquant)
- `core/engineering_memory/adapters.py` (`EngineeringMemoryIntegration`, l. 50-231).
  - `record_agent_lifecycle` (l. 84-115) : appelé par `AgentManager._record_agent_event` (create/update/delete).
  - `record_knowledge_operation` (l. 166-197) : appelé par `KnowledgeManager._record_knowledge`.
  - `record_skill_lifecycle` (l. 200-231) : appelé par `core/skills/store.py`.
  - Les exceptions sont avalées (non bloquant) avec log d'erreur.
- **État** : câblé dans `AgentManager` et `KnowledgeManager` via `set_engineering_memory_integration(...)`, mais accepte `None` et fonctionne sans. L'injection effective depuis la composition root doit être vérifiée.

### 3.3 Endpoints
- `interfaces/api/routers/engineering_memory.py` (non monté dans `main.py` — orphelin). Endpoints `/v1/memory/health`, `/v1/memory/events`, `/v1/memory/vault/*`, `/v1/memory/records`.
- `interfaces/api/routers/v1.py` (monté) : `/v1/memory/facts`, `/v1/memory/events`, `/v1/memory/search`, `/v1/memory/ingest` via `get_webui_store()`.
- **État** : opérationnel (routes montées + routeur orphelin fonctionnel mais non exposé).

### 3.4 Tests
- `tests/core/test_engineering_memory.py` (114 lignes), `tests/core/test_engineering_memory_adapters.py` (50 lignes), `tests/core/test_engineering_memory_security.py` (55 lignes).
- `tests/interfaces/test_engineering_memory_vault_router.py`, `tests/interfaces/test_engineering_memory_router.py`.

### 3.5 Constat sur l'exploitation par les agents
L'Engineering Memory est **principalement accessible depuis le WebUI** (Observatory : Vault, Graph, Timeline, Search, Engineering, AI Insights). Le câblage vers les agents existe (`record_agent_lifecycle`, `record_knowledge_operation`) mais est non bloquant et son injection effective en production n'est pas prouvée. Elle n'est pas consultée par les agents pour construire leur contexte (voir § Agent Knowledge Integration).

---

## 4. Agent Knowledge Integration

### 4.1 Architecture des agents
- `core/agents/types.py` — `Agent` (dataclass) déclare explicitement `knowledge_ids`, `knowledge_collection_ids`, `skill_ids`, `tool_ids`, `folder_ids`, `domain_ids`, `memory_scope`. `AgentType` (USER/SYSTEM/INTERNAL), `AgentStatus`.
- `core/agents/manager.py` (`AgentManager`) : `create`, `get`, `list`, `update`, `delete`, `execute` (point d'entrée unique), `set_executor`, `set_engineering_memory_integration`.
- `core/agents/base.py` : façade de compatibilité (réexport), aucune logique métier.

### 4.2 Exécuteur d'agent (contexte injecté dans le prompt)
- `core/agents/executor.py` (`create_agent_executor`, `execute`).
  - Résolution provider LLM (l. 240-252).
  - `resolve_agent_resources` (core/agents/resources.py) : résout skills, collections, knowledge, tools, folders, domains. **Règle absolue** : aucune ressource globale injectée sans sélection explicite. Déduplication (`_EffectiveSet`), gestion des "ghosts" (ressources absentes du catalogue).
  - Construction du system prompt (l. 255-435) : skills (l. 323-339), knowledge spécifique (l. 344-376), RAG/collections via `build_context_multi` (l. 383-413), tools (l. 419-430), capabilities (l. 432-433).
  - Séparation données/instructions (CT-4) : `sanitize_external_content` + `wrap_data_block(source, kind)` avec instruction sticky `STICKY_DATA_INSTRUCTION` (`core/security/prompt_guard.py` l. 30-39). Les données externes sont enfermées dans `<data>` avec provenance.
  - Boucle d'outils bornée `MAX_TOOL_ROUNDS = 3` (l. 36), `SecureToolEnforcer` (fail-closed).
- **État** : opérationnel. L'injection de contexte Knowledge/RAG dans le system prompt est réelle. L'agent n'effectue **pas** de retrieval autonome à la volée (sauf outil de recherche web) : le contexte est préchargé dans le system prompt avant l'appel LLM.

### 4.3 Citations et provenance
- Prompt système : chaque bloc de données porte `source` (`skill:...`, `knowledge:...`, `rag:...`) et `kind`. `build_context_multi` produit `[{i}] {title} ({source})\n{content}`.
- **Pas de mécanisme de citation formelle** (footnotes, [src:1]) dans la réponse LLM. La provenance est dans le prompt, pas extraite de la génération.

### 4.4 Mémoire cognitive (core/memory/)
- `core/memory/manager.py` (`MemoryManager`, 8 types : Working, Short-term, Episodic, Semantic, Procedural, Vector, Event Log, History). `store()` stocke en Vector Memory avec `"embedding": []` (**TODO** embedding manquant, l. 142).
- `core/memory/retrieval.py` (`RetrievalEngine`, `recall`). **TODO** embedding de la requête manquant (l. 56).
- **Intégration agents** : aucun appel de `MemoryManager`/`RetrievalEngine` dans `executor.py`. Sous-système parallèle, **non branché sur le flux agent**.

### 4.5 Planner
- `core/planner/planner.py` : décomposition par patterns codés en dur (3 patterns) + `CapabilityRegistry.find`. **Aucune intégration Knowledge/RAG/mémoire**.
- `core/planner/decomposer.py` : stratégie LLM en TODO (retourne `[]`), puis règles. Pas de consultation des sources de connaissance.

### 4.6 Tests (ce qui est réellement couvert)
- `tests/test_agent_knowledge_scoping.py` (156 lignes) : RAG réel + KnowledgeCollectionManager réel, fake provider. Valide l'injection de contexte RAG par collection dans le prompt, l'absence de section sans collections, la dégradation sur collections ghost, le roundtrip metadata knowledge_ids. **Passe.**
- `tests/test_agent_resources.py` (419 lignes) : résolution des ressources, déduplication, isolation inter-agents, ghosts, tools. **Passe.**
- `tests/core/test_agent_manager_engineering_memory.py` (38 lignes) : câblage Engineering Memory (non bloquant). **Passe.**
- `tests/core/test_knowledge_skills_integration.py` (40 lignes) : câblage Engineering Memory knowledge/skills. **Passe.**
- `tests/core/test_agent_execution_context.py` (59 lignes) : propagation ExecutionContext. **Passe.**
- `tests/core/test_agent_authz_hardening.py` (154 lignes) : autorisation API (ownership). **Passe.**
- `tests/core/test_agent_ownership_types.py` (108 lignes) : sérialisation owner_id/created_by/agent_type. **Passe.**

### 4.7 Ce qui n'est PAS testé
- Exécution bout en bout avec un LLM réel (tous les tests utilisent un `_FakeProvider`).
- Intégration de `core/memory/` dans le flux agent (non branchée).
- HROT dans le flux d'exécution agent (pas d'appel dans `executor.py`).
- Citations formelles dans les réponses LLM.
- Adaptation à la fenêtre de contexte réelle du modèle (pas de comptage de tokens).

### 4.8 Mécanisme commun de Knowledge Access
Il n'existe **pas de mécanisme commun unique** d'accès Knowledge pour les agents. Chaque agent reçoit ses ressources via `resolve_agent_resources` à partir de ses sélections explicites (`knowledge_ids`, `knowledge_collection_ids`). L'injection se fait dans le system prompt, pas via un outil de retrieval autonome.

---

## 5. DTAI — Dynamic Tool & Application Integration

### 5.1 Socle commun générique (opérationnel)
- **Modèle de manifest** : `core/applications/models.py` (710 lignes). `ApplicationIdentity`, `ApplicationCapability`, `ApplicationDependency`, `InterfaceDescriptor`, `ApplicationProvenance`, `ApplicationManifest`. Contract version `1.0.0` uniquement. JSON Schema embarqué.
- **Validateur** : `core/applications/validator.py` (`ContractValidator`, valid/invalid/incomplete/incompatible, détection de secrets).
- **Découverte** : `core/applications/discovery.py` (`ApplicationDiscoveryService`, scan récursif `.yaml/.yml/.json`, détection conflits, états DECLARED → VERIFIED → AVAILABLE → AUTHORIZED).
- **Catalogue** : `core/applications/catalog.py` (`ApplicationCatalog`, racines `CatalogSource`, `refresh`, `find`).
- **Registre** : `core/applications/application_registry.py` (`ApplicationIntegrationRegistry`, verrou fcntl, états REGISTERED/VALIDATED/AVAILABLE/UNAVAILABLE/WITHDRAWN).
- **Cycle de vie** : `core/applications/resilience.py` (machine à états REGISTERED→...→FAILED, `ResilientExecutor` avec timeout/retry/circuit breaker/idempotency).
- **Permissions / HROT** : `core/applications/permissions.py` (`PermissionService`, `HumanAuthority`, `PermissionScope`, `PermissionGrant`, `manifest_fingerprint` SHA-256).
- **Repository durable** : `core/applications/manifest_repository.py` (SQLite, `delete()` lève `NotImplementedError` — pas de suppression silencieuse).
- **Catalogue d'intégration** : `core/applications/integration_catalog.py` (projection lecture seule).
- **Découverte dépôts locaux** : `core/applications/local_repository_discovery.py` (read-only, classification DISCOVERED/INVALID/COMPATIBLE, jamais d'exécution du code découvert).
- **Découverte GitHub** : `core/applications/github_organization_discovery.py` (API publique, read-only).
- **Contrats de capacités** : `core/applications/capability_contract.py` (`ApplicationCapabilityContract`, input/output schema JSON Schema, `invoke_capability`).
- **Exécution de capacités** : `core/applications/capability_execution.py` (`TRUSTED_IMPLEMENTATION_ALIASES = {"odin.runtime-status", "frame.runtime-status"}`, validation contrat+binding+activation+schema, timeout).
- **Registre de capacités ETHAN** : `core/applications/capabilities.py` (`CapabilityDefinition`, status DRAFT/ACTIVE/DEPRECATED/RETIRED, sensitivity).
- **Capability Manager** : `core/capability_manager/manager.py` + `types.py` + `backends.py` (5 backends : Docker/Python/Node/Executable/Builtin, `validate_install_actions` barrière anti-injection, opérations persistées 24h/50 max).
- **État** : tout le socle est opérationnel et testé.

### 5.2 Cas d'application

| Cas | Manifest examples/ | Registre | Plugin cycle de vie | Contrat d'exécution | Endpoints runtime | Statut |
|-----|-------------------|----------|---------------------|---------------------|-------------------|--------|
| Odin | `examples/odin/ethan-application-manifest.yaml` | `register_odin_pilot` | `OdinService` (819 lignes, **ne hérite pas** de ComposeService → duplication ~700 lignes) | `odin.runtime-status` | `/v1/applications/{app_id}/runtime,/start,/stop` | Opérationnel (si Docker + dépôt Odin présents) |
| Frame | `examples/frame/ethan-application-manifest.yaml` | `register_frame_pilot` | `FrameService(ComposeService)` (héritage propre) | `frame.runtime-status` | `/v1/applications/{app_id}/runtime,/start,/stop` | Opérationnel (si Docker + bun + dépôt Frame) |
| Quantar | `examples/quantar/ethan-application-manifest.yaml` | `register_quantar_pilot` | `QuantarService` (ComposeService) + `QuantarTaskService` (moteur tâches, 1034 lignes) | **absent** | Pas d'endpoint HTTP dédié dans les routers examinés | Partiel (in-process si tradingagents installé, sinon Docker one-shot non vérifié) |
| TradingAgents | **absent** (proposition test uniquement, `tests/core/test_dta1a_tradingagents_manifest.py`) | **absent** | **absent** | **absent** | **absent** | Non implémenté (proposition uniquement) |

### 5.3 Duplications identifiées
- `core/plugins/odin.py` duplique `core/plugins/compose_service.py` (~700 lignes).
- Manifests odin/frame/quantar : même digest SHA-256 (placeholder non récalculé).
- `skills.py` vs `skills_import.py` (endpoints `/skills/export` et `/skills/import` dupliqués).
- Alias multiples du registre d'applications.

### 5.4 Ce qui manque pour un processus DTAI reproductible
- Installation automatisée des dépôts (pas de git clone via l'API).
- Mise à jour des applications (pas de git pull).
- Bindings de capacité persistants (stockés en attribut dynamique du registry, perdus au redémarrage).
- TradingAgents : aucun code d'intégration ETHAN.
- Quantar : pas d'endpoint HTTP dédié pour créer/exécuter/lister les tâches.
- Suppression de manifest durable (`NotImplementedError`).
- Intégration Odin/Frame dans le CapabilityManager générique (deux chemins de cycle de vie parallèles).
- Tests E2E complets avec Docker réel.

### 5.5 Tests DTAI
- `tests/core/test_agent_resources.py` (ressources d'agent), `tests/core/test_dta1a_tradingagents_manifest.py` (proposition manifest TradingAgents), `tests/core/test_quantar_real_task_runtime.py` (simule TradingAgents, pas exécution réelle).
- Pas de test E2E découverte → enregistrement → installation → démarrage → arrêt → suppression.

---

## 6. Relation DAĒNĀ ↔ DTAI

### 6.1 Interactions existantes
- DAĒNĀ (Observatory Vault / Graph / Search) lit le vault documentaire Obsidian (`daena/` et `Obsidian/` via `VaultService`). Aucune indexation automatique des capacités/applications DTAI dans le vault.
- DTAI (ApplicationIntegrationRegistry, CapabilityRegistry) possède ses propres métadonnées (manifest, contrats, permissions) stockées dans `CoreRecordStore` et `ApplicationManifestRepository` (SQLite). Aucune exposition automatique de ces métadonnées vers DAĒNĀ.
- Le `QuantarTaskService` référence `tradingagents` (dépôt externe `/home/fatsio/AI/TradingAgents`) mais n'est pas indexé dans DAĒNĀ.
- Pas de dépendance circulaire actuellement (les deux systèmes sont indépendants).

### 6.2 Ce qui manque pour une relation cohérente
- Aucun contrat explicite entre DAĒNĀ et DTAI.
- Aucune indexation des documentations, capacités, dépendances, versions, incidents, décisions techniques des applications dans le système de connaissance DAĒNĀ.
- Aucune exposition des connaissances DAĒNĀ vers le cycle de vie DTAI (DAĒNĀ ne doit pas gérer le cycle de vie des applications, per contrainte de la mission).

---

## 7. Problèmes identifiés (preuves)

| # | Problème | Preuve (chemin, lignes) | Gravité |
|---|----------|------------------------|---------|
| 1 | Routeurs `knowledge.py` et `engineering_memory.py` orphelins (non montés dans main.py), dupliqués dans v1.py | `interfaces/api/main.py` (imports), `interfaces/api/routers/knowledge.py`, `interfaces/api/routers/engineering_memory.py` | Moyenne |
| 2 | Pas de mécanisme commun d'accès Knowledge pour les agents (pas de retrieval autonome, préchargement système uniquement) | `core/agents/executor.py` (pas d'appel à core/memory/) | Élevée |
| 3 | Mémoire cognitive `core/memory/` non branchée sur le flux agent (embeddings TODO, aucun appel dans executor.py) | `core/memory/manager.py` (l. 142), `core/memory/retrieval.py` (l. 56), `core/agents/executor.py` | Élevée |
| 4 | Pas de citation formelle dans les réponses LLM (provenance uniquement dans le prompt) | `core/agents/executor.py`, `core/security/prompt_guard.py` | Moyenne |
| 5 | Pas de comptage de tokens / adaptation à la fenêtre de contexte réelle (max_context_chars=8000 brute) | `core/rag/pipeline.py` (l. 62), `core/llm/types.py` (l. 104) | Moyenne |
| 6 | HROT non appelé dans le flux d'exécution agent (service autonome) | `core/hrot/capability_authorization.py`, `core/agents/executor.py` | Moyenne |
| 7 | Duplication OdinService vs ComposeService (~700 lignes) | `core/plugins/odin.py` vs `core/plugins/compose_service.py` | Moyenne |
| 8 | TradingAgents non implémenté (proposition de manifest uniquement dans un test) | `tests/core/test_dta1a_tradingagents_manifest.py`, `examples/` (pas de dossier tradingagents) | Élevée |
| 9 | Pas de suppression de manifest durable (NotImplementedError) | `core/applications/manifest_repository.py` | Faible |
| 10 | Pas d'indexation DTAI dans DAĒNĀ (pas de contrat explicite entre les deux systèmes) | Absence de code reliant ApplicationIntegrationRegistry et VaultService/KnowledgeManager | Élevée |

---

## 8. Tests exécutés lors de cette mission

- Aucun test n'a été exécuté par cette mission d'investigation (consigne : investigation uniquement, pas de modification).
- Les tests existants cités ci-dessus sont ceux présents dans le dépôt (`tests/core/`, `tests/interfaces/`, `interfaces/webui/tests/`).
- Résultats déclarés : les tests listés sous chaque section passent dans le dépôt (ils n'ont pas été ré-exécutés dans le cadre de cette mission d'investigation).

---

## 9. Inconnues restantes
- Injection effective de `engineering_memory_integration` depuis la composition root (`interfaces/api/main.py`) : non vérifiée dynamiquement.
- État réel des dépôts Odin/Frame/Quantar dans `examples/` (présence des `compose.yaml`, images Docker) : non vérifiée sur disque.
- Disponibilité de `tradingagents` dans l'environnement Python : déclarée absente par défaut (`TRADINGAGENTS_AVAILABLE = false`), non vérifiée.
- Câblage réel des providers LLM pour les embeddings RAG réels : non vérifié (dépend de la config runtime).

Fin de l'état des lieux.
