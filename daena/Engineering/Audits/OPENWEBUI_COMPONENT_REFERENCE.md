# Open-WebUI — Référence des composants et contrats

## Point d'entrée et ownership de l'état

| Couche | Fichiers clés | Responsabilité confirmée |
|---|---|---|
| Application Svelte | `src/routes/+layout.svelte` | `ssr=false`, i18n, token/session, Socket.IO (`/ws/socket.io`), version/deployment refresh, Pyodide worker persistant, stores globaux. |
| Shell authentifié | `src/routes/(app)/+layout.svelte` | redirection auth, chargement config/bannières/outils/réglages/modèles/serveurs, raccourcis, sidebar, modals globaux. |
| Chat route | `(app)/+page.svelte`, `(app)/c/[id]/+page.svelte` | instancient `Chat.svelte`, avec ou sans `chatIdProp`. |
| Workspace/Admin | leurs `+layout.svelte` | garde permissions, navigation secondaire, conteneur scrollable. |
| API frontend | `src/lib/apis/*.ts` | clients `fetch`, bearer token, conversion d'erreur; aucun état métier durable. |
| Backend | `backend/open_webui/main.py`, `routers/*.py`, `utils/middleware.py`, `utils/chat.py`, `models/*.py` | ACL, persistance, providers, retrieval, exécution d'outils et événements. |

## Stores Svelte

`src/lib/stores/index.ts` centralise les stores. Les groupes utiles à une réimplémentation sont :

| Groupe | Stores |
|---|---|
| Session/app | `config`, `user`, `settings`, `WEBUI_NAME`, version/deployment, `theme`, `mobile`, `isApp` |
| Temps réel | `socket`, `socketConnected`, `activeUserIds`, `activeChatIds`, `chatRequestQueues` |
| Navigation | `showSidebar`, `sidebarWidth`, `showSearch`, `showSettings`, `showShortcuts`, `showArchivedChats`, `selectedFolder`, `chatId`, `chatTitle` |
| Catalogues | `models`, `knowledge`, `tools`, `skills`, `functions`, `toolServers`, `terminalServers` |
| Conversations | `chats`, `pinnedChats`, `folders`, `tags`, `temporaryChatEnabled`, pagination |
| Panneaux | `showControls`, `showEmbeds`, `showArtifacts`, `showOverview`, `showFileNav`, `selectedTerminalId`, `artifactCode`, `artifactContents` |

Le composant propriétaire de l'état transactionnel de la conversation est `Chat.svelte`, non le store global. Il reçoit/remonte les événements de ses enfants et persiste par API.

## Carte des composants par fonctionnalité

| Fonction | Composition frontend | Contrat entrant/sortant important |
|---|---|---|
| Chat | `Chat.svelte` → `Navbar`, `Messages`, `MessageInput`, `ChatControls`, `FilesOverlay`, `Placeholder` | `history`, modèles, files, feature toggles; handlers `submit`, `regenerate`, `action`, `history-change`, upload. |
| Input | `MessageInput.svelte` → `RichTextInput`, `InputMenu`, `CommandSuggestionList`, voice, files, integrations, terminal, variables | dispatch `submit`, `change`, `upload`; prend `selectedToolIds`, `selectedFilterIds`, `pendingOAuthTools`, `files`, `generating`. |
| Messages | `Messages.svelte` → `Message.svelte` → `UserMessage` ou `ResponseMessage` | rendu branché; Response compose Markdown, citations, execution, feedback, follow-ups, status history et regenerate menu. |
| Modèles | `ModelSelector.svelte` → `Selector`, `ModelItem`, `ModelItemMenu` | binding `selectedModels`, `onChange`; affiche ACL/capabilities provenant de `model.info`. |
| Knowledge | `workspace/Knowledge.svelte` → `Knowledge/KnowledgeBase.svelte` → `Files`, `AddContentMenu`, `AddTextContentModal`, `ItemMenu` | liste paginée/recherche; association fichiers/ACL. |
| Skills | `workspace/Skills.svelte` → `SkillEditor`, `SkillMenu` ; chat `Commands/Skills.svelte` | CRUD skill, clone sessionStorage; insertion d'une mention structurée dans RichTextInput. |
| Tools | `workspace/Tools.svelte` → `Tools/ToolkitEditor`, `ToolMenu`, `AddToolMenu`; chat `ToolServersModal` | tool content → specs/manifest/valves; sélection par `tool_ids`. |
| MCP/connections | `Settings/Integrations.svelte`, `Settings/Tools/Connection.svelte`, `ToolServersModal.svelte` | configurations app et serveurs directs utilisateur; OAuth/valves selon connexion. |
| Fichiers | `FilesOverlay`, `FileItem`, `FilesModal`, `FileNav/*`, `PyodideFileNav` | upload/processing, preview, filesystem terminal/Pyodide. |
| Mémoire | `Settings/Personalization.svelte` → Manage/Add/Edit modals | switch UI + CRUD mémoire par utilisateur. |
| Sidebar | `layout/Sidebar.svelte` + `common/ChatList`, folder/tag/channel modals | store navigation; API folders/chats/tags/channels; responsive drawer. |
| Settings | `SettingsModal.svelte` → General, Interface, Connections, Integrations, Personalization, Audio, DataControls, Account, About | sauvegarde `ui` avec `updateUserSettings`, route vers Admin Settings pour admin. |

## Pages et composants rendus

| Route | Page légère | Composant de contenu |
|---|---|---|
| `/workspace/models` | recharge `$models` | `workspace/Models.svelte` |
| `/workspace/models/create|edit` | contrôle ID, accès et navigation | `workspace/Models/ModelEditor.svelte` |
| `/workspace/knowledge` | import simple | `workspace/Knowledge.svelte` |
| `/workspace/knowledge/create|[id]` | import simple | `CreateKnowledgeBase` / `KnowledgeBase` |
| `/workspace/prompts` | import simple | `workspace/Prompts.svelte` |
| `/workspace/skills/create|edit` | charge/clone puis action API | `workspace/Skills/SkillEditor.svelte` |
| `/workspace/tools/create|edit` | vérifie frontmatter/version et accès | `workspace/Tools/ToolkitEditor.svelte` |
| `/admin/*` | import ou sélection par tab | `admin/Users`, `Analytics`, `Evaluations`, `Functions`, `Settings` |

## Frontend API → backend

| Module TS | Préfixe HTTP | Modèle/persistance primaire |
|---|---|---|
| `apis/chats` | `/api/v1/chats` | `Chat`, `ChatMessage`, `ChatFile`, tags/folders/shared chats |
| `apis/models`, `apis/index` | `/api/v1/models`, `/openai`, `/ollama` | `Model` + catalogues de providers |
| `apis/knowledge`, `apis/retrieval` | `/api/v1/knowledge`, `/api/v1/retrieval` | `Knowledge`, `KnowledgeFile`, `File`, vector store |
| `apis/skills` | `/api/v1/skills` | `Skill` + `AccessGrant` |
| `apis/tools` | `/api/v1/tools` | `Tool` (content/specs/meta/valves) + grants |
| `apis/functions` | `/api/v1/functions` | `Function` + valves |
| `apis/files` | `/api/v1/files` | `File`, storage provider, processing retrieval |
| `apis/memories` | `/api/v1/memories` | `Memory` |
| `apis/configs` | `/api/v1/configs` | persistent application configuration, tool/MCP/terminal connections |
| `apis/users`, `apis/auths` | `/api/v1/users`, `/api/v1/auths` | `User`, user settings, permissions, API keys/session |
| `apis/openai` | `/openai` plus `/api/chat/completions` | provider proxy / chat orchestration |

Tous les clients authentifiés ajoutent `Authorization: Bearer <localStorage.token>`. Ils transforment les réponses non-OK en erreur pour que les composants affichent un toast ou reviennent à un état sûr.

## Modèles de données essentiels

| Entité | Champs structurants lus dans le code | Relations/usage |
|---|---|---|
| `Chat` | `id,user_id,title,chat,meta,folder_id,share_id,archived,pinned,tasks,summary,last_read_at` | `chat` contient historique/UI; `ChatMessage` stocke les messages structurés; `ChatFile` lie fichiers. |
| `Model` | `id,user_id,base_model_id,name,params,meta,is_active,access_grants` | `meta.capabilities`, knowledge, skills/actions orientent l'UI et middleware. |
| `Knowledge` | `id,user_id,name,description,meta,access_grants` | relation `KnowledgeFile(knowledge_id,file_id,user_id)`. |
| `File` | `id,user_id,hash,filename,path,data,meta,timestamps` | blob/storage derrière `path`; `data` porte le résultat/état d'ingestion. |
| `Skill` | `id,user_id,name,description,content,meta.tags,is_active,access_grants` | contenu système injecté après validation ACL/activation. |
| `Tool` | `id,user_id,name,content,specs,meta, valves,access_grants` | specs sont les fonctions exposées au modèle; valves configureront leur comportement. |
| `Memory` | `id,user_id,content,timestamps` | recherche/injection sur feature memory. |
| `AccessGrant` | ressource, sujet user/groupe, permission | employé par modèles, knowledge, skills, tools; UI reçoit `write_access`. |

## Backend : responsabilités à ne pas déplacer dans le WebUI

`main.py:chat_completion` est le coordinateur : validation du modèle et ACL, création de l'arbre durable, messages/fichiers, tâches concurrencées, annulation et cycle d'événements. `utils/middleware.py:process_chat_payload` est le point d'assemblage de contexte et d'exécution; `utils/chat.py` route le provider; les routeurs CRUD ne remplacent aucun de ces services.

Pour MCP, la résolution s'effectue côté serveur dans le middleware : configuration app, ACL, headers OAuth/session, création de `MCPClient`, découverte des specs, wrapper callable et cleanup. Une UI peut choisir une connexion, mais ne doit pas reconstituer cette sécurité ni exécuter les calls métier côté navigateur.

## Dépendances significatives

- Svelte 5 / SvelteKit SPA, Tailwind, Bits UI, Svelte Sonner, i18next.
- Socket.IO pour événements live; `eventsource-parser` pour SSE des réponses.
- `fuse.js` pour recherche de modèles; `paneforge` pour panes; Tiptap/ProseMirror pour entrée riche; Marked/KaTeX/Mermaid/Shiki pour rendu.
- FastAPI, SQLAlchemy async, Pydantic; stockage, retrieval/embeddings et providers OpenAI/Ollama/pipelines; client MCP côté Python.
- Pyodide worker pour code interpreter navigateur et XTerm/terminal pour intégrations de terminal.

## Points d'intégration ETHAN

Pour adopter cette référence, ETHAN doit fournir des contrats stables pour : catalogue+ACL modèles, chat tree/message events, upload/processing/status, collections/retrieval/sources, resources workspace et grants, skills activables, tool registry/valves, MCP server registry et execution, mémoire, préférences utilisateur et tâches annulables. Les composants Svelte peuvent être remplacés; ces contrats et ownership Core/Runtime ne le doivent pas.
