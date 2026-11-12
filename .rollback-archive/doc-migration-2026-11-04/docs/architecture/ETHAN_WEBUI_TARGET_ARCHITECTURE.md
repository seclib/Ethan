# ETHAN WebUI — Architecture cible

**Date :** 13 août 2026
**Révision ETHAN inspectée :** `c9252ca87493d0b291ba1289fa077c7ab87b86d1`
**Références :** `docs/architecture/OPENWEBUI_ETHAN_MAPPING.md`, `docs/audit/WEBUI_CURRENT_STATE.md`, `docs/audit/OPENWEBUI_FUNCTIONAL_REFERENCE.md`, `docs/audit/OPENWEBUI_UX_REFERENCE.md`, `docs/audit/OPENWEBUI_COMPONENT_REFERENCE.md`

## 1. Vision

ETHAN WebUI est l'interface de référence pour interagir avec ETHAN. Elle
présente les capacités du Core/Runtime ; elle ne les recrée jamais.

La WebUI adopte l'UX et les workflows d'Open-WebUI comme référence de
conception, mais **toute la logique métier, la persistance et l'exécution
appartiennent au Core/Runtime ETHAN**.

```text
                    ┌─────────────────────────────┐
                    │        ETHAN WebUI          │
                    │   (UX Open-WebUI adaptée)   │
                    │  Svelte / React / Next      │
                    └──────────────┬──────────────┘
                                   │  HTTP + SSE/WebSocket
                                   ▼
                    ┌─────────────────────────────┐
                    │        API ETHAN           │
                    │   FastAPI (gateway HTTP)   │
                    │   Contrats versionnés      │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │        Core / Runtime       │
                    │  Managers + Stores + Bus    │
                    │  (source de vérité)         │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  Services (NATS, PG, Redis) │
                    │  Providers LLM, RAG, MCP    │
                    └─────────────────────────────┘
```

## 2. Principes d'architecture

### 2.1. La WebUI est un client, pas un backend

| Règle | Description |
|---|---|
| **Aucune logique métier** | La WebUI ne stocke pas d'état métier durable, ne définit pas de providers, agents, mémoire, RAG, missions |
| **Aucune persistance métier** | La WebUI ne maintient que le cache de présentation et les brouillons temporaires |
| **Aucune exécution métier** | La WebUI ne résout pas MCP, n'exécute pas de tools, ne fait pas de retrieval |
| **Contrats stables** | L'API expose des contrats versionnés ; la WebUI consomme ces contrats |

### 2.2. Le Core est la source de vérité

| Domaine | Source de vérité |
|---|---|
| Providers LLM | `core/llm/provider_manager.py` |
| Modèles | `core/llm/` + store fiches custom |
| Skills | `core/skills/manager.py` |
| Tools | `core/tools/manager.py` |
| MCP / serveurs d'outils | `core/tools/servers.py` |
| Functions / pipelines | `core/tools/functions.py` |
| Knowledge | `core/knowledge/manager.py` |
| RAG / documents | `core/rag/pipeline.py` |
| Memory / facts | `core/memory/manager.py`, `core/facts/` |
| Chats / conversations | `core/state/chats.py` |
| Fichiers | `core/state/files.py` |
| Utilisateurs / groupes | `core/auth/users.py`, `core/auth/groups.py` |
| Configuration | `core/config/service.py` |
| Prompts | `core/config/prompts.py` |
| Agents | `core/agents/manager.py` |
| Missions | `core/missions/manager.py` |
| Goals | `core/goals/manager.py` (ou `core/planner/`) |
| Automations / calendar | `core/scheduler/` |
| Audio / images | `core/llm/tts.py`, `core/llm/images.py` |
| Évaluations / analytics | `core/learning/evaluations.py`, `core/metrics/analytics.py` |
| Notes / channels | `core/state/notes.py`, `core/state/channels.py` |

### 2.3. Suppression des doublons

Le `CoreWebUIStore` (`core/state/webui_store.py`) doit être démantelé. Chaque
domaine qu'il duplique est rebranché sur le manager Core spécialisé :

| Domaine | Doublon à supprimer | Manager de référence |
|---|---|---|
| Goals | `webui_goals` | `core/goals/manager.py` |
| Facts/Memory | `webui_facts`, `webui_events` | `core/memory/manager.py`, `core/facts/` |
| Skills | `webui_skills` | `core/skills/manager.py` |
| Chat | `webui_chat` | `core/state/chats.py` |
| Settings | `webui_settings` | `core/config/service.py` |
| Providers | `webui_providers` | `core/llm/provider_manager.py` |
| Plugins | `webui_plugins` | `plugins/manager.py` |

## 3. Contrats API cibles

### 3.1. Convention de réponse

Une seule convention, jamais les deux :

```text
Réponse brute :  [ { ... }, { ... } ]          (listes)
Réponse objet :  { "id": "...", ... }          (ressources)
```

Pas d'enveloppe `{ "data": [...] }` sauf si le contrat l'exige explicitement
(pagination, recherche). Les types TypeScript sont générés depuis l'OpenAPI.

### 3.2. Routes cibles par domaine

| Domaine | Routes cibles | Manager Core |
|---|---|---|
| **Auth** | `POST /auth/login`, `POST /auth/register` (persistant), `GET /auth/me`, `POST /auth/refresh`, `POST /auth/logout` | `core/auth/users.py` |
| **Providers** | `GET/POST /providers`, `PUT/DELETE /providers/{id}`, `GET /providers/{id}/models`, `POST /providers/{id}/test`, `PUT /providers/{id}/default` | `core/llm/provider_manager.py` |
| **Models** | `GET /models` (agrégation), `POST /models`, `PUT/DELETE /models/{id}`, `GET /models/tags` | `core/llm/` + store fiches |
| **Chat** | `POST /chat/completions` (pipeline), `GET/POST /chats`, `GET/PUT/DELETE /chats/{id}`, `GET/POST /chats/{id}/messages`, `POST /chats/{id}/share` | `core/state/chats.py` + pipeline |
| **Knowledge** | `GET/POST /v1/knowledge`, `GET/PUT/DELETE /v1/knowledge/{id}`, `GET /v1/knowledge/search` | `core/knowledge/manager.py` |
| **RAG** | `GET/POST /v1/rag/documents`, `GET/DELETE /v1/rag/documents/{id}`, `POST /v1/rag/retrieve`, `POST /v1/rag/context` | `core/rag/pipeline.py` |
| **Files** | `GET/POST /files` (upload multipart), `GET/DELETE /files/{id}`, `GET /files/{id}/process/status` | `core/state/files.py` |
| **Skills** | `GET/POST /v1/skills`, `GET/PUT/DELETE /v1/skills/{id}`, `POST /v1/skills/{id}/toggle`, `POST /v1/skills/{id}/access/update` | `core/skills/manager.py` |
| **Tools** | `GET/POST /v1/tools`, `GET/PUT/DELETE /v1/tools/{id}`, `POST /v1/tools/{id}/toggle` | `core/tools/manager.py` |
| **Tool servers / MCP** | `GET/POST /v1/tools/servers`, `GET/PUT/DELETE /v1/tools/servers/{id}`, `PUT /v1/tools/servers/{id}/status` | `core/tools/servers.py` |
| **Functions** | `GET/POST /v1/functions`, `GET/DELETE /v1/functions/{id}`, `GET/POST /v1/pipelines`, `GET/DELETE /v1/pipelines/{id}` | `core/tools/functions.py` |
| **Memory** | `GET/POST /v1/memories`, `GET/PUT/DELETE /v1/memories/{id}`, `POST /v1/memories/query`, `POST /v1/memories/reset` | `core/memory/manager.py` |
| **Prompts** | `GET/POST /v1/prompts`, `GET/PUT/DELETE /v1/prompts/{id}` | `core/config/prompts.py` |
| **Agents** | `GET/POST /v1/agents`, `GET/PUT/DELETE /v1/agents/{id}`, `POST /v1/agents/{id}/execute` | `core/agents/manager.py` |
| **Missions** | `GET/POST /v1/missions`, `GET/PUT/DELETE /v1/missions/{id}`, `POST /v1/missions/{id}/steps/{step}/verify` | `core/missions/manager.py` |
| **Goals** | `GET/POST /v1/goals`, `GET/PUT/DELETE /v1/goals/{id}` | `core/goals/manager.py` |
| **Users** | `GET/POST /users`, `GET/PUT/DELETE /users/{id}`, `GET/PUT /users/{id}/settings` | `core/auth/users.py` |
| **Groups** | `GET/POST /groups`, `GET/PUT/DELETE /groups/{id}`, `POST/DELETE /groups/{id}/members/{user_id}` | `core/auth/groups.py` |
| **Config** | `GET /config`, `GET/PUT/PATCH/DELETE /config/{domain}`, `POST /config/import`, `GET /config/export`, `GET /config/validate` | `core/config/service.py` |
| **Temps réel** | `GET /events` (SSE) ou `WS /ws` | `core/bus/` (NATS) |
| **Capacités** | `/v1/automations`, `/v1/calendar`, `/v1/audio/*`, `/v1/images/*`, `/v1/evaluations`, `/v1/analytics/*`, `/v1/channels`, `/v1/notes`, `/v1/scim/*` | managers Core dédiés |

## 4. Pipeline de chat cible

Le pipeline de chat est le cœur de l'expérience. Il doit être orchestré par le
Core/Runtime, pas par la WebUI.

```text
POST /chat/completions
        │
        ▼
┌─────────────────────────────────────────────┐
│  ChatPipeline (Core)                        │
│                                             │
│  1. Valider modèle + ACL                    │
│  2. Charger conversation (arbre)            │
│  3. Résoudre contexte :                     │
│     - dossier/projet                        │
│     - knowledge attachée au modèle          │
│     - variables système                     │
│     - mémoire (si activée)                  │
│     - web search (si activé)                │
│     - skills (mentions + modèle)            │
│     - tools / MCP / terminal                │
│     - RAG des fichiers                      │
│  4. Appliquer filters (inlet)               │
│  5. Générer via ProviderManager             │
│  6. Appliquer filters (outlet)              │
│  7. Persister messages + arbre              │
│  8. Émettre événements (SSE/WebSocket)      │
│  9. Lancer tâches de fond (titre, tags)     │
└─────────────────────────────────────────────┘
```

### 4.1. Arbre de messages

Le modèle de message doit supporter le branching :

```text
Message {
  id, chat_id, parent_id, children_ids[],
  role, content, model, files[],
  tool_calls[], sources[], status, done,
  created_at, updated_at
}
```

Régénérer ou éditer crée un enfant ; le chemin courant est produit par
`createMessagesList` (logique Core, pas frontend).

### 4.2. Streaming et événements

| Événement | Payload | Usage |
|---|---|---|
| `chat.message.delta` | `{chat_id, message_id, delta}` | Streaming du contenu |
| `chat.message.done` | `{chat_id, message_id, content}` | Finalisation |
| `chat.message.error` | `{chat_id, message_id, error}` | Erreur |
| `chat.tool.call` | `{chat_id, message_id, tool_id, args}` | Affichage tool call |
| `chat.tool.result` | `{chat_id, message_id, tool_id, result}` | Résultat tool |
| `chat.sources` | `{chat_id, message_id, sources[]}` | Citations RAG |
| `chat.task.status` | `{chat_id, task_id, status}` | Tâches de fond |
| `chat.title` | `{chat_id, title}` | Titre généré |

Le protocole est SSE (Server-Sent Events) ou WebSocket, alimenté par NATS
(`core/bus/`). La WebUI consomme, ne produit pas.

## 5. Structure frontend cible

### 5.1. Choix technologique

Deux options sont possibles :

| Option | Avantages | Inconvénients |
|---|---|---|
| **A. Adopter Open-WebUI (SvelteKit) comme frontend** | UX mature, composants prêts, workflows testés | Migration Svelte → contrat ETHAN ; fork à assainir |
| **B. Réécrire en React/Next avec l'UX Open-WebUI** | Cohérent avec la WebUI Next existante | Réécriture complète des composants |

**Recommandation :** Option A (adopter Open-WebUI comme frontend) est la plus
rapide pour atteindre une UX mature, à condition de :
1. Créer un fork ETHAN suivi et propre (sans modifications non versionnées).
2. Remplacer le backend Open-WebUI par l'API ETHAN (adaptateur).
3. Conserver le login ETHAN (cookie HttpOnly `ethan_token`).

### 5.2. Layout cible

```text
┌──────────────────────────────────────────────────────────┐
│  Topbar (logo, recherche, actions, user)                 │
├──────────┬───────────────────────────────────────────────┤
│ Sidebar  │  Contenu principal                            │
│          │                                               │
│ - Chats  │  Chat (composer, messages, citations, tools)  │
│ - Favoris│  Workspace (models, knowledge, prompts,       │
│ - Doss.  │            skills, tools)                     │
│ - Notes  │  Admin (users, analytics, evaluations,        │
│ - Admin  │         functions, settings)                  │
│          │                                               │
└──────────┴───────────────────────────────────────────────┘
```

### 5.3. Écrans cibles

| Écran | Route | Source de données |
|---|---|---|
| Chat | `/`, `/c/[id]` | `POST /chat/completions`, `GET/POST /chats` |
| Workspace Models | `/workspace/models` | `GET /models` |
| Workspace Knowledge | `/workspace/knowledge` | `GET /v1/knowledge` |
| Workspace Prompts | `/workspace/prompts` | `GET /v1/prompts` |
| Workspace Skills | `/workspace/skills` | `GET /v1/skills` |
| Workspace Tools | `/workspace/tools` | `GET /v1/tools` |
| Admin Users | `/admin/users` | `GET /users` |
| Admin Analytics | `/admin/analytics` | `GET /v1/analytics/summary` |
| Admin Evaluations | `/admin/evaluations` | `GET /v1/evaluations` |
| Admin Functions | `/admin/functions` | `GET /v1/functions` |
| Admin Settings | `/admin/settings` | `GET /config` |
| Settings (user) | modal | `GET/PUT /users/{id}/settings` |
| Notes | `/notes` | `GET /v1/notes` |
| Channels | `/channels/[id]` | `GET /v1/channels` |
| Automations | `/automations` | `GET /v1/automations` |
| Calendar | `/calendar` | `GET /v1/calendar` |

## 6. Séquence de migration

### Phase 0 — Prérequis (P0)

1. **Geler les contrats** : générer les types TypeScript depuis OpenAPI ;
   choisir brut ou enveloppe ; corriger les hooks Missions, Memory, Skills, Goals.
2. **Rétablir l'ownership Core** : supprimer les doublons `CoreWebUIStore` ;
   rebrancher `/v1/skills`, `/v1/memory/*`, `/v1/goals`, `/v1/providers` sur les
   managers spécialisés.
3. **Consolider l'auth** : persister `/auth/register` ; propager le vrai
   utilisateur/role dans la réponse login.
4. **Unifier le chat** : un seul modèle de conversation Core ; supprimer le
   double historique (`/chats` vs `/v1/chat`).
5. **Définir le protocole temps réel** : endpoint SSE/WebSocket alimenté par
   NATS ; ou supprimer temporairement la promesse WebSocket.
6. **Assainir la référence Open-WebUI** : créer un fork ETHAN suivi, propre,
   reproductible ; isoler un adaptateur API ETHAN testé.

### Phase 1 — Chat et sidebar (P0)

1. Implémenter le pipeline de chat Core (arbre, streaming, événements).
2. Brancher le composer, le sélecteur de modèles, les messages, les citations.
3. Brancher la sidebar (chats, dossiers, tags, favoris).
4. Tester E2E authentifié : login → chat → streaming → persistance.

### Phase 2 — Workspace (P0/P1)

1. Models : catalogue agrégé + fiches custom + ACL.
2. Knowledge : bases documentaires + fichiers + retrieval.
3. Skills : registre + mentions dans le chat.
4. Tools : registre + sélection + exécution.
5. Prompts : registre + commandes slash.

### Phase 3 — Admin et settings (P1)

1. Users : gestion + permissions + settings utilisateur.
2. Providers : connexions + test + modèles.
3. Functions : registre + valves.
4. MCP : serveurs + ACL + exécution.
5. Config : settings admin via `/config`.

### Phase 4 — Produits et observabilité (P2)

1. Notes, Channels, Automations, Calendar.
2. Audio, Images, Evaluations, Analytics.
3. Search, Web Search, Terminal.
4. Logs, Metrics, Health.

## 7. Tests requis

| Niveau | Description |
|---|---|
| **Contrats** | Tests UI → proxy → API → Core pour chaque domaine (Goals, Missions, Facts, Skills, Chat) |
| **Unitaires Core** | Managers Core (SkillManager, ToolManager, MemoryManager, ChatStore, etc.) |
| **API** | Routes FastAPI avec fixtures authentifiées |
| **E2E** | Parcours authentifié complet : login → chat → streaming → persistance → workspace → admin |

## 8. Risques et mitigations

| Risque | Impact | Mitigation |
|---|---|---|
| Réécrire la WebUI sans contrat Core | Haut | Geler les contrats avant tout composant |
| Garder deux backends (ETHAN + Open-WebUI) | Haut | Open-WebUI frontend seulement ; backend ETHAN seul |
| Continuer deux chats | Haut | Consolider sur un modèle Core de conversation |
| Fausse confiance issue du build | Haut | E2E authentifiés et tests de contrats obligatoires |
| Référence Open-WebUI modifiée/non suivie | Moyen | Fork explicite, propre, reproductible |
| Doublons `CoreWebUIStore` persistants | Haut | Démantèlement progressif, domaine par domaine |

## 9. Critères de sortie

La migration est considérée complète lorsque :

1. **Aucun doublon** : `CoreWebUIStore` est supprimé ; chaque domaine passe par
   son manager Core.
2. **Contrats stables** : types TypeScript générés depuis OpenAPI ; une seule
   convention de réponse.
3. **Chat unifié** : un seul modèle de conversation ; streaming et événements
   fonctionnels.
4. **Auth persistante** : register écrit en base ; rôle réel propagé.
5. **Temps réel** : endpoint SSE/WebSocket alimenté par NATS.
6. **E2E verts** : parcours authentifié complet testé.
7. **ETHAN fonctionne sans WebUI** : CLI et autres interfaces utilisent les
   mêmes capacités Core.