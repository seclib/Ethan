# Open-WebUI — Référence fonctionnelle

## Périmètre et méthode

Cette référence décrit le code réellement présent dans `examples/open-webui` au moment de l'audit : frontend Svelte 5/Vite, backend FastAPI, commit `0a8a620fb`. Elle a été établie en lisant les composants, clients API, routeurs FastAPI, middleware et modèles SQLAlchemy ; elle ne déduit pas un comportement d'après les seuls noms de fichiers.

Le sous-dépôt contient des modifications non commitées, notamment `backend/open_webui/config.py`, `routers/auths.py`, `routers/chats.py`, `routers/openai.py`, ainsi qu'un nouveau client ETHAN. Elles font partie du snapshot audité. Les parcours principaux de l'UI passent toutefois par `main.py:/api/chat/completions`, qui utilise le pipeline complet `utils/middleware.py` et `utils/chat.py`; le routeur `/openai/chat/completions` modifié est une façade distincte vers ETHAN.

## Architecture exécutable

```text
Svelte SPA (SSR=false)
  +layout.svelte  -> session, config, stores, Socket.IO, worker Pyodide
  (app)/+layout   -> garde utilisateur, chargement modèles/outils/réglages
  Chat.svelte     -> arbre local de messages, composer, multi-modèles
       POST /api/chat/completions
FastAPI main.py   -> ACL modèle, persistance chat/message/fichier, tâche par modèle
  process_chat_payload
       -> params, folder/project, filters, mémoire, recherche, skills,
          outils/MCP/terminal, RAG fichiers, citations
  utils.chat.generate_chat_completion -> Ollama/OpenAI/pipelines/arena
  process_chat_response -> SSE + Socket.IO + sauvegarde + tâches de fond
SQLAlchemy + storage + vector DB / retrieval
```

Les stores Svelte sont le cache partagé de l'interface, pas la source métier : `user`, `config`, `settings`, `models`, `knowledge`, `tools`, `skills`, `functions`, `chats`, `folders`, `tags`, `toolServers`, `terminalServers`, `chatId`, et les états d'overlays. La persistance est côté API/DB; les brouillons restent temporairement dans `sessionStorage`.

## Routes de l'interface

| Domaine | Route | Composant de page | Contrôle d'accès observé |
|---|---|---|---|
| Chat nouveau/existant | `/`, `/c/[id]` | `Chat.svelte` | session `user` ou `admin` |
| Recherche/partage public | `/s/[id]` | page partage; recherche via overlay | selon partage/ACL |
| Workspace | `/workspace/{models,knowledge,prompts,skills,tools}` | layouts Workspace + listes/éditeurs | admin ou permission `workspace.*` |
| Modèles | `/workspace/models/{create,edit?id=}` | `ModelEditor.svelte` | `write_access` à l'édition |
| Knowledge | `/workspace/knowledge/{create,[id]}` | `Knowledge.svelte`, `KnowledgeBase.svelte` | `workspace.knowledge` |
| Administration | `/admin`, `/admin/{users,analytics,evaluations,functions,settings}` | layout Admin + composants dédiés | admin, redirection sinon |
| Autres produits | `/notes`, `/channels/[id]`, `/automations`, `/calendar`, `/playground/*`, `/home`, `/watch` | composants dédiés | feature flags/permissions |
| Auth | `/auth` | authentification | hors layout applicatif |

Les layouts Workspace et Admin rendent une barre secondaire horizontale, et masquent les onglets non autorisés. Ils testent aussi l'autorisation au montage avant de rendre le contenu.

## Chat

### Composer, sélection, messages et streaming

| Élément | Implémentation et état | API / données | Workflow effectif |
|---|---|---|---|
| Composer | `MessageInput.svelte`, `RichTextInput.svelte`; propriétés remontées depuis `Chat`: `prompt`, `files`, modèles, filtres, outils et toggles de features. | upload `POST /api/v1/files/`; envoi `POST /api/chat/completions`. | Saisie riche, collage, glisser-déposer, variables, fichiers, dictée/voix, queue. `submit` crée un nœud user puis un placeholder assistant par modèle. |
| Modèle | `ModelSelector.svelte` → `Selector.svelte` / `ModelItem.svelte`. État local `selectedModels`, persistance du défaut et des favoris dans `users/user/settings`. | `GET /api/models` agrège providers et modèles custom; CRUD `/api/v1/models/*`. | Recherche Fuse, tags/type de connexion, multi-sélection. Pinner/définir le défaut ne modifie que les préférences utilisateur. |
| Arbre de conversation | `Chat.svelte` garde `history={currentId,messages}`. Chaque message a `id`, `parentId`, `childrenIds`, rôle, contenu, fichiers, modèle, `done`. | `Chat.chat` JSON et `ChatMessage`; `POST /api/v1/chats/{id}/messages/{message_id}`. | Brancher/éditer/régénérer crée ou pointe vers des enfants; le chemin courant est produit par `createMessagesList`. |
| Streaming | `createOpenAITextStream` lit SSE avec `eventsource-parser`; `chatCompletionEventHandler` ajoute les deltas et finalise. | tâche backend; événements Socket.IO par chat/message et SSE upstream. | La requête initiale retourne `task_ids`/`chat_id`; les mises à jour de message viennent des événements. Les gros deltas peuvent être découpés visuellement (`settings.splitLargeDeltas`). |
| Multi-modèle / arena | `selectedModels` peut contenir plusieurs IDs et crée un assistant par modèle. | `message_ids: {model_id: assistant_message_id}`; `main.py` lance une tâche par modèle. | Le premier modèle peut générer titre/tags; les autres n'exécutent que les follow-ups. Un modèle arena est résolu au hasard dans le middleware. |
| Actions de message | `UserMessage.svelte`, `ResponseMessage.svelte`, `RegenerateMenu.svelte`, `RateComment.svelte`. | mise à jour de message/chat, feedbacks, `chatAction` pour actions de modèle. | Éditer, sauvegarder une copie, copier (texte/formaté), TTS, index de réponse, évaluer, régénérer, supprimer et exécuter une action de modèle. Tous sont conditionnés par permissions/feature flags. |
| Citations, outils, artefacts | `Citations.svelte`, `ToolCallDisplay.svelte`, `ContentRenderer.svelte`, `Artifacts.svelte`, panneau `ChatControls`. | événements `sources`, `status`, `files`, `chat:*`; metadata de réponse. | Les sources RAG s'affichent à proximité du message; les appels/outils sont rendus en détails; les artefacts, embeds et aperçu de fichiers sont des panneaux, non du contenu de chat brut. |

`Chat.svelte:sendMessageSocket` construit le contrat de requête. Il inclut paramètres globaux+chat, fichiers de contexte, `filter_ids`, `tool_ids`, `skill_ids`, terminal, serveurs d'outils directs, features, variables système, socket/session, dossier, message parent et tâches de fond. Les images sont intégrées comme `image_url` dans les conversations temporaires; les chats persistés récupèrent leurs messages structurés depuis la DB côté serveur.

### Pipeline serveur d'un message

1. `main.py:chat_completion` charge/contrôle le modèle, calcule paramètres et `metadata`, crée ou met à jour `Chat`, `ChatMessage` et `ChatFile`, avec les placeholders assistant.
2. Une tâche async par modèle exécute `process_chat_payload`.
3. Le middleware résout dossier/projet, connaissance attachée au modèle, variables, pipeline/filter inlet, mémoire, web-search/image/code interpreter, skills, tools/MCP/terminal et RAG des fichiers.
4. `utils.chat.generate_chat_completion` route vers Ollama, OpenAI-compatible, pipeline ou arena. `process_chat_response` propage les flux/événements, stocke la réponse et lance titre/tags/follow-ups.
5. Le frontend reçoit deltas, erreurs, sources, usages et statuts, marque `done`, sauvegarde le chat et traite la file locale suivante.

L'arrêt annule les tâches via `/api/v1/tasks`; la déconnexion/reconnexion Socket.IO est gérée au layout racine, avec heartbeat de 30 s. Les conversations temporaires utilisent un ID `local:<socket-id>` et ne sont pas persistées.

## Modèles et providers

Les modèles sont de deux natures : modèles découverts depuis Ollama/OpenAI (store `models`) et fiches personnalisées persistées. `ModelEditor.svelte` construit une fiche avec `id`, `base_model_id`, `name`, `params`, `meta`, `is_active` et ACL. `meta` accepte notamment image, description, capabilities, tags, knowledge, `skillIds`, actions et suggestions; `params` est volontairement extensible.

| Besoin | Route UI / composants | APIs et backend |
|---|---|---|
| Lister/sélectionner | `/workspace/models`, `Models.svelte`, `ModelSelector/*` | agrégation `getModels`; `GET /api/v1/models/list`, `/base`, `/tags` |
| Créer/éditer/activer/supprimer | `/workspace/models/create`, `/edit?id=`, `ModelEditor.svelte`, `ModelMenu.svelte` | `POST /create`, `/model/update`, `/model/toggle`, `/model/delete`; ACL `/model/access/update` |
| Préréglages utilisateur | selector + settings | `settings.pinnedModels`, modèle par défaut sauvegardés via `/users/user/settings/update` |
| Connections providers | Admin Settings + `openai`/`ollama` APIs | `/openai/config*`, `/ollama/config*`, vérification, tags/pull/create/delete Ollama |

La sélection est filtrée par access grants côté serveur et par flags UI. Les connexions directes utilisateur sont une préférence, activée seulement si `config.features.enable_direct_connections`.

## Knowledge, documents, fichiers et retrieval

| Fonction | UI / route | État et API | Données / traitement |
|---|---|---|---|
| Base documentaire | `/workspace/knowledge`, `Knowledge.svelte`, `KnowledgeBase.svelte` | store `knowledge`; `GET/POST /api/v1/knowledge/*` | `Knowledge(id,user_id,name,description,meta)` + `KnowledgeFile` et grants. |
| Création/permissions | `/workspace/knowledge/create`, `CreateKnowledgeBase.svelte`, `AccessControl.svelte` | `POST /knowledge/create`, `/{id}/access/update` | propriétaire/admin ou grants utilisateur/groupe; `write_access` est renvoyé à l'UI. |
| Ajouter du contenu | `KnowledgeBase/Files.svelte`, `AddContentMenu.svelte`, `AddTextContentModal.svelte` | `POST /files/`, `/knowledge/{id}/file/add`, batch/add, remove/update | fichier stocké puis traité; association knowledge-fichier distincte. |
| Ingestion | upload client attend le flux `/files/{id}/process/status?stream=true`; backend `files.py` → `retrieval.process_file`. | `/retrieval/process/file|text|web|youtube`, config/embedding | extraction, chunking, embeddings/vector store; reindex/reset disponibles. |
| Retrieval en chat | menu Input: `InputMenu/Knowledge.svelte`, commande `/` `Commands/Knowledge.svelte`; modèle peut aussi embarquer `meta.knowledge`. | fichiers/collections dans payload; `/retrieval/query/doc|collection` utilisé par middleware. | recherche sur le prompt; sources injectées dans le contexte puis émises à `Citations.svelte`. |
| Fichiers généraux | `FilesOverlay.svelte`, `FilesModal.svelte`, file navigator / preview | `POST /files`, `GET /files`, search/content/delete | `File(id,user_id,hash,filename,path,data,meta,timestamps)`; `ChatFile` lie fichier au chat/message. |

Un fichier sélectionné dans le chat est soit image multimodale, soit contexte retrieval. Les objets `doc`, `text`, `note`, `chat`, `folder`, `collection` sont distingués du fichier binaire dans `sendMessageSocket`; un dossier peut étendre sa liste de fichiers dans le middleware.

## Skills

Une skill est une instruction textuelle versionnée, pas un outil exécutable. Son modèle DB est `Skill(id,user_id,name,description,content,meta.tags,is_active,timestamps)` avec access grants.

| Étape | Implémentation |
|---|---|
| Créer/gérer | `/workspace/skills`, `/create`, `/edit?id=`; `Skills.svelte`, `SkillEditor.svelte`, `SkillMenu.svelte`. APIs CRUD `/api/v1/skills`, toggle et `/access/update`; import/export/list paginée. |
| Sélection chat | `MessageInput/Commands/Skills.svelte` insère une mention `&lt;$skillId|label&gt;`; `Chat.svelte` l'extrait en `skill_ids` et retire la mention du prompt. |
| Activation/exécution | `process_chat_payload` prend l'union des mentions utilisateur et `model.meta.skillIds`, vérifie l'accès et `is_active`. Une skill explicitement choisie injecte tout `content` dans un message système; une skill attachée au modèle injecte seulement id/nom/description comme inventaire disponible. |

## Tools, fonctions, MCP et terminal

| Type | Découverte/configuration | Sélection/exécution dans le chat |
|---|---|---|
| Tool local | `/workspace/tools`, `ToolkitEditor.svelte`, spécifications extraites du code/frontmatter; valves admin et utilisateur. | `ToolServersModal.svelte` / composer; `tool_ids`. Le middleware charge les callables, injecte specs et soit exécute le loop d'outils, soit fournit les tools natifs au provider. |
| Function/filter/pipe | `/admin/functions`, `Functions.svelte`; code, valves, activation globale. | inlet/outlet filters sont triés et appliqués au pipeline; actions de modèle peuvent déléguer au backend. |
| Serveur OpenAPI direct | Settings > Integrations/Tools; `getToolServersData` charge la spec client. | le client passe les specs et connexion dans `tool_servers`; middleware les ajoute à `tools_dict` avec `direct=true`. |
| MCP | Admin `configs/tool_servers`, structure `ToolServerConnection(type='mcp', url, key, auth_type, headers, info, access_control)`. | le tool ID `server:mcp:<id>` déclenche connexion `MCPClient`, `list_tools`, ACL, OAuth/session headers et wrappers d'appel. Les clients sont déconnectés en `finally`. |
| Terminal | Settings Integrations/Terminals, `TerminalMenu.svelte`, `XTerminal.svelte`, navigation fichiers. | `terminal_id` et serveurs activés; le middleware résout `get_terminal_tools`, ajoute tools+system prompt si capability modèle active. |

Les tools persistés sont `Tool(id,user_id,name,content,specs,meta, valves, timestamps)`. Les `specs` sont donc matérialisées à la création/mise à jour, tandis que `content` et `valves` restent conservés. Les MCP servers ne sont pas des lignes `Tool`: ils sont une configuration applicative persistante `TOOL_SERVER_CONNECTIONS` avec ACL.

## Memory

La personnalisation expose un switch `settings.memory` et un gestionnaire (`Personalization.svelte` et sous-modals) : lister, ajouter, éditer, supprimer un item ou tout le compte. L'API est `/api/v1/memories/`, `/add`, `/{id}/update`, `/{id}`, `/delete/user`, `/query`, `/reset`.

La table est volontairement simple : `Memory(id,user_id,content,created_at,updated_at)`. Lorsqu'une requête active `features.memory`, `process_chat_payload` appelle `chat_memory_handler`/`query_memory`; ses résultats sont ajoutés au contexte fichiers/collections, sauf function calling natif qui laisse les outils mémoire le faire.

## Conversations, sidebar, partage et navigation

`Sidebar.svelte` charge chats, tags, dossiers et notes épinglées; elle fournit nouveau chat/temporaire, recherche globale, import, dossiers hiérarchiques par drag-and-drop, tags, channels, chats archivés et items épinglables (notes/workspace/automations/calendar/admin). Les conversations utilisent `/api/v1/chats`: liste/recherche/pinned/archivés, create/import, get/update, delete, clone, archive, share, tags et folder. `Chat` contient `meta`, `folder_id`, `tasks`, `summary`, `last_read_at`; le contenu détail est dans `chat` JSON et la table de messages.

`Navbar.svelte` + `layout/Navbar/Menu.svelte` donnent les actions de contexte de la conversation : settings/chat controls, artefacts, partage, export PDF, déplacer vers dossier, archiver. Le partage crée un `share_id`, avec endpoints dédiés d'accès (`/shared/{id}/access*`).

## Settings et administration

| Portée | UI | Persisté / API |
|---|---|---|
| Utilisateur | `SettingsModal.svelte`: General, Interface, Connections, Integrations, Personalization, Audio, Data Controls, Account, About. Recherche de réglage intégrée. | `User.settings` JSON via `/api/v1/users/user/settings`; thèmes, paramètres de génération, modèles épinglés, mémoire, audio, ergonomie, privacy/import-export. |
| Application/admin | `/admin/settings/[tab]`, `admin/Settings.svelte` | `configs` (connections, tool/terminal servers, modèles par défaut, bannières, code execution), `openai/config`, `ollama/config`, retrieval/audio/images/pipelines. |
| Opérations admin | `/admin/users`, analytics, evaluations, functions | users/permissions/groupes, analytics, feedback/evaluations, fonctions/valves. |

Les permissions se trouvent dans `User.permissions` et couvrent chat (édition, suppression, partage, temporaire, rating), features et workspace. Les access grants portés par modèle/knowledge/skill/tool apportent un contrôle plus fin par utilisateur/groupe; les endpoints calculent `write_access` pour la UI.

## Référentiel de routes backend

Préfixes enregistrés par `backend/open_webui/main.py`: `/ollama`, `/openai`, puis `/api/v1/{pipelines,tasks,images,audio,retrieval,configs,auths,users,channels,chats,notes,models,knowledge,prompts,tools,skills,memories,folders,groups,files,functions,evaluations,analytics,utils,terminals,automations,calendars}`. Le contrat central interne est `POST /api/chat/completions` (alias `/api/v1/chat/completions`); ce n'est pas le routeur CRUD `/api/v1/chats`.

## Ce que cette référence impose à une réimplémentation ETHAN

Conserver le découpage : Core/Runtime doit posséder messages, exécution, RAG, skills, tools, MCP, mémoire et ACL; l'API expose ces capacités; le WebUI ne garde que le cache, le brouillon et l'orchestration d'affichage. Reproduire seulement les écrans sans le contrat de tâche/événements, la persistance des arbres ou la résolution serveur des contextes donnerait une imitation visuelle, pas une expérience Open-WebUI fonctionnelle.
