# DAĒNĀ — Audit global d'architecture et de capacités

**Projet** : ETHAN OS  
**Dépôt** : `/home/fatsio/AI/Ethan`  
**Branche** : `refactor/ethan-rebuild-p0`  
**Date de l'audit** : 2026-11-11  
**Rapport** : `docs/memory/DAENA_GLOBAL_ARCHITECTURE_AUDIT.md`  
**Nature** : audit en lecture seule — aucune modification de code, aucune migration, aucun commit.

---

## 0. Périmètre et méthode

Cet audit examine DAĒNĀ comme capacité centrale de connaissance, de mémoire technique et de compréhension exploitable par les agents ETHAN. Il ne s'agit pas d'un simple visualiseur Markdown ni d'un système RAG isolé.

Sources croisées :

- documents d'architecture et ADR : `daena/Knowledge/Architecture/DAENA_KNOWLEDGE_INTELLIGENCE.md`, `ETHAN_ENGINEERING_MEMORY_ARCHITECTURE.md`, `MEMORY_DATA_MODEL.md`, `ECOSYSTEM_SHARED_INTELLIGENCE_ARCHITECTURE.md`, `EM-SERVICE-ARCHITECTURE.md`, `RECORD_TEMPLATES.md` ;
- mémoire opérationnelle : `docs/memory/PROJECT_STATE.md`, `docs/memory/DECISIONS.md`, `docs/memory/assessments/daena-dtai/*` ;
- code réel : `core/knowledge/`, `core/rag/`, `core/engineering_memory/`, `core/search/`, `core/agents/`, `core/cognition/memory/`, `core/memory/` ;
- API : `interfaces/api/main.py`, `interfaces/api/routers/v1.py`, `interfaces/api/routers/knowledge.py`, `interfaces/api/routers/knowledge_imports.py`, `interfaces/api/routers/engineering_memory.py` ;
- interfaces : WebUI Observatory (`interfaces/webui/src/components/features/observatory/`), CLI (`interfaces/cli/commands/knowledge.py`, `memory.py`) ;
- tests présents dans le dépôt (non ré-exécutés dans ce rapport ; inventaire et couverture documentés).

Règle appliquée : le code et l'état réel du système priment sur toute documentation historique obsolète. Les intentions non implémentées sont signalées comme telles.

---

## 1. Architecture existante

### 1.1 Vue d'ensemble

DAĒNĀ est déjà présent dans le dépôt sous forme d'un ensemble de capacités Core, non d'une application isolée. La séparation Core / Runtime / Interfaces est respectée : les interfaces (WebUI, CLI) ne contiennent pas de logique métier ; elles appellent les managers Core via l'API HTTP.

Composants principaux :

- **Knowledge Base** : `core/knowledge/manager.py` (`KnowledgeManager`), `core/knowledge/collections.py` (`KnowledgeCollectionManager`), `core/knowledge/types.py`, `core/knowledge/imports.py`, `core/knowledge/web_ingest.py`, `core/knowledge/web_search.py`, `core/knowledge/web_research_service.py`, `core/knowledge/web_inspiration.py` ;
- **RAG** : `core/rag/pipeline.py` (`RAGPipeline`), `core/rag/ingestion.py`, `core/rag/retrieval.py`, `core/rag/context.py`, `core/rag/embeddings.py`, `core/rag/strategies.py`, `core/rag/vector_store.py`, `core/rag/extractors.py`, `core/rag/extract.py` ;
- **Engineering Memory** : `core/engineering_memory/service.py` (`EngineeringMemoryService`), `models.py`, `registry.py`, `persistence.py`, `security.py`, `validators.py`, `adapters.py`, `vault.py` (`VaultService`) ;
- **Search unifié** : `core/search/__init__.py` (`SearchManager`) ;
- **Intégration agents** : `core/agents/executor.py`, `core/agents/resources.py`, `core/agents/types.py` ;
- **Mémoire cognitive** : `core/cognition/memory/manager.py` (`MemoryManager`), `core/memory/*` ;
- **API** : `interfaces/api/routers/v1.py` (canonique, monté), `interfaces/api/routers/knowledge.py` (orphelin, non monté), `interfaces/api/routers/knowledge_imports.py` (monté), `interfaces/api/routers/engineering_memory.py` (monté) ;
- **Interfaces** : WebUI Observatory (8 espaces), CLI `knowledge`/`memory` ;
- **Stockage documentaire** : `daena/` (archives, knowledge synthétisée, mémoire opérationnelle), `Obsidian/` (racine vault Engineering Memory).

### 1.2 Couches conceptuelles (selon `DAENA_KNOWLEDGE_INTELLIGENCE.md`)

1. DAĒNĀ — environnement Knowledge & Engineering Memory.
2. Knowledge Base — nœuds, collections, documents, ADR.
3. Engineering Memory — composants, historique, relations, provenance, audit.
4. RAG Pipeline — ingestion, embeddings, retrieval, contexte.
5. Knowledge Intelligence — synthèses, relations, insights, contextualisation.
6. Knowledge Access Interface — API, MCP, retrieval, provenance, permissions.
7. Consumers — agents ETHAN, OpenCode, Cline, WebUI, CLI.

Le RAG est une capacité interne de DAĒNĀ, pas l'ensemble de DAĒNĀ. La Knowledge Base est distincte du moteur de retrieval.

### 1.3 Propriétaires architecturaux

| Capacité | Propriétaire | Emplacement |
|---|---|---|
| Nœuds de connaissance | Core | `core/knowledge/manager.py` |
| Collections RAG + contrôle d'accès | Core | `core/knowledge/collections.py` |
| Import de fichiers/dossiers | Core | `core/knowledge/imports.py` |
| Web ingestion/recherche/research | Core | `core/knowledge/web_*.py` |
| RAG pipeline | Core | `core/rag/*.py` |
| Engineering Memory records | Core | `core/engineering_memory/service.py` |
| Vault (lecture/écriture managée) | Core | `core/engineering_memory/vault.py` |
| Search unifié | Core | `core/search/__init__.py` |
| Accès agents aux connaissances | Core (agents) | `core/agents/executor.py`, `core/agents/resources.py` |
| Mémoire cognitive | Core | `core/cognition/memory/manager.py`, `core/memory/*` |
| API HTTP | Interface (passerelle mince) | `interfaces/api/routers/*` |
| Affichage/exploration | Interface | `interfaces/webui/.../observatory/`, CLI |

---

## 2. Cartographie des composants

| Composant | Fichier principal | Rôle | État |
|---|---|---|---|
| `KnowledgeManager` | `core/knowledge/manager.py` | Nœuds, sources, relations, recherche textuelle, ingestion vers RAG | Implémenté |
| `KnowledgeCollectionManager` | `core/knowledge/collections.py` | Collections, grants, tree, retrieve/retrieve_multi, build_context, reindex | Implémenté |
| `KnowledgeImportManager` | `core/knowledge/imports.py` | Import fichiers/dossiers, jobs, validation MIME/taille, FileStore | Implémenté |
| `WebIngestionManager` | `core/knowledge/web_ingest.py` | Web → knowledge pipeline | Implémenté |
| `WebSearchManager` | `core/knowledge/web_search.py` | Recherche web | Implémenté |
| `WebResearchService` | `core/knowledge/web_research_service.py` | Recherche → knowledge | Implémenté |
| `WebInspirationEngine` | `core/knowledge/web_inspiration.py` | Inspiration web | Implémenté |
| `RAGPipeline` | `core/rag/pipeline.py` | Ingestion, chunking, embeddings, retrieval, contexte | Implémenté |
| `RAGIngestion` | `core/rag/ingestion.py` | Découpage et préparation | Implémenté |
| `RAGRetrieval` | `core/rag/retrieval.py` | Recherche de chunks | Implémenté |
| `RAGEmbeddings` | `core/rag/embeddings.py` | Embeddings (textuel par défaut, LLM si client) | Implémenté |
| `VectorStore` | `core/rag/vector_store.py` | Backends mémoire/chromadb/qdrant | Implémenté (optionnels) |
| `SearchManager` | `core/search/__init__.py` | Search unifié 4 types | Implémenté |
| `EngineeringMemoryService` | `core/engineering_memory/service.py` | Records, historique, audit log | Implémenté |
| `VaultService` | `core/engineering_memory/vault.py` | Vault read-only + écriture managée, wikiliens, backlinks, graph, search | Implémenté |
| `MemoryManager` (cognition) | `core/cognition/memory/manager.py` | Mémoire multi-niveaux, outcomes, procédures | Implémenté (non branché) |
| `Agent executor` | `core/agents/executor.py` | Injection RAG/knowledge/skills, tools, CT-4 | Implémenté |
| `resolve_agent_resources` | `core/agents/resources.py` | Résolution effective, déduplication, ghosts | Implémenté |
| `CapabilityAuthorizationService` | `core/hrot/capability_authorization.py` | Autorisation HROT | Implémenté (durci P0-1S) |
| `Vault` WebUI | `interfaces/webui/.../observatory` | 8 espaces | 6 opérationnels |
| CLI `knowledge` | `interfaces/cli/commands/knowledge.py` | Client API | Implémenté |
| Router `v1.py` | `interfaces/api/routers/v1.py` | Canonique, monté | Monté |
| Router `knowledge.py` | `interfaces/api/routers/knowledge.py` | Orphelin, non monté, doublon partiel | Non monté |
| Router `engineering_memory.py` | `interfaces/api/routers/engineering_memory.py` | Monté | Monté |
| Router `knowledge_imports.py` | `interfaces/api/routers/knowledge_imports.py` | Monté | Monté |

---

## 3. Capacités fonctionnelles

### 3.1 États normalisés

Pour chaque capacité, l'état est l'un de : **Fonctionnel et vérifié**, **Implémenté mais non vérifié**, **Partiellement implémenté**, **Absent**, **Bloqué par une dépendance**.

### 3.2 Tableau de synthèse

| Capacité | État | Preuve / limitation |
|---|---|---|
| CRUD nœuds Knowledge | Implémenté mais non vérifié bout-en-bout | `manager.py` complet ; tests unitaires présents mais pas E2E API |
| Relations entre nœuds (`connect`) | Implémenté mais non vérifié | `manager.py:connect` ; pas de test dédié visible |
| Recherche textuelle Knowledge | Implémenté mais non vérifié | `manager.py:search` ; `tests/test_*` partiels |
| Collections RAG + contrôle d'accès | Implémenté mais non vérifié E2E | `collections.py` complet ; 4 tests (`test_knowledge_collections.py`) |
| Arborescence de collections (`list_tree`) | Implémenté mais non vérifié | 5 tests (`test_knowledge_tree.py`) |
| Import fichiers/dossiers | Implémenté mais non vérifié E2E | 7 tests (`test_knowledge_imports.py`) |
| Web ingestion / recherche / research | Implémenté mais non vérifié | routes et managers présents ; tests `test_web_ingest.py`, `test_web_research_service.py`, `test_web_inspiration.py` |
| RAG ingestion / chunking | Implémenté mais non vérifié E2E | `ingestion.py` ; tests `test_rag_engine.py` (9) |
| RAG retrieval keyword/semantic/hybrid | Implémenté mais non vérifié E2E | `retrieval.py`, `strategies.py` ; 11 tests (`test_rag_strategies.py`) |
| RAG contexte borné avec sources | Implémenté mais non vérifié E2E | `context.py`, `pipeline.py:build_context` |
| Embeddings | Implémenté mais non vérifié | mode textuel par défaut ; LLM si client configuré |
| Vector store (chromadb/qdrant) | Partiellement implémenté | backends optionnels ; mémoire par défaut |
| Search unifié 4 types | Implémenté mais non vérifié | `core/search/__init__.py` ; `tests/test_search.py` |
| Engineering Memory records | Implémenté mais non vérifié E2E | 5 tests (`test_engineering_memory.py`) |
| Vault read-only + écriture managée | Implémenté mais non vérifié E2E | 15 tests (`test_engineering_memory_vault.py`) |
| Wikiliens / backlinks / graph | Implémenté mais non vérifié E2E | `vault.py:graph`, `backlinks`, `resolve_wikilink` |
| Agent executor (injection RAG/knowledge/skills) | Implémenté mais non vérifié avec LLM réel | `executor.py` ; tests avec `_FakeProvider` uniquement |
| Résolution effective des ressources agent | Implémenté mais non vérifié E2E | `resources.py` ; `test_agent_resources.py`, `test_agent_knowledge_scoping.py` |
| Autorisation HROT dans exécution capacité | Fonctionnel et vérifié (P0-1S) | 75 tests passés ; fail-closed |
| Mémoire cognitive branchée aux agents | Absent | `core/cognition/memory/manager.py` non appelé dans `executor.py` |
| Citations formelles dans réponses LLM | Absent | aucune extraction de footnote `[src:n]` |
| Comptage de tokens / fenêtre de contexte | Absent | `max_context_chars=8000` brut ; `ModelInfo.context_length` inutilisé |
| Accès OpenCode à DAĒNĀ via API/MCP | Non démontré | aucune route knowledge montée ; pas de serveur MCP dédié |
| Accès Cline à DAĒNĀ | Absent (connecteur d'archivage uniquement) | `core/knowledge/agent_traces/cline_connector.py` |
| Serveur MCP dédié DAĒNĀ | Absent | aucun serveur dans `mcp-servers.json` |
| Contrat DAĒNĀ ↔ DTAI | Absent | systèmes indépendants |
| AI Insights (synthèses agents, RPT-*) | Partiellement implémenté | WebUI opérationnel (lecture) ; dépend du vault et des records ; synthèses absentes par défaut |
| Graphe de connaissances (wikilinks) | Implémenté mais non vérifié E2E | `vault.py:graph` ; WebUI Graph (SVG maison) |
| Provenance sur documents/chunks | Implémenté mais non vérifié E2E | `document_source`, `document_title`, `source` présents |
| Persistance durable des grants HROT | Bloqué par dépendance | `ApplicationStateStore` requis ; mémoire par défaut |
| Piste d'audit durable | Bloqué par dépendance | `store` ou `EventCollector` requis |

---

## 4. État du Knowledge et du RAG

### 4.1 Knowledge (Knowledge Base)

- `KnowledgeManager` : CRUD, recherche textuelle déterministe, relations (`connect`), ingestion vers RAG (`ingest_into_rag`), événements bus, intégration Engineering Memory (non bloquante). Stockage via `CoreRecordStore`.
- `KnowledgeCollectionManager` : collections avec contrôle d'accès (owner, admin, grants user/groupe), arborescence, stratégie de retrieval par collection, retrieve/retrieve_multi, build_context/build_context_multi, reindex. Très développé.
- `KnowledgeImportManager` : import fichiers/dossiers, validation MIME/taille, FileStore, jobs asynchrones, erreurs isolées par fichier. Très développé.
- Web : ingestion, recherche, research, inspiration — pipelines Core.

Limitations :

- `KnowledgeManager.search()` est une recherche textuelle par termes (pas sémantique). La recherche sémantique est déléguée au RAG.
- Les routes `knowledge.py` (extrait) sont orphelines : écrites mais non montées dans `main.py`. Le canonique monté est `v1.py` (qui duplique partiellement les mêmes routes).
- Aucun test E2E API pour Knowledge (les tests sont unitaires Core).

### 4.2 RAG (Retrieval-Augmented Generation)

- `RAGPipeline` : ingestion, chunking (stratégies), embeddings, retrieval (keyword/semantic/hybrid RRF), `build_context()` avec attribution de source, `build_messages()`.
- `RAGIngestion` : découpage et préparation.
- `RAGRetrieval` : recherche de chunks pertinents.
- `RAGEmbeddings` : mode textuel par défaut, LLM si client configuré.
- `VectorStore` : mémoire par défaut, chromadb/qdrant optionnels.
- `strategies.py` : normalisation/validation des stratégies.

Limitations :

- Borne à `max_context_chars=8000` caractères bruts ; pas d'adaptation à la fenêtre de contexte du modèle (`ModelInfo.context_length` déclaratif et inutilisé).
- Pas de citation formelle extraite de la réponse générée (provenance portée dans le prompt uniquement).
- Pas de test avec LLM réel (tests avec `_FakeProvider`).

### 4.3 Parcours document complet (avec ruptures)

1. Upload bytes → WebUI → API `knowledge_imports` (monté) → `KnowledgeImportManager` (Core).
2. Validation MIME/taille → `FileStore` (root-local) → extraction → `RAGIngestion.ingest` → `Collection.add_document`.
3. Retrieval → `RAGPipeline.retrieve` → chunks scorés → `build_context` / `build_context_multi`.
4. Injection dans le prompt agent → `executor.py` (sanitization + balise `<data>` + provenance).

Ruptures identifiées (selon `KNOWLEDGE_RAG_ASSESSMENT.md`) :

- La mémoire cognitive `core/memory/` n'est pas branchée sur le flux agent.
- Pas de citation formelle.
- Pas de comptage de tokens.
- La route Knowledge canonique est dupliquée (`v1.py` + `knowledge.py` orphelin).

---

## 5. Engineering Memory

### 5.1 Rôle

Mémoire technique d'ETHAN : historique des composants, relations, provenance, audit log. Distinct de la Knowledge Base générale. Écriture principale dans `Obsidian/` (fichiers Markdown/YAML).

### 5.2 Composants

- `EngineeringMemoryService` : validation, enregistrement, recherche, intégrité, audit log NDJSON.
- `MemoryRecord` : enveloppe canonique (types, statuts, provenance, confiance, composants, evidence_refs, authors, origin).
- `EngineeringMemoryRegistry` : destinations par type (relative_directory, schema, statuses, naming, required_fields).
- `ObsidianPersistence` : lecture/écriture dans le vault.
- `SecurityPolicy` : validation sécurité.
- `MemoryRecordValidator` : validation.
- `VaultService` : browse/search/graph/backlinks/wikilinks, lecture, écriture managée (Archives/ immutables), path safety.

### 5.3 État

- Implémenté et partiellement vérifié (5 tests service, 15 tests vault, 4+7 tests routers).
- Vault accessible via API (Engineering Memory router monté).
- Intégration avec `KnowledgeManager` : `_record_knowledge` non bloquant, appelle `record_knowledge_operation` si disponible.
- Les archives (`Archives/`) sont immutables depuis l'interface (par construction).

### 5.4 Limitations

- Persistance durable des grants HROT : mémoire par défaut (`PermissionService`), grants volatils au redémarrage sans `ApplicationStateStore`.
- Piste d'audit durable : en mémoire uniquement sans `store`/`EventCollector`.
- L'injection effective de `engineering_memory_integration` depuis la composition root n'est pas prouvée dynamiquement (hypothèse).

---

## 6. Intégration des agents

### 6.1 Mécanisme

- Chaque agent déclare `knowledge_ids` (nœuds) et `knowledge_collection_ids` (collections RAG), plus `domain_ids`, `folder_ids`, `skill_ids`, `tool_ids`.
- `resolve_agent_resources` (Core) résout l'ensemble effectif : déduplication par identité, sources de provenance (`explicit` ou `folder:<id>`), ghosts pour les ressources disparues.
- `executor.py` injecte :
  - le contenu des nœuds autorisés comme données sanitizées (balise `<data>` + provenance) ;
  - le contexte RAG scopé sur les collections autorisées (sanitized) ;
  - les skills, tools, capabilities.
- CT-4 : séparation données/instructions (sanitization + balise `<data>`).

### 6.2 État

- Implémenté mais non vérifié avec un LLM réel (tests avec `_FakeProvider` uniquement).
- Autorisation HROT : intégrée dans le cycle d'exécution des capacités applicatives (P0-1S, 75 tests passés, fail-closed).
- Pas de retrieval autonome à la volée : le RAG est injecté une fois dans le system prompt, pas consulté dynamiquement pendant l'exécution.

### 6.3 Limitations

- Mémoire cognitive `core/memory/` et `core/cognition/memory/` non branchées sur le flux agent (embeddings TODO, aucun appel dans `executor.py`).
- Pas de citation formelle extraite de la réponse.
- Pas de comptage de tokens / adaptation à la fenêtre de contexte.
- Pas de serveur MCP dédié à DAĒNĀ pour les agents externes (OpenCode, Cline).

---

## 7. Graphe et provenance

### 7.1 Graphe

- `KnowledgeManager.connect()` : relations dirigées entre nœuds (relation_type, strength, metadata).
- `VaultService.graph()` : graphe de wikiliens `[[...]]` entre documents Markdown, borné (limit_nodes=150), priorité aux documents porteurs de liens, archives en dernier.
- WebUI : espace Graph (SVG maison) sur le vault ; Canvas (arrangement local) ; Timeline.

### 7.2 Provenance

- Chaque `KnowledgeNode` porte `source`, `metadata`, `created_at`, `updated_at`.
- Chaque document RAG porte `document_title`, `document_source`, `chunk` avec `content`.
- Chaque chunk récupéré porte `score`.
- Chaque `MemoryRecord` porte `source_of_fact`, `provenance_level`, `origin`, `confidence`, `evidence_refs`, `authors`.
- AI Insights : distinction explicite entre synthèses d'agents (non vérifiées) et rapports RPT-* (PROVISIONAL → REVIEWED → VALIDATED).

### 7.3 Limitations

- Le graphe de connaissance (`KnowledgeManager.connect`) et le graphe de wikiliens (`VaultService.graph`) sont deux systèmes distincts, non fusionnés.
- Pas de détection automatique de contradictions documentaires.
- Pas de graphe de dépendances composants unifié (Engineering Memory records vs Knowledge nodes).

---

## 8. AI Insights

### 8.1 État

- WebUI : espace AI Insights opérationnel en lecture : liste les synthèses d'agents sous `Knowledge/Syntheses/by-agent/` et les rapports RPT-* de l'Engineering Memory.
- Provenance explicite : synthèses d'agents marquées « non vérifiées », rapports avec statut PROVISIONAL → REVIEWED → VALIDATED (promotion requiert relecture humaine).
- Aucune synthèse d'agent n'est indexée par défaut (dossier vide) ; les archives existent mais aucune synthèse n'est produite automatiquement.

### 8.2 Limitations

- Pas de génération automatique d'insights (synthèses) depuis les données.
- Pas de détection de contradictions ou d'obsolescence automatisée.
- Dépend du vault (Obsidian root) et des records Engineering Memory.

---

## 9. API et contrats

### 9.1 Routes montées

- `v1_router` (`interfaces/api/routers/v1.py`) : monté (ligne 1214), canonique. Contient les routes Knowledge (nodes, collections, documents, retrieve, reindex, connect, imports status) et de nombreux autres domaines.
- `knowledge_imports_router` : monté (ligne 1207).
- `engineering_memory_router` : monté (ligne 1240).

### 9.2 Routeurs orphelins

- `interfaces/api/routers/knowledge.py` : écrit, expose `set_knowledge_manager`/`set_knowledge_collections`, mais **non monté** dans `main.py`. Doublon partiel des routes de `v1.py`. Incohérence à consolider.

### 9.3 Contrats

- Authentification : `current_user_id`, `resolve_user_scope` (JWT), isolation par utilisateur.
- Contrôle d'accès collections : owner, admin, grants user/groupe (read/write).
- HROT : `verify_trusted_principal()` (HMAC-SHA256) appliqué dans `CapabilityAuthorizationService._evaluate()` avant autorisation.
- Manifestes applicatifs : `core/applications/` (MEM-014, version de contrat `1.0.0`).
- API Knowledge CLI : contrat documenté dans `docs/specs/CLI_CONTRACT.md §8.6`.

### 9.4 Limitations

- Pas de serveur MCP dédié à DAĒNĀ.
- Pas de contrat explicite DAĒNĀ ↔ DTAI (métadonnées canoniques, événements, synchronisation).
- Pas de suppression durable de manifest (`NotImplementedError`).

---

## 10. Tests et validations réelles

### 10.1 Inventaire (non ré-exécutés dans cet audit)

| Fichier | Tests | Cible |
|---|---|---|
| `tests/test_knowledge_collections.py` | 4 | collections RAG |
| `tests/test_knowledge_imports.py` | 7 | import fichiers/dossiers |
| `tests/test_knowledge_tree.py` | 5 | arborescence collections |
| `tests/test_rag_engine.py` | 9 | moteur RAG |
| `tests/test_rag_strategies.py` | 11 | stratégies retrieval |
| `tests/test_agent_knowledge_scoping.py` | 4 | scoping knowledge agent |
| `tests/core/test_knowledge_skills_integration.py` | 2 | intégration knowledge/skills |
| `tests/core/test_engineering_memory.py` | 5 | service Engineering Memory |
| `tests/core/test_engineering_memory_vault.py` | 15 | vault |
| `tests/interfaces/test_engineering_memory_router.py` | 4 | router EM |
| `tests/interfaces/test_engineering_memory_vault_router.py` | 7 | router vault |
| `tests/interfaces/test_application_capability_execution_p01s.py` | 17 | HROT durci (P0-1S) |
| `tests/core/test_agent_resources.py` | ? | résolution ressources agent |
| `tests/test_search.py` | ? | search unifié |
| `tests/test_web_ingest.py`, `test_web_research_service.py`, `test_web_inspiration.py` | ? | web pipelines |
| WebUI : `interfaces/webui/tests/unit/knowledge/knowledge-hub-library-tab.test.tsx` | 1 | knowledge hub |

### 10.2 Couverture

- Les tests couvrent bien le cœur opérationnel : scoping RAG par collection, résolution des ressources d'agent, injection dans le prompt, contrôle d'accès API (ownership), câblage Engineering Memory (non bloquant), persistance RAG, stratégies RAG, vault.
- Non testés : exécution bout-en-bout avec LLM réel (tests avec `_FakeProvider`), intégration `core/memory/` dans le flux agent, citations formelles, adaptation à la fenêtre de contexte, tests E2E DTAI avec Docker réel, accès OpenCode/Cline à DAĒNĀ.

### 10.3 Validations réelles documentées

- Typecheck WebUI, eslint (0 warning), 421 tests WebUI, build Next OK (8 routes prérendues) — session Observatory (2026-11-10).
- Smoke read-only réel sur le vault : tree 0,06 s, graph 155 nœuds / 10 arêtes.
- P0-1S : 75 tests passés (58 existants + 17 nouveaux), aucun test régressé.

---

## 11. Duplications et incohérences

1. **Routeurs Knowledge dupliqués** : `interfaces/api/routers/v1.py` (monté, canonique) et `interfaces/api/routers/knowledge.py` (orphelin, non monté) exposent des routes similaires. Incohérence à consolider (P3).
2. **Graphe double** : `KnowledgeManager.connect()` (graphe de nœuds) et `VaultService.graph()` (wikiliens de documents) sont deux systèmes distincts, non fusionnés.
3. **Mémoire double** : `core/cognition/memory/manager.py` (MemoryManager multi-niveaux) et `core/memory/*` sont présents mais non branchés aux agents. La mémoire cognitive est implémentée mais non intégrée.
4. **Plugins dupliqués** : `core/plugins/odin.py` vs `core/plugins/compose_service.py` (~700 lignes de duplication) — consolidation à faire (P3).
5. **Knowledge nodes vs Engineering Memory records** : deux modèles de connaissance distincts (nœuds vs records) sans lien formel.
6. **Stratégie de retrieval** : résolution par collection + stratégie globale (`rag-config`) ; complexité de résolution (auto/keyword/semantic/hybrid) — bien documentée mais à valider E2E.

---

## 12. Blocages

| Blocage | Dépendance | Impact |
|---|---|---|
| Persistance durable des grants HROT | `ApplicationStateStore` | Grants volatils au redémarrage |
| Piste d'audit durable | `store` ou `EventCollector` | Audit en mémoire uniquement |
| Accès OpenCode/Cline à DAĒNĀ | Route Knowledge montée + serveur MCP dédié | Non disponible actuellement |
| Intégration mémoire cognitive aux agents | Branchement dans `executor.py` + embeddings | Absent |
| Contrat DAĒNĀ ↔ DTAI | Métadonnées canoniques, événements, synchronisation | Absent |
| Vector store avancé | chromadb/qdrant optionnels | Mémoire par défaut (limité en volume) |
| Synthèses d'agents automatiques | Génération + indexation dans vault | Absent par défaut |

---

## 13. Recommandations priorisées

### P0 — Sécurité et accès unifié (critique)

1. **P0-1** (implémenté, P0-1S) : autorisation HROT dans le cycle d'exécution des capacités applicatives — fail-closed, 75 tests passés.
2. **P0-1P** : persistance durable des autorisations HROT et de la piste d'audit (`ApplicationStateStore`, `store`/`EventCollector`) — diagnostic terminé, implémentation en attente des conditions C1-C5.

### P1 — Intelligence opérationnelle de DAĒNĀ (haute)

3. **P1-0** : audit de sécurité et d'intégration de l'accès Knowledge (planifié, après P0-1P).
4. **P1-1** : récupération Knowledge/RAG par les agents sous autorisation P0 (retrieval à la volée, citations formelles, comptage de tokens / adaptation à la fenêtre de contexte).
5. **P1-2** : branchement de la mémoire cognitive (`core/memory/`, `core/cognition/memory/`) dans le flux agent.
6. **P1-3** : serveur MCP dédié à DAĒNĀ pour l'accès OpenCode/Cline.

### P2 — Intégration DAĒNĀ ↔ DTAI (haute)

7. **P2-1** : contrats de métadonnées canoniques (lecture seule).
8. **P2-2** : stratégie d'événements et synchronisation.
9. **P2-3** : clarification de propriété des entités et prévention des dépendances circulaires.

### P3 — Consolidation (consolidation)

10. **P3-1** : consolidation des routeurs Knowledge orphelins (identification du canonique, migration des routes manquantes).
11. **P3-2** : fusion des graphes (Knowledge nodes + wikiliens) ou exposition unifiée.
12. **P3-3** : consolidation des plugins Odin/Frame/Quantar.
13. **P3-4** : détection de contradictions et d'obsolescence documentaires.
14. **P3-5** : génération automatique de synthèses d'agents (AI Insights).

---

## 14. Architecture cible argumentée (proposition, non implémentée)

### 14.1 Principes directeurs

1. **DAĒNĀ est une plateforme de Knowledge Intelligence intégrant un RAG**, pas un simple RAG avec interface. Le RAG reste une capacité interne.
2. **La Knowledge Base est distincte du moteur de retrieval** : stockage (nœuds, collections) et retrieval (RAG pipeline) sont des responsabilités séparées.
3. **L'Engineering Memory conserve son rôle spécifique** : historique technique, composants, relations, provenance, audit.
4. **Les consommateurs partagent les mêmes interfaces de connaissance** : agents ETHAN, OpenCode, Cline, WebUI, CLI utilisent la même interface canonique.
5. **Aucune duplication** : un seul index RAG, un seul registre de collections, un seul service de provenance.
6. **Permissions et provenance obligatoires** : RBAC, HROT, provenance sur chaque document récupéré.
7. **Le code et l'état réel priment** sur la documentation historique.

### 14.2 Architecture cible

```
                    Consommateurs
        ┌─────────────────────────────────┐
        │ Agents ETHAN · OpenCode · Cline │
        │ WebUI · CLI · API externes      │
        └─────────────┬───────────────────┘
                      │ Interface canonique commune
                      ▼
┌─────────────────────────────────────────────────────────────┐
│         Knowledge Access Interface (canonique)             │
│   API HTTP montée · MCP DAĒNĀ · retrieval · provenance    │
│   permissions · HROT · RBAC · citations · token budget     │
└──────┬──────────────────────────────┬───────────────────────┘
       │                              │
       ▼                              ▼
┌──────────────────┐        ┌──────────────────────┐
│ Knowledge        │        │ RAG Pipeline         │
│ Intelligence     │        │ ingestion · embed    │
│ synthèses ·      │        │ retrieval · context  │
│ relations ·      │        │ citations · tokens   │
│ insights ·       │        └──────────┬───────────┘
│ contradictions   │                   │
└──────┬───────────┘                   │
       │                              │
       ▼                              ▼
┌──────────────────┐        ┌──────────────────────┐
│ Knowledge Base   │        │ Engineering Memory   │
│ nœuds · coll.    │        │ composants · hist.   │
│ documents · ADR  │        │ relations · graph    │
│ provenance       │        │ audit · vault        │
└──────┬───────────┘        └──────────┬───────────┘
       │                              │
       └──────────────┬───────────────┘
                      ▼
              DAĒNĀ — Knowledge &
              Engineering Memory
              Environment
```

### 14.3 Améliorations clés proposées (sans implémentation)

- **Interface canonique unique** : monter le routeur Knowledge (ou consolider dans `v1.py`), exposer via MCP dédié, unifier les contrats.
- **Retrieval à la volée pour les agents** : permettre aux agents de consulter DAĒNĀ dynamiquement (pas seulement injection statique), sous autorisation HROT.
- **Citations formelles** : extraire les références `[src:n]` de la réponse générée et les vérifier contre les sources fournies.
- **Adaptation à la fenêtre de contexte** : utiliser `ModelInfo.context_length` pour borner le contexte en tokens, pas en caractères bruts.
- **Branchement de la mémoire cognitive** : intégrer `core/memory/` et `core/cognition/memory/` dans le flux agent (outcomes, procédures, validation).
- **Fusion des graphes** : exposer un graphe unifié (nœuds + wikiliens + dépendances composants) ou une vue consolidée.
- **Détection de contradictions/obsolescence** : analyser les documents pour identifier les incohérences et les marquer (statuts PROPOSED/DEPRECATED).
- **Synthèses automatiques** : générer des synthèses d'agents indexées dans le vault (AI Insights) avec provenance explicite.
- **Persistance durable** : `ApplicationStateStore` pour les grants HROT, `store`/`EventCollector` pour l'audit.
- **Contrat DAĒNĀ ↔ DTAI** : métadonnées canoniques, stratégie d'événements, synchronisation, propriété des entités.

### 14.4 Ordre de mise en œuvre recommandé

1. Persistance durable (P0-1P) — prérequis sécurité.
2. Accès Knowledge sécurisé (P1-0) — audit préalable.
3. Récupération Knowledge/RAG par les agents (P1-1) — citations, tokens.
4. Branchement mémoire cognitive (P1-2).
5. Serveur MCP DAĒNĀ (P1-3).
6. Contrat DAĒNĀ ↔ DTAI (P2).
7. Consolidation (P3) — routeurs, graphes, plugins, détection, synthèses.

---

## 15. Conclusion

DAĒNĀ dispose déjà d'un socle technique substantiel et bien typé : `KnowledgeManager`, `KnowledgeCollectionManager`, `RAGPipeline`, `EngineeringMemoryService`, `VaultService`, `SearchManager`, intégration agents, WebUI Observatory. Les principales lacunes sont d'ordre **sécurité et intégration** (persistance durable, accès Knowledge gated, citations, comptage de tokens, contrat DAĒNĀ↔DTAI) et de **consolidation** (routeurs orphelins, graphes doubles, mémoire cognitive non branchée). La roadmap révisée progresse par missions incrémentales et vérifiables. Aucune implémentation n'a été effectuée dans cet audit.

**Sources principales** : `daena/Knowledge/Architecture/DAENA_KNOWLEDGE_INTELLIGENCE.md`, `docs/memory/assessments/daena-dtai/*`, code sous `core/knowledge/`, `core/rag/`, `core/engineering_memory/`, `core/agents/`, `core/search/`, `interfaces/api/`.

---

*Fin du rapport — audit en lecture seule, aucune modification de code, aucune migration, aucun commit.*
