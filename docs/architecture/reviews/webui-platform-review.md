# ETHAN WebUI — Architecture Review

**Date** : 2026-09-09
**Scope** : Projects, Knowledge, AI, Integrations, Library, Settings, Chat
**Reviewer** : CTO / Principal Architect
**Verdict** : **GO**

---

## 1. Méthodologie

Revue exhaustive de l'architecture WebUI et de son intégration avec le Core ETHAN :

1. **Analyse statique** : recherche de patterns anti-architecturaux (imports directs Core, accès DB, logique métier frontend)
2. **Revue de code** : examination des composants, hooks, stores, et routes API
3. **Tests** : exécution des suites de tests Python et TypeScript
4. **Validation** : build complet et vérification de type

---

## 2. Résumé Exécutif

| Critère | Statut | Notes |
|---------|--------|-------|
| Source de vérité unique | ✅ | Core est la seule source de vérité |
| Pas de duplication providers | ✅ | ProviderManager Core uniquement |
| Pas de duplication RAG | ✅ | RAGPipeline Core uniquement |
| Pas de logique métier frontend | ✅ | UI pure, délègue au Core |
| Pas d'accès direct DB | ✅ | Aucun import asyncpg/psycopg dans WebUI |
| Pas d'accès direct Qdrant | ✅ | Aucun QdrantClient dans WebUI |
| Pas de Runtime bypass | ✅ | Tout passe par l'API |
| Sécurité | ✅ | JWT HttpOnly, RBAC, pas de secrets frontend |
| Migrations | ✅ | Aucune migration cassée |
| Incohérences API | ✅ | API cohérente |
| Code mort | ⚠️ | Commentaire obsolète (P2) |
| Régressions | ✅ | Aucune régression détectée |

---

## 3. Findings Détaillés

### 3.1. Source de Vérité

**Statut** : ✅ **OK**

- **Core** (`core/`) est la seule source de vérité pour :
  - Providers LLM (`core/llm/provider_manager.py`)
  - RAG (`core/rag/pipeline.py`)
  - Documents (`core/projects/`)
  - Knowledge (`core/knowledge/`)
  - Agents (`core/agents/`)
  - Skills (`core/skills/`)
  - Memory (`core/state/`)

- **WebUI** (`interfaces/webui/src/`) ne contient que :
  - État UI (Zustand stores)
  - Composants d'affichage
  - Hooks de gestion d'état local
  - Client API léger (`lib/api/client.ts`)

**Preuve** : Aucun import `from core.*` dans `interfaces/webui/src/`.

### 3.2. Duplication de Providers

**Statut** : ✅ **OK**

- **ProviderManager** (`core/llm/provider_manager.py`) est le seul gestionnaire de providers
- Le router `interfaces/api/routers/providers.py` est une passerelle HTTP sans logique métier
- **WebUI** utilise `useActiveModel` hook qui délègue au Core via l'API

**Aucune classe provider dupliquée** dans la WebUI.

### 3.3. Duplication RAG

**Statut** : ✅ **OK**

- **RAGPipeline** (`core/rag/pipeline.py`) est le seul pipeline RAG
- **WebUI** ne parse ni n'embede jamais de documents
- L'ingestion est déléguée au Core via `POST /v1/projects/{id}/documents`

### 3.4. Logique Métier Frontend

**Statut** : ✅ **OK**

- **use-chats.ts** : gestion d'état UI uniquement (streaming buffer, optimistic rendering)
- **use-active-model.ts** : délégation au Core via `PUT /providers/{id}/default`
- **use-active-agent.ts** : délégation au Core via API
- **projects.ts store** : délègue au Core via `/v1/projects*`

**Aucune règle métier** (validation, calcul, décision) dans le frontend.

### 3.5. Accès Direct à la Base de Données

**Statut** : ✅ **OK**

- **Aucun import** de `asyncpg`, `psycopg2`, `create_engine` dans `interfaces/webui/`
- **Toutes les données** passent par l'API (`/v1/*`, `/api/*`)
- **PostgreSQL** n'est accessible que depuis `core/state/` et `interfaces/api/`

### 3.6. Accès Direct à Qdrant

**Statut** : ✅ **OK**

- **Aucun import** de `QdrantClient` dans `interfaces/webui/`
- **Qdrant** n'est accessible que depuis `core/rag/vector_store.py`

### 3.7. Runtime Bypasses

**Statut** : ✅ **OK**

- **Toutes les requêtes** passent par l'API FastAPI (`interfaces/api/`)
- **Aucun appel direct** au Core depuis le frontend
### 3.8. Sécurité

**Statut** : ✅ **OK**

- **JWT HttpOnly** : cookie `ethan_token` inaccessible au JavaScript
- **RBAC** : permissions vérifiées côté serveur (`core/auth/__init__.py`)
- **Pas de secrets** dans le code frontend
- **CORS** : configuré correctement
- **Validation** : toutes les entrées sont validées côté serveur

### 3.9. Migrations

**Statut** : ✅ **OK**

- **Aucune migration cassée** détectée
- **Schéma PostgreSQL** cohérent avec le code
- **Migrations applicatives** (stores Zustand) gérées via `onRehydrateStorage`

### 3.10. Incohérences API

**Statut** : ✅ **OK**

- **API v1** (`/v1/*`) : cohérente, bien documentée
- **API providers** (`/api/providers/*`) : cohérente
- **SSE streaming** : implémenté correctement dans `client.ts`

### 3.11. Code Mort

**Statut** : ⚠️ **P2**

| Fichier | Ligne | Issue |
|---------|-------|-------|
| `interfaces/api/routers/providers.py` | 141 | Commentaire "DOUBLON avec registry.py" obsolète |

### 3.12. Régressions

**Statut** : ✅ **OK**

- **Tests Python** : 94 passed
- **Tests TypeScript** : 29 passed
- **Build** : ✓ Compiled successfully
- **Type checking** : ✓ No errors

---

## 4. Architecture Validée

### 4.1. Flux de Données

```
┌─────────────────────────────────────────────────────────────────┐
│                        WebUI (Next.js)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Components  │  │    Hooks     │  │   Zustand Stores     │  │
│  │  (UI only)   │←─│  (state)     │←─│   (UI state only)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│                    ┌──────────────────┐                         │
│                    │   API Client     │                         │
│                    │   (lib/api/*)    │                         │
│                    └──────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (FastAPI)                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Routers (v1, providers, projects, knowledge, ...)       │   │
│  │  - Validation                                             │   │
│  │  - RBAC                                                   │   │
│  │  - Délégation au Core                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Core ETHAN                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │  LLM       │ │  RAG       │ │  Projects  │ │  Knowledge │   │
│  │  Providers │ │  Pipeline  │ │  Manager   │ │  Manager   │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │  Agents    │ │  Skills    │ │  Memory    │ │  State     │   │
│  │  Manager   │ │  Store     │ │  Store     │ │  (Redis/PG)│   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2. Composants Validés

| Composant | Rôle | Délègue au Core | Statut |
|-----------|------|-----------------|--------|
| `AssistantInput` | Saisie utilisateur | via `onSend`, `onPlan`, `onAgent` | ✅ |
| `AssistantChat` | Affichage messages | via `useChats` | ✅ |
| `useChats` | État conversation | via `/v1/chat/*` | ✅ |
| `useActiveModel` | Sélection provider | via `/api/providers/*` | ✅ |
| `useActiveAgent` | Sélection agent | via `/v1/agents/*` | ✅ |
| `projects.ts` | État projets | via `/v1/projects/*` | ✅ |
| `agent.store.ts` | Sélection agent (UI) | Non (UI state) | ✅ |
| `model.store.ts` | Sélection modèle (UI) | Non (UI state) | ✅ |

---

## 5. Recommandations

### 5.1. P2 — Dettes Techniques Mineures

1. **Nettoyer le commentaire obsolète** dans `interfaces/api/routers/providers.py:141`
2. **Documenter les TODO** dans `assistant-input.tsx` (voice, file picker, tools, search)

### 5.2. P3 — Améliorations Futures

1. **Tests d'intégration** : ajouter des tests E2E pour le flux chat complet
2. **Monitoring** : ajouter des métriques de performance frontend
3. **Accessibilité** : auditer les composants pour WCAG 2.1

---

## 6. Verdict

### **GO**

L'architecture respecte les principes ETHAN :
- ✅ **Core est la source de vérité**
- ✅ **WebUI est une interface pure**
- ✅ **Aucune duplication de logique métier**
- ✅ **Sécurité validée**
- ✅ **Aucune régression**

Les fonctionnalités implémentées (Projects, Knowledge, AI, Integrations, Library, Settings, Chat) sont architecturalement saines et prêtes pour la production contrôlée.

---

**Signé** : CTO / Principal Architect
**Date** : 2026-09-09