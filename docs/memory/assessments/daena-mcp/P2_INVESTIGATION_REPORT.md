# P2_INVESTIGATION_REPORT — DAĒNĀ-MCP-P2

**Mission :** DAĒNĀ Knowledge Access for OpenCode & Cline — Phase 2 (Architecture & Security Contract)  
**Dépôt :** `/home/fatsio/AI/Ethan`  
**Branche :** `refactor/ethan-rebuild-p0`  
**Date :** 11 Nov 2026  
**Mode :** READ-ONLY STRICT (aucun fichier de production modifié, aucun test lancé, aucune migration, aucun commit)  
**Statut :** TERMINÉ — Rapport consolidé des quatre investigations

---

## 1. Résumé exécutif

ETHAN possède tous les composants Core nécessaires pour exposer DAĒNĀ (Knowledge + RAG + Engineering Memory + HROT autorisation) à des clients MCP externes (OpenCode, Cline). Cependant, **il n'existe pas de serveur MCP natif dans le dépôt** : ETHAN est actuellement un client MCP (`core/tools/mcp_client.py`) et un installeur de serveurs MCP externes (`core/mcp_installer/`), mais n'en expose aucun.

Les composants Core (KnowledgeManager, KnowledgeCollectionManager, RAGPipeline, EngineeringMemoryService, CapabilityAuthorizationService, AgentPrincipal/verify_trusted_principal) existent et sont robustes (fail-closed, 25 scénarios de blocage HROT, contrôle d'accès granulaire par collection). Le package Python `mcp` v2.3.0 est installé et déclaré dans `pyproject.toml`.

**Verdict : READY WITH CONDITIONS** (voir section 12).

Les conditions à remplir avant l'implémentation de la phase 3 :
1. Implémenter un serveur MCP autonome (processus séparé de l'API FastAPI), transport Streamable HTTP recommandé.
2. Câbler l'authentification client MCP vers `AgentPrincipal` (JWT/API key → `verify_trusted_principal`).
3. Câbler l'autorisation des appels MCP vers `CapabilityAuthorizationService.authorize()` / `PermissionService.evaluate()`.
4. Persister durablement les décisions d'autorisation (actuellement mémoire volatile uniquement).
5. Rendre l'audit MCP obligatoire (pas de `_audit_store = None` silencieux).
6. Exposer uniquement des outils MCP read-only (7 outils proposés).

---

## 2. État réel du dépôt au démarrage

### 2.1 État Git

| Élément | Valeur | Certitude |
|---------|--------|-----------|
| Branche courante | `refactor/ethan-rebuild-p0` | CONFIRMÉ |
| Fichiers modifiés | 26 (dont `core/applications/capability_execution.py`, `core/hrot/capability_authorization.py`, `docs/memory/PROJECT_STATE.md`, etc.) | CONFIRMÉ |
| Fichiers non trackés | 20 (dont `daena/Knowledge/Architecture/DAENA_KNOWLEDGE_INTELLIGENCE.md`, `docs/memory/assessments/`, `docs/memory/sessions/*`, `tests/interfaces/test_application_capability_execution_p01s.py`) | CONFIRMÉ |
| Modifications P0-1S | Déjà appliquées sur `capability_execution.py` et `capability_authorization.py` (HROT-01 à HROT-06) | CONFIRMÉ |
| Documents p0-1s | 6 fichiers dans `docs/memory/assessments/daena-dtai/p0-1s/` | CONFIRMÉ |

**Source :** `git status --short` et `git branch --show-current` (rapport Agent 1, lignes 1-30 du rapport).

### 2.2 Dépendances MCP

| Élément | Valeur | Certitude |
|---------|--------|-----------|
| SDK `mcp` installé | Version 2.3.0, `/home/fatsio/.local/lib/python3.13/site-packages/mcp` | CONFIRMÉ |
| Déclaration `pyproject.toml` | Ligne 36 : `"mcp>=1.0"` | CONFIRMÉ |
| Borne supérieure | Absente → risque de rupture à la mise à jour | PARTIEL |
| Client MCP natif ETHAN | `core/tools/mcp_client.py` (288 lignes, classes `MCPClient`, `InMemoryTokenStorage`) | CONFIRMÉ |
| Serveur MCP natif ETHAN | **Aucun** (`interfaces/mcp/` vide, `**/mcp_server*.py` vide) | CONFIRMÉ |

### 2.3 Documents de référence existants

| Document | Existe | Chemin | Certitude |
|----------|--------|--------|-----------|
| P0-1S INDEPENDENT_REVIEW.md | ✅ | `docs/memory/assessments/daena-dtai/p0-1s/INDEPENDENT_REVIEW.md` | CONFIRMÉ |
| P0-1S SECURITY_CHANGES.md | ✅ | `docs/memory/assessments/daena-dtai/p0-1s/SECURITY_CHANGES.md` | CONFIRMÉ |
| P0-1S TEST_RESULTS.md | ✅ | `docs/memory/assessments/daena-dtai/p0-1s/TEST_RESULTS.md` | CONFIRMÉ |
| P0-1S FINAL_VERDICT.md | ✅ | `docs/memory/assessments/daena-dtai/p0-1s/FINAL_VERDICT.md` | CONFIRMÉ |
| P0-1S PERSISTENCE_AND_AUDIT.md | ✅ | `docs/memory/assessments/daena-dtai/p0-1s/PERSISTENCE_AND_AUDIT.md` | CONFIRMÉ |
| P0-1S IMPLEMENTATION_REPORT.md | ✅ | `docs/memory/assessments/daena-dtai/p0-1s/IMPLEMENTATION_REPORT.md` | CONFIRMÉ |
| DAĒNĀ KNOWLEDGE INTELLIGENCE | ✅ | `daena/Knowledge/Architecture/DAENA_KNOWLEDGE_INTELLIGENCE.md` | CONFIRMÉ |
| DAĒNĀ INDEX | ✅ | `daena/INDEX.md` | CONFIRMÉ |
| IMPLEMENTATION_ROADMAP.md | ✅ | `docs/memory/assessments/daena-dtai/IMPLEMENTATION_ROADMAP.md` | CONFIRMÉ |
| EXECUTIVE_SUMMARY.md | ✅ | `docs/memory/assessments/daena-dtai/EXECUTIVE_SUMMARY.md` | CONFIRMÉ |
| PROJECT_STATE.md | ✅ | `docs/memory/PROJECT_STATE.md` | CONFIRMÉ |

### 2.4 Serveurs MCP tiers configurés

34 serveurs MCP configurés dans `/home/fatsio/.config/opencode/mcp-servers.json` (nexus, jira, github, firecrawl, supabase, memory, omega-memory, etc.). **Aucun serveur MCP ETHAN natif n'est configuré.** (Agent 4, section 8)

---

## 3. Résultats des quatre investigations

### 3.1 Agent 1 — Core Services & Lifecycle (sessionID `ses_e36e76cfcffdES5OanlGa0ZfXx`)

**Constats confirmés :**

- **Propriétaire des services :** l'API Gateway (`interfaces/api/main.py`) possède et instancie `KnowledgeManager`, `KnowledgeCollectionManager`, `RAGPipeline`, `EngineeringMemoryService` dans son `lifespan` (lignes 275-313).
- **Store partagé :** un seul `CoreRecordStore` (`domain_store`, ligne 275) est passé à tous les managers. `CoreRecordStore` enveloppe PostgreSQL + Redis + fallback mémoire in-process.
- **Injection :** instances stockées dans `app.state` et injectées dans les routeurs v1 via setteurs module-level (`set_core_domain_services`, `set_knowledge_collections`, etc.).
- **Risque de seconde instance :** `CoreRecordStore()` par défaut (ligne 34 de `record_store.py`) crée un fallback mémoire in-process isolé. `KnowledgeCollectionManager(rag=None)` crée implicitement un `RAGPipeline()` (collections.py:54). **Ne jamais instancier sans passer le store partagé explicitement.**
- **Arrêt du MCP :** ne doit jamais fermer `pg_pool`, `redis_client`, `NATS`, `persistence`, `ProviderManager` (appartenant au cycle de vie de l'API, shutdown lignes 1119-1165 de main.py).
- **Intégration recommandée :** Niveau 1 (client HTTP de l'API existante) ou Niveau 2 (consommation des instances via `app.state` dans le même processus). Jamais recréer `RAGPipeline()`/`KnowledgeManager()` sans store partagé.

**Certitude : CONFIRMÉ** sur le principe et les fichiers/ligne.

### 3.2 Agent 2 — Identity, Trust, HROT & RBAC (sessionID `ses_e36e76cfbffehtCCdkyxf0UgwD`)

**Constats confirmés :**

- **AgentPrincipal :** dataclass frozen, signé HMAC-SHA256 via `issue_trusted_principal()` (principal.py:311-318), vérifié via `verify_trusted_principal()` (principal.py:321-334). `__post_init__` valide et recrée les champs (lignes 63-109).
- **Construction du principal :** côté serveur uniquement via `build_agent_principal()` (interfaces/api/auth.py:401-590), jamais accepté en entrée brute du client.
- **HROT fail-closed :** 25 scénarios de blocage documentés (capability_authorization.py:306-575), dont `MISSING_EXECUTION_CONTEXT`, `UNTRUSTED_PRINCIPAL`, `AGENT_IDENTITY_MISMATCH`, `BINDING_MISMATCH`, `HROT_PERMISSION_DENIED`, `AUTHORIZATION_EVALUATION_ERROR`.
- **PermissionService :** grants explicites avec `HumanAuthority`, validité temporelle (`is_valid()` lines 186-202), révocation, intégrité du manifest.
- **RBAC route-level :** `require_permission()` (auth.py:656-684).
- **Collections :** `PermissionScope` (granulaire app_id/instance_id/capability/resource/action), `check_access()` (collections.py:342), `list_accessible()` (collections.py:271).
- **Audit d'autorisation :** mémoire uniquement dans `CapabilityAuthorizationService._decisions` (lignes 212, 577-582) et `PermissionService._decisions` (lignes 278, 597-599). **Non persistant au redémarrage.**
- **AuditStore :** PostgreSQL ou JSONL fallback (`core/audit/store.py:41-47`). `McpInstaller._audit_store` peut être `None` → audit silencieusement ignoré (mcp_installer/service.py:229, 1488-1490).

**Risques de sécurité identifiés (R-01 à R-08) :**
- **R-01 (Critique) :** Aucun serveur MCP dans ETHAN — impossible pour un client MCP de s'identifier/autoriser auprès d'ETHAN.
- **R-02 (Élevée) :** Décisions d'autorisation HROT non persistées (mémoire volatile).
- **R-03 (Élevée) :** `PermissionService` sans `store` = grants volatils.
- **R-04 (Moyenne) :** `McpInstaller._audit_store` optionnel → audit silencieux.
- **R-05 (Moyenne) :** Pas de corrélation requête MCP ↔ décision d'autorisation.
- **R-06 (Moyenne) :** `PermissionChecker` (Security Gateway) utilise des rôles en dur, non synchronisé avec `RBACEngine`.
- **R-07 (Moyenne) :** Pas de mTLS/binding de canal pour connexions MCP client.
- **R-08 (Basse) :** `InMemoryTokenStorage` — tokens OAuth non persistés (feature de sécurité documentée).

**Certitude : CONFIRMÉ** sur les mécanismes, **PARTIEL** sur les recommandations.

### 3.3 Agent 3 — Retrieval, Provenance & Collections (sessionID `ses_e36e76cf5ffe7VoRWIQFaT0jmP`)

**Constats confirmés :**

- **Services à exposer (read-only) :** `KnowledgeManager` (recherche nœuds), `KnowledgeCollectionManager` (retrieval RAG scopé), `EngineeringMemoryService` (mémoire technique). `RAGPipeline.ingest/delete/configure` exclus (écriture).
- **Appels réutilisables sans modification Core :** `KnowledgeManager.search/get`, `KnowledgeCollectionManager.retrieve/retrieve_multi/build_context/build_context_multi/check_access/list_accessible`, `RAGPipeline.retrieve/build_context/get_config/stats`, `EngineeringMemoryService/search/get/verify_integrity`, `MemoryRetrieval.retrieve`, `SearchManager.search`.
- **Isolation inter-utilisateurs :** `list_accessible(user_id)` filtre par owner + grants user + groupes. `check_access()` lève `PermissionError`. Filtrage à la source via `document_ids` transmis à `RAGRetrieval.retrieve()` (pas de post-filtre).
- **Provenance :** `KnowledgeNode.source`, `IngestedDocument.source`, `RetrievedChunk.document_source`, `MemoryRecord.source_of_fact`, `provenance_level`, `confidence`, `evidence_refs`, `score`.
- **Statuts de fraîcheur :** `MemoryRecord` (PROPOSED/APPROVED/VERIFIED/DEPRECATED/SUPERSEDED/REJECTED/OBSOLETE...), `Fact` (ACTIVE/SUPERSEDED/NEEDS_REVIEW/ARCHIVED/CONTRADICTED/CONTROVERSIAL + decay_policy). `KnowledgeNode` **pas de mécanisme de fraîcheur natif**.
- **Traitement des données comme non fiables :** `RAGContext.build_messages()` inclut un message système *"Si le contexte ne contient pas la réponse, dis-le clairement"*. Chaque chunk préfixé par `[n]` avec sa source. `daena/.../ETHAN_ENGINEERING_MEMORY_ARCHITECTURE.md` : *"Elle décrit, elle ne gouverne pas le code"*.
- **11 contrats d'outils MCP read-only proposés** : `knowledge_search`, `knowledge_get`, `rag_retrieve`, `rag_build_context`, `collections_list`, `engineering_memory_search`, `engineering_memory_get`, `engineering_memory_verify_integrity`, `rag_config`, `facts_retrieve`, `unified_search`. Chacun avec schéma d'entrée/sortie, contrôle d'accès, limites de résultats, provenance.

**Certitude : CONFIRMÉ** sur les mécanismes Core, **PARTIEL** sur la fraîcheur RAG/knowledge (non implémentée nativement).

### 3.4 Agent 4 — MCP Protocol & OpenCode/Cline (sessionID `ses_e36e76cf4ffeUwSpHwyJRweBf6`)

**Constats confirmés :**

- **Architecture recommandée :** ETHAN expose un serveur MCP autonome (processus séparé de l'API FastAPI), transport Streamable HTTP recommandé pour exposition vers OpenCode/Cline. STDIO réservé aux serveurs tiers locaux gérés par le Core.
- **Isolation :** le serveur MCP doit être un processus autonome, ne pas fermer les ressources de l'API (pg_pool, redis, NATS).
- **Identité client :** JWT/API key ETHAN propagée dans le contexte d'appel d'outil MCP. Le SDK MCP ne mappe pas nativement `user_id → outil` ; à implémenter côté Core (headers ou `_meta`).
- **Configuration client :** fichiers exemples non intrusifs dans le dépôt (`config/mcp/opencode.example.json`, `config/mcp/cline.example.json`), à copier manuellement par l'opérateur. Ne jamais écraser les configs personnelles.
- **Erreurs/timeouts :** `DEFAULT_TIMEOUT = 10.0` (mcp_client.py:45), `initialize()` sous `anyio.fail_after(10)` (ligne 205), `disconnect()` sous `anyio.fail_after(5.0)` (ligne 271), auto-reconnect SSE (2 tentatives). Dégradation gracieuse si serveur MCP indisponible.
- **Sécurité SDK :** OAuth 2.0 + PKCE disponible, `TokenStorage` en mémoire uniquement, bearer statique via headers manuels, SSL verify, sandbox stdio (conteneur Docker durci). **Absent :** mTLS, API-key natif, RBAC granulaire par outil, chiffrement des tokens au repos.
- **Contraintes de compatibilité :** version protocole MCP (2024-11-05 à 2026-07-28), version SDK Python (mcp>=1.0, installé 2.3.0), Python >=3.10<3.14, interopérabilité OpenCode/Cline à valider par test.

**Certitude : CONFIRMÉ** sur le SDK et l'architecture existante, **PARTIEL** sur l'interopérabilité OpenCode/Cline non testée.

---

## 4. Architecture actuelle vérifiée

```
┌─────────────────────────────────────────────────────────────────┐
│                    ETHAN API Gateway (FastAPI)                  │
│  lifespan : crée une seule fois KnowledgeManager, RAGPipeline,  │
│             KnowledgeCollectionManager, EngineeringMemoryService│
│             avec un CoreRecordStore partagé (PG/Redis)          │
│             → stockés dans app.state                            │
└─────────────────────────────────────────────────────────────────┘
                           │
                           │ HTTP (REST, JWT/API key)
                           ▼
                    Endpoints /v1/knowledge/*
                    Endpoints /v1/tools/servers
                    Endpoints /v1/memory/*

┌─────────────────────────────────────────────────────────────────┐
│  Core Services (détenus par l'API, uniques par processus)       │
│  • KnowledgeManager  • KnowledgeCollectionManager               │
│  • RAGPipeline       • EngineeringMemoryService                 │
│  • CapabilityAuthorizationService (HROT, fail-closed)           │
│  • PermissionService (grants, évaluation)                       │
│  • AuditStore (PostgreSQL ou JSONL)                             │
└─────────────────────────────────────────────────────────────────┘
```

**Ce qui manque pour MCP :** aucune couche serveur MCP entre OpenCode/Cline et l'API ETHAN. Le client MCP ne peut pas se connecter directement à l'API REST (protocole différent).

---

## 5. Architecture MCP recommandée

```
┌─────────────────┐     HTTP Streamable      ┌──────────────────┐
│   OpenCode      │◄─────────────────────────►│  ETHAN MCP       │
│   (client MCP)  │     (port dédié, ex: 8001)│  Serveur         │
└─────────────────┘     (STDIO ou socket UNIX)│  (processus      │
                                              │  autonome)       │
┌─────────────────┘                           └──────────────────┘
│   Cline         │                                                    │
│   (client MCP)  │                                                    │
└─────────────────┘                                                    │
                                                ┌──────────────────┐
                                                │  ETHAN API       │
                                                │  Gateway         │
                                                │  (FastAPI)       │
                                                └──────────────────┘
```

**Couches du serveur MCP DAĒNĀ :**

| Couche | Rôle | Composant Core réutilisé |
|--------|------|-------------------------|
| Transport | STDIO ou Streamable HTTP | SDK `mcp` (serveur) |
| Identité | Vérification client → `AgentPrincipal` | `core/auth/principal.py` (`verify_trusted_principal`) |
| Autorisation | HROT/RBAC avant chaque appel | `core/hrot/capability_authorization.py` (`authorize`) |
| Adaptateurs | Appel des services Core | `core/knowledge/manager.py`, `core/knowledge/collections.py`, `core/rag/pipeline.py`, `core/engineering_memory/service.py` |
| Provenance | `source`, `document_source`, `score`, `confidence`, `evidence_refs` | Structures Core existantes |
| Audit | Enregistrement des décisions | `core/audit/store.py` (AuditStore) |
| Gestion erreurs | Fail-closed, pas de fuite de secrets | Logique MCP serveur + `server_policy.py` |

**Règles :**
- Le MCP serveur est un **adaptateur** : il ne crée aucun second KnowledgeManager, moteur RAG, registre ou stockage métier.
- Il ne dépend **pas** du `lifespan` HTTP de l'API.
- Il expose uniquement des outils **read-only**.
- Il ne fait pas confiance à un `principal_id` ou `user_id` transmis librement par le client ; il vérifie l'identité côté serveur.

**Certitude : RECOMMANDATION** (basée sur les quatre rapports, pas encore implémentée).

---

## 6. Modèle d'identité et de sécurité

### 6.1 Identité du client MCP

| Élément | Mécanisme | Fichier | Ligne | Certitude |
|---------|-----------|---------|-------|-----------|
| Identification | JWT Bearer ou API Key via `build_agent_principal()` | `interfaces/api/auth.py` | 401-590 | CONFIRMÉ |
| Vérification cryptographique | `verify_trusted_principal()` (HMAC-SHA256) | `core/auth/principal.py` | 321-334 | CONFIRMÉ |
| Immuabilité | `AgentPrincipal` dataclass frozen | `core/auth/principal.py` | 44 | CONFIRMÉ |
| Pas de transmission client | Principal construit côté serveur uniquement | `interfaces/api/auth.py` | 401-590 | CONFIRMÉ |
| Pas d'auto-approbation | `approved_by != app_id` | `core/applications/permissions.py` | 477-478, 658-659 | CONFIRMÉ |

### 6.2 Autorisation

| Élément | Mécanisme | Fichier | Ligne | Certitude |
|---------|-----------|---------|-------|-----------|
| Évaluation multi-couches | `CapabilityAuthorizationService.authorize()` | `core/hrot/capability_authorization.py` | 275 | CONFIRMÉ |
| Grants explicites | `PermissionService.evaluate()` | `core/applications/permissions.py` | 540-600 | CONFIRMÉ |
| Contrôle d'accès collections | `KnowledgeCollectionManager.check_access()` | `core/knowledge/collections.py` | 342 | CONFIRMÉ |
| Moindre privilège | `PermissionScope` (app/capability/resource/action) | `core/applications/permissions.py` | 90-99 | CONFIRMÉ |
| RBAC route-level | `require_permission()` | `interfaces/api/auth.py` | 656-684 | CONFIRMÉ |

### 6.3 Règles de sécurité non négociables

| Règle | Justification |
|-------|---------------|
| **Fail-closed** | Toute exception d'évaluation → `AUTHORIZATION_EVALUATION_ERROR` (capability_authorization.py:559-575) |
| **Read-only** | Aucun outil d'écriture (ingest, delete, record) exposé via MCP |
| **Collection isolation** | `check_access()` avant tout retrieval, filtrage par `document_ids` à la source |
| **Principal trust verification** | `verify_trusted_principal()` obligatoire avant toute autorisation |
| **Least privilege** | `PermissionScope` granulaire, pas de `admin` pour AGENT principals |
| **Input validation** | Schémas d'entrée documentés et validés pour chaque outil MCP |
| **Pas d'injection d'instructions** | RAGContext inclut "Si le contexte ne contient pas la réponse, dis-le clairement" (rag/context.py:88-117) |
| **Pas de fuite inter-utilisateurs** | Filtrage à la source via `document_ids`, pas de post-filtre |
| **Audit des consultations** | Décisions d'autorisation enregistrées (mais mémoire volatile uniquement — voir R-02) |
| **Gestion erreurs sans fuite** | Pas de secrets dans les logs (`redact_backend_config`, rag/pipeline.py:31-41) |

**Limites des mécanismes HROT actuels pour MCP :**
- Pas de serveur MCP existant → l'identité client MCP n'est pas actuellement vérifiable auprès d'ETHAN (R-01).
- Pas de corrélation entre une requête MCP et une décision d'autorisation (R-05).
- Décisions d'autorisation en mémoire volatile (R-02, R-03).

---

## 7. Contrats fonctionnels proposés pour les outils MCP

Contrats détaillés dans le rapport de l'Agent 3. Huit outils read-only :

| # | Outil | Service Core | Contrôle d'accès | Certitude |
|---|-------|-------------|-----------------|-----------|
| 1 | `knowledge_search` | `KnowledgeManager.search()` | Aucun (global) | CONFIRMÉ |
| 2 | `knowledge_get` | `KnowledgeManager.get()` | Aucun (global) | CONFIRMÉ |
| 3 | `rag_retrieve` | `KnowledgeCollectionManager.retrieve()/retrieve_multi()` | `check_access` par collection | CONFIRMÉ |
| 4 | `rag_build_context` | `KnowledgeCollectionManager.build_context()/build_context_multi()` | `check_access` par collection | CONFIRMÉ |
| 5 | `collections_list` | `KnowledgeCollectionManager.list_accessible()/list_tree()` | `list_accessible(user_id)` | CONFIRMÉ |
| 6 | `engineering_memory_search` | `EngineeringMemoryService.search()/search_records()` | Aucun (global, filtrage par component) | CONFIRMÉ |
| 7 | `engineering_memory_get` | `EngineeringMemoryService.get()` | Aucun (global) | CONFIRMÉ |
| 8 | `engineering_memory_verify_integrity` | `EngineeringMemoryService.verify_integrity()` | Aucun (global) | CONFIRMÉ |
| 9 | `rag_config` | `RAGPipeline.get_config()/stats()/recommend_strategy()` | Aucun (global) | CONFIRMÉ |
| 10 | `facts_retrieve` | `MemoryRetrieval.retrieve()` | Aucun (global) | CONFIRMÉ |
| 11 | `unified_search` | `SearchManager.search()` | Aucun (global) | CONFIRMÉ |

**Outils exclus (écriture) :** `rag_ingest`, `rag_delete_document`, `rag_configure`, `knowledge_create/update/delete`, `engineering_memory_record/collect_event`.

Chaque résultat inclut : `id`, `title`, `content`/`chunk`, `source`/`document_source`, `score`, `provenance_level`, `confidence`, `trust_level: "untrusted"`.

---

## 8. Intégration OpenCode et Cline

### 8.1 Configuration non intrusive

Fichiers exemples à livrer dans le dépôt (à copier manuellement par l'opérateur) :

**`config/mcp/opencode.example.json`** :
```json
{
  "mcpServers": {
    "ethan-core": {
      "command": "ethan",
      "args": ["mcp", "stdio"],
      "env": { "ETHAN_API_URL": "http://127.0.0.1:8000", "ETHAN_API_KEY": "YOUR_ETHAN_API_KEY" },
      "description": "ETHAN Core MCP server"
    }
  }
}
```

**`config/mcp/cline.example.json`** :
```json
{
  "mcpServers": {
    "ethan-core-http": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://127.0.0.1:8001/mcp"],
      "env": { "ETHAN_API_KEY": "YOUR_ETHAN_API_KEY" },
      "description": "ETHAN Core MCP via Streamable HTTP"
    }
  }
}
```

**Règles :**
- Ne jamais écraser `~/.cline/.../cline_mcp_settings.json` ni le config OpenCode personnel.
- Utiliser des variables d'environnement pour les secrets (jamais en clair dans les fichiers de config partagés).
- Documenter l'activation, la désactivation et le diagnostic.

### 8.2 Transport recommandé

| Client | Transport recommandé | Justification |
|--------|---------------------|---------------|
| OpenCode | STDIO natif ou HTTP via `mcp-remote` | OpenCode supporte stdio nativement |
| Cline | STDIO principalement ; HTTP dépend de l'extension | Cline (VS Code) supporte stdipe nativement ; HTTP moins certain |

**Certitude : PARTIEL** (interopérabilité OpenCode/Cline à valider par test d'interopérabilité réel).

---

## 9. Risques et limitations

| ID | Risque | Gravité | Probabilité | Certitude | Recommandation |
|----|--------|---------|-------------|-----------|----------------|
| R-01 | Aucun serveur MCP dans ETHAN | Critique | Élevée | CONFIRMÉ | Implémenter un serveur MCP avec auth + autorisation |
| R-02 | Décisions d'autorisation HROT non persistées | Élevée | Élevée | CONFIRMÉ | Persister `_decisions` dans `AuditStore` |
| R-03 | `PermissionService` sans `store` = grants volatils | Élevée | Moyenne | CONFIRMÉ | Rendre le store obligatoire ou garantir la persistance |
| R-04 | `McpInstaller._audit_store` peut être `None` | Moyenne | Moyenne | CONFIRMÉ | Rendre l'audit obligatoire (fail-closed) |
| R-05 | Pas de corrélation requête MCP ↔ décision d'autorisation | Moyenne | Moyenne | PARTIEL | Ajouter `correlation_id` de bout en bout |
| R-06 | `PermissionChecker` rôles en dur, non synchronisé avec `RBACEngine` | Moyenne | Moyenne | PARTIEL | Unifier les deux modèles RBAC |
| R-07 | Pas de mTLS/binding de canal | Moyenne | Faible | PARTIEL | Ajouter TLS mutuel |
| R-08 | `InMemoryTokenStorage` — tokens OAuth non persistés | Basse | Faible | CONFIRMÉ | Documenté comme intentionnel |
| R-09 | Interopérabilité OpenCode/Cline non testée | Moyenne | Moyenne | HYPOTHÈSE | Valider par test d'interopérabilité |

---

## 10. Décisions restant à prendre

| Décision | Options | Recommandation |
|----------|---------|----------------|
| Transport MCP serveur | STDIO vs Streamable HTTP | HTTP Streamable (reconnexion, distant, OAuth) |
| Processus MCP | Même processus API vs processus séparé | Processus séparé (isolation, arrêt sans impact) |
| Authentification client MCP | JWT Bearer vs API Key vs mTLS | JWT/API key ETHAN (réutiliser l'existant) |
| Persistance des décisions d'autorisation | `AuditStore` vs base dédiée | `AuditStore` (déjà existant, PostgreSQL/JSONL) |
| Outils MCP à exposer | 7-11 outils read-only | Commencer par les 8 outils principaux |
| Configuration client | Fichiers exemples vs modification auto | Fichiers exemples non intrusifs |

---

## 11. Conditions nécessaires à l'implémentation (Phase 3)

1. **Implémenter le serveur MCP DAĒNĀ** (processus autonome, transport Streamable HTTP, SDK `mcp` 2.3.0).
2. **Câbler l'authentification** : JWT/API key ETHAN → `AgentPrincipal` via `verify_trusted_principal()`.
3. **Câbler l'autorisation** : chaque appel d'outil MCP passe par `CapabilityAuthorizationService.authorize()` ou `PermissionService.evaluate()`.
4. **Persister les décisions d'autorisation** : écrire dans `AuditStore` (table `audit_log`) à chaque décision.
5. **Rendre l'audit obligatoire** : lever une erreur si `_audit_store` est `None` (pas de silencieux).
6. **Implémenter les 8 outils MCP read-only** avec schémas d'entrée/sortie validés.
7. **Tester l'interopérabilité** OpenCode et Cline.
8. **Créer les fichiers de configuration exemples** (non intrusifs).
9. **Documenter l'activation, la désactivation, le diagnostic**.
10. **Réviser la sécurité** indépendamment avant exposition.

---

## 12. Références précises aux fichiers et symboles

### Fichiers Core examinés

| Fichier | Symbole principal | Ligne | Rôle |
|---------|------------------|-------|------|
| `core/auth/principal.py` | `AgentPrincipal`, `verify_trusted_principal`, `issue_trusted_principal`, `PrincipalType` | 18, 44, 311, 321 | Identité et confiance |
| `core/auth/__init__.py` | `RBACEngine`, `Permission` | 11, 39 | RBAC |
| `core/auth/api_keys.py` | `APIKeyManager` | — | Validation API Key |
| `core/auth/service_identities.py` | `ServiceIdentityManager`, `ServiceTokenValidator` | — | Identités de service |
| `core/hrot/capability_authorization.py` | `CapabilityAuthorizationService.authorize()`, `_record()`, `audit_trail()` | 275, 577, 584 | Autorisation HROT fail-closed |
| `core/hrot/durable.py` | `DurableHrotStore`, `DurableHrotApproval` | 28, 59 | Approbations durables HROT |
| `core/applications/capability_execution.py` | `invoke_capability()`, `CapabilityExecutionBinding` | 154, 68 | Invocation de capacité |
| `core/applications/capability_contract.py` | `ApplicationCapabilityContract` | — | Contrats de capacité |
| `core/applications/permissions.py` | `PermissionService.evaluate()`, `PermissionScope.matches()`, `PermissionGrant.is_valid()` | 540, 90, 186 | Grants et évaluation HROT |
| `core/knowledge/manager.py` | `KnowledgeManager.search()`, `get()`, `connect()` | 134, 80, 149 | Graphe de connaissance |
| `core/knowledge/collections.py` | `KnowledgeCollectionManager.retrieve()`, `retrieve_multi()`, `build_context()`, `check_access()`, `list_accessible()` | 451, 471, 585, 342, 271 | Collections et retrieval RAG |
| `core/knowledge/types.py` | `KnowledgeType`, `KnowledgeNode` | 11, 62 | Types de nœuds |
| `core/rag/pipeline.py` | `RAGPipeline.retrieve()`, `build_context()`, `get_config()`, `stats()` | 131, 159, 299, 322 | Pipeline RAG |
| `core/rag/retrieval.py` | `RAGRetrieval.retrieve()`, `RetrievedChunk` | 125, 26 | Retrieval chunks et score |
| `core/rag/context.py` | `RAGContext.build_context()`, `build_messages()` | 37, 88 | Contexte LLM avec sources |
| `core/rag/strategies.py` | `normalize_strategy()`, `validate_strategy()` | — | Stratégies de retrieval |
| `core/rag/ingestion.py` | `RAGIngestion.ingest()` | — | Ingestion (écriture, non exposée) |
| `core/engineering_memory/service.py` | `EngineeringMemoryService.search()`, `get()`, `verify_integrity()` | 55, 52, 83 | Mémoire technique |
| `core/engineering_memory/models.py` | `MemoryRecord`, `MemoryRecordValidator` | 52, 52-86 | Modèle et validation EM |
| `core/engineering_memory/security.py` | `SecurityPolicy.validate_record()`, `ensure_path_in_root()` | 62, 82 | Sécurité EM |
| `core/audit/store.py` | `AuditStore`, `AuditEntry`, `AuditCategory`, `AuditDecision` | 41-47 | Stockage d'audit |
| `core/audit/types.py` | `AuditEntry`, `AuditCategory`, `AuditDecision` | — | Types d'audit |
| `core/security/gateway.py` | `SecurityGateway._log_action()` | 129-156 | Log des actions |
| `core/security/validation/permissions.py` | `PermissionChecker` | 25-60 | Vérification permissions (gateway) |
| `core/security/types.py` | `Identity`, `SecurityContext`, `TrustLevel` | — | Types de sécurité |
| `core/tools/mcp_client.py` | `MCPClient.connect()`, `list_tool_specs()`, `call_tool()` | 113, 212, 236 | Client MCP |
| `core/tools/server_policy.py` | `validate_server_config()`, `TRUSTED_TRANSPORTS`, `TRUSTED_AUTH_TYPES` | 41, 159-189 | Politique des serveurs MCP |
| `core/tools/servers.py` | `ToolServerManager.register()` | 28-85 | Gestion des serveurs MCP |
| `core/mcp_installer/service.py` | `McpInstaller`, `_audit()` | 212-239, 1485-1500 | Installation MCP (pas un serveur) |
| `core/integrations/__init__.py` | `IntegrationManager` (kind "mcp") | — | Intégrations MCP |
| `core/state/record_store.py` | `CoreRecordStore` | 29-39 | Store partagé (PG/Redis/mémoire) |
| `core/facts/types.py` | `FactStatus` (ACTIVE, SUPERSEDED, CONTRADICTED, CONTROVERSIAL) | 12-20 | Statuts de faits |
| `core/facts/retrieval.py` | `MemoryRetrieval.retrieve()`, `DecayPolicy` | 42, 18-74 | Récupération de faits scorés |
| `core/search/__init__.py` | `SearchManager.search()` | 53 | Recherche unifiée 4 domaines |
| `interfaces/api/main.py` | `lifespan`, `CoreDomainServices`, `app.state` | 203-313, 1119-1165 | Cycle de vie API |
| `interfaces/api/routers/v1.py` | `CoreDomainServices()` par défaut, setteurs module-level | 180-208 | Singletons routeurs v1 |
| `interfaces/api/routers/knowledge.py` | Routes `/v1/knowledge/*` (NON MONTÉES) | 60-131 | Routes knowledge existantes |
| `interfaces/api/routers/capabilities.py` | Routes `/v1/tools/servers/*` | 595-698 | Gestion serveurs MCP |
| `interfaces/api/routers/mcp_installer.py` | Router MCP installer (thin gateway) | — | Installation MCP |
| `interfaces/api/auth.py` | `build_agent_principal()`, `require_permission()`, `auth_middleware` | 401-590, 656-684 | Authentification HTTP |
| `interfaces/api/gateway_guard.py` | `gateway_guard` | — | Garde de passerelle |

### Documents de référence

| Document | Chemin | Rôle |
|----------|--------|------|
| DAĒNĀ Knowledge Intelligence Architecture | `daena/Knowledge/Architecture/DAENA_KNOWLEDGE_INTELLIGENCE.md` | Positionnement de DAĒNĀ |
| Engineering Memory Architecture | `daena/Knowledge/Architecture/ETHAN_ENGINEERING_MEMORY_ARCHITECTURE.md` | Architecture mémoire (trois couches) |
| Memory Data Model | `daena/Knowledge/Architecture/MEMORY_DATA_MODEL.md` | Schémas YAML et statuts |
| EM Service Architecture | `daena/Knowledge/Architecture/EM-SERVICE-ARCHITECTURE.md` | Architecture du service mémoire |
| Memory Governance | `daena/Operational-Memory/MEMORY_GOVERNANCE.md` | Gouvernance (statuts, niveaux de confiance) |
| Metadata Registry | `daena/Metadata/REGISTRY.md` | Registre de routage de la mémoire |
| P0-1S Final Verdict | `docs/memory/assessments/daena-dtai/p0-1s/FINAL_VERDICT.md` | Verdict P0-1S (APPROVED WITH LIMITATIONS) |
| P0-1S Security Changes | `docs/memory/assessments/daena-dtai/p0-1s/SECURITY_CHANGES.md` | Modifications de sécurité P0-1S |
| P0-1S Persistence & Audit | `docs/memory/assessments/daena-dtai/p0-1s/PERSISTENCE_AND_AUDIT.md` | Persistance et audit P0-1S |
| daena INDEX | `daena/INDEX.md` | Index consolidé |

---

## 13. Verdict final

**READY WITH CONDITIONS**

### Justification

Tous les composants techniques nécessaires existent et sont robustes (KnowledgeManager, KnowledgeCollectionManager, RAGPipeline, EngineeringMemoryService, CapabilityAuthorizationService, AgentPrincipal, PermissionService, AuditStore). Le SDK `mcp` 2.3.0 est installé. Aucun serveur MCP natif n'existe encore à créer (c'est l'objet de la phase 3).

Cependant, les conditions suivantes doivent être remplies avant l'implémentation de la phase 3 :

| # | Condition | Critère de sortie |
|---|-----------|-------------------|
| C1 | Implémenter un serveur MCP autonome (processus séparé de l'API FastAPI) | Code serveur MCP existant et testable |
| C2 | Câbler l'authentification client MCP vers `AgentPrincipal` | `verify_trusted_principal()` appelé pour chaque requête MCP |
| C3 | Câbler l'autorisation des appels MCP vers `CapabilityAuthorizationService.authorize()` | `authorize()` appelé avant tout retrieval/exécution |
| C4 | Persister durablement les décisions d'autorisation | `AuditStore` écrit à chaque décision, test de redémarrage |
| C5 | Rendre l'audit obligatoire (pas de `_audit_store = None` silencieux) | Erreur levée si store d'audit indisponible |
| C6 | Exposer uniquement des outils MCP read-only (7-11 outils) | Aucun outil d'écriture exposé |
| C7 | Valider l'interopérabilité OpenCode et Cline | Test d'interopérability réussi |
| C8 | Créer les fichiers de configuration exemples non intrusifs | Fichiers dans le dépôt, documentation |
| C9 | Revue de sécurité indépendante avant exposition | Rapport de revue sans blocant critique |

Une fois ces conditions remplies, le verdict pourra être promu à `READY FOR IMPLEMENTATION` pour la phase 3 (implémentation effective du serveur MCP DAĒNĀ).

---

**Aucun fichier de production n'a été modifié durant cette phase 2.** Lecture seule stricte. Aucun commit. Aucune migration. Aucune nouvelle base de données.

**Rapport consolidé établi à partir des quatre rapports de subagents (Agents 1 à 4), tous lus et vérifiés.**