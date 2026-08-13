# Open-WebUI — Functional Reference

**Source** : `examples/open-webui/` (v0.9.1, non suivi par git)
**Objectif** : Comprendre **comment** Open-WebUI fonctionne — architecture, flux de données, modèles, workflows — pour servir de référence fonctionnelle à la WebUI ETHAN.

---

## 1. Architecture globale

### Backend (Python FastAPI + SQLAlchemy)

```
backend/open_webui/
├── main.py              # Point d'entrée FastAPI, monte tous les routers
├── config.py            # Configuration (env vars, secrets)
├── constants.py         # Constantes (permissions, types)
├── functions.py         # Fonctions utilitaires (auth, validation)
├── tasks.py             # Tâches Celery (background jobs)
├── routers/             # 29 routers REST
├── models/              # 23 modèles SQLAlchemy (ORM)
├── services/            # ethan_client.py (client HTTP vers ETHAN Core)
├── retrieval/           # Pipeline RAG (loaders, embeddings, vector stores)
├── socket/              # WebSocket (socket/main.py, socket/utils.py)
├── tools/               # Outils intégrés (builtin.py)
├── utils/               # Utilitaires (auth, LLM, migrations)
├── internal/            # Code interne (db, migrations)
└── migrations/          # Alembic migrations
```

**29 routers** : `analytics`, `automations`, `audio`, `auths`, `calendar`, `channels`, `chats`, `configs`, `evaluations`, `files`, `folders`, `functions`, `groups`, `images`, `knowledge`, `memories`, `models`, `notes`, `ollama`, `openai`, `prompts`, `retrieval`, `scim`, `skills`, `tasks`, `terminals`, `tools`, `users`, `utils`.

**23 modèles SQLAlchemy** : `Auth`, `Chat`, `ChatFile`, `ChatMessage`, `File`, `Folder`, `Function`, `Group`, `Knowledge`, `Memory`, `Model`, `Note`, `OauthSession`, `Prompt`, `Skill`, `Tag`, `Tool`, `User`, `SharedChat`, `AccessGrant`, `Automation`, `Calendar`, `Evaluation`, `Feedback`, `PromptHistory`.

### Frontend (SvelteKit + TypeScript)

```
src/
├── routes/
│   ├── (app)/           # Routes authentifiées (chat, workspace, admin, etc.)
│   ├── auth/            # Login, register, reset password
│   ├── +layout.svelte   # Layout racine
│   └── +error.svelte    # Page d'erreur
├── lib/
│   ├── apis/            # Clients API (29 modules, un par domaine)
│   ├── components/      # Composants Svelte (chat, layout, workspace, admin, etc.)
│   ├── stores/          # Stores Svelte (état global)
│   ├── types/           # Types TypeScript
│   ├── utils/           # Utilitaires
│   ├── workers/         # Web Workers (pyodide, tts)
│   └── i18n/            # Internationalisation
└── app.html             # Template HTML
```

### Flux de données

```
Frontend SvelteKit
   │  fetch("/api/v1/...")  [Authorization: Bearer <token>]
   │  ou WebSocket (socket.io) pour le streaming
   ▼
Backend FastAPI (port 8080)
   │  auth middleware (JWT)
   │  routers → modèles SQLAlchemy → PostgreSQL
   │  services → providers LLM (Ollama, OpenAI, etc.)
   │  retrieval → embeddings → vector store (Qdrant/Pinecone/Chroma)
   ▼
Providers LLM (Ollama, OpenAI, Anthropic, etc.)
```

---

## 2. CHAT

### Composer (MessageInput.svelte)

**Route** : `/chat` (page principale)
**Composant** : `src/lib/components/chat/MessageInput.svelte`

**Fonctionnalités** :
- Zone de texte avec support du multi-ligne (Shift+Enter pour un saut de ligne, Enter pour envoyer)
- Détection automatique du mode "continuer" (Ctrl+Enter)
- Attachments : pièces jointes via `FileNav.svelte` (PDF, images, documents)
- Tools : sélection des outils (MCP, fonctions) via `ToolServersModal.svelte`
- Knowledge : sélection des collections de connaissance via `KnowledgeSelector`
- Skills : sélection des skills via `SkillsSelector`
- Prompts : sélection des prompts prédéfinis via `PromptSelector`
- Model selector : `ModelSelector.svelte` (dans `src/lib/components/chat/ModelSelector/`)
- Voice input : micro intégré (KokoroWorker)
- Actions : bouton d'envoi, bouton d'annulation, bouton de régénération

**Stores utilisés** : `models`, `settings`, `tools`, `toolServers`, `knowledge`, `skills`, `functions`, `prompts`, `mobile`, `config`, `showCallOverlay`

**API** : `src/lib/apis/chats.ts` → `POST /api/v1/chat` (streaming via SSE)

### Messages (Messages.svelte)

**Composant** : `src/lib/components/chat/Messages.svelte` + `src/lib/components/chat/Messages/`

**Fonctionnalités** :
- Rendu des messages utilisateur et assistant
- Streaming en temps réel (token par token) via SSE
- Markdown rendering (marked.js + DOMPurify)
- Code blocks avec syntax highlighting (highlight.js)
- Images intégrées (base64 ou URLs)
- Artifacts (sorties de code exécutable)
- Citations (sources RAG affichées en bas de message)
- Message actions : copier, régénérer, épingler, éditer, supprimer, partager, télécharger
- Context menus : clic droit sur message pour actions rapides
- Typing indicator (assistant en train de taper)
- Suggestions de réponses (Suggestions.svelte)

**Modèle de données** (Message) :
```typescript
{
  id: string;
  chat_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
  model: string;
  user_id: string;
  done: boolean;
  action: "stream" | "stop";
  files?: File[];
  source_documents?: Document[];
  citations?: Citation[];
  info?: {
    usage?: { prompt_tokens, completion_tokens, total_tokens };
    duration?: number;
  };
}
```

### Streaming

**Mécanisme** : Server-Sent Events (SSE) via `src/lib/apis/chats.ts` → `POST /api/v1/chat`

**Flux** :
1. Le frontend envoie la requête avec `stream: true`
2. Le backend répond avec `text/event-stream`
3. Chaque token est envoyé comme un événement SSE
4. Le frontend accumule les tokens et met à jour l'affichage en temps réel
5. Le WebSocket (`socket/main.py`) est utilisé pour les événements de statut (nouveau message, mise à jour de chat)

**Store** : `chatId`, `chats`, `pinnedChats`, `tags`, `folders` (dans `src/lib/stores/index.ts`)

### Model Selector

**Composant** : `src/lib/components/chat/ModelSelector.svelte` + `src/lib/components/chat/ModelSelector/Selector.svelte`

**Fonctionnalités** :
- Sélection du modèle principal (dropdown)
- Sélection de modèles secondaires (multi-select pour comparaison)
- Épinglage des modèles favoris (localStorage via `settings.pinnedModels`)
- Configuration par modèle (paramètres avancés)
- Presets de paramètres (temperature, top_p, max_tokens, etc.)
- Provider connections (Ollama, OpenAI, Anthropic, etc.)

**API** : `src/lib/apis/models.ts` → `GET /api/v1/models`, `GET /api/vl/ollama/loaded/models`, `GET /api/v1/openai/loaded/models`

**Store** : `models` (Writable<Model[]>)

### Attachments

**Composant** : `src/lib/components/chat/FileNav/FileNav.svelte`

**Fonctionnalités** :
- Upload de fichiers (PDF, images, documents)
- Association aux messages
- Prévisualisation (PDF, images)
- Extraction de texte (OCR pour images)
- RAG : les fichiers sont ingérés dans le pipeline de connaissance

**API** : `src/lib/apis/files.ts` → `POST /api/v1/files/`, `GET /api/v1/files/`, `GET /api/v1/files/{id}/content`

### Tools

**Composant** : `src/lib/components/chat/ChatControls.svelte` (section tools)

**Fonctionnalités** :
- Découverte des outils (MCP servers, fonctions intégrées)
- Activation/désactivation par conversation
- Configuration des paramètres d'outils
- Affichage des résultats d'outils dans le chat
- Sélection manuelle des outils à utiliser

**API** : `src/lib/apis/tools.ts` → `GET /api/v1/tools/`, `GET /api/v1/tools/{tool_id}/specs`

**Store** : `tools` (Writable), `toolServers` (Writable)

### Knowledge

**Composant** : `src/lib/components/chat/ChatControls.svelte` (section knowledge)

**Fonctionnalités** :
- Sélection des collections de connaissance par conversation
- Activation/désactivation
- Affichage des sources dans les réponses (citations)
- Upload de documents directement depuis le chat

**API** : `src/lib/apis/knowledge.ts` → `GET /api/v1/knowledge/`, `POST /api/v1/knowledge/{id}/search`

**Store** : `knowledge` (Writable<Document[] | null>)

### Skills

**Composant** : `src/lib/components/chat/ChatControls.svelte` (section skills)

**Fonctionnalités** :
- Sélection des skills par conversation
- Activation/désactivation
- Configuration des paramètres de skills
- Affichage des résultats dans le chat

**API** : `src/lib/apis/skills.ts` → `GET /api/v1/skills/`, `POST /api/v1/skills/{id}/use`

**Store** : `skills` (Writable)

### Actions (Message Actions)

**Composant** : `src/lib/components/chat/Messages/MessageActions.svelte` (ou similaire)

**Actions disponibles** :
- **Copy** : copier le contenu du message
- **Regenerate** : régénérer la réponse
- **Edit** : éditer le message (mode édition inline)
- **Delete** : supprimer le message
- **Pin** : épingler le message
- **Share** : partager le message
- **Download** : télécharger le message
- **Report** : signaler un message (feedback)
- **Continue** : continuer la conversation à partir de ce message

### Context Menus

**Mécanisme** : Clic droit sur un message → menu contextuel

**Actions** :
- Copy content
- Edit message
- Delete message
- Regenerate response
- Pin/Unpin
- Share
- Download as markdown

---

## 3. NAVIGATION

### Sidebar

**Composant** : `src/lib/components/layout/Sidebar.svelte` + `src/lib/components/layout/Sidebar/`

**Structure** :
- **Conversations** : liste des chats (avec recherche, filtres par tags/folders)
- **Workspace** : liens vers les sections (Models, Knowledge, Skills, Tools, Prompts, etc.)
- **Administration** : liens admin (Users, Groups, Configs, etc.)
- **Settings** : paramètres utilisateur et application
- **New Chat** : bouton pour créer une nouvelle conversation
- **Archived Chats** : chats archivés
- **Shared Chats** : chats partagés
- **Folders** : organisation par dossiers
- **Tags** : organisation par tags

**Store** : `chats`, `pinnedChats`, `pinnedNotes`, `tags`, `folders`, `selectedFolder`

### Conversations

**Composant** : `src/lib/components/layout/Sidebar/Chats.svelte`

**Fonctionnalités** :
- Liste des conversations avec titre, date, modèle utilisé
- Recherche dans les conversations
- Archivage/désarchivage
- Partage/départage
- Tags et folders
- Épinglage
- Menu contextuel (supprimer, archiver, partager, renommer)

**API** : `src/lib/apis/chats.ts` → `GET /api/v1/chats/`, `POST /api/v1/chats/{id}/archive`, `POST /api/v1/chats/{id}/share`

### Workspace

**Route** : `/workspace`
**Composant** : `src/lib/components/workspace/`

**Sections** :
- **Models** : gestion des modèles et providers
- **Knowledge** : gestion des collections et documents
- **Skills** : gestion des skills
- **Tools** : gestion des outils et serveurs MCP
- **Prompts** : gestion des prompts prédéfinis
- **Functions** : gestion des fonctions personnalisées
- **Automations** : gestion des automatisations
- **Channels** : gestion des canaux
- **Notes** : gestion des notes
- **Calendar** : gestion du calendrier
- **Evaluations** : gestion des évaluations
- **Terminals** : gestion des serveurs de terminal

### Settings

**Route** : `/settings` (ou via le workspace)
**Composant** : `src/lib/components/chat/Settings/`

**Sections** :
- **User Settings** : profil, préférences, thème, langue
- **Application Settings** : configuration globale, providers, modèles
- **Administration** : gestion des utilisateurs, groupes, permissions
- **Connections** : configuration des providers (Ollama, OpenAI, etc.)
- **Personalization** : thème, langue, layout, raccourcis clavier

**API** : `src/lib/apis/users.ts` → `POST /api/v1/users/{id}/update/settings`

### Administration

**Route** : `/admin`
**Composant** : `src/lib/components/admin/`

**Sections** :
- **Users** : gestion des utilisateurs (CRUD, permissions, groupes)
- **Groups** : gestion des groupes et permissions
- **Configs** : configuration système
- **Analytics** : statistiques d'utilisation
- **System** : état du système, logs, santé

**API** : `src/lib/apis/users.ts`, `src/lib/apis/groups.ts`, `src/lib/apis/configs.ts`, `src/lib/apis/analytics.ts`

### Menus secondaires

- **Command Palette** : Ctrl+K (recherche globale)
- **Inspector** : Ctrl+J (détails de l'élément sélectionné)
- **Search Modal** : Ctrl+Shift+F (recherche dans les chats)
- **Chats Modal** : gestion des conversations
- **Files Modal** : gestion des fichiers
- **Shared Chats Modal** : chats partagés
- **Archived Chats Modal** : chats archivés

### Navigation mobile

**Store** : `mobile` (Writable<boolean>)

**Fonctionnalités** :
- Détection automatique de la taille d'écran
- Menu latéral collapsible (drawer)
- Header adaptatif (compact sur mobile)
- Touch-friendly controls
- Gestures (swipe pour naviguer)

---

## 4. MODELS

### Création

**Route** : `/workspace/models`
**Composant** : `src/lib/components/workspace/Models/`

**Fonctionnalités** :
- Ajout de modèles manuellement (nom, provider, type)
- Découverte automatique (Ollama, OpenAI, etc.)
- Import de modèles depuis des fichiers
- Configuration des paramètres par défaut

**API** : `src/lib/apis/models.ts` → `POST /api/v1/models/`, `GET /api/v1/ollama/loaded/models`

### Configuration

**Composant** : `src/lib/components/workspace/Models/ModelForm.svelte`

**Paramètres** :
- `name` : nom du modèle
- `model` : identifiant du modèle (ex: "gpt-4", "llama3")
- `provider` : fournisseur (Ollama, OpenAI, Anthropic, etc.)
- `type` : type (LLM, embedding, etc.)
- `meta` : métadonnées (context_length, architecture, etc.)
- `params` : paramètres par défaut (temperature, top_p, max_tokens, etc.)
- `preset` : presets de paramètres
- `info` : informations sur le modèle

**Modèle de données** (Model) :
```typescript
{
  name: string;           // Identifiant unique (ex: "ollama/llama3")
  model: string;          // Nom du modèle
  display_name?: string;  // Nom affiché
  description?: string;
  type: "ollama" | "openai" | "anthropic" | "huggingface" | "openai-compatible";
  info?: {
    context_length?: number;
    embedding_length?: number;
    family?: string;
    format?: string;
    parameter_size?: string;
    quant?: string;
  };
  params?: {
    temperature?: number;
    top_p?: number;
    top_k?: number;
    max_tokens?: number;
    repeat_penalty?: number;
    repeat_last_n?: number;
    tfs?: number;
    mirostat?: number;
    mirostat_eta?: number;
    mirostat_tau?: number;
  };
  preset?: Record<string, any>;
  access_control?: Record<string, any>;
}
```

### Sélection

**Composant** : `src/lib/components/chat/ModelSelector.svelte`

**Fonctionnalités** :
- Dropdown avec recherche par nom
- Épinglage des modèles favoris
- Affichage des capabilities (context_length, format, etc.)
- Sélection de modèles secondaires (multi-select)
- Presets de paramètres

**Store** : `models` (Writable<Model[]>)

### Presets

**Composant** : `src/lib/components/workspace/Models/PresetForm.svelte`

**Fonctionnalités** :
- Création de presets de paramètres (temperature, top_p, max_tokens, etc.)
- Application des presets au modèle sélectionné
- Gestion des presets (CRUD)

**API** : `src/lib/apis/models.ts` → `GET /api/v1/models/{model}/presets`, `POST /api/v1/models/{model}/presets`

### Paramètres

**Composant** : `src/lib/components/chat/Settings/ModelSettings.svelte`

**Paramètres disponibles** :
- Temperature (0.0 - 1.0)
- Top P (0.0 - 1.0)
- Top K (0 - 100)
- Max Tokens (0 - 8192+)
- Repeat Penalty (0.0 - 5.0)
- Repeat Last N (0 - 1024)
- TFS (0.0 - 1.0)
- Mirostat (0, 1, 2)
- Mirostat Eta (0.0 - 1.0)
- Mirostat Tau (0.0 - 10.0)
- Min P (0.0 - 1.0)
- NumCtx (context length)
- NumBatch (batch size)
- NumGPU (GPU layers)
- Main GPU
- NumThread (CPU threads)
- NumThreadBatch (batch threads)

### Providers/Connections

**Route** : `/workspace/models` → onglet "Connections"
**Composant** : `src/lib/components/workspace/Models/Connections.svelte`

**Providers supportés** :
- **Ollama** : connexion locale (http://localhost:11434)
- **OpenAI** : clé API
- **Anthropic** : clé API
- **HuggingFace** : clé API
- **OpenAI-Compatible** : URL personnalisée + clé API
- **Azure OpenAI** : endpoint + clé API
- **Google AI** : clé API
- **Mistral** : clé API
- **Groq** : clé API
- **Together** : clé API
- **Cohere** : clé API
- **NVIDIA** : clé API

**API** : `src/lib/apis/models.ts` → `GET /api/v1/models`, `GET /api/v1/ollama/loaded/models`, `GET /api/v1/openai/loaded/models`

---

## 5. KNOWLEDGE

### Documents

**Route** : `/workspace/knowledge`
**Composant** : `src/lib/components/workspace/Knowledge/`

**Fonctionnalités** :
- Liste des collections de connaissance
- Création/édition/suppression de collections
- Upload de documents (PDF, Word, texte, etc.)
- Gestion des métadonnées
- Statut d'ingestion (traité, en cours, erreur)

**API** : `src/lib/apis/knowledge.ts` → `GET /api/v1/knowledge/`, `POST /api/v1/knowledge/`, `GET /api/v1/knowledge/{id}/file/{file_id}/content`

### Collections

**Modèle de données** (Knowledge) :
```typescript
{
  id: string;
  name: string;
  description?: string;
  data: {
    embeddings: string;       // Provider d'embeddings
    embedding_model: string;  // Modèle d'embeddings
    embedding_dimensions: number;
    filename: string;
    file_size: number;
    file_content_type: string;
    source: string;
    status: "uploaded" | "processed" | "error";
    error: string | null;
    timestamps: { created_at, updated_at };
  };
  access_control?: Record<string, any>;
}
```

### Upload

**Composant** : `src/lib/components/workspace/Knowledge/FileUpload.svelte`

**Fonctionnalités** :
- Drag & drop
- Sélection de fichiers
- Prévisualisation
- Extraction de texte (PDF, Word, etc.)
- Chunking (segmentation)
- Embeddings (génération de vecteurs)

**API** : `src/lib/apis/files.ts` → `POST /api/v1/files/`, `POST /api/v1/knowledge/{id}/file/{file_id}/process`

### Ingestion

**Pipeline** : `backend/open_webui/retrieval/`

**Étapes** :
1. **Loading** : extraction du texte (PDF, Word, HTML, etc.) via `loaders/`
2. **Chunking** : segmentation en chunks (RecursiveCharacterTextSplitter, etc.)
3. **Embedding** : génération de vecteurs via le provider configuré
4. **Vector Store** : stockage dans Qdrant/Pinecone/Chroma
5. **Indexing** : indexation pour la recherche

**API** : `src/lib/apis/retrieval.ts` → `POST /api/v1/retrieval/upsert`, `POST /api/v1/retrieval/query`

### Retrieval

**Composant** : `src/lib/components/chat/ChatControls.svelte` (section knowledge)

**Fonctionnalités** :
- Recherche sémantique dans les collections
- Filtrage par similarité
- Affichage des sources dans les réponses
- Citations (numérotées dans le texte)

**API** : `src/lib/apis/knowledge.ts` → `POST /api/v1/knowledge/{id}/search`

### Sélection depuis le chat

**Composant** : `src/lib/components/chat/ChatControls.svelte`

**Fonctionnalités** :
- Sélection des collections de connaissance par conversation
- Activation/désactivation
- Affichage des sources dans les réponses

### Permissions

**Fonctionnalités** :
- Contrôle d'accès par utilisateur/groupe
- Permissions de lecture/écriture
- Partage des collections

**API** : `src/lib/apis/knowledge.ts` → `PUT /api/v1/knowledge/{id}/access/update`

### UI

**Composant** : `src/lib/components/workspace/Knowledge/Knowledge.svelte`

**Structure** :
- Liste des collections (avec statut, nombre de fichiers)
- Bouton d'upload
- Bouton de création
- Menu contextuel (supprimer, partager, paramètres)
- Vue détaillée (fichiers, métadonnées, logs d'ingestion)

---

## 6. SKILLS

### Création

**Route** : `/workspace/skills`
**Composant** : `src/lib/components/workspace/Skills/`

**Fonctionnalités** :
- Création de skills personnalisés
- Configuration des paramètres
- Définition des actions
- Gestion des versions

**API** : `src/lib/apis/skills.ts` → `POST /api/v1/skills/`, `PUT /api/v1/skills/{id}`

### Gestion

**Fonctionnalités** :
- Liste des skills (avec statut, version)
- Activation/désactivation
- Mise à jour
- Suppression
- Duplication
- Export/Import

**API** : `src/lib/apis/skills.ts` → `GET /api/v1/skills/`, `DELETE /api/v1/skills/{id}`

### Activation

**Composant** : `src/lib/components/chat/ChatControls.svelte` (section skills)

**Fonctionnalités** :
- Activation par conversation
- Configuration des paramètres par conversation
- Affichage des résultats dans le chat

### Sélection

**Fonctionnalités** :
- Sélection des skills à utiliser
- Priorisation des skills
- Configuration des paramètres

### Configuration

**Modèle de données** (Skill) :
```typescript
{
  id: string;
  name: string;
  description?: string;
  version: string;
  status: "active" | "inactive";
  data: {
    params?: Record<string, any>;
    actions?: Array<{ type: string; params: Record<string, any> }>;
  };
  access_control?: Record<string, any>;
}
```

### Utilisation dans le chat

**Fonctionnalités** :
- Les skills sont exécutés automatiquement ou manuellement
- Les résultats sont affichés dans le chat
- Les skills peuvent modifier le contexte de conversation

---

## 7. TOOLS

### Découverte

**Route** : `/workspace/tools`
**Composant** : `src/lib/components/workspace/Tools/`

**Fonctionnalités** :
- Découverte des outils intégrés
- Découverte des outils MCP
- Découverte des fonctions personnalisées
- Catégorisation des outils

**API** : `src/lib/apis/tools.ts` → `GET /api/v1/tools/`, `GET /api/v1/tools/{tool_id}/specs`

### Activation

**Composant** : `src/lib/components/chat/ChatControls.svelte` (section tools)

**Fonctionnalités** :
- Activation par conversation
- Sélection manuelle des outils
- Configuration des paramètres

### Configuration

**Composant** : `src/lib/components/workspace/Tools/ToolForm.svelte`

**Paramètres** :
- `name` : nom de l'outil
- `description` : description
- `parameters` : schéma JSON des paramètres
- `command` : commande à exécuter
- `env` : variables d'environnement
- `timeout` : durée maximale d'exécution

### Sélection

**Fonctionnalités** :
- Sélection des outils à utiliser
- Priorisation des outils
- Configuration des paramètres par conversation

### Exécution

**Fonctionnalités** :
- Exécution des outils par l'assistant
- Affichage des résultats dans le chat
- Gestion des erreurs
- Retry des outils échoués

**API** : `src/lib/apis/tools.ts` → `POST /api/v1/tools/{tool_id}/call`

---

## 8. MCP (Model Context Protocol)

### Servers

**Route** : `/workspace/tools` → onglet "MCP Servers"
**Composant** : `src/lib/components/workspace/Tools/ToolServers.svelte`

**Fonctionnalités** :
- Découverte des serveurs MCP
- Connexion aux serveurs MCP (stdio, HTTP)
- Gestion des serveurs (CRUD)
- Test de connexion

**API** : `src/lib/apis/tools.ts` → `GET /api/v1/tools/servers`, `POST /api/v1/tools/servers`

### Tools

**Fonctionnalités** :
- Découverte des outils exposés par les serveurs MCP
- Affichage des spécifications (schéma JSON)
- Activation/désactivation

### Configuration

**Paramètres** :
- `name` : nom du serveur
- `url` : URL du serveur (pour HTTP)
- `command` : commande (pour stdio)
- `env` : variables d'environnement
- `auth_type` : type d'authentification
- `auth_config` : configuration d'authentification

### Activation

**Fonctionnalités** :
- Activation par conversation
- Sélection des outils MCP à utiliser

### Utilisation

**Fonctionnalités** :
- Les outils MCP sont exécutés par l'assistant
- Les résultats sont affichés dans le chat
- Les outils MCP peuvent être combinés avec d'autres outils

---

## 9. FILES

### Upload

**Route** : `/workspace/files` (ou depuis le chat)
**Composant** : `src/lib/components/layout/Sidebar/FilesModal.svelte`

**Fonctionnalités** :
- Drag & drop
- Sélection de fichiers
- Prévisualisation
- Association aux conversations

**API** : `src/lib/apis/files.ts` → `POST /api/v1/files/`, `GET /api/v1/files/`

### Gestion

**Fonctionnalités** :
- Liste des fichiers (avec type, taille, date)
- Recherche
- Téléchargement
- Suppression
- Partage

**API** : `src/lib/apis/files.ts` → `GET /api/v1/files/`, `DELETE /api/v1/files/{id}`

### Association aux conversations

**Fonctionnalités** :
- Les fichiers peuvent être associés à des conversations
- Les fichiers sont ingérés dans le pipeline RAG
- Les fichiers sont affichés dans le contexte de la conversation

**API** : `src/lib/apis/chats.ts` → `POST /api/v1/chats/{id}/file/{file_id}`

---

## 10. MEMORY

### Stockage

**Route** : `/workspace/memory` (ou depuis le chat)
**Composant** : `src/lib/components/workspace/Memory.svelte`

**Fonctionnalités** :
- Stockage des souvenirs (messages, faits, préférences)
- Indexation sémantique
- Gestion des expirations

**API** : `src/lib/apis/memories.ts` → `POST /api/v1/memories/`, `GET /api/v1/memories/`

### Affichage

**Fonctionnalités** :
- Liste des souvenirs
- Recherche
- Filtrage par type
- Affichage des métadonnées

### Gestion

**Fonctionnalités** :
- Création/édition/suppression
- Activation/désactivation
- Partage
- Export/Import

### Utilisation

**Fonctionnalités** :
- Les souvenirs sont utilisés automatiquement par l'assistant
- Les souvenirs sont affichés dans le contexte de la conversation
- Les souvenirs peuvent être modifiés depuis le chat

---

## 11. WORKSPACE

### Organisation

**Route** : `/workspace`
**Composant** : `src/lib/components/workspace/`

**Structure** :
- **Models** : gestion des modèles et providers
- **Knowledge** : gestion des collections et documents
- **Skills** : gestion des skills
- **Tools** : gestion des outils et serveurs MCP
- **Prompts** : gestion des prompts prédéfinis
- **Functions** : gestion des fonctions personnalisées
- **Automations** : gestion des automatisations
- **Channels** : gestion des canaux
- **Notes** : gestion des notes
- **Calendar** : gestion du calendrier
- **Evaluations** : gestion des évaluations
- **Terminals** : gestion des serveurs de terminal

### Modèles

Voir section 4.

### Knowledge

Voir section 5.

### Skills

Voir section 6.

### Tools

Voir section 7.

### Prompts

**Route** : `/workspace/prompts`
**Composant** : `src/lib/components/workspace/Prompts.svelte`

**Fonctionnalités** :
- Création/édition/suppression de prompts
- Catégorisation (tags)
- Utilisation depuis le chat
- Variables de substitution

**API** : `src/lib/apis/prompts.ts` → `GET /api/v1/prompts/`, `POST /api/v1/prompts/`

### Fonctions

**Route** : `/workspace/functions`
**Composant** : `src/lib/components/workspace/Functions.svelte`

**Fonctionnalités** :
- Création/édition/suppression de fonctions
- Configuration des paramètres
- Utilisation depuis le chat
- Pipelines (enchaînement de fonctions)

**API** : `src/lib/apis/functions.ts` → `GET /api/v1/functions/`, `POST /api/v1/functions/`

---

## 12. SETTINGS

### Utilisateur

**Route** : `/settings/user`
**Composant** : `src/lib/components/chat/Settings/UserSettings.svelte`

**Paramètres** :
- Profil (nom, email, avatar)
- Mot de passe
- Langue
- Fuseau horaire
- Thème (light, dark, system)
- Notifications

**API** : `src/lib/apis/users.ts` → `POST /api/v1/users/{id}/update/settings`

### Application

**Route** : `/settings`
**Composant** : `src/lib/components/chat/Settings/AppSettings.svelte`

**Paramètres** :
- Configuration générale
- Providers et modèles
- RAG (embeddings, vector store)
- Audio (TTS, STT)
- Images
- Sécurité
- Performance
- Logs

**API** : `src/lib/apis/configs.ts` → `GET /api/v1/configs/`, `POST /api/v1/configs/`

### Administration

**Route** : `/admin`
**Composant** : `src/lib/components/admin/`

**Sections** :
- **Users** : gestion des utilisateurs
- **Groups** : gestion des groupes
- **Configs** : configuration système
- **Analytics** : statistiques
- **System** : état du système

**API** : `src/lib/apis/users.ts`, `src/lib/apis/groups.ts`, `src/lib/apis/configs.ts`, `src/lib/apis/analytics.ts`

### Connexions

**Route** : `/workspace/models` → onglet "Connections"
**Composant** : `src/lib/components/workspace/Models/Connections.svelte`

**Fonctionnalités** :
- Configuration des providers (Ollama, OpenAI, Anthropic, etc.)
- Test de connexion
- Gestion des clés API
- Configuration des paramètres par défaut

**API** : `src/lib/apis/models.ts` → `GET /api/v1/models`, `GET /api/v1/ollama/loaded/models`

### Personnalisation

**Fonctionnalités** :
- Thème (light, dark, system)
- Langue (i18n)
- Layout (sidebar, header)
- Raccourcis clavier
- Command palette
- Inspector
- Atmosphère (animations)

**Store** : `settings` (Writable<Settings>), `theme` (writable)

---

## 13. Modèles de données backend (SQLAlchemy)

### Chat

```python
class Chat(Base):
    id: str (UUID)
    user_id: str
    parent_id: Optional[str]
    title: str
    models: List[str]
    embed_model: str
    timestamp: int
    updated_at: int
    share_id: Optional[str]
    share_settings: Optional[dict]
    pinned: bool
    archived: bool
    category_ids: List[str]
    form: dict
    data: dict
```

### ChatMessage

```python
class ChatMessage(Base):
    id: str (UUID)
    chat_id: str
    user_id: str
    parent_id: Optional[str]
    children_ids: List[str]
    role: str ("user" | "assistant" | "system")
    content: str
    timestamp: int
    model: str
    embedding: Optional[List[float]]
    done: bool
    action: str
    files: List[dict]
    source_documents: List[dict]
    citations: List[dict]
    info: dict
```

### Model

```python
class Model(Base):
    id: str
    user_id: str
    model: str
    name: str
    description: str
    type: str
    timestamp: int
    updated_at: int
    meta: dict
    params: dict
    access_control: Optional[dict]
```

### Knowledge

```python
class Knowledge(Base):
    id: str (UUID)
    user_id: str
    name: str
    description: str
    data: dict
    timestamp: int
    updated_at: int
    access_control: Optional[dict]
```

### File

```python
class File(Base):
    id: str (UUID)
    user_id: str
    type: str
    collection_name: str
    file: dict
    source: str
    status: str
    error: Optional[str]
    updated_at: int
    created_at: int
    expiration_date: Optional[int]
    data: dict
    meta: dict
    access_control: Optional[dict]
```

### Tool

```python
class Tool(Base):
    id: str (UUID)
    name: str
    description: str
    type: str
    user_id: str
    organization_id: Optional[str]
    meta: dict
    access_control: Optional[dict]
    updated_at: int
    created_at: int
```

### Function

```python
class Function(Base):
    id: str (UUID)
    user_id: str
    name: str
    description: str
    code: str
    return_description: str
    parameters: dict
    file_ids: List[str]
    source_uri: Optional[str]
    meta: dict
    access_control: Optional[dict]
    updated_at: int
    created_at: int
```

### Skill

```python
class Skill(Base):
    id: str (UUID)
    user_id: str
    name: str
    description: str
    data: dict
    access_control: Optional[dict]
    updated_at: int
    created_at: int
```

### Prompt

```python
class Prompt(Base):
    id: str (UUID)
    user_id: str
    name: str
    content: str
    timestamp: int
    updated_at: int
    access_control: Optional[dict]
```

### Memory

```python
class Memory(Base):
    id: str (UUID)
    user_id: str
    content: str
    embedding: Optional[List[float]]
    created_at: int
    updated_at: int
    expires_at: Optional[int]
    type: str
    metadata: dict
    access_control: Optional[dict]
```

### Channel

```python
class Channel(Base):
    id: str (UUID)
    user_id: str
    name: str
    description: str
    type: str
    data: dict
    access_control: Optional[dict]
    updated_at: int
    created_at: int
```

### Note

```python
class Note(Base):
    id: str (UUID)
    user_id: str
    title: str
    content: str
    tags: List[str]
    pinned: bool
    user_id: str
    updated_at: int
    created_at: int
    access_control: Optional[dict]
```

### Automation

```python
class Automation(Base):
    id: str (UUID)
    user_id: str
    name: str
    description: str
    trigger: dict
    actions: List[dict]
    enabled: bool
    access_control: Optional[dict]
    updated_at: int
    created_at: int
```

### Calendar

```python
class Calendar(Base):
    id: str (UUID)
    user_id: str
    title: str
    description: str
    start_time: int
    end_time: Optional[int]
    all_day: bool
    recurring: Optional[dict]
    access_control: Optional[dict]
    updated_at: int
    created_at: int
```

### Evaluation

```python
class Evaluation(Base):
    id: str (UUID)
    user_id: str
    name: str
    description: str
    data: dict
    access_control: Optional[dict]
    updated_at: int
    created_at: int
```

### Terminal

```python
class Terminal(Base):
    id: str (UUID)
    user_id: str
    name: str
    command: str
    env: dict
    access_control: Optional[dict]
    updated_at: int
    created_at: int
```

---

## 14. Stores frontend (Svelte)

**Fichier** : `src/lib/stores/index.ts`

**Stores clés** :
| Store | Type | Description |
|---|---|---|
| `user` | Writable<SessionUser> | Utilisateur connecté |
| `settings` | Writable<Settings> | Paramètres utilisateur |
| `models` | Writable<Model[]> | Modèles disponibles |
| `chats` | Writable | Conversations |
| `chatId` | Writable<string> | Conversation active |
| `knowledge` | Writable<Document[] \| null> | Collections de connaissance |
| `tools` | Writable | Outils disponibles |
| `skills` | Writable | Skills disponibles |
| `functions` | Writable | Fonctions personnalisées |
| `toolServer` | Writable | Serveurs d'outils |
| `terminalServers` | Writable | Serveurs de terminal |
| `channels` | Writable | Canaux |
| `channelId` | Writable | Canal actif |
| `pinnedChats` | Writable | Conversations épinglées |
| `pinnedNotes` | Writable | Notes épinglées |
| `tags` | Writable | Tags |
| `folders` | Writable | Dossiers |
| `selectedFolder` | Writable | Dossier sélectionné |
| `mobile` | Writable<boolean> | Mode mobile |
| `socket` | Writable<Socket> | Connexion WebSocket |
| `socketConnected` | Writable<boolean> | État de la connexion |
| `theme` | Writable<string> | Thème (light/dark/system) |
| `config` | Writable<Config> | Configuration système |
| `banners` | Writable<Banner[]> | Bannières |
| `audioQueue` | Writable<AudioQueue> | File audio |
| `chatRequestQueues` | Writable | Files de requêtes chat |

---

## 15. API clients frontend

**Répertoire** : `src/lib/apis/`

**Modules** (29) :
| Module | Fonctionnalités |
|---|---|
| `analytics` | record_event, get_events, get_usage_summary |
| `automations` | CRUD automations, trigger |
| `audio` | config TTS, synthesize |
| `auths` | signin, signup, signout, update profile, api keys, ldap |
| `calendar` | CRUD calendar events |
| `channels` | CRUD channels, messages |
| `chats` | CRUD chats, messages, archive, share, stats |
| `configs` | get/update system config |
| `evaluations` | CRUD evaluations, results |
| `files` | upload, list, search, get, delete, content |
| `folders` | CRUD folders |
| `functions` | CRUD functions, pipelines |
| `groups` | CRUD groups, permissions |
| `images` | config, generate |
| `knowledge` | CRUD knowledge, search, files |
| `memories` | CRUD memories, search |
| `models` | CRUD models, loaded models, presets |
| `notes` | CRUD notes, search |
| `ollama` | CRUD ollama models, pull, delete |
| `openai` | CRUD openai models |
| `prompts` | CRUD prompts |
| `retrieval` | upsert, query, process |
| `scim` | config, status |
| `skills` | CRUD skills, use |
| `tasks` | CRUD tasks, status |
| `terminal` | CRUD terminal servers |
| `tools` | CRUD tools, servers, call |
| `users` | CRUD users, settings, permissions |
| `utils` | utils, version, health |

---

## 16. WebSocket (Socket.IO)

**Fichier** : `backend/open_webui/socket/main.py`

**Événements** :
- `connect` : connexion d'un utilisateur
- `disconnect` : déconnexion
- `chat` : nouveau message dans une conversation
- `chat-update` : mise à jour d'une conversation
- `user-count` : nombre d'utilisateurs connectés
- `notification` : notification système
- `status` : statut du système

**Store** : `socket`, `socketConnected`, `activeUserIds`, `activeChatIds`

---

## 17. Pipeline RAG

**Répertoire** : `backend/open_webui/retrieval/`

**Structure** :
```
retrieval/
├── loaders/       # Extracteurs de texte (PDF, Word, HTML, etc.)
├── models/        # Modèles de données (Chunk, Document, etc.)
├── utils.py       # Utilitaires (tokenisation, etc.)
├── vector/        # Stores vectoriels (Qdrant, Pinecone, Chroma, FAISS)
│   ├── qdrant.py
│   ├── pinecone.py
│   ├── chroma.py
│   └── faiss.py
└── web/           # Loaders web (URL, sitemap)
```

**Pipeline** :
1. **Load** : extraction du texte via `loaders/`
2. **Split** : segmentation en chunks (RecursiveCharacterTextSplitter)
3. **Embed** : génération de vecteurs via le provider configuré
4. **Store** : stockage dans le vector store
5. **Retrieve** : recherche sémantique (similarité cosinus)
6. **Rerank** : réordonnancement (optionnel)
7. **Context** : construction du contexte pour le LLM

**API** : `src/lib/apis/retrieval.ts` → `POST /api/v1/retrieval/upsert`, `POST /api/v1/retrieval/query`
