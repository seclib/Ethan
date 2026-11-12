# KNOWLEDGE_RAG_ASSESSMENT.md

Évaluation détaillée des capacités Knowledge et RAG d'ETHAN Core. Distinction opérationnel / partiel / absent, avec preuves (chemins, lignes, flux). Mission exclusivement d'investigation : aucune modification de code.

---

## 1. Connaissances (Knowledge)

### 1.1 Collections et sources
- **Backend** : `core/knowledge/manager.py` (`KnowledgeManager`).
- **Modèle de nœud** : `core/knowledge/types.py` — `KnowledgeNode` (id, label, node_type, content, source, connections, metadata, created_at, updated_at). `KnowledgeType` : CONCEPT, FACT, RULE, ENTITY, SOURCE, DOCUMENT.
- **Source** : champ `source` (chaîne libre) sur chaque nœud. Pas de schémas de sources prédéfinis au-delà du champ texte.
- **Statut** : opérationnel (CRUD complet : create/get/list/update/delete).

### 1.2 Ingestion des documents
- Pas d'ingestion de documents bruts (fichiers, URLs) dans le module Knowledge proprement dit. L'ingestion de documents texte passe par le RAG (`RAGPipeline.ingest`, `core/rag/ingestion.py`).
- `KnowledgeManager.ingest_into_rag(node_id, rag)` (l. 190-201) : ingère le contenu d'un nœud Knowledge dans le RAG en tant que document sourcé (`source=f"knowledge:{node.id}"`). Nécessite un `RAGPipeline` passé explicitement. **Pas d'auto-ingestion implicite.**
- Endpoint : `POST /v1/knowledge/{knowledge_id}/rag` (v1.py l. 1306-1312) → `ingest_into_rag()`.
- Endpoint d'import de fichiers : `POST /v1/knowledge/import` et `POST /v1/knowledge/import-batch` (knowledge_imports.py) → `KnowledgeImportManager.start_import` (job asynchrone, `Permission.WRITE`).
- Endpoint d'ingestion RAG depuis fichier uploadé : `POST /v1/rag/documents/from-file/{file_id}` (v1.py l. 1434-1504) → `extract_text()` (PDF/DOCX) + `rag.ingest()` + attache optionnelle à collection (`Permission.MEMORY`).
- **Statut** : opérationnel (endpoints réels, tests `tests/interfaces/test_knowledge_tree.py`, `tests/interfaces/test_rag_strategies.py`). L'import de fichiers est un job asynchrone ; la progression est consultable via `GET /v1/knowledge/imports/{job_id}`.

### 1.3 Parsing et normalisation
- Extraction de texte depuis fichiers uploadés : `extract_text()` (appelé dans `ingest_rag_document_from_file`, v1.py l. 1434-1504). Format supporté implicite : PDF, DOCX (via l'outil d'extraction Core, non détaillé dans ce périmètre).
- Normalisation des nœuds Knowledge : `KnowledgeManager.create` normalise le label (`label.strip()`), valide la non-vacuité. Pas de normalisation de contenu plus poussée (pas de déduplication de contenu, pas de canonicalisation d'entités).
- **Statut** : partiel (parsing fichiers réel via `extract_text`, mais normalisation Knowledge limitée au nettoyage de label).

### 1.4 Métadonnées
- Champ `metadata` (dict) sur `KnowledgeNode` et sur chaque `KnowledgeConnection`. Champ `source` sur le nœud.
- Collections : champ `metadata` sur la collection, `access_grants`, `icon`, `order`, `parent_id`, `retrieval_strategy`.
- **Statut** : opérationnel. Pas de schéma de métadonnées imposé (dict libre).

### 1.5 Indexation
- Les nœuds Knowledge ne sont pas indexés automatiquement dans le RAG. L'indexation RAG se fait via `RAGPipeline.ingest` (chunking + embedding + stockage `CoreRecordStore` domaine `rag-documents` + index vecteur optionnel).
- `KnowledgeCollectionManager.reindex_collection` (l. 536-578) : re-découpe et re-embed les documents d'une collection (utile après changement de modèle d'embedding).
- **Statut** : opérationnel (indexation explicite, pas d'indexation automatique des nœuds Knowledge).

### 1.6 Classification
- `KnowledgeType` (CONCEPT, FACT, RULE, ENTITY, SOURCE, DOCUMENT) sur chaque nœud. Pas de taxonomie hiérarchique de classification au-delà du type.
- Collections peuvent être imbriquées (`parent_id`, arborescence `list_tree`).
- **Statut** : partiel (typage des nœuds + arborescence des collections, pas de classification documentaire automatique).

### 1.7 Mise à jour et suppression
- `KnowledgeManager.update` (l. 91-115) : met à jour label/type/contenu/source/métadonnées, republie `KNOWLEDGE_UPDATED`, nettoie les relations pointant vers le nœud supprimé.
- `KnowledgeManager.delete` (l. 117-132) : supprime le nœud et retire les connexions pointant vers lui de tous les autres nœuds.
- `KnowledgeCollectionManager.delete_collection` (l. 151-172) : supprime la collection, re-parente les enfants, les documents restent dans le catalogue RAG.
- `RAGPipeline.delete_document` (l. 123-129) : retire du stockage et de l'index de retrieval.
- **Statut** : opérationnel.

### 1.8 Provenance des sources
- Champ `source` sur chaque `KnowledgeNode`. `ingest_into_rag` met `source=f"knowledge:{node.id}"`.
- Pas de traçabilité de provenance au niveau fichier (ligne, page, hash) dans le module Knowledge.
- **Statut** : partiel (provenance textuelle libre, pas de provenance granulaire fichier/offset).

---

## 2. RAG

### 2.1 Pipeline d'ingestion
- `core/rag/pipeline.py` (`RAGPipeline.ingest`, l. 83-111) : chunking, embedding, persistance, indexation vecteur externe si branchée.
- `core/rag/ingestion.py` (`RAGIngestion`) : stratégies de découpage `character` (défaut), `sentence`, `paragraph`. Validation dimensionnelle des embeddings (cohérence inter-chunks et inter-documents).
- `document_id` optionnel pour aligner l'id RAG sur une entité source (ex: record projet).
- **Statut** : opérationnel.

### 2.2 Chunking
- `core/rag/ingestion.py` : `_chunk_character` (découpage par taille avec coupure de phrase), `_chunk_sentences` (regroupement de phrases), `_chunk_paragraphs` (un paragraphe par chunk, fusion si trop court).
- `chunk_size` défaut 1000, `chunk_overlap` défaut 200.
- **Statut** : opérationnel (3 stratégies réelles, exposées via `get_config()`).

### 2.3 Embeddings
- `core/rag/embeddings.py` (`RAGEmbeddings`) : utilise `LLMClient` du Core. Si absent → mode mock (vecteurs nuls de dim 8, warning journalisé).
- `attach_llm_client` (pipeline l. 232-234) : branche un client LLM réel.
- **Statut** : opérationnel, mais l'embedding réel dépend d'un provider LLM configuré au runtime. Sans provider → dégradation textuelle documentée.

### 2.4 Vector stores
- `core/rag/vector_store.py` : `SUPPORTED_VECTOR_BACKENDS`, `create_vector_store`. Backends externes (ChromaDB, Qdrant) supportés avec fallback mémoire en cas d'indisponibilité.
- `vector_backend` défaut `"memory"`.
- **Statut** : opérationnel (mémoire par défaut, externes optionnels avec graceful fallback).

### 2.5 Recherche lexicale
- `core/rag/retrieval.py` : `_textual_retrieve` (présence des mots de la requête dans le contenu des chunks, score = nombre de mots trouvés). Stratégie `keyword`.
- **Statut** : opérationnel (recherche par mots-clés réelle, sans dépendance embedding).

### 2.6 Recherche vectorielle
- `core/rag/retrieval.py` : `_semantic_retrieve` (similarité cosinus en mémoire, ou index externe ChromaDB/Qdrant si branché). Stratégie `semantic`.
- Nécessite des embeddings réels ; sinon fallback keyword avec warning.
- **Statut** : opérationnel (cosinus mémoire réel, externe optionnel).

### 2.7 Recherche hybride
- `core/rag/retrieval.py` : `_hybrid_retrieve` (RRF : reciprocal rank fusion de keyword + semantic). Stratégie `hybrid`.
- Sans embeddings réels → composante keyword uniquement, warning journalisé.
- **Statut** : opérationnel (hybride réel si embeddings, dégradation keyword sinon).

### 2.8 Reranking
- `core/rag/strategies.py` (l. 13-14) : **le reranking n'est pas exposé**. Aucune capacité cross-encoder, aucune méthode `rank`/`rerank` sur un provider LLM.
- **Statut** : **absent**.

### 2.9 Construction du contexte
- `core/rag/context.py` (`RAGContext.build_context`, l. 37-86) : assemblage borné par `max_context_chars` (défaut 8000 caractères), numérotation `[1]`, `[2]`..., sources `(Source: titre — source)`.
- `core/knowledge/collections.py` : `build_context_multi` / `build_context` (l. 515-604) : contexte texte borné `[{i}] {title} ({source})\n{content}` scoped aux collections.
- **Statut** : opérationnel. Borne en caractères (pas de tokens).

### 2.10 Citations et références
- `RAGContext.build_context` inclut `(Source: titre — source)`.
- `build_context_multi` produit `[{i}] {title} ({source})\n{content}`.
- **Pas de mécanisme de citation formelle** (footnotes, [src:1]) dans la réponse LLM. La provenance est dans le contexte injecté, pas extraite de la génération.
- **Statut** : partiel (sources dans le contexte, pas de citation formelle post-génération).

### 2.11 Évaluation de la pertinence
- Score de similarité cosinus (mémoire) ou score du index externe. Score de présence de mots (keyword). RRF (hybride).
- Pas d'évaluation de pertinence externe (pas de juge LLM, pas de métrique de qualité de retrieval persistée).
- `RAGPipeline.stats()` : volumes documents/chunks, mode embedding, backend, stratégie, recommandation.
- **Statut** : partiel (scores de retrieval réels, pas d'évaluation qualité externe).

---

## 3. Parcours document complet — ruptures identifiées

Parcours : **Document → Ingestion → Indexation → Recherche → Retrieval → Contexte → Agent → Réponse sourcée**

| Étape | Composant | Statut | Preuve |
|-------|-----------|--------|--------|
| Ingestion (document texte) | `RAGPipeline.ingest` (core/rag/pipeline.py l. 83-111) | ✅ Opérationnel | `tests/core/test_rag_engine.py`, `tests/interfaces/test_rag_strategies.py` |
| Ingestion (fichier PDF/DOCX) | `extract_text()` + `rag.ingest` (v1.py l. 1434-1504) | ✅ Opérationnel | `require_permission(Permission.MEMORY)` |
| Indexation (vecteur) | `RAGRetrieval.index_document` → vector store externe ou mémoire (core/rag/retrieval.py l. 57-108) | ✅ Opérationnel | fallback mémoire si backend indisponible |
| Recherche | `RAGPipeline.retrieve` (core/rag/pipeline.py l. 131-157) | ✅ Opérationnel | stratégies auto/keyword/semantic/hybrid |
| Retrieval (scoped collection) | `KnowledgeCollectionManager.retrieve_multi` (core/knowledge/collections.py l. 471-513) | ✅ Opérationnel | union des document_ids, un passage RAG |
| Contexte | `RAGContext.build_context` (core/rag/context.py l. 37-86) | ✅ Opérationnel | max_context_chars=8000, sources incluses |
| Injection dans l'agent | `core/agents/executor.py` (l. 383-413, `build_context_multi`) | ✅ Opérationnel | `<data source="rag:...">` dans le system prompt |
| Réponse sourcée | **Rupture** : pas de citation formelle dans la réponse LLM | `core/agents/executor.py`, `core/security/prompt_guard.py` | provenance uniquement dans le prompt, pas extraite de la génération |

**Rupture principale** : le parcours fonctionne jusqu'à l'injection du contexte dans le prompt de l'agent, mais la réponse produite par le LLM n'est pas sourcée formellement (pas de mécanisme de citation, pas de vérification que la réponse s'appuie sur les sources fournies).

### 3.2 Ce qui est absent
- Ingestion automatique des nœuds Knowledge dans le RAG (nécessite `ingest_into_rag` explicite).
- Reranking cross-encoder.
- Comptage de tokens / adaptation à la fenêtre de contexte réelle du modèle (`max_context_chars` en caractères seulement).
- Évaluation de la qualité de retrieval (juge LLM, métrique persistée).
- Mémoire cognitive (`core/memory/`) branchée sur le flux RAG/agent (embeddings TODO, aucun appel dans `executor.py`).

---

## 4. Tests et couverture réelle

### 4.1 Tests existants
- `tests/core/test_rag_engine.py` : moteur RAG (stratégies, retrieval).
- `tests/core/test_rag_strategies.py` : stratégies keyword/semantic/hybrid/auto.
- `tests/core/test_rag_infrastructure.py` : infrastructure RAG.
- `tests/integration/knowledge/test_rag_persistence_integration.py` : persistance RAG.
- `tests/core/test_knowledge_collections.py` : collections de connaissances.
- `tests/core/test_knowledge_tree.py` : arbre de collections.
- `tests/interfaces/test_knowledge_tree.py` (201 lignes) : création collections avec parent, update, arbre, move (cycle → 422), retrieve-multi, validation agent → knowledge_collection_ids.
- `tests/interfaces/test_rag_strategies.py` (132 lignes) : catalogue stratégies, recommandation Core, stratégie par collection persistée, rejet stratégie inconnue, PUT/GET /rag/config, retrieve utilise stratégie collection.

### 4.2 Couverture réelle
- **Couvert** : CRUD knowledge, collections (CRUD, arbre, accès, retrieval scoped), RAG (ingest, retrieve, stratégies, config, stats), ingestion fichiers, import de fichiers.
- **Non couvert** : exécution bout en bout avec LLM réel (tous les tests utilisent un `_FakeProvider`), citation formelle dans les réponses, évaluation qualité retrieval, intégration `core/memory/` dans le flux RAG.

---

## 5. Synthèse opérationnel / partiel / absent

| Capacité | Statut | Preuve principale |
|----------|--------|-------------------|
| CRUD nœuds Knowledge | Opérationnel | `core/knowledge/manager.py` |
| Collections RAG + contrôle d'accès | Opérationnel | `core/knowledge/collections.py` |
| Ingestion RAG (texte + fichier) | Opérationnel | `core/rag/pipeline.py`, v1.py l. 1434-1504 |
| Chunking (3 stratégies) | Opérationnel | `core/rag/ingestion.py` |
| Embeddings (réels ou mock) | Opér. (dépend provider) | `core/rag/embeddings.py` |
| Vector store (mémoire + externe) | Opérationnel | `core/rag/vector_store.py` |
| Recherche keyword | Opérationnel | `core/rag/retrieval.py` `_textual_retrieve` |
| Recherche vectorielle (cosinus) | Opérationnel | `core/rag/retrieval.py` `_semantic_retrieve` |
| Recherche hybride (RRF) | Opérationnel | `core/rag/retrieval.py` `_hybrid_retrieve` |
| Contexte borné avec sources | Opérationnel | `core/rag/context.py`, `collections.py` build_context_multi |
| Injection contexte agent | Opérationnel | `core/agents/executor.py` l. 383-413 |
| Reranking cross-encoder | Absent | `core/rag/strategies.py` l. 13-14 |
| Citation formelle réponse LLM | Absent | pas de mécanisme post-génération |
| Comptage de tokens / adaptation fenêtre | Absent | `max_context_chars=8000` caractères seulement |
| Ingestion auto Knowledge→RAG | Absent | `ingest_into_rag` explicite uniquement |
| Mémoire cognitive branchée RAG/agent | Absent | aucun appel `core/memory/` dans `executor.py` |

---

## 6. Recommandations (constat, non action)

1. Clarifier l'absence de citation formelle comme limitation documentée si la traçabilité source dans les réponses est requise.
2. Ajouter un comptage de tokens basé sur `ModelInfo.context_length` pour éviter le dépassement de fenêtre (actuellement 8000 caractères bruts).
3. Évaluer l'opportunité d'un reranking léger si la qualité de retrieval s'avère insuffisante.
4. Clarifier l'injection de `engineering_memory_integration` dans la composition root pour s'assurer que les événements knowledge sont effectivement enregistrés en production.

Fin de l'évaluation Knowledge/RAG.
