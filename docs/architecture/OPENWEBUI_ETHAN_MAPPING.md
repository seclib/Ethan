# Open-WebUI → ETHAN — Mapping des concepts

**Date :** 13 août 2026
**Révision ETHAN inspectée :** `c9252ca87493d0b291ba1289fa077c7ab87b86d1`
**Références :** `docs/audit/WEBUI_CURRENT_STATE.md`, `docs/audit/OPENWEBUI_FUNCTIONAL_REFERENCE.md`, `docs/audit/OPENWEBUI_UX_REFERENCE.md`, `docs/audit/OPENWEBUI_COMPONENT_REFERENCE.md`

## Principe directeur

La WebUI présente les capacités ETHAN. Elle ne les recrée pas.

Chaque concept Open-WebUI doit être résolu par une chaîne de la forme :

```text
Écran Open-WebUI (UX)
        ↓
API ETHAN (contrat HTTP)
        ↓
Manager / Store Core (source de vérité)
        ↓
Runtime / Services (exécution)
```

Toute capacité qui n'existe pas encore dans Core/Runtime doit y être créée
**avant** d'être exposée dans une interface. Une interface ne doit jamais
devenir propriétaire d'une logique métier.

---

## Légende des colonnes

| Colonne | Signification |
|---|---|
| **Équivalent ETHAN** | Le concept Core/Runtime qui remplace le concept Open-WebUI |
| **État actuel** | `✅` présent et branché · `⚠️` présent mais doublon/incomplet · `❌` absent |
| **Code existant** | Fichiers Core/API concernés |
| **API disponible** | Routes HTTP déjà exposées |
| **API manquante** | Routes à créer pour couvrir le besoin Open-WebUI |
| **Frontend à conserver** | Éléments UX Open-WebUI à réutiliser |
| **Frontend à modifier** | Éléments à adapter au contrat ETHAN |
| **Backend à remplacer** | Backend Open-WebUI à ne pas conserver |
| **Priorité** | P0 (bloquant) / P1 (important) / P2 (secondaire) |

---

## 1. Models

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | `ProviderManager` + `ModelInfo` (`core/llm/`) |
| **État actuel** | ⚠️ Partiel — catalogue réel via `ProviderManager`, mais pas de fiches modèles custom ni d'ACL |
| **Code existant** | `core/llm/provider_manager.py`, `core/llm/types.py` (`ModelInfo`), `core/llm/registry.py` |
| **API disponible** | `GET /providers`, `GET /providers/{id}/models`, `GET /v1/providers` (doublon) |
| **API manquante** | CRUD de fiches modèles custom (`base_model_id`, `params`, `meta`, `is_active`, ACL) ; agrégation `GET /models` ; tags ; modèles épinglés/défaut par utilisateur |
| **Frontend à conserver** | `ModelSelector.svelte`, `ModelItem.svelte`, `ModelEditor.svelte` (UX de sélection/édition) |
| **Frontend à modifier** | Brancher sur l'agrégation ETHAN au lieu du store local `models` ; retirer la liste fixe `useState` de la WebUI Next |
| **Backend à remplacer** | `GET /api/models` Open-WebUI (agrégation providers + custom) → API ETHAN |
| **Priorité** | P0 |

**Décision :** Le catalogue de modèles doit être agrégé par l'API ETHAN à partir
de `ProviderManager.list_models()` + un nouveau store Core de fiches modèles
custom. La WebUI ne doit jamais maintenir sa propre liste de modèles.

---

## 2. Providers

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | `ProviderManager` (`core/llm/provider_manager.py`) |
| **État actuel** | ✅ Réel et branché via `/providers` ; ⚠️ doublon `/v1/providers` via `CoreWebUIStore` |
| **Code existant** | `core/llm/provider_manager.py`, `core/llm/store.py`, `core/llm/provider_factory.py`, `interfaces/api/routers/providers.py` |
| **API disponible** | `GET/POST /providers`, `PUT/DELETE /providers/{id}`, `GET /providers/{id}/models`, `POST /providers/{id}/test`, `PUT /providers/{id}/default` |
| **API manquante** | Suppression du doublon `/v1/providers` ; vérification de connexion enrichie ; gestion des clés API via secret manager (jamais en base) |
| **Frontend à conserver** | `Settings/Connections.svelte`, `openai`/`ollama` config UI (UX de connexion) |
| **Frontend à modifier** | Brancher sur `/providers` ETHAN ; retirer l'écran Providers Next qui lit `/v1/providers` |
| **Backend à remplacer** | `/openai/config*`, `/ollama/config*` Open-WebUI → `/providers` ETHAN |
| **Priorité** | P0 |

**Décision :** `/providers` (réel `ProviderManager`) est la source de vérité.
`/v1/providers` (records WebUI) doit être supprimé. Les clés API passent par
`core/config/secrets.py` / env, jamais persistées.

---

## 3. Connections

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | `ToolServerManager` (`core/tools/servers.py`) |
| **État actuel** | ✅ Présent pour les serveurs d'outils ; ❌ pas de connexions directes utilisateur ni OAuth |
| **Code existant** | `core/tools/servers.py`, `interfaces/api/routers/capabilities.py` |
| **API disponible** | `GET/POST /v1/tools/servers`, `PUT/DELETE /v1/tools/servers/{id}`, `PUT /v1/tools/servers/{id}/status` |
| **API manquante** | Connexions directes utilisateur (préférence) ; OAuth/session headers ; vérification de connexion |
| **Frontend à conserver** | `Settings/Integrations.svelte`, `Settings/Tools/Connection.svelte` (UX de connexion) |
| **Frontend à modifier** | Brancher sur `/v1/tools/servers` ETHAN |
| **Backend à remplacer** | `configs` Open-WebUI (tool/terminal servers) → `ToolServerManager` ETHAN |
| **Priorité** | P1 |

---

## 4. Knowledge

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | `KnowledgeManager` (`core/knowledge/`) |
| **État actuel** | ✅ Présent et branché via `/v1/knowledge` |
| **Code existant** | `core/knowledge/manager.py`, `core/knowledge/types.py`, `interfaces/api/routers/v1.py` |
| **API disponible** | `GET/POST /v1/knowledge`, `GET/PUT/DELETE /v1/knowledge/{id}`, `GET /v1/knowledge/search`, `POST /v1/knowledge/{id}/connections`, `POST /v1/knowledge/{id}/rag` |
| **API manquante** | Notion de « base documentaire » (collection) avec fichiers associés ; ACL/access grants ; `write_access` pour l'UI |
| **Frontend à conserver** | `Knowledge.svelte`, `KnowledgeBase.svelte`, `CreateKnowledgeBase.svelte`, `AccessControl.svelte` (UX registre + navigation 2 niveaux) |
| **Frontend à modifier** | Brancher sur `/v1/knowledge` ETHAN ; adapter le modèle de données (Knowledge ETHAN = nœud, pas base) |
| **Backend à remplacer** | `/api/v1/knowledge/*` Open-WebUI → `/v1/knowledge` ETHAN |
| **Priorité** | P0 |

**Décision :** Le modèle ETHAN `Knowledge` (nœud de graphe) doit être étendu ou
complété par une notion de collection/base pour couvrir l'UX Open-WebUI, sans
déplacer la logique dans la WebUI.

---

## 5. Documents

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | `RAGPipeline` (`core/rag/`) |
| **État actuel** | ✅ Présent et branché via `/v1/rag/documents` |
| **Code existant** | `core/rag/pipeline.py`, `core/rag/ingestion.py`, `core/rag/retrieval.py`, `core/rag/embeddings.py`, `interfaces/api/routers/v1.py` |
| **API disponible** | `GET/POST /v1/rag/documents`, `GET/DELETE /v1/rag/documents/{id}`, `POST /v1/rag/retrieve`, `POST /v1/rag/context` |
| **API manquante** | Upload de fichiers binaires avec cycle « upload → processing stream → disponible/erreur » ; ingestion web/youtube ; reindex/reset ; association fichier↔knowledge |
| **Frontend à conserver** | `FilesOverlay.svelte`, `FilesModal.svelte`, `AddContentMenu.svelte`, `AddTextContentModal.svelte` (UX upload/processing) |
| **Frontend à modifier** | Brancher sur `/v1/rag/*` ETHAN ; retirer l'écran Documents Next qui lit `/v1/rag/documents` |
| **Backend à remplacer** | `/api/v1/files/*`, `/api/v1/retrieval/*` Open-WebUI → `/v1/rag/*` + `/files` ETHAN |
| **Priorité** | P0 |

---

## 6. Skills

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | `SkillManager` (`core/skills/manager.py`) |
| **État actuel** | ⚠️ `SkillManager` Core existe mais **n'est pas exposé** via l'API ; `/v1/skills` passe par `CoreWebUIStore` (doublon) |
| **Code existant** | `core/skills/manager.py`, `core/skills/registry.py`, `core/skills/types.py` ; `core/state/webui_store.py` (doublon) |
| **API disponible** | `GET/POST /v1/skills`, `GET/PUT/DELETE /v1/skills/{id}`, `POST /v1/skills/{id}/execute` (via `CoreWebUIStore`) |
| **API manquante** | Gateway vers le vrai `SkillManager` ; toggle `is_active` ; ACL/access grants ; import/export ; injection dans le pipeline de chat |
| **Frontend à conserver** | `Skills.svelte`, `SkillEditor.svelte`, `SkillMenu.svelte`, `Commands/Skills.svelte` (UX registre + mention dans l'input) |
| **Frontend à modifier** | Brancher sur le vrai `SkillManager` ; corriger le contrat de réponse (enveloppe vs brut) |
| **Backend à remplacer** | `/api/v1/skills/*` Open-WebUI → `SkillManager` ETHAN ; **supprimer le doublon `CoreWebUIStore`** |
| **Priorité** | P0 |

**Décision :** Le `SkillManager` Core est la source de vérité. La route `/v1/skills`
doit être rebranchée sur ce manager et le store `webui_skills` de
`CoreWebUIStore` supprimé. L'exécution d'une skill doit passer par le pipeline
de chat ETHAN, pas par un écho.

---

## 7. Tools

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | `ToolManager` (`core/tools/manager.py`) |
| **État actuel** | ⚠️ `ToolManager` Core existe mais **n'est pas exposé** via l'API ; seuls les serveurs d'outils le sont |
| **Code existant** | `core/tools/manager.py`, `core/tools/registry.py`, `core/tools/executor.py`, `core/tools/selector.py`, `core/tools/types.py` |
| **API disponible** | `GET/POST /v1/tools/servers` (serveurs, pas les tools) |
| **API manquante** | CRUD de tools locaux (`content`, `specs`, `meta`, `valves`, ACL) ; sélection par `tool_ids` dans le chat ; exécution via `ToolManager` |
| **Frontend à conserver** | `Tools.svelte`, `ToolkitEditor.svelte`, `ToolMenu.svelte`, `ToolServersModal.svelte` (UX registre + sélection) |
| **Frontend à modifier** | Brancher sur le vrai `ToolManager` ; retirer l'écran Tools Next (démo locale) |
| **Backend à remplacer** | `/api/v1/tools/*` Open-WebUI → `ToolManager` ETHAN |
| **Priorité** | P0 |

**Décision :** Le `ToolManager` Core est la source de vérité. Il faut créer une
gateway API `/v1/tools` vers ce manager et l'intégrer au pipeline de chat.

---

## 8. Functions

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | `FunctionManager` (`core/tools/functions.py`) |
| **État actuel** | ✅ Présent et branché via `/v1/functions` et `/v1/pipelines` |
| **Code existant** | `core/tools/functions.py`, `interfaces/api/routers/capabilities.py` |
| **API disponible** | `GET/POST /v1/functions`, `GET/DELETE /v1/functions/{id}`, `GET/POST /v1/pipelines`, `GET/DELETE /v1/pipelines/{id}` |
| **API manquante** | Valves ; activation globale ; inlet/outlet filters appliqués au pipeline de chat ; actions de modèle |
| **Frontend à conserver** | `Functions.svelte` (UX admin) |
| **Frontend à modifier** | Brancher sur `/v1/functions` ETHAN |
| **Backend à remplacer** | `/api/v1/functions/*` Open-WebUI → `FunctionManager` ETHAN |
| **Priorité** | P1 |

---

## 9. MCP

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | `ToolServerManager` (`core/tools/servers.py`) — à étendre pour le type MCP |
| **État actuel** | ⚠️ Serveurs d'outils génériques présents ; ❌ pas de type MCP dédié, ni ACL, ni OAuth, ni exécution serveur |
| **Code existant** | `core/tools/servers.py` |
| **API disponible** | `GET/POST /v1/tools/servers`, `PUT/DELETE /v1/tools/servers/{id}` |
| **API manquante** | Type `mcp` avec `url`, `key`, `auth_type`, `headers`, `info`, `access_control` ; client MCP côté serveur ; découverte des specs ; wrapper callable ; cleanup |
| **Frontend à conserver** | `Settings/Tools/Connection.svelte`, `ToolServersModal.svelte` (UX de configuration) |
| **Frontend à modifier** | Brancher sur `/v1/tools/servers` ETHAN avec type MCP |
| **Backend à remplacer** | `TOOL_SERVER_CONNECTIONS` Open-WebUI → `ToolServerManager` ETHAN étendu |
| **Priorité** | P1 |

**Décision :** La résolution MCP s'effectue côté serveur (Core), jamais dans le
navigateur. La WebUI choisit une connexion, le Core exécute les calls métier.

---

## 10. Memory

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | `MemoryManager` (`core/memory/manager.py`) + `core/facts/` |
| **État actuel** | ⚠️ `MemoryManager` Core existe mais **n'est pas exposé** via l'API ; `/v1/memory/*` passe par `CoreWebUIStore` (doublon) |
| **Code existant** | `core/memory/manager.py`, `core/memory/types.py`, `core/facts/store.py`, `core/facts/types.py` ; `core/state/webui_store.py` (doublon) |
| **API disponible** | `GET /v1/memory/facts`, `POST /v1/memory/facts`, `GET /v1/memory/facts/search`, `GET /v1/memory/facts/{id}`, `GET /v1/memory/events`, `POST /v1/memory/ingest`, `GET /v1/memory/search`, `GET /v1/memory/{id}` (via `CoreWebUIStore`) |
| **API manquante** | Gateway vers le vrai `MemoryManager` ; CRUD mémoire par utilisateur (lister/ajouter/éditer/supprimer) ; `query` ; `reset` ; injection dans le pipeline de chat |
| **Frontend à conserver** | `Settings/Personalization.svelte`, `Manage/Add/Edit` modals (UX mémoire) |
| **Frontend à modifier** | Brancher sur le vrai `MemoryManager` ; corriger le contrat de réponse (enveloppe vs brut) |
| **Backend à remplacer** | `/api/v1/memories/*` Open-WebUI → `MemoryManager` ETHAN ; **supprimer le doublon `CoreWebUIStore`** |
| **Priorité** | P0 |

**Décision :** Le `MemoryManager` Core est la source de vérité. La route
`/v1/memory/*` doit être rebranchée sur ce manager et le store `webui_facts` /
`webui_events` de `CoreWebUIStore` supprimé.

---

## 11. Files

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | `FileStore` (`core/state/files.py`) |
| **État actuel** | ✅ Présent et branché via `/files` (métadonnées) ; ❌ pas d'upload binaire réel ni de processing |
| **Code existant** | `core/state/files.py`, `interfaces/api/routers/domains.py` |
| **API disponible** | `GET/POST /files`, `GET/DELETE /files/{id}` |
| **API manquante** | Upload multipart réel ; stockage physique ; cycle de processing ; preview ; association fichier↔chat↔knowledge |
| **Frontend à conserver** | `FilesOverlay.svelte`, `FileItem.svelte`, `FilesModal.svelte`, `FileNav/*` (UX fichiers) |
| **Frontend à modifier** | Brancher sur `/files` ETHAN avec upload réel |
| **Backend à remplacer** | `/api/v1/files/*` Open-WebUI → `FileStore` ETHAN |
| **Priorité** | P0 |

---

## 12. Prompts

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | `PromptManager` (`core/config/prompts.py`) |
| **État actuel** | ✅ Présent et branché via `/v1/prompts` |
| **Code existant** | `core/config/prompts.py`, `interfaces/api/routers/capabilities.py` |
| **API disponible** | `GET/POST /v1/prompts`, `GET/PUT/DELETE /v1/prompts/{id}` |
| **API manquante** | Commandes slash dans le composer ; variables de prompt ; import/export |
| **Frontend à conserver** | `Prompts.svelte` (UX registre) |
| **Frontend à modifier** | Brancher sur `/v1/prompts` ETHAN |
| **Backend à remplacer** | `/api/v1/prompts/*` Open-WebUI → `PromptManager` ETHAN |
| **Priorité** | P1 |

---

## 13. Agents

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | `AgentManager` (`core/agents/manager.py`) |
| **État actuel** | ✅ Présent et branché via `/v1/agents` |
| **Code existant** | `core/agents/manager.py`, `core/agents/types.py`, `core/agents/base.py`, `interfaces/api/routers/v1.py` |
| **API disponible** | `GET/POST /v1/agents`, `GET/PUT/DELETE /v1/agents/{id}`, `POST /v1/agents/{id}/execute`, `GET /v1/agents/{id}/executions` |
| **API manquante** | ACL/access grants ; sélection dans le chat ; intégration au pipeline de chat |
| **Frontend à conserver** | `Agents.svelte` (UX registre) — à adapter |
| **Frontend à modifier** | Brancher sur `/v1/agents` ETHAN (déjà fait en partie) |
| **Backend à remplacer** | Aucun équivalent direct Open-WebUI (concept ETHAN natif) |
| **Priorité** | P1 |

---

## 14. Search

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | Recherche globale à créer dans Core (catalogue unifié) |
| **État actuel** | ❌ Absent |
| **Code existant** | Aucun |
| **API disponible** | Aucune |
| **API manquante** | Recherche globale sur chats, fichiers, knowledge, skills, tools, prompts, notes |
| **Frontend à conserver** | `Search.svelte` (overlay de recherche) |
| **Frontend à modifier** | Brancher sur l'API de recherche ETHAN |
| **Backend à remplacer** | Recherche Open-WebUI → API ETHAN |
| **Priorité** | P2 |

---

## 15. Web Search

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | Capacité web search à créer dans Core (intégration au pipeline de chat) |
| **État actuel** | ❌ Absent |
| **Code existant** | Aucun |
| **API disponible** | Aucune |
| **API manquante** | Recherche web ; injection des résultats dans le contexte ; citations |
| **Frontend à conserver** | Toggle Web Search dans le composer ; `Citations.svelte` |
| **Frontend à modifier** | Brancher sur la capacité ETHAN |
| **Backend à remplacer** | Web search Open-WebUI → capacité Core ETHAN |
| **Priorité** | P2 |

---

## 16. Workspace

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | Pas un concept Core — c'est un regroupement UX de ressources Core (models, knowledge, prompts, skills, tools) |
| **État actuel** | ⚠️ Les ressources existent dans Core ; le regroupement Workspace est absent |
| **Code existant** | Ressources dispersées dans `core/` |
| **API disponible** | Routes par ressource (voir sections précédentes) |
| **API manquante** | Aucune spécifique — le Workspace est un layout frontend qui agrège les routes existantes |
| **Frontend à conserver** | `workspace/+layout.svelte`, `workspace/Models.svelte`, `workspace/Knowledge.svelte`, `workspace/Prompts.svelte`, `workspace/Skills.svelte`, `workspace/Tools.svelte` (UX registre) |
| **Frontend à modifier** | Brancher chaque onglet sur la route ETHAN correspondante |
| **Backend à remplacer** | Aucun — le Workspace est purement UX |
| **Priorité** | P1 |

**Décision :** Le Workspace est une interface de regroupement. Il ne doit pas
recréer de logique métier : chaque onglet appelle la route ETHAN de la ressource.

---

## 17. Settings

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | `ConfigurationService` (`core/config/`) + `CoreWebUIStore` (settings) |
| **État actuel** | ⚠️ `ConfigurationService` branché via `/config` ; `/v1/settings` via `CoreWebUIStore` (doublon) |
| **Code existant** | `core/config/service.py`, `core/config/store.py`, `interfaces/api/routers/config.py`, `core/state/webui_store.py` |
| **API disponible** | `GET /config`, `GET/PUT/PATCH/DELETE /config/{domain}`, `POST /config/import`, `GET /config/export`, `GET /config/validate` ; `GET/PUT /v1/settings` |
| **API manquante** | Settings utilisateur (préférences UI, modèles épinglés, mémoire, audio, ergonomie) ; settings admin (connections, tool/terminal servers, modèles par défaut, bannières) |
| **Frontend à conserver** | `SettingsModal.svelte` (General, Interface, Connections, Integrations, Personalization, Audio, Data Controls, Account, About) ; `admin/Settings.svelte` |
| **Frontend à modifier** | Brancher sur `/config` ETHAN ; retirer le doublon `/v1/settings` |
| **Backend à remplacer** | `User.settings` + `configs` Open-WebUI → `ConfigurationService` ETHAN |
| **Priorité** | P1 |

---

## 18. Users

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | `UserManager` (`core/auth/users.py`) |
| **État actuel** | ✅ Présent et branché via `/users` ; ⚠️ `/auth/register` ne persiste pas l'utilisateur |
| **Code existant** | `core/auth/users.py`, `interfaces/api/routers/domains.py`, `interfaces/api/main.py` |
| **API disponible** | `GET/POST /users`, `GET/PUT/DELETE /users/{id}` ; `/auth/login`, `/auth/register`, `/auth/me`, `/auth/refresh`, `/auth/logout` |
| **API manquante** | Persistance de `/auth/register` ; API keys ; sessions ; settings utilisateur ; permissions fines |
| **Frontend à conserver** | `admin/Users.svelte` (UX admin) |
| **Frontend à modifier** | Brancher sur `/users` ETHAN |
| **Backend à remplacer** | `/api/v1/users/*`, `/api/v1/auths/*` Open-WebUI → `UserManager` ETHAN |
| **Priorité** | P0 (register) / P1 (reste) |

---

## 19. Permissions

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | `Permission` enum (`core/auth/`) + `require_permission` |
| **État actuel** | ✅ Rôles et permissions de base présents ; ❌ pas d'ACL/access grants par ressource |
| **Code existant** | `core/auth/__init__.py`, `interfaces/api/auth.py` |
| **API disponible** | `require_permission(Permission.*)` sur les routes |
| **API manquante** | Access grants par ressource (modèle/knowledge/skill/tool) ; `write_access` renvoyé à l'UI ; permissions workspace.* |
| **Frontend à conserver** | `AccessControl.svelte` (UX grants) |
| **Frontend à modifier** | Brancher sur l'API grants ETHAN |
| **Backend à remplacer** | `User.permissions` + `AccessGrant` Open-WebUI → système de permissions ETHAN |
| **Priorité** | P1 |

---

## 20. Chat / Conversations

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | `ChatStore` (`core/state/chats.py`) + `ProviderManager.chat()` |
| **État actuel** | ⚠️ `ChatStore` branché via `/chats` ; mais deux chemins de conversation (`/chats` et `/v1/chat`) ; pas de streaming ni d'arbre de messages |
| **Code existant** | `core/state/chats.py`, `interfaces/api/routers/domains.py`, `interfaces/api/routers/v1.py` (`/v1/chat`) |
| **API disponible** | `GET/POST /chats`, `GET/PUT/DELETE /chats/{id}`, `GET/POST /chats/{id}/messages`, `POST /chats/{id}/share` ; `POST /v1/chat`, `GET /v1/chat/history` |
| **API manquante** | Arbre de messages (`parentId`, `childrenIds`) ; streaming SSE ; tâches annulables ; événements temps réel ; multi-modèles/arena ; citations ; tool calls |
| **Frontend à conserver** | `Chat.svelte`, `MessageInput.svelte`, `RichTextInput.svelte`, `Messages.svelte`, `ResponseMessage.svelte`, `Citations.svelte`, `ToolCallDisplay.svelte` (UX chat) |
| **Frontend à modifier** | Brancher sur un contrat de chat ETHAN unifié ; retirer le double historique |
| **Backend à remplacer** | `/api/chat/completions` Open-WebUI → pipeline de chat ETHAN |
| **Priorité** | P0 |

**Décision :** Un seul modèle de conversation Core doit exister. Le pipeline de
chat ETHAN doit orchestrer : persistance de l'arbre, génération LLM, RAG,
skills, tools, MCP, mémoire, web search, streaming et événements.

---

## 21. Temps réel (WebSocket / SSE)

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | Protocole temps réel à créer dans Core/Runtime (NATS + SSE/WebSocket) |
| **État actuel** | ❌ Client tente `ws://…/api/v1/ws` ; aucune route serveur |
| **Code existant** | `core/bus/` (NATS), `interfaces/api/routers/message.py` |
| **API disponible** | Aucune route WebSocket/SSE |
| **API manquante** | Endpoint SSE/WebSocket ; événements de chat, tâches, statuts ; heartbeat |
| **Frontend à conserver** | `createOpenAITextStream` (SSE), Socket.IO client (à remplacer par le protocole ETHAN) |
| **Frontend à modifier** | Brancher sur le protocole temps réel ETHAN |
| **Backend à remplacer** | Socket.IO Open-WebUI → protocole ETHAN (NATS + SSE) |
| **Priorité** | P0 |

---

## 22. Terminal

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | Capacité terminal à créer dans Core (intégration au pipeline de chat) |
| **État actuel** | ❌ Écran Terminal Next est une démo locale |
| **Code existant** | Aucun (démo `useState`) |
| **API disponible** | Aucune |
| **API manquante** | Serveurs de terminal ; `get_terminal_tools` ; exécution ; navigation fichiers |
| **Frontend à conserver** | `TerminalMenu.svelte`, `XTerminal.svelte` (UX terminal) |
| **Frontend à modifier** | Brancher sur la capacité ETHAN |
| **Backend à remplacer** | Terminal Open-WebUI → capacité Core ETHAN |
| **Priorité** | P2 |

---

## 23. Autres produits (Notes, Channels, Automations, Calendar, Audio, Images, Evaluations, Analytics)

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | Managers Core dédiés (NoteStore, ChannelStore, AutomationManager, CalendarManager, TTSEngine, ImageGenerator, EvaluationManager, AnalyticsManager) |
| **État actuel** | ✅ Tous présents et branchés via `/v1/*` (capabilities router) |
| **Code existant** | `core/state/notes.py`, `core/state/channels.py`, `core/scheduler/automations.py`, `core/scheduler/calendar.py`, `core/llm/tts.py`, `core/llm/images.py`, `core/learning/evaluations.py`, `core/metrics/analytics.py` |
| **API disponible** | `/v1/notes`, `/v1/channels`, `/v1/automations`, `/v1/calendar`, `/v1/audio/*`, `/v1/images/*`, `/v1/evaluations`, `/v1/analytics/*` |
| **API manquante** | Surfaces UI dédiées (écrans Notes, Channels, Automations, Calendar) |
| **Frontend à conserver** | `Notes.svelte`, `Channels.svelte`, `Automations.svelte`, `Calendar.svelte` (UX produits) |
| **Frontend à modifier** | Brancher sur `/v1/*` ETHAN |
| **Backend à remplacer** | `/api/v1/notes`, `/api/v1/channels`, `/api/v1/automations`, `/api/v1/calendars` Open-WebUI → managers ETHAN |
| **Priorité** | P2 |

---

## 24. Observabilité (Logs, Analytics, Metrics)

| Attribut | Valeur |
|---|---|
| **Équivalent ETHAN** | `core/telemetry/`, `core/metrics/`, `core/audit/` |
| **État actuel** | ✅ Présent (Prometheus, OpenTelemetry, healthchecks) ; ❌ écran Logs Next est une démo |
| **Code existant** | `core/telemetry/`, `core/metrics/`, `core/audit/`, `interfaces/api/main.py` (`/health`, `/metrics`) |
| **API disponible** | `GET /health`, `GET /health/live`, `GET /health/ready`, `GET /health/detailed`, `GET /metrics` |
| **API manquante** | Endpoint de logs ; analytics UI ; évaluations UI |
| **Frontend à conserver** | `admin/Analytics.svelte`, `admin/Evaluations.svelte` (UX admin) |
| **Frontend à modifier** | Brancher sur `/v1/analytics/*`, `/v1/evaluations` ETHAN ; retirer `DEMO_LOGS` |
| **Backend à remplacer** | Analytics/évaluations Open-WebUI → managers ETHAN |
| **Priorité** | P2 |

---

## Synthèse des doublons à supprimer

Le `CoreWebUIStore` (`core/state/webui_store.py`) duplique plusieurs managers
Core spécialisés. Ces doublons doivent être supprimés au profit des managers :

| Domaine | Doublon `CoreWebUIStore` | Manager Core de référence |
|---|---|---|
| Goals | `webui_goals` | `core/goals/manager.py` (ou `core/planner/`) |
| Facts/Memory | `webui_facts`, `webui_events` | `core/memory/manager.py`, `core/facts/` |
| Skills | `webui_skills` | `core/skills/manager.py` |
| Chat | `webui_chat` | `core/state/chats.py` |
| Settings | `webui_settings` | `core/config/service.py` |
| Providers | `webui_providers` | `core/llm/provider_manager.py` |
| Plugins | `webui_plugins` | `plugins/manager.py` |

---

## Matrice de priorité globale

| Priorité | Concepts |
|---|---|
| **P0** | Models, Providers, Knowledge, Documents, Skills, Tools, Memory, Files, Chat, Temps réel, Users (register) |
| **P1** | Connections, Functions, MCP, Prompts, Agents, Workspace, Settings, Permissions |
| **P2** | Search, Web Search, Terminal, Notes, Channels, Automations, Calendar, Audio, Images, Evaluations, Analytics, Observabilité |

---

## Règle de non-régression

Avant toute implémentation d'un écran Open-WebUI :

1. Vérifier que la capacité existe dans `core/` (manager spécialisé).
2. Vérifier que l'API expose cette capacité via une gateway vers le manager.
3. Vérifier que le contrat de réponse est cohérent (brut ou enveloppe, jamais les deux).
4. **Ensuite seulement**, construire l'écran frontend branché sur l'API.

Un écran sans capacité Core testée est une imitation visuelle, pas une
fonctionnalité ETHAN.