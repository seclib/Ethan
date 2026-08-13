# Migration — Backend Open-WebUI → ETHAN API

**Date** : 11/08/2026  
**Statut** : Proposition — aucune modification de code  
**Référence** : `examples/open-webui/backend/open_webui` (v0.9.1)  
**Cible** : `interfaces/api` (ETHAN API Gateway)

---

## Principe obligatoire

**ETHAN Core est la seule source de vérité.**

La WebUI ne doit jamais :
- gérer la logique agent ;
- gérer les providers directement ;
- appeler Ollama directement ;
- stocker les capacités ETHAN.

Toute fonctionnalité du backend Open-WebUI doit être :
- **gardée** si elle est purement UI (affichage, configuration, déclenchement) ;
- **remplacée** par une capacité ETHAN Core/API existante ;
- **supprimée** si elle est redondante avec ETHAN Core ;
- **déplacée dans ETHAN Core** si elle représente une capacité intelligente.

---

## 1. Analyse du backend Open-WebUI

### 1.1 Routers Open-WebUI (29 routers)

| Router | Fonction | Lignes |
|--------|----------|--------|
| `auths.py` | Auth JWT, OAuth, LDAP, API keys | 1348 |
| `chats.py` | CRUD chats, partage, archivage | ~2000 |
| `models.py` | Gestion modèles, accès, meta | 678 |
| `ollama.py` | Proxy Ollama (chat, generate, models) | 1684 |
| `openai.py` | Proxy OpenAI-compatible | 1571 |
| `knowledge.py` | RAG, documents, embeddings | ~800 |
| `memories.py` | Mémoire utilisateur | ~400 |
| `files.py` | Upload, stockage fichiers | ~600 |
| `tools.py` | Outils, tool servers | ~500 |
| `functions.py` | Fonctions (pipeline) | ~700 |
| `skills.py` | Skills | ~400 |
| `users.py` | Gestion utilisateurs, rôles | ~800 |
| `groups.py` | Groupes, permissions | ~400 |
| `configs.py` | Configuration globale | ~500 |
| `retrieval.py` | RAG retrieval | ~300 |
| `terminals.py` | Terminaux distants | ~300 |
| `automations.py` | Automatisations | ~400 |
| `channels.py` | Canaux de discussion | ~500 |
| `calendar.py` | Calendrier | ~300 |
| `notes.py` | Notes | ~300 |
| `prompts.py` | Prompts prédéfinis | ~200 |
| `tasks.py` | Tâches | ~300 |
| `analytics.py` | Analytics | ~200 |
| `audio.py` | Audio/TTS | ~300 |
| `images.py` | Génération d'images | ~300 |
| `evaluations.py` | Évaluations | ~300 |
| `pipelines.py` | Pipelines | ~400 |
| `scim.py` | SCIM provisioning | ~300 |
| `utils.py` | Utilitaires | ~200 |

### 1.2 Modèles Open-WebUI (SQLAlchemy)

| Modèle | Table | Fonction |
|--------|-------|----------|
| `User` | `user` | Utilisateurs |
| `Chat` | `chat` | Conversations |
| `ChatMessage` | `chat_message` | Messages |
| `Model` | `model` | Modèles |
| `Knowledge` | `knowledge` | Documents RAG |
| `Memory` | `memory` | Mémoires |
| `File` | `file` | Fichiers |
| `Tool` | `tool` | Outils |
| `Function` | `function` | Fonctions |
| `Skill` | `skill` | Skills |
| `Group` | `group` | Groupes |
| `Config` | `config` | Configuration |
| `Prompt` | `prompt` | Prompts |
| `Tag` | `tag` | Tags |
| `Folder` | `folder` | Dossiers |
| `Channel` | `channel` | Canaux |
| `Note` | `note` | Notes |
| `Automation` | `automation` | Automatisations |
| `Calendar` | `calendar` | Calendrier |
| `Task` | `task` | Tâches |
| `Evaluation` | `evaluation` | Évaluations |
| `OAuthSession` | `oauth_session` | Sessions OAuth |
| `AccessGrant` | `access_grant` | Grants d'accès |

---

## 2. Tableau de migration

### 2.1 Routers Open-WebUI → Action

| Fonction actuelle (Open-WebUI) | Action | Destination |
|-------------------------------|--------|-------------|
| **Auth** | | |
| `auths.py` — JWT login/logout | **Remplacer** | `interfaces/api/main.py` — `/auth/login`, `/auth/logout` (déjà existant) |
| `auths.py` — OAuth (Google, GitHub, etc.) | **Déplacer dans ETHAN Core** | `core/auth/` — ajouter support OAuth |
| `auths.py` — LDAP | **Déplacer dans ETHAN Core** | `core/auth/` — ajouter support LDAP |
| `auths.py` — API keys | **Déplacer dans ETHAN Core** | `core/auth/` — ajouter gestion API keys |
| `auths.py` — Signup/Register | **Remplacer** | `interfaces/api/main.py` — `/auth/register` (déjà existant) |
| `auths.py` — Sessions | **Remplacer** | `core/auth/` — sessions JWT ETHAN |
| **Chats** | | |
| `chats.py` — CRUD chats | **Déplacer dans ETHAN Core** | `core/state/` — ajouter store chats |
| `chats.py` — Partage | **Déplacer dans ETHAN Core** | `core/state/` — ajouter partage |
| `chats.py` — Archivage | **Déplacer dans ETHAN Core** | `core/state/` — ajouter archivage |
| `chats.py` — Import/Export | **Déplacer dans ETHAN Core** | `core/state/` — ajouter import/export |
| **Modèles** | | |
| `models.py` — CRUD modèles | **Remplacer** | `core/config/schema.py` — `ModelsConfig` (déjà existant) |
| `models.py` — Accès par utilisateur/groupe | **Déplacer dans ETHAN Core** | `core/auth/` — ajouter RBAC modèles |
| `models.py` — Modèles par défaut | **Remplacer** | `core/config/schema.py` — `ModelsConfig.default` (déjà existant) |
| **Providers LLM** | | |
| `ollama.py` — Proxy Ollama | **Supprimer** | `core/llm/provider_manager.py` — ProviderManager gère Ollama |
| `ollama.py` — Pull/Push modèles | **Déplacer dans ETHAN Core** | `core/llm/` — ajouter gestion modèles Ollama |
| `openai.py` — Proxy OpenAI | **Supprimer** | `core/llm/provider_manager.py` — ProviderManager gère OpenAI |
| `openai.py` — Azure OpenAI | **Supprimer** | `core/llm/provider_manager.py` — ProviderManager gère Azure |
| `openai.py` — Anthropic | **Supprimer** | `core/llm/provider_manager.py` — ProviderManager gère Anthropic |
| `openai.py` — Gemini | **Supprimer** | `core/llm/provider_manager.py` — ProviderManager gère Gemini |
| `openai.py` — vLLM | **Supprimer** | `core/llm/provider_manager.py` — ProviderManager gère vLLM |
| `openai.py` — Custom OpenAI | **Supprimer** | `core/llm/provider_manager.py` — ProviderManager gère custom |
| **RAG / Knowledge** | | |
| `knowledge.py` — CRUD documents | **Remplacer** | `interfaces/api/routers/v1.py` — `/v1/knowledge` (déjà existant) |
| `knowledge.py` — Embeddings | **Remplacer** | `core/rag/embeddings.py` (déjà existant) |
| `knowledge.py` — Ingestion | **Remplacer** | `core/rag/ingestion.py` (déjà existant) |
| `retrieval.py` — Retrieval | **Remplacer** | `core/rag/retrieval.py` (déjà existant) |
| `retrieval.py` — Context | **Remplacer** | `core/rag/context.py` (déjà existant) |
| **Mémoire** | | |
| `memories.py` — CRUD mémoires | **Remplacer** | `interfaces/api/routers/v1.py` — `/v1/memory` (déjà existant) |
| `memories.py` — Recherche | **Remplacer** | `core/memory/` — recherche mémoire ETHAN |
| **Fichiers** | | |
| `files.py` — Upload | **Déplacer dans ETHAN Core** | `core/state/` — ajouter store fichiers |
| `files.py` — Stockage | **Déplacer dans ETHAN Core** | `core/state/` — ajouter stockage fichiers |
| **Outils / Fonctions / Skills** | | |
| `tools.py` — CRUD outils | **Remplacer** | `interfaces/api/routers/v1.py` — `/v1/skills` (déjà existant) |
| `tools.py` — Tool servers | **Déplacer dans ETHAN Core** | `core/tools/` — ajouter tool servers |
| `functions.py` — CRUD fonctions | **Déplacer dans ETHAN Core** | `core/tools/` — ajouter fonctions |
| `functions.py` — Pipelines | **Déplacer dans ETHAN Core** | `core/tools/` — ajouter pipelines |
| `skills.py` — CRUD skills | **Remplacer** | `interfaces/api/routers/v1.py` — `/v1/skills` (déjà existant) |
| **Utilisateurs / Groupes** | | |
| `users.py` — CRUD utilisateurs | **Déplacer dans ETHAN Core** | `core/auth/` — ajouter gestion utilisateurs |
| `users.py` — Rôles | **Déplacer dans ETHAN Core** | `core/auth/` — ajouter RBAC |
| `users.py` — Profil | **Déplacer dans ETHAN Core** | `core/auth/` — ajouter profils |
| `groups.py` — CRUD groupes | **Déplacer dans ETHAN Core** | `core/auth/` — ajouter groupes |
| `groups.py` — Permissions | **Déplacer dans ETHAN Core** | `core/auth/` — ajouter permissions |
| **Configuration** | | |
| `configs.py` — Configuration globale | **Remplacer** | `interfaces/api/routers/config.py` — `/config` (déjà existant) |
| `configs.py` — Bannières | **Déplacer dans ETHAN Core** | `core/config/` — ajouter bannières |
| **Terminaux** | | |
| `terminals.py` — Terminaux distants | **Déplacer dans ETHAN Core** | `core/tools/` — ajouter terminaux |
| **Automatisations** | | |
| `automations.py` — CRUD automatisations | **Déplacer dans ETHAN Core** | `core/scheduler/` — ajouter automatisations |
| `automations.py` — Déclencheurs | **Déplacer dans ETHAN Core** | `core/scheduler/` — ajouter déclencheurs |
| **Canaux** | | |
| `channels.py` — CRUD canaux | **Déplacer dans ETHAN Core** | `core/state/` — ajouter canaux |
| `channels.py` — Messages canal | **Déplacer dans ETHAN Core** | `core/state/` — ajouter messages canal |
| **Calendrier** | | |
| `calendar.py` — CRUD calendrier | **Déplacer dans ETHAN Core** | `core/scheduler/` — ajouter calendrier |
| **Notes** | | |
| `notes.py` — CRUD notes | **Déplacer dans ETHAN Core** | `core/state/` — ajouter notes |
| **Prompts** | | |
| `prompts.py` — CRUD prompts | **Déplacer dans ETHAN Core** | `core/config/` — ajouter prompts |
| **Tâches** | | |
| `tasks.py` — CRUD tâches | **Remplacer** | `interfaces/api/routers/v1.py` — `/v1/missions` (déjà existant) |
| **Analytics** | | |
| `analytics.py` — Analytics | **Déplacer dans ETHAN Core** | `core/metrics/` — ajouter analytics |
| **Audio** | | |
| `audio.py` — TTS/STT | **Déplacer dans ETHAN Core** | `core/llm/` — ajouter TTS/STT |
| **Images** | | |
| `images.py` — Génération d'images | **Déplacer dans ETHAN Core** | `core/llm/` — ajouter génération images |
| **Évaluations** | | |
| `evaluations.py` — CRUD évaluations | **Déplacer dans ETHAN Core** | `core/learning/` — ajouter évaluations |
| **Pipelines** | | |
| `pipelines.py` — CRUD pipelines | **Déplacer dans ETHAN Core** | `core/tools/` — ajouter pipelines |
| **SCIM** | | |
| `scim.py` — SCIM provisioning | **Déplacer dans ETHAN Core** | `core/auth/` — ajouter SCIM |

### 2.2 Modèles Open-WebUI → Action

| Modèle Open-WebUI | Action | Destination |
|-------------------|--------|-------------|
| `User` | **Remplacer** | `core/auth/` — utilisateurs ETHAN |
| `Chat` | **Déplacer dans ETHAN Core** | `core/state/` — chats ETHAN |
| `ChatMessage` | **Déplacer dans ETHAN Core** | `core/state/` — messages ETHAN |
| `Model` | **Remplacer** | `core/config/schema.py` — `ModelsConfig` |
| `Knowledge` | **Remplacer** | `core/rag/` — documents RAG ETHAN |
| `Memory` | **Remplacer** | `core/memory/` — mémoire ETHAN |
| `File` | **Déplacer dans ETHAN Core** | `core/state/` — fichiers ETHAN |
| `Tool` | **Remplacer** | `core/tools/` — outils ETHAN |
| `Function` | **Déplacer dans ETHAN Core** | `core/tools/` — fonctions ETHAN |
| `Skill` | **Remplacer** | `core/skills/` — skills ETHAN |
| `Group` | **Déplacer dans ETHAN Core** | `core/auth/` — groupes ETHAN |
| `Config` | **Remplacer** | `core/config/` — configuration ETHAN |
| `Prompt` | **Déplacer dans ETHAN Core** | `core/config/` — prompts ETHAN |
| `Tag` | **Déplacer dans ETHAN Core** | `core/state/` — tags ETHAN |
| `Folder` | **Déplacer dans ETHAN Core** | `core/state/` — dossiers ETHAN |
| `Channel` | **Déplacer dans ETHAN Core** | `core/state/` — canaux ETHAN |
| `Note` | **Déplacer dans ETHAN Core** | `core/state/` — notes ETHAN |
| `Automation` | **Déplacer dans ETHAN Core** | `core/scheduler/` — automatisations ETHAN |
| `Calendar` | **Déplacer dans ETHAN Core** | `core/scheduler/` — calendrier ETHAN |
| `Task` | **Remplacer** | `core/missions/` — missions ETHAN |
| `Evaluation` | **Déplacer dans ETHAN Core** | `core/learning/` — évaluations ETHAN |
| `OAuthSession` | **Déplacer dans ETHAN Core** | `core/auth/` — sessions OAuth ETHAN |
| `AccessGrant` | **Déplacer dans ETHAN Core** | `core/auth/` — grants ETHAN |

---

## 3. Résumé des actions

| Action | Nombre | Exemples |
|--------|--------|----------|
| **Garder** | 0 | Aucun router Open-WebUI n'est conservé tel quel |
| **Remplacer** | 12 | Auth JWT, modèles, providers, RAG, mémoire, skills, config, missions |
| **Supprimer** | 7 | Proxy Ollama, Proxy OpenAI, Azure, Anthropic, Gemini, vLLM, Custom |
| **Déplacer dans ETHAN Core** | 10 | Chats, fichiers, outils, fonctions, utilisateurs, groupes, automatisations, canaux, notes, calendrier |

---

## 4. Nouveaux routers ETHAN nécessaires

### 4.1 Routers à créer dans `interfaces/api/routers/`

| Router | Fonction | Endpoints |
|--------|----------|-----------|
| `chats.py` | CRUD chats, partage, archivage | `/v1/chats` |
| `files.py` | Upload, téléchargement fichiers | `/v1/files` |
| `users.py` | Gestion utilisateurs, profils | `/v1/users` |
| `groups.py` | Groupes, permissions | `/v1/groups` |
| `automations.py` | Automatisations | `/v1/automations` |
| `channels.py` | Canaux de discussion | `/v1/channels` |
| `notes.py` | Notes | `/v1/notes` |
| `prompts.py` | Prompts prédéfinis | `/v1/prompts` |
| `tools.py` | Outils, tool servers | `/v1/tools` |
| `functions.py` | Fonctions, pipelines | `/v1/functions` |
| `audio.py` | TTS/STT | `/v1/audio` |
| `images.py` | Génération d'images | `/v1/images` |
| `evaluations.py` | Évaluations | `/v1/evaluations` |
| `analytics.py` | Analytics | `/v1/analytics` |
| `calendar.py` | Calendrier | `/v1/calendar` |
| `tasks.py` | Tâches | `/v1/tasks` |

### 4.2 Modules Core à créer

| Module Core | Fonction |
|-------------|----------|
| `core/state/chats.py` | Store chats (CRUD, partage, archivage) |
| `core/state/files.py` | Store fichiers (upload, stockage) |
| `core/state/channels.py` | Store canaux (CRUD, messages) |
| `core/state/notes.py` | Store notes (CRUD, épinglage) |
| `core/auth/users.py` | Gestion utilisateurs (CRUD, profils) |
| `core/auth/groups.py` | Gestion groupes (CRUD, permissions) |
| `core/auth/oauth.py` | Support OAuth (Google, GitHub, etc.) |
| `core/auth/ldap.py` | Support LDAP |
| `core/auth/api_keys.py` | Gestion API keys |
| `core/auth/scim.py` | SCIM provisioning |
| `core/scheduler/automations.py` | Automatisations (règles, déclencheurs) |
| `core/scheduler/calendar.py` | Calendrier |
| `core/tools/servers.py` | Tool servers |
| `core/tools/functions.py` | Fonctions, pipelines |
| `core/llm/tts.py` | TTS/STT |
| `core/llm/images.py` | Génération d'images |
| `core/learning/evaluations.py` | Évaluations |
| `core/metrics/analytics.py` | Analytics |

---

## 5. Ordre de migration — État actuel

### Phase 1 — Fondations (semaine 1-2) ✅ Implémentée (Core) / ⚠️ En cours (API)

1. ✅ `core/state/chats.py` — ChatStore
2. ✅ `core/state/files.py` — FileStore
3. ✅ `core/auth/users.py` — UserManager
4. ✅ `core/auth/groups.py` — GroupManager
5. ⚠️ `interfaces/api/routers/domains.py` — CRUD `/chats`, `/files`, `/users`, `/groups` (Partiellement exposé)
6. ✅ `interfaces/api/main.py` — injection des managers via `set_domain_managers`

### Phase 2 — Capacités avancées (semaine 3-4) ✅ Implémentée (Core) / ❌ Non exposée (API)

7. ✅ `core/auth/oauth.py` — OAuthManager
8. ✅ `core/auth/ldap.py` — LDAPManager
9. ✅ `core/auth/api_keys.py` — APIKeyManager
10. ✅ `core/scheduler/automations.py` — AutomationManager
11. ✅ `core/tools/servers.py` — ToolServerManager

### Phase 3 — Extensions (semaine 5-6) ✅ Implémentée (Core) / ❌ Non exposée (API)

12. ✅ `core/llm/tts.py` — TTSEngine
13. ✅ `core/llm/images.py` — ImageGenerator
14. ✅ `core/learning/evaluations.py` — EvaluationManager
15. ✅ `core/metrics/analytics.py` — AnalyticsManager
16. ✅ `core/state/channels.py` — ChannelStore
17. ✅ `core/state/notes.py` — NoteStore

### Phase 4 — Finalisation (semaine 7-8) ✅ Implémentée (Core) / ❌ Non exposée (API)

18. ✅ `core/auth/scim.py` — SCIMManager
19. ✅ `core/scheduler/calendar.py` — CalendarManager
20. ✅ `core/tools/functions.py` — FunctionManager
21. ✅ Tests — `tests/core/test_domain_stores.py` (25/25 passants)

### Reste à faire

- Supprimer le backend Open-WebUI de `examples/open-webui/backend/`
- Ajouter les routers ETHAN manquants (prompts, tasks, audio, images, evaluations, analytics, calendar)
- Intégration WebUI progressive (sélecteur de modèles, chat, etc.)

---

## 6. Conclusion

Le backend Open-WebUI est **entièrement remplaçable** par les capacités ETHAN Core/API.

**Aucun router Open-WebUI n'est conservé tel quel** — tous sont soit remplacés par des capacités ETHAN existantes, soit déplacés dans ETHAN Core, soit supprimés.

La migration est **progressive** (4 phases, 8 semaines) et **respecte le principe ETHAN** : toute la logique métier est dans Core/Runtime, la WebUI ne fait qu'afficher et contrôler.