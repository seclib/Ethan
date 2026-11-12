# Open-WebUI → ETHAN — Analyse UX et Tableau de Migration

> **Objective** : Analyser l'expérience Open-WebUI (`examples/openwebui`) pour reproduire son **organisation visuelle UX** (et non son code) dans ETHAN WebUI.
> **Principe (AGENTS.md)** : la WebUI **présente** les capacités ETHAN ; elle ne les recrée pas. Open-WebUI est référence **indépendante**.
> **Backend ETHAN** : Core/Runtime + `interfaces/api` ≠ backend monolithique Open-WebUI.

---

## 1. Synthèse exécutive

| Critère | Open-WebUI | ETHAN Core | Verdict migration |
|---|---|---|---|
| **Nature** | App web complète (UI + backend monolithique FastAPI) | Runtime IA modulaire + interfaces thin | OWUI = référence UX ; ETHAN = source de vérité |
| **Frontend** | Svelte 5 (SvelteKit), tightly-coupled | Next.js 15 (React), clients API modulaires + React Query thin | OWUI UX mature ; ETHAN architecture client propre |
| **Providers LLM** | Valves par connexion (Ollama, OpenAI, Anthropic, Google, LMStudio…) | `core/llm/` providers homogènes + `routing.yaml` | P0 — recâbler le selector |
| **RAG** | 15 vectordbs + 20 moteurs recherche + rerankers | `core/rag/` (Qdrant/PG/Chroma) + `core/knowledge` graphe | OWUI + riche ; ETHAN architecture modulaire (P2) |
| **MCP** | Client MCP complet (`utils/mcp/client.py`) | `core/tools/servers.py` ToolServerManager (enregistrement) | P1 — rapport client MCP dans Core |
| **Agents** | **Pas natifs** (functions/pipelines = tools) | `core/agents/` (AgentManager, états, exécutions) | **ETHAN dominant** — recréer l'UX agent |
| **Permissions** | UserPermissions granulaire (15 dims UX) | `Permission` enum (10) | OWUI + granularité ; ETHAN + simple (mapping) |

**Verdict** : OWUI est **inspiration UX**, jamais **base code directe**. Fork du frontend OWUI comme référence ; backend remplacé par ETHAN Core via l'API gateway.

---

## 2. Cartographie par élément UX — tableau de coverage

> Légende : ✅ existe dans ETHAN · ⚠️ existe ailleurs/partiellement · ❌ n'existe pas

### Shell & navigation

| Élément OWUI | Comportement observé | Équivalent ETHAN | Coverage | Notes migration |
|---|---|---|---|---|
| Sidebar unifiée | Conversations épinglées, favoris modèles, historique groupé | `useChats` + `chat-sidebar.store.ts` | ✅ | Ajouter épinglage modèles dans la sidebar (cf. `useActiveModel`) |
| Navigation secondaire | Workspace/Admin, onglets horizontaux scrollables | Sections Settings (10) | ⚠️ | Scinder : Workspace (gestion) vs Admin (config) ; migrer vers `/admin` unifié |
| Gating par permission | Route cachée si feature absente | `Permission.*` côté API | ✅ | Garder — masquer actions si permission absente |
| Commandes globales (Ctrl+K) | Recherche, nouveau chat, focus | `GlobalCommandPalette` | ✅ | Conforter : ouvrir via `Ctrl+K`, naviguer vers les mêmes destinations |
| Comptes utilisateurs | User menu (avatar/login) | Auth provider | ✅ | Ajouter le dropdown avatar avec logout/paramètres |
| Thème (system) | `system` clair/sombre/auto | `ThemeProvider` | ✅ | Étendre : ajouter `system` + échelle texte dans Settings |

### Chat & composer

| Élément OWUI | Comportement observé | Équivalent ETHAN | Coverage | Notes migration |
|---|---|---|---|---|
| Chat route | `(app)/c/[id]/+page.svelte` (URL par conversation) | `app/page.tsx` (aucune route) | ❌ | **Créer `/c/[id]`** pour deep-link + retour navigateur (backend `/chats` + `/chats/{id}/messages` déjà prêt) |
| RichTextInput | Focus global, slash-commands, mentions skills | `AssistantInput` + textarea | ⚠️ | Ajouter slash-commands (`/model`, `/agent`) + mentions structurées skills |
| Sélecteur modèle | Popover ancré, recherche, tags, épingles | `ModelSelector` variant `full` (jamais monté) | ⚠️ | Promouvoir le variant `full` dans le header chat |
| Sélecteur agent (new) | **N/A — OWUI n'a pas d'agents natifs** | `AgentSelector` (créé §4) | ✅ (déjà fait ETHAN) | L'UI ETHAN a **dépassé** OWUI ici |
| Tool calls | Blocs repliables, status stream | `patchAssistant({tools})` dans `use-chats.ts` | ✅ | Rendre inspectables dans un drawer (ex: bouton "Outils (2)" sous le message) |
| Sources / fichiers | Preview images, PDF, liens dans le message | Attachments dans `AssistantInput` | ⚠️ | Ajouter preview des fichiers joints dans le message (upload API existe) |

### Catalogues & workspaces

| Élément OWUI | Comportement observé | Équivalent ETHAN | Coverage | Notes migration |
|---|---|---|---|---|
| Knowledge liste | Liste/recherche/pagination, vue détail par base | `KnowledgeWorkspace` | ⚠️ | Regrouper : `/knowledge` devient Workspace ; les réglages RAG → Admin |
| Knowledge détail | Fichiers, upload, reindex, permissions | même | ✅ | Conservation — ajouter statut d'ingestion "upload → processing → available" |
| Skills | CRUD, clone sessionStorage, insertion mention | `SkillsWorkspace` + `SkillDialog` | ⚠️ | Fusionner Settings↔page ; le slash-command insère la mention (déjà chat-supporté) |
| Tools | ToolkitEditor, ToolMenu, ToolServersModal | `ToolsWorkspace` + Settings→mcp | ⚠️ | Absorber MCP sous `/tools` (onglet serveurs) — Settings→mcp doublon |
| Model cards | `ModelItem`, métadonnées, capabilities, menu c | `ModelsWorkspace` | ⚠️ | Équilibrer le design UX OWUI (tags, épinglage) avec le catalogue agrégé Core |
| Provider forms | Valves, connexion, test | `ProviderFormDialog` | ✅ | Migrer les *valves* vers un secret manager Core (P1) |
| Admin Settings | Users, Analytics, Evaluations, Functions | SettingsWorkspace (10 sections) | ⚠️ | Découper : Admin = Users/Analytics/Evaluations → Core ; garder UX |
| Connections | MCP/serveur configuration | `core/tools/servers.py` + Settings→mcp | ⚠️ | Client MCP complet OWUI → reporter dans Core (`core/tools/mcp_client.py` existe) |

### Patterns UI observés chez OWUI (à reprendre)

| Pattern | Usage | Migration ETHAN |
|---|---|---|
| Overlay spécialisé | Recherche, fichiers, partage, valves, OAuth | Garder — modals/drawers existants (`Dialog`, `AgentEditorDialog`, `ProviderFormDialog`) |
| Stores de présentation | `show*` (sidebar, controls, embeds, artifacts) | Adopté : `ui.store.ts` Zustand — **déjà fait** |
| Vue registre | List/recherche/pagination + création + vue détail + menu | Appliquer à chaque workspace (Agents, Tools, Models, Knowledge) |
| États transitoires | `svelte-sonner` toasts | `useUIStore().addToast` — **déjà fait** |

---

## 3. Éléments UX OWUI absents de ETHAN (débloquants)

| Fonctionnalité OWUI | Pourquoi migrer | Coverage ETHAN | Priorité | Action |
|---|---|---|---|---|
| Route par conversation `/c/[id]` | Deep-link, retour arrière | ❌ (`/`) | **P1** | Créer `app/c/[id]/page.tsx` branché sur `/chats/{id}/messages` |
| Preview fichiers joints dans le message | Compréhension des pièces | ⚠️ (upload seul) | P1 | Rendre les `file_ids` en preview dans `assistant-message` |
| Branches de chat navigables | Régénérer/éditer = navigation | ⚠️ (arbre Core) | P2 | V1 versions ‹ › ; V2 arbre paginée |
| System prompt / Prompts | Prompts réutilisables | ❌ | P1 | Endpoint `/v1/prompts` Core puis page Workspace |
| Feedback thumbs | Noter qualité réponses | ❌ | P2 | Endpoint `/v1/feedback` Core + bouton sous message |

---

## 4. Ce que fait *mieux* ETHAN que OWUI

| Domaine | ETHAN Core | Avantage |
|---|---|---|
| **Agents** | `core/agents/` (AgentExecutor, états, exécutions) | **Agents natifs** tandis qu'OWUI n'en a pas (functions ≠ agents) |
| Architecture clean | Core/Runtime/Services, EventBus | OWUI = monolithique |
| Secrets | `core/config/secrets.py` (env/Vault) | OWUI stocke en DB → violation AGENTS.md |

→ **Conserver** dans la refonte UX ; ne pas recréer le monolithisme OWUI.

---

## 5. Risques de régression UX

| Risque | Origine | Mitigation |
|---|---|---|
| Perte historique chats | Route `/c/[id]` change source de vérité | Sync `chat-sidebar.store.ts` ; tests e2e |
| Doublons Settings↔pages | Migration incomplète | Table §2 — chaque capability **une fois** |
| Perf selector modèle | `variant full` jamais monté | Recherche client `useModels().searchModels` |
| Cohérence thème | Tokens CSS personnalisés | Vérifier `ThemeProvider` couvre `system` |

---

## 6. Feuille de route (ordre recommandé)

| Phase | Élément | Action | Fichier |
|---|---|---|---|
| 1 | Navigation | Taxinomie unique → sidebar + header | `components/layout/` |
| 2 | Header chat | `[Agent ▼] [Model ▼]` + context bar | `assistant-top-bar.tsx` |
| 3 | Composer | Toolbar (Tools/Knowledge/Skills) | `assistant-input.tsx` |
| 4 | Conversations | `/c/[id]` | `app/c/[id]/page.tsx` (NEW) |
| 5 | Grilles | Cards inspirées OWUI | workspaces existants |
| 6 | Admin | `/admin` unifié | `app/admin/*` |
| 7 | Fichiers | Preview + drawers | `assistant-message.tsx` |

---

## 7. Légende

| Symbole | Signification |
|---|---|
| ✅ | Présente + branchée (Core + API + WebUI) |
| ⚠️ | Core/API présent, WebUI incomplet/dispersé/doublon |
| ❌ | N'existe pas côté Core — implémenter Core d'abord |

> Avant de construire : vérifier existence dans `core/`, route HTTP exposée, contrat de réponse cohérent.

