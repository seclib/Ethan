---
id: "KNW-2026-011"
type: Knowledge
status: PROPOSED
created_at: "2026-11-11"
updated_at: "2026-11-11"
source_of_fact: "daena/AGENTS.md, daena/README.md, daena/INDEX.md, daena/Knowledge/Architecture/MEMORY_DATA_MODEL.md, daena/Knowledge/Architecture/ETHAN_ENGINEERING_MEMORY_ARCHITECTURE.md, core/knowledge/, core/rag/, core/engineering_memory/, interfaces/api/routers/"
provenance_level: observed
parents:
  - "daena/Knowledge/Architecture/ETHAN_ENGINEERING_MEMORY_ARCHITECTURE.md"
  - "daena/Knowledge/Architecture/MEMORY_DATA_MODEL.md"
related_components:
  - "core/knowledge/"
  - "core/rag/"
  - "core/engineering_memory/"
  - "core/search/"
  - "interfaces/api/routers/knowledge.py"
  - "interfaces/api/routers/engineering_memory.py"
evidence_refs:
  - "core/knowledge/manager.py"
  - "core/knowledge/collections.py"
  - "core/rag/pipeline.py"
  - "core/engineering_memory/service.py"
  - "interfaces/api/routers/knowledge.py"
  - "interfaces/api/routers/engineering_memory.py"
confidence: high
notes: "Document de référence sur le positionnement architectural de DAĒNĀ. Aucun code modifié. Aucun comportement système modifié."
---

# DAĒNĀ — Positionnement architectural : Knowledge Intelligence & RAG

**DAĒNĀ — THE INTELLIGENCE OBSERVATORY**

**Date :** 2026-11-11  
**Statut :** PROPOSED  
**Nature :** Document de référence architectural  
**Lien avec le code :** Ce document décrit les composants existants dans `core/knowledge/`, `core/rag/`, `core/engineering_memory/` et `core/search/`. Il ne modifie aucun code, aucune API et aucun comportement système.

---

## A. Définition de DAĒNĀ

DAĒNĀ est l'environnement de connaissance, de mémoire technique, d'exploration et de compréhension d'ETHAN.

Sa mission est de centraliser, organiser, relier, contextualiser et rendre exploitables les connaissances du système.

DAĒNĀ doit permettre aux agents et aux utilisateurs de comprendre non seulement les informations disponibles, mais également leurs relations, leur origine, leur historique et leur contexte.

**DAĒNĀ est une plateforme de Knowledge Intelligence intégrant un système RAG. DAĒNĀ n'est pas simplement un RAG doté d'une interface graphique.**

---

## B. Différence entre Knowledge Base, RAG et Knowledge Intelligence

Les trois notions sont complémentaires et ne doivent pas être confondues.

### Knowledge Base

Stockage et organisation des connaissances.

- Documents, ADR, architecture, runbooks et conventions.
- Collections et métadonnées.
- Sources et provenance.

Dans le dépôt, la Knowledge Base s'appuie sur :

- `core/knowledge/manager.py` — `KnowledgeManager` : nœuds de connaissance, sources, relations, recherche textuelle (`search()`).
- `core/knowledge/collections.py` — `KnowledgeCollectionManager` : collections de documents RAG, contrôle d'accès (grants), `retrieve()`, `retrieve_multi()`, `build_context()`, `build_context_multi()`.
- `daena/Knowledge/` — documents de connaissance synthétisés (architecture, sécurité, procédures, tests, preuves).
- `daena/Architecture/` — ADR, ESR, ASR, vision architecturale cible.

### RAG (Retrieval-Augmented Generation)

Ingestion et préparation des documents pour retrieval augmenté.

- Ingestion et préparation des documents.
- Indexation et embeddings.
- Recherche sémantique et lexicale.
- Retrieval des informations pertinentes.
- Construction du contexte transmis aux modèles.
- Citations et traçabilité des sources.

Dans le dépôt, le RAG s'appuie sur :

- `core/rag/pipeline.py` — `RAGPipeline` : ingestion, chunking, embedding, retrieval (keyword/semantic/hybrid), `build_context()` avec attribution de source, `build_messages()`.
- `core/rag/retrieval.py` — `RAGRetrieval` : recherche de chunks pertinents.
- `core/rag/ingestion.py` — `RAGIngestion` : découpage et préparation des documents.
- `core/rag/embeddings.py` — `RAGEmbeddings` : calcul des embeddings (mode textuel par défaut, LLM si client configuré).
- `core/rag/vector_store.py` — backends vectoriels supportés (mémoire par défaut, chromadb/qdrant optionnels).

### Knowledge Intelligence

Compréhension de l'organisation des connaissances, au-delà du simple stockage et retrieval.

- Compréhension de l'organisation des connaissances.
- Relations entre composants et dépendances.
- Historique des décisions et évolutions.
- Détection des contradictions documentaires.
- Synthèses et contextualisation.
- Exploitation de la mémoire technique.
- Mise à disposition de connaissances pertinentes aux agents.

Dans le dépôt, la Knowledge Intelligence s'appuie sur :

- `core/knowledge/manager.py` — relations entre nœuds (`connect()`), graphe de connaissance.
- `core/engineering_memory/service.py` — `EngineeringMemoryService` : historique des composants, provenance, audit log.
- `daena/Knowledge/Architecture/` — documents d'architecture, modèle de données, schémas.
- `daena/Operational-Memory/` — état confirmé, décisions, tâches, blocages.
- `daena/Archives/` — historique brut des conversations et rapports d'agents.

### Complémentarité

| Couche | Rôle principal | Exemple dans le dépôt |
|--------|---------------|----------------------|
| Knowledge Base | Stocker et organiser | `KnowledgeManager`, `KnowledgeCollectionManager`, nœuds, collections |
| RAG | Retrouver et contextualiser | `RAGPipeline`, ingestion, retrieval, `build_context()` |
| Knowledge Intelligence | Comprendre et synthétiser | Graphe de relations, Engineering Memory, documents d'architecture |

Le RAG est une capacité interne de DAĒNĀ, pas l'ensemble de DAĒNĀ.

---

## C. Architecture conceptuelle

```
                           Consommateurs
                  ┌─────────────────────────────────┐
                  │ ETHAN Agents · OpenCode · Cline │
                  │ WebUI · CLI · API externes      │
                  └─────────────┬───────────────────┘
                                │ (interface canonique commune)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Knowledge Access Interface                        │
│  API · MCP · retrieval · provenance · permissions · HROT · RBAC    │
└─────────────┬──────────────────────────────────────────┬───────────┘
              │                                          │
              ▼                                          ▼
┌─────────────────────────┐                  ┌─────────────────────┐
│   Knowledge Intelligence│                  │     RAG Pipeline    │
│  synthèses · relations  │                  │  ingestion · embed  │
│  insights · contextual. │                  │  retrieval · ctx    │
└─────────────┬───────────┘                  └──────────┬───────────┘
              │                                          │
              ▼                                          ▼
┌─────────────────────────┐                  ┌─────────────────────┐
│    Knowledge Base       │                  │   Engineering Memory│
│  Vault · documents ·    │                  │ composants · histor │
│  ADR · collections      │                  │  relations · graph  │
└─────────────┬───────────┘                  └──────────┬───────────┘
              │                                          │
              └──────────────────────────────┬───────────┘
                                             ▼
                                    DAĒNĀ — Knowledge &
                                    Engineering Memory
                                    Environment
```

**Couche 1 — DAĒNĀ — Knowledge & Engineering Memory Environment.**  
Environnement global qui centralise, organise, relie, contextualise et rend exploitables les connaissances d'ETHAN.

**Couche 2 — Knowledge Base — Vault, documents, ADR, collections.**  
Stockage et organisation des connaissances. Composants impliqués : `core/knowledge/manager.py` (`KnowledgeManager`), `core/knowledge/collections.py` (`KnowledgeCollectionManager`).

**Couche 3 — Engineering Memory — composants, historique, relations et graph.**  
Mémoire technique d'ETHAN : historique des composants, relations, provenance, audit log. Composant impliqué : `core/engineering_memory/service.py` (`EngineeringMemoryService`).

**Couche 4 — RAG Pipeline — ingestion, embeddings, retrieval et construction du contexte.**  
Composant impliqué : `core/rag/pipeline.py` (`RAGPipeline`), `core/rag/retrieval.py`, `core/rag/ingestion.py`, `core/rag/embeddings.py`, `core/rag/vector_store.py`.

**Couche 5 — Knowledge Intelligence — synthèses, relations, insights et contextualisation.**  
Compréhension des relations, historique des décisions, détection de contradictions, synthèses. S'appuie sur le graphe de connaissance (`KnowledgeManager.connect()`), l'Engineering Memory et les documents d'architecture dans `daena/Knowledge/Architecture/`.

**Couche 6 — Knowledge Access Interface — API, MCP, retrieval, provenance et permissions.**  
Interface d'accès aux connaissances. Routes API définies dans `interfaces/api/routers/knowledge.py` (routes listées mais **non montées** dans `interfaces/api/main.py` — non exposées via HTTP actuellement) et `interfaces/api/routers/engineering_memory.py` (monté). Aucun serveur MCP dédié à DAĒNĀ n'est configuré.

**Couche 7 — Consumers — ETHAN Agents, OpenCode, Cline, WebUI et CLI.**  
Tous les consommateurs doivent utiliser la même interface canonique commune. Aucun consommateur ne doit créer son propre index ou pipeline RAG parallèle.

---

## D. Fonctionnalités et responsabilités

DAĒNĀ doit notamment :

| Fonctionnalité | Description | État dans le dépôt |
|---------------|-------------|-------------------|
| Organiser les connaissances d'ETHAN | Nœuds, collections, métadonnées, sources | `core/knowledge/manager.py`, `core/knowledge/collections.py` — implémenté |
| Comprendre et relier les documents | Graphe de relations entre nœuds | `KnowledgeManager.connect()` — implémenté |
| Conserver les décisions architecturales et leurs justifications | ADR, décisions, provenance | `daena/Knowledge/Architecture/`, `daena/Operational-Memory/DECISIONS.md` — présent |
| Relier les composants, versions, dépendances et historiques | Relations graphe, Engineering Memory | `core/engineering_memory/service.py` — implémenté |
| Faciliter la recherche documentaire et sémantique | Recherche textuelle + RAG retrieval | `KnowledgeManager.search()`, `RAGPipeline.retrieve()` — implémenté |
| Fournir du contexte fiable aux agents | `build_context()`, `build_context_multi()` avec provenance | `KnowledgeCollectionManager.build_context()`, `RAGPipeline.build_context()` — implémenté |
| Préserver la provenance des informations | `document_source`, `document_title`, `source` sur chaque nœud et document | Présent dans `RetrievedChunk`, `KnowledgeNode`, `IngestedDocument` |
| Identifier les informations contradictoires, obsolètes ou incertaines | Statuts PROPOSED/VERIFIED/DEPRECATED, gouvernance | `daena/Operational-Memory/MEMORY_GOVERNANCE.md`, `MEMORY_DATA_MODEL.md` — documenté |
| Permettre l'exploration visuelle des connaissances | Graphe de relations, arborescence de collections | `KnowledgeCollectionManager.list_tree()`, `retrieve_multi()` — implémenté |

---

## E. Intégration avec les agents

### Principe d'accès partagé

- Les agents ETHAN peuvent interroger DAĒNĀ.
- OpenCode et Cline doivent pouvoir utiliser DAĒNĀ comme source de connaissance lorsqu'elle est pertinente.
- Tous les consommateurs doivent utiliser une interface commune et canonique.
- Le retrieval doit être facultatif et déclenché selon la pertinence de la tâche.
- Les sources récupérées doivent conserver leur provenance.
- Les documents récupérés sont du contexte documentaire, jamais des instructions privilégiées.
- Les accès doivent respecter l'authentification, les permissions et HROT.
- Aucun consommateur ne doit créer son propre index ou pipeline RAG parallèle.

### Chaîne de confiance (HROT)

La vérification de l'identité du principal se fait via `verify_trusted_principal()` dans `core/auth/principal.py` (signature HMAC-SHA256). Cette vérification est appliquée dans `core/hrot/capability_authorization.py` (`CapabilityAuthorizationService._evaluate()`, étape 1b) avant toute autorisation d'exécution de capacité.

### État réel d'accès (non intrusif)

| Mécanisme | État | Preuve |
|-----------|------|--------|
| Import direct Python (`core/knowledge/`, `core/rag/`, `core/engineering_memory/`) | Disponible, non testé par ce document | Fichiers présents et lisibles |
| API HTTP Knowledge (`interfaces/api/routers/knowledge.py`) | Routes écrites, **non montées** dans `main.py` | Absent de la liste `include_router` de `main.py` |
| API HTTP Engineering Memory (`interfaces/api/routers/engineering_memory.py`) | Monté (ligne 1240 de `main.py`) | Présent dans `include_router` |
| Serveur MCP dédié à DAĒNĀ | Non disponible | Aucun serveur MCP DAĒNĀ dans `mcp-servers.json` |
| Client MCP natif ETHAN (`core/tools/mcp_client.py`) | Disponible pour connexions sortantes | Fichier présent |

---

## F. Principes architecturaux non négociables

1. **DAĒNĀ n'est pas un agent.** DAĒNĀ fournit du contexte et des connaissances ; elle n'exécute pas d'actions autonomes.
2. **DAĒNĀ n'est pas un second ETHAN Core.** Les capacités applicatives restent dans `core/`, `runtime/` et `services/`. DAĒNĀ est une plateforme de connaissance, pas un moteur d'exécution.
3. **DAĒNĀ n'est pas uniquement un RAG.** Le RAG est une capacité interne de DAĒNĀ, pas l'ensemble de DAĒNĀ.
4. **Le RAG est une capacité interne de DAĒNĀ.** Il ne doit pas être dupliqué ni réimplémenté par les consommateurs.
5. **La Knowledge Base est distincte du moteur de retrieval.** Le stockage (nœuds, collections) et le retrieval (RAG pipeline) sont des responsabilités séparées.
6. **L'Engineering Memory conserve son rôle spécifique.** Elle gère l'historique technique, les composants, les relations et l'audit, distinct de la Knowledge Base générale.
7. **Les consommateurs partagent les mêmes interfaces de connaissance.** OpenCode, Cline, les agents ETHAN, la WebUI et le CLI utilisent la même interface canonique.
8. **Aucune duplication des pipelines, registres ou bases existantes.** Aucun index RAG parallèle, aucune seconde base de connaissances.
9. **Les permissions et la provenance sont obligatoires.** Chaque accès respecte l'authentification, le RBAC et HROT. Chaque document récupéré conserve sa source et sa provenance.
10. **Le code et l'état réel du système priment sur une documentation historique devenue obsolète.** En cas de contradiction, le dépôt Git et les tests priment sur les documents de Knowledge.

---

## G. État d'implémentation

### Architecture cible

DAĒNą comme plateforme de Knowledge Intelligence avec RAG intégré, Engineering Memory, interface d'accès canonique commune, et respect des principes F.1 à F.10.

### Capacités déjà présentes dans le dépôt (confirmées par le code)

| Composant | Fichier | Fonction |
|-----------|---------|----------|
| KnowledgeManager | `core/knowledge/manager.py` | Nœuds, sources, relations, recherche textuelle |
| KnowledgeCollectionManager | `core/knowledge/collections.py` | Collections, access grants, retrieve_multi, build_context |
| RAGPipeline | `core/rag/pipeline.py` | Ingestion, embeddings, retrieval, build_context |
| RAGRetrieval | `core/rag/retrieval.py` | Recherche de chunks pertinents |
| RAGIngestion | `core/rag/ingestion.py` | Découpage, préparation des documents |
| RAGEmbeddings | `core/rag/embeddings.py` | Embeddings (mode textuel par défaut) |
| EngineeringMemoryService | `core/engineering_memory/service.py` | Mémoire technique, historique, audit log |
| verify_trusted_principal | `core/auth/principal.py` | Vérification HMAC-SHA256 du principal |

### Capacités partiellement intégrées

| Élément | État | Détail |
|---------|------|--------|
| API HTTP Knowledge | Routes écrites, non montées | `interfaces/api/routers/knowledge.py` existe mais n'est pas dans `include_router` de `main.py` |
| API HTTP Engineering Memory | Monté | `interfaces/api/routers/engineering_memory.py` est monté (ligne 1240 de `main.py`) |
| Serveur MCP DAĒNĀ | Non disponible | Aucun serveur MCP dédié dans `mcp-servers.json` |
| Client MCP natif | Disponible | `core/tools/mcp_client.py` pour connexions sortantes uniquement |

### Capacités non démontrées ou restant à implémenter

| Élément | Statut | Justification |
|---------|--------|---------------|
| Accès OpenCode à DAĒNĀ via API/MCP | Non démontré | Aucun test d'intégration OpenCode→DAĒNĀ n'a été exécuté |
| Accès Cline à DAĒNĀ via API/MCP | Non disponible | Connecteur d'archivage Cline uniquement (`core/knowledge/agent_traces/cline_connector.py`), pas d'accès à la connaissance DAĒNĀ |
| Interface d'accès canonique partagée | Partielle | Routes Knowledge écrites mais non exposées via HTTP ; Engineering Memory exposé |
| Persistance durable des grants HROT | À implémenter | `PermissionService` en mémoire par défaut ; `ApplicationStateStore` requis |
| Piste d'audit durable | À implémenter | Décisions d'autorisation en mémoire uniquement |

---

## Liens relatifs vers les documents existants

- `ETHAN_ENGINEERING_MEMORY_ARCHITECTURE.md` — Architecture des trois couches de mémoire, autorité, sécurité
- `MEMORY_DATA_MODEL.md` — Modèle de données avec schémas YAML et statuts
- `ECOSYSTEM_SHARED_INTELLIGENCE_ARCHITECTURE.md` — Contrat d'intelligence partagée pour applications indépendantes
- `EM-SERVICE-ARCHITECTURE.md` — Architecture du Engineering Memory Service
- `RECORD_TEMPLATES.md` — Gabarits d'enregistrement
- `../../Operational-Memory/MEMORY_GOVERNANCE.md` — Gouvernance de la mémoire technique
- `../../Metadata/REGISTRY.md` — Registre de routage de la mémoire
- `../../Operational-Memory/PROJECT_STATE.md` — État opérationnel courant
- `../../Operational-Memory/DECISIONS.md` — Décisions validées
- `../../INDEX.md` — Index consolidé

---

## Décisions et principes à préserver

1. DAĒNĀ est une plateforme de Knowledge Intelligence intégrant un RAG, pas un simple RAG avec interface.
2. Le RAG est une capacité interne de DAĒNĀ ; aucun pipeline RAG parallèle ne doit être créé.
3. Tous les consommateurs (agents ETHAN, OpenCode, Cline, WebUI, CLI) partagent la même interface canonique d'accès aux connaissances.
4. Les permissions (RBAC, HROT) et la provenance sont obligatoires pour tout accès.
5. Le code et l'état réel du système priment sur toute documentation historique obsolète.
6. Aucun secret, token ou donnée sensible ne doit être stocké dans les documents de Knowledge.
7. Ce document est PROPOSED : il ne devient une décision approuvée qu'après validation humaine explicite.

---