# ETHAN — Knowledge, Skills, Tools/MCP, Memory : Audit Open-WebUI vs ETHAN

> **Statut** : Audit d'architecture
> **Portée** : Knowledge, Documents, Skills, Tools, Functions, MCP, Memory
> **Principe** : Conserver les patterns Open-WebUI pertinents, sans inventer une UX ETHAN arbitraire. Toute capacité appartient au Core/Runtime avant d'être exposée dans une interface.

---

## 1. Vue d'ensemble

Open-WebUI organise ses capacités autour de **collections** (Knowledge), **marketplace** (Skills/Functions), **serveurs** (Tools/MCP) et **mémoire persistante** (Memory). Chaque capacité est sélectionnable dans le chat et injectée dans le contexte LLM.

ETHAN possède déjà les briques Core correspondantes. Ce document mappe chaque pattern Open-WebUI vers l'existant ETHAN et identifie les écarts à combler.

```
Open-WebUI                          ETHAN
─────────────────                    ─────
Knowledge collections   ────────►   KnowledgeManager + RAGPipeline
Documents + upload      ────────►   RAGPipeline.ingest()
Skills marketplace       ────────►   SkillStore
Functions/Pipelines     ────────►   FunctionManager
Tools/MCP servers       ────────►   ToolServerManager
Memory persistante      ────────►   CoreWebUIStore (facts/events)
```

---

## 2. KNOWLEDGE

### 2.1 Implémentation Open-WebUI

**Workflow utilisateur**
1. L'utilisateur crée une **collection** (ex. "Documentation ETHAN").
2. Il **upload** des fichiers (PDF, TXT, MD, DOCX) ou colle du texte.
3. Open-WebUI **ingère** : chunking + embeddings + index vectoriel.
4. Dans le chat, l'utilisateur **sélectionne** une ou plusieurs collections.
5. Le backend **retrieve** les chunks pertinents et les injecte dans le prompt.
6. Les **citations** (sources) sont affichées sous la réponse.

**Modèle de données**
```
Collection
├── id, name, description
├── user_id, permissions (read/write)
├── created_at, updated_at
└── documents[]

Document
├── id, collection_id
├── filename, content_type, size
├── content (chunké)
├── metadata (source, date, tags)
└── chunks[]
```

**API**
- `GET/POST /api/v1/knowledge` — collections
- `POST /api/v1/knowledge/{id}/file/add` — upload
- `POST /api/v1/knowledge/{id}/file/update` — ingestion
- `GET /api/v1/knowledge/{id}/file` — documents
- `DELETE /api/v1/knowledge/{id}/file/{file_id}` — suppression
- `POST /api/v1/retrieval` — retrieval RAG
- `POST /api/v1/chat/completions` — avec `files: [{type: "collection", id}]`

**Interface**
- Page "Workspace → Knowledge" : liste des collections, upload, aperçu des documents.
- Sélecteur de collections dans le composer (icône 📚).
- Citations cliquables sous les réponses.

**Utilisation dans Chat**
Le payload de chat inclut `files: [{type: "collection", id: "..."}]`. Le backend retrieves les chunks et les injecte comme contexte système avec attribution de source.

### 2.2 Existant ETHAN

**`KnowledgeManager`** (`core/knowledge/manager.py`)
- Graphe de nœuds (`KnowledgeNode`) avec types (`concept`, `fact`, `rule`, `entity`, `source`, `document`).
- Connexions typées (`KnowledgeConnection`) avec force.
- Recherche déterministe (label/source/content).
- `ingest_into_rag()` : expose un nœud au RAG.

**`RAGPipeline`** (`core/rag/pipeline.py`)
- `ingest(content, title, source, metadata)` : chunking + embeddings + persistance.
- `retrieve(query, top_k)` : retrieval vectoriel.
- `build_context(query)` : contexte borné avec attribution de source.
- `list_documents()`, `get_document()`, `delete_document()`.

**Routes API existantes** (`interfaces/api/routers/v1.py`)
- `GET/POST /v1/knowledge` — nœuds
- `GET/POST /v1/rag/documents` — documents
- `POST /v1/rag/retrieve` — retrieval
- `POST /v1/rag/context` — contexte

### 2.3 Écarts et mapping

| Pattern Open-WebUI | Existant ETHAN | Écart |
|---|---|---|
| Collection | `KnowledgeNode` type `document` | Pas de notion de collection regroupant plusieurs documents |
| Upload fichier | `RAGPipeline.ingest(content)` | Pas d'upload binaire (PDF/DOCX) |
| Sélection dans chat | `ChatPipeline._build_llm_messages` (RAG auto) | Pas de sélection explicite de collection par l'utilisateur |
| Citations | `RAGContext` (attribution source) | Pas d'affichage structuré des citations dans l'UI |
| Permissions | — | Pas de permissions par collection |

**Décision** : introduire une entité **Collection** dans le Core (`core/knowledge/collections.py`) qui regroupe des documents RAG. La WebUI affiche les collections et envoie `collection_ids` dans le chat.

---

## 3. SKILLS

### 3.1 Implémentation Open-WebUI

**Workflow utilisateur**
1. L'utilisateur parcourt le **marketplace** (galerie) ou crée une skill.
2. Il **installe** une skill (import de code Markdown).
3. Il **active/désactive** la skill.
4. Dans le chat, il **sélectionne** les skills actives.
5. Le contenu de la skill est injecté dans le **system prompt**.

**Modèle de données**
```
Skill
├── id, name, description
├── content (Markdown : instructions + variables)
├── meta (tags, author, version)
├── is_active
└── user_id
```

**API**
- `GET/POST /api/v1/skills`
- `GET/PUT/DELETE /api/v1/skills/{id}`
- `POST /api/v1/skills/{id}/toggle`
- `POST /api/v1/skills/import` — import depuis la galerie

**Interface**
- Page "Workspace → Skills" : liste, création, édition Markdown, activation.
- Sélecteur de skills dans le composer (icône ⚡).

**Utilisation dans Chat**
Le payload inclut `skills: [{id, content}]`. Le backend concatène les contenus dans le system prompt.

### 3.2 Existant ETHAN

**`SkillStore`** (`core/skills/store.py`)
- CRUD complet : `list_skills`, `get_skill`, `create_skill`, `update_skill`, `delete_skill`.
- `toggle_skill()` : activation/désactivation.
- `search_skills(q)` : recherche par nom/description/tags.
- Champs Open-WebUI : `content`, `meta.tags`, `is_active`.

**`ChatPipeline`** (`core/chat/pipeline.py`)
- `_build_llm_messages()` : injecte les skills actives dans le system prompt via `skill_ids`.

**Routes API existantes**
- `GET/POST /v1/skills`
- `GET/PUT/DELETE /v1/skills/{id}`
- `POST /v1/skills/{id}/toggle`
- `POST /v1/skills/{id}/execute`
- `GET /v1/skills/search`

### 3.3 Écarts et mapping

| Pattern Open-WebUI | Existant ETHAN | Écart |
|---|---|---|
| Marketplace | — | Pas de galerie de skills |
| Import | — | Pas de route d'import |
| Sélection dans chat | `skill_ids` dans `ChatPipeline.run()` | Le frontend n'envoie pas encore `skill_ids` |
| Édition Markdown | `content` (Markdown) | L'éditeur WebUI n'existe pas encore |
| Permissions | — | Pas de permissions par skill |

**Décision** : le Core est prêt. Il manque l'UI (page Skills, sélecteur dans le composer) et l'envoi de `skill_ids` dans le chat. La galerie/marketplace est un ajout ultérieur (hors périmètre immédiat).

---

## 4. TOOLS / MCP

### 4.1 Implémentation Open-WebUI

**Workflow utilisateur**
1. L'utilisateur **configure** un serveur MCP (URL, auth, headers).
2. Open-WebUI **découvre** les outils exposés par le serveur.
3. L'utilisateur **active** les outils souhaités.
4. Dans le chat, les outils activés sont disponibles pour le LLM (function calling).
5. Les **appels d'outils** sont affichés dans l'UI (nom, durée, statut).

**Modèle de données**
```
ToolServer
├── id, name, url
├── auth (type, config)
├── enabled
└── tools[]

Tool
├── id, name, description
├── parameters (JSON Schema)
└── enabled
```

**API**
- `GET/POST /api/v1/tools/servers`
- `GET/PUT/DELETE /api/v1/tools/servers/{id}`
- `POST /api/v1/tools/servers/{id}/status`
- `GET /api/v1/tools` — outils découverts

**Interface**
- Page "Workspace → Tools" : liste des serveurs, configuration, activation.
- Affichage des appels d'outils dans le chat (cartes avec statut).

**Utilisation dans Chat**
Le LLM reçoit la liste des outils activés (JSON Schema). Il émet des `tool_calls` ; le backend exécute et renvoie les résultats.

### 4.2 Existant ETHAN

**`ToolServerManager`** (`core/tools/servers.py`)
- `register(name, url, description, auth_type, auth_config, enabled)`.
- `list(enabled)`, `get(id)`, `update(id, data)`, `delete(id)`.
- `set_status(id, status)` : connexion/déconnexion.

**`FunctionManager`** (`core/tools/functions.py`)
- `create_function(name, description, parameters, code)`.
- `create_pipeline(name, steps)` : composition ordonnée de fonctions.
- CRUD complet pour fonctions et pipelines.

**Routes API existantes**
- `GET/POST /v1/tools/servers`
- `GET/PUT/DELETE /v1/tools/servers/{id}`
- `PUT /v1/tools/servers/{id}/status`
- `GET/POST /v1/functions`, `GET/POST /v1/pipelines`

### 4.3 Écarts et mapping

| Pattern Open-WebUI | Existant ETHAN | Écart |
|---|---|---|
| Découverte d'outils | — | Pas de découverte automatique des outils MCP |
| Exécution d'outils | `FunctionManager` (définition) | Pas d'exécution réelle dans le ChatPipeline |
| Affichage dans chat | `AssistantMessage.tools` (type frontend) | Le pipeline n'émet pas d'événements `tool_call` |
| Permissions | — | Pas de permissions par outil |

**Décision** : le Core gère la **configuration** des serveurs. L'**exécution** des outils dans le ChatPipeline (function calling) est un ajout Phase 2. L'UI affichera les appels via les événements SSE `tool_call`.

---

## 5. MEMORY

### 5.1 Distinction conceptuelle (Open-WebUI)

| Concept | Définition | Persistance | Injection |
|---|---|---|---|
| **Memory** | Faits persistants sur l'utilisateur ("l'utilisateur préfère Python") | Durable, globale | System prompt |
| **Knowledge** | Documents structurés (collections) | Durable, par collection | Retrieval RAG |
| **Conversation context** | Historique du fil de discussion | Par conversation | Messages LLM |
| **RAG** | Mécanisme de retrieval sur documents | Index vectoriel | Contexte système |

**Règle Open-WebUI** : ces quatre concepts sont **distincts** dans l'UI :
- Memory → page "Settings → Personalization → Memory"
- Knowledge → page "Workspace → Knowledge"
- Conversation → le fil de chat lui-même
- RAG → invisible (mécanisme sous-jacent)

### 5.2 Existant ETHAN

**`CoreWebUIStore`** (`core/state/webui_store.py`)
- `list_facts`, `create_fact`, `search_facts` — faits persistants.
- `list_events`, `append_event` — événements mémoire.
- `search_memory(q)` — recherche mémoire.

**`ChatStore`** (`core/state/chats.py`)
- `list_messages(chat_id)` — historique de conversation.
- `get_branch(chat_id)` — arbre de messages.

**`RAGPipeline`** — retrieval documentaire.

**Routes API existantes**
- `GET/POST /v1/memory/facts`
- `GET /v1/memory/events`
- `POST /v1/memory/ingest`
- `GET /v1/memory/search`

### 5.3 Écarts et mapping

| Concept | Existant ETHAN | Écart |
|---|---|---|
| Memory (faits) | `CoreWebUIStore.list_facts` | Pas d'injection dans le ChatPipeline |
| Knowledge | `KnowledgeManager` + `RAGPipeline` | Pas de collections |
| Conversation context | `ChatStore.get_branch` | ✅ Fonctionnel |
| RAG | `RAGPipeline.build_context` | ✅ Fonctionnel (auto dans pipeline) |

**Décision** : injecter les **faits mémoire** dans le system prompt du ChatPipeline (comme les skills). L'UI distinguera clairement : Memory (faits personnels) vs Knowledge (documents) vs Conversation (fil).

---

## 6. Synthèse des décisions

| Capacité | Pattern Open-WebUI conservé | Implémentation ETHAN |
|---|---|---|
| Knowledge | Collections + upload + sélection dans chat | `KnowledgeCollection` (Core) + `RAGPipeline` |
| Skills | Marketplace + activation + sélection | `SkillStore` (✅) + UI + `skill_ids` dans chat |
| Tools/MCP | Serveurs + découverte + exécution | `ToolServerManager` (✅ config) + function calling (Phase 2) |
| Functions | Pipelines composables | `FunctionManager` (✅) |
| Memory | Faits persistants distincts du RAG | `CoreWebUIStore` + injection dans ChatPipeline |

**Règle d'or** : la WebUI ne stocke jamais ces capacités. Elle affiche et envoie des actions. Le Core possède les données et la logique.

---

## 7. Prochaines étapes d'implémentation

1. **Collections Knowledge** : `core/knowledge/collections.py` + routes `/v1/knowledge/collections`.
2. **Injection mémoire** : ajouter les faits au system prompt du `ChatPipeline`.
3. **UI Skills** : page Skills (liste, création, édition, activation) + sélecteur dans le composer.
4. **UI Knowledge** : page Collections (upload, documents, sélection).
5. **UI Tools** : page Serveurs (configuration, activation) + affichage des appels dans le chat.
6. **UI Memory** : page Faits (liste, création, suppression) distincte de Knowledge.