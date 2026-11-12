# Audit WebUI ETHAN — Refonte UX inspirée d'Open-WebUI

> **Date** : 26 août 2026 · **Branche** : `main` @ `725dd1d5`
> **Portée** : cartographie uniquement — aucune modification fonctionnelle.
> **Référence UX/UI** : `examples/open-webui/` (Open WebUI 0.9.x, SvelteKit/Svelte) — **référence d'expérience, pas de code à copier**.
> **Documents apparentés** : `docs/audit/WEBUI_CURRENT_STATE.md`, `docs/audit/OPENWEBUI_UX_REFERENCE.md`, `docs/audit/OPENWEBUI_COMPONENT_REFERENCE.md`, `docs/architecture/OPENWEBUI_ETHAN_MAPPING.md`, `docs/plans/ETHAN_WEBUI_MASTER_PLAN.md`.

---

## Résumé exécutif

La WebUI ETHAN est déjà un **client mince Next.js 15 / React 19** correctement branché sur l'API ETHAN (proxy `/api/*` → FastAPI :8000, JWT cookie HttpOnly, SSE streaming, React Query, Zustand). La frontière Core/WebUI est globalement respectée : toutes les capacités métier (providers, modèles, agents, skills, tools/MCP, RAG/knowledge, memory, settings) sont servies par `core/` via `interfaces/api/routers/`.

Le problème n'est donc **pas architectural**, il est **UX** :

1. **Trois couches de navigation redondantes et divergentes** (IconRail, AppSidebar "Navigation", sections Settings) qui listent les mêmes capacités différemment.
2. **Changement de LLM/agent trop discret** : sélecteur compact dans deux endroits, dropdown riche jamais monté, sélection d'agent enfouie dans le menu "+" du composer.
3. **Pas de route par conversation** (`/c/[id]`) : pas de deep-link, pas de retour navigateur, rechargement = perte du contexte courant.
4. **Duplication Settings ↔ pages dédiées** : Providers/Models/Skills/Agents/Tools/MCP existent deux fois, avec des niveaux de complétude différents.
5. **Surfaces UI incomplètes alors que l'API existe** (fiches modèles custom, memory, exécutions d'agents, archivage/tags de conversations).

La refonte recommandée consiste à **réorganiser visuellement** autour d'un shell unique type Open-WebUI (sidebar opérationnelle + chat central + Workspace/Admin distincts), **sans toucher aux contrats API ni au Core**.

## 1. Architecture frontend actuelle

### 1.1 Stack

| Élément | Valeur |
|---|---|
| Framework | **Next.js 15 App Router + React 19** ("use client" SPA) — `interfaces/webui/package.json` |
| Styles | Tailwind CSS 3 + design tokens CSS vars (`--bg`, `--panel`, `--accent`…) + système accent custom (`src/lib/accent.ts`) |
| État serveur | TanStack Query v5 |
| État local | Zustand (`ui.store.ts`, `chat-sidebar.store.ts`) |
| Animation | framer-motion (transitions de page) |
| Markdown | react-markdown + remark-gfm |
| Icônes | lucide-react · Tests : Jest/RTL, Playwright, Storybook |

### 1.2 Chaîne réseau

```
Navigateur ── fetch('/api/*') + cookie HttpOnly ethan_token
      ▼
Next proxy src/app/api/[...path]/route.ts
  (strip /api · cookie → Bearer · pipe SSE sans buffering · binaire préservé)
      ▼
FastAPI interfaces/api/main.py (:8000)
  ├─ /auth/*     auth.py            login/register/refresh/me
  ├─ /providers  providers.py       CRUD + {id}/models + {id}/test + {id}/default
  ├─ /models     models.py          catalogue agrégé + search + cartes custom + toggle
  ├─ /chats      core/state/chats   ChatStore : arbre de messages, pin, titre
  └─ /v1/*       v1.py + routers    agents(+execute), goals, missions(+steps),
                                    tools(+servers MCP), knowledge, rag,
                                    memory facts/events/search, flux, settings,
                                    chat/completions(+stream SSE), chat/history,
                                    plugins, capabilities (calendar/notes/audio/
                                    images/research/cookbook/email/security…)
```

### 1.3 Layout global

`src/app/layout.tsx` monte : ThemeProvider → QueryProvider → AuthProvider → I18nProvider → WebSocketProvider → ToastProvider ; puis overlays globaux permanents (`GlobalShortcuts`, `GlobalCommandPalette` Ctrl+K, `GlobalInspector`, `MissionControlOverlay`, `AtmosphereLayer`) ; **IconRail** + **AppSidebar** ; `<main>` avec transition framer-motion par route.

### 1.4 Routing (`src/app/*`)

| Route | Contenu | Branchement backend |
|---|---|---|
| `/` | Chat (page d'accueil) | `/chats`, `/v1/chat/completions/stream`, catalogues |
| `(auth)/login·register` | formulaires | `/auth/*` |
| `/workspace` | dashboard multi-tabs : métriques missions/goals/flux/**memory explorer** | `/v1/missions·goals·flux`, `/v1/memory/facts` |
| `/calendar` · `/notes` | CRUD événements / notes | capabilities |
| `/knowledge` | collections ↔ documents RAG, ingestion texte/fichier | `/v1/knowledge*`, `/v1/rag/documents` |
| `/missions` | missions + goals | `/v1/missions`, `/v1/goals` |
| `/agents` | workspace CRUD agents | `/v1/agents` |
| `/skills` · `/tools` | workspaces skills / tools+MCP catalogue | skills, `/v1/tools*` |
| `/providers` | CRUD provider, test connexion, toggle, popover modèles | `/providers` |
| `/models` | catalogue agrégé, recherche, pin, disponibilité | `/models` |
| `/settings` | **10 sections** : general, appearance, models, providers, knowledge, rag, skills, agents, tools, mcp | mixte |
| `/security` | 2FA TOTP + gestion utilisateurs admin | `/security/*` |
| `/inbox` | mail lecture seule | email router |
| `/research` | deep research requête→rapport | research router |
| `/cookbook` | recettes installables en records Core | cookbook router |

Middleware `src/middleware.ts` : protège toutes routes sauf auth/API/assets.

### 1.5 Sidebar & header actuels

- **IconRail** (`components/layout/sidebar.tsx::IconRail`) : bouton Search (**sans onClick — inerte**), Nouveau chat, 10 entrées fixes, Settings en bas. Sa liste **ne concorde pas** avec la NavigationContent (Skills, Inbox, Research, Cookbook, Security absents).
- **AppSidebar** : sur `/` → vue Chats (recherche par titre, épinglés, groupage temporel, rename double-clic, pin/delete, **ModelSelector compact** en pied) ; ailleurs → `NavigationContent` (11 liens + section Système à 4). UserBar statique "User" en bas.
- **Header chat** (`AssistantTopBar`) : titre + dot statut agent + ModelSelector compact. Aucun menu contextuel ni accès aux réglages du chat.

### 1.6 Chat actuel

- Composer `AssistantInput` : textarea auto-resize, upload fichiers multi (chips supprimables), menu "+" → sous-groupes cochables **Skills / Knowledge / Tools (badge builtin·mcp) / Agent**, chips récapitulatives.
- `page.tsx::runStream` → `sendMessageStream({message, chat_id, provider_id, model, file_ids, skill_ids, tool_ids, knowledge_ids+collection_ids, agent_id, metadata})` → SSE `POST /v1/chat/completions/stream`. **Les sélections sont réellement transmises au backend.**
- Commande slash `/model <id>` interceptée côté client.
- Messages : markdown, sections repliables (reasoning/tools/documents/memory), footer modèle/provider, actions régénérer/éditer (nouvelle branche Core), typing indicator, scroll-to-bottom, bannière erreur dismissable.
- L'arbre existe dans le ChatStore Core (`parent_id`/`children_ids` du contrat) mais **n'est pas navigable dans l'UI**.
- Historique des conversations : pont Zustand `chat-sidebar.store.ts` page→shell, **aucune URL par conversation**.

### 1.7 Sélection LLM (`useActiveModel`)

- `GET /providers` ; défaut = `is_default` sinon premier `enabled`.
- localStorage `ethan.active-provider` / `ethan.active-model` ; changement de provider ⇒ `PUT /providers/{id}/default` + toast.
- `setModel` local uniquement. UI : variant `full` du `ModelSelector` (dropdown recherche/pin/capabilities) — **jamais monté** ; seuls les usages `compact` existent.

### 1.8 Clients API frontend (`lib/api/*`)

`agents, audio, capabilities, chat, client, extensions, files, flux, goals, knowledge, memory, missions, models, providers, rag, security, settings, skills, tools` — wrappers fetch fins sans logique métier. Conforme au principe « WebUI = client » ✔.

---

## 2. Où sont exposées les fonctionnalités aujourd'hui

| Capacité | Endroit(s) UI | État |
|---|---|---|
| Sélection LLM | `AssistantTopBar` (compact) + pied de sidebar chats (compact) ; variant full jamais monté ; commande `/model` cachée | ⚠️ trop discret |
| Sélection agent | menu "+" du composer uniquement (liste cochable) | ⚠️ peu découvrable |
| Création/config agent | `/agents` + AgentEditorDialog | ✔ branché |
| Providers | `/providers` (CRUD complet) **et** Settings→providers (CRUD dupliqué) | 🔴 doublon |
| Modèles | `/models` (lecture + pin) **et** Settings→models (toggle) ; cartes custom (`POST/PUT/DELETE /models`) **sans UI** | ⚠️ partiel |
| Skills | `/skills` **et** Settings→skills (toggle) ; sélection au chat via composer | ⚠️ doublon |
| Tools/MCP | `/tools` (catalogue) ; MCP = Settings→mcp uniquement (CRUD servers `/v1/tools/servers`) ; Tools badge mcp au composer | ⚠️ dispersé |
| RAG/Knowledge | `/knowledge` (collections+documents) **et** Settings→knowledge (état live+liens) **et** Settings→rag (config) | 🔴 éclaté |
| Memory | aucun écran dédié : `useFacts` dans un onglet de `/workspace` ; API complète (`/v1/memory/facts`, search, events) non exposée | 🔴 |
| Paramètres utilisateur | Settings→general/appearance (thème, accent) | ✔ |
| Paramètres système | Settings (rag config…), `/security` (2FA, users) | ⚠️ mélange user/admin |
| Missions/Goals | `/missions` + onglets Workspace | ⚠️ doublon partiel |

## 3. Problèmes UX identifiés

### 3.1 Constat principal

1. **Changer de LLM** : deux sélecteurs compactes discrets ; le dropdown riche (recherche, pins, capabilities) existe mais n'est jamais monté.
2. **Changer d'agent** : uniquement dans le menu "+" du composer — invisible tant qu'on n'a pas ouvert le menu.
3. **Informations dispersées** : la même capacité apparaît à 2-4 endroits (cf. tableau §2), avec des niveaux de complétude inégaux.
4. **Navigation trop complexe** : IconRail ≠ AppSidebar ≠ Settings (3 taxinomies différentes des mêmes capacités).
5. **Découvrabilité faible** : memory, MCP, exécutions d'agents, cartes modèles custom sont cachés ou absents ; bouton Search de l'IconRail mort alors qu'une palette Ctrl+K existe.
6. **Pages redondantes** : `/providers` vs Settings→providers ; `/models` vs Settings→models ; missions dans deux écrans.
7. **Composants inutilisés/sous-utilisés** : `ModelSelector` variant `full`, `InsightsPanel`, onglets Workspace redondants avec pages dédiées.
8. **États UI déconnectés du backend** : UserBar "User" statique ; icône Search sans action ; badges disponible/indisponible des modèles non rafraîchis au retour sur la page.
9. **Boutons non fonctionnels** : le Search rail (identifié §1.5).
10. **Logique dupliquée côté frontend** : logiques CRUD provider/skill/agent réécrites dans Settings **au lieu de réutiliser les hooks `features/*` existants** (`use-providers.ts`, `use-skills.ts`, etc.) — duplication React Query côté client uniquement, pas de logique métier déplacée hors Core.

### 3.2 Détail par symptôme

- Recharger `/knowledge` après ingestion ne force pas le refresh des stats RAG affichées ailleurs.
- Le changement d'agent en cours de conversation modifie uniquement les requêtes suivantes — aucun feedback clair « conversation pilotée par X ».
- Les chips composer (skills/knowledge/tools) récapitulent un compte sans nom lisible quand plusieurs éléments (ex. « Knowledge (2) »).
- Pas d'archivage ni de tags/dossiers de conversations (API ChatStore absent → besoin backend avant UI, cf. §10).
- Absence d'écran dédié Memory & Learning bien que l'API soit complète.

---

## 4. Patterns Open-WebUI à reprendre (référence UX)

| Zone | Pattern observé | Transposition ETHAN |
|---|---|---|
| Sidebar | Bibliothèque opérationnelle unique : chats groupés/pinnés + modèles pinnés + items applicatifs | AppSidebar devient la source unique : vue Chats contextuelle + raccourcis capacités |
| Sélecteur modèle | Popover ancré : recherche Fuse, tags, connexions locales/distantes, pins, capabilities, sous-menu info/actions (admin settings) | Élever `model-selector.tsx` variant `full` en sélecteur hero du top bar chat |
| Composer | Une seule zone de saisie ; contextes actifs visibles et supprimables ; slash commands skills/models/knowledge ; toggles conditionnels selon capabilities du modèle ; bouton stop pendant génération | Garder la structure actuelle (déjà conforme), ajouter slash commands riches + toggles conditionnels |
| Overlays plutôt que navigation | Recherche, fichiers, tagging, partage, valves, paramètres : modals qui gardent le contexte du chat | Rechercher skills/collections/agents au composer via popovers ancrés |
| Workspace vs Admin | Workspace = registres durables (modèles, knowledge, prompts, tools, functions) ; Admin = Users/Analytics/Settings système | Scinder Settings actuel : préférences utilisateur vs administration système |
| Knowledge | Liste de bases → page base avec fichiers, cycle visible upload→processing→disponible | Conserver notre architecture 2 niveaux, ajouter état processing par document |
| Menus par item | menus à 3 points (rename, archive, clone, delete) avec confirmation | Généraliser aux listes chats/knowledge/skills/agents |

## 5. Architecture UI cible

### 5.1 Shell unique (style Open-WebUI, identité ETHAN conservée)

```
┌──────┬───────────────┬──────────────────────────────────────────┐
│ Rail │  AppSidebar   │  Zone principale                         │
│ 48px │  240-260px    │                                          │
│      │ ┌───────────┐ │  TopBar chat : [Modèle ▾] [Agent ▾] menu │
│ New  │ │Vue context│ │  ────────────────────────────────────────│
│ Chat │ │uelle :    │ │  Messages (arbre Core, sources, tools)   │
│ CtrlK│ │ Chats sur │ │  ────────────────────────────────────────│
│ ⚙    │ │ une route │ │  Composer : chips contextes actifs       │
│      │ │ chat      │ │  [+ menu] [/] [send/stop]                │
│      │ │ Nav       │ │                                          │
│      │ │ ailleurs  │ │  Panneau contexte (optionnel, right)     │
│      │ └───────────┘ │                                          │
│ User │  + modèle     │                                          │
└──────┴───────────────┴──────────────────────────────────────────┘
```

- **Rail** : purement afféral (toggle sidebar, nouveau chat, palette Ctrl+K fonctionnelle, settings). Aucune entrée de navigation métier.
- **AppSidebar** : une seule taxinomie. Sur une route de conversation → vue Chats (pins, groupes temporels, recherche) ; ailleurs → vue Navigation (liens vers Chat, Workspace, Missions, Calendar, Notes, Inbox, Knowledge, Agents, Skills, Tools, Research, Cookbook, Security).
- **UserBar** remplacée par menu utilisateur réel (`useAuth`) : profil, préférences, admin (si permission), déconnexion.

### 5.2 Navigation cible

```
Chat (défaut)          /            conversation + /c/[id]
Espace opérationnel    /workspace   missions, goals, flux, memory
                       /missions · /calendar · /notes · /inbox
Capacités (registres)  /knowledge   collections + documents RAG
                       /agents      agents + exécutions
                       /skills · /tools (+ serveurs MCP intégrés)
Système                /providers   providers + modèle défaut
                       /models      catalogue + cartes custom
                       /research · /cookbook
Préférences utilisateur  /settings  (general, appearance, chat)
Administration système   /admin     (providers, models, rag, mcp,
                                     security/users) — garde par rôle
```

### 5.3 Chat cible

- Route `/c/[id]` parallèle à `/` (nouvelle conversation sans URL) — deep-link, retour navigateur, reprise après reload.
- Top bar : sélecteur **modèle** (hero, popover ancré : recherche, pins, badges local/remote, capabilities, disponibilité) + sélecteur **agent** (popover dédié : nom, description, provider/model résolus) + menu ⋮ (paramètres du chat, arche…).
- Composer inchangé structurellement ; ajouts : slash commands riches (skills/collections/agents/modèles), chips nommées, toggles conditionnels.
- Message : arbre Core navigable (parents/enfants), sections inspectables inchangées, régénération = nouvelle branche explicite.

## 6. Mapping ancien composant → nouveau rôle

| Composant actuel | Rôle cible | Destination |
|---|---|---|
| `layout/sidebar.tsx::IconRail` | Rail afféral épuré ; Search relié à la palette | `components/layout/rail.tsx` (ou refactor in place) |
| `layout/sidebar.tsx::AppSidebar`/`NavigationContent`/`ChatSidebarContent` | Sidebar opérationnelle unique, vue contextuelle par route | conserve le pont `chat-sidebar.store.ts` |
| `shared/model-selector.tsx` variant `full` | Sélecteur hero du chat + entrées sidebar (« modèles pinnés ») | monté dans `assistant-top-bar.tsx` |
| `assistant-top-bar.tsx` | Ajoute sélecteur d'agent popover + menu ⋮ du chat | même fichier, enrichi |
| `assistant-input.tsx` | Composer inchangé + slash commands riches + chips nommées | même fichier, enrichi |
| `assistant-chat.tsx` | Ajoute navigation de l'arbre de messages | même fichier |
| `providers/components/providers-workspace.tsx` | Source unique CRUD providers — **remplace** Settings→providers | `/providers` (Settings→lien) |
| `providers/components/models-workspace.tsx` | Catalogue + UI des cartes custom manquantes | `/models` |
| `providers/hooks/use-models·use-providers` | Réutilisés par la nouvelle UI Admin ; duplication Settings supprimée | inchangés |
| `settings/settings-workspace.tsx` | Scindé : user → `/settings` ; sections métier → `/admin` en réutilisant les hooks features | réécrit en 2 workspaces légers |
| `knowledge/knowledge-workspace.tsx` | Conservé ; ajoute état processing/document | `/knowledge` |
| `skills/skills-workspace+dialog` | Conservés | `/skills` |
| `tools/tools-workspace.tsx` | Catalogue outils **absorbe** la gestion MCP servers (ex-Settings→mcp) | `/tools` |
| `agents/*` | AgentsWorkspace + editor + **nouvel onglet exécutions** (`GET /v1/agents/{id}/executions`) | `/agents` |
| `workspace/page.tsx` multi-tabs | Dashboard unique : missions/goals/flux + Memory section pleine (facts/search/events) ; tabs redondants retirés | `/workspace` |
| `global-command-palette.tsx` | Reste Ctrl+K ; bouton rail Search s'y branche ; index conversations ajouté | inchangé |
| `inspector/global-inspector` · `MissionControlOverlay` | Conservés tels quels (différenciateurs ETHAN) | inchangés |

## 7. Fonctionnalités existantes à conserver

1. Chaîne proxy/SSE/JWT (`app/api/[...path]/route.ts`, middleware auth).
2. Tous les clients `lib/api/*` et hooks TanStack `features/*/hooks`.
3. Composer : menu "+" multi-sélection skills/knowledge/tools/agent, upload fichiers, chips.
4. Chat streaming avec tool events, stop, régénérer/éditer (branches Core), sections repliables, metrics footer.
5. Vue Chats de la sidebar (pins, groupes temporels, rename inline) et son pont Zustand.
6. Knowledge 2 niveaux + ingestion texte/fichier ; Skills CRUD ; Tools catalogue ; Agents CRUD.
7. Providers CRUD/test/toggle/popover models ; Models catalogue/pin/recherche/disponibilité.
8. Overlays globaux : palette, inspector, mission control, toasts, WebSocket status.
9. Design tokens, thème/accent, AtmosphereLayer, i18n, responsive <768px auto-collapse.
10. Storybook + tests existants.

## 8. Fonctionnalités à déplacer visuellement (pas réécrire)

| Capacité | D'où | Vers | Nature du changement |
|---|---|---|---|
| CRUD providers | `/providers` + Settings→providers (2 implémentations) | `/providers` seule (Admin garde un lien) | supprimer la section Settings, garder les hooks |
| Toggle modèles | Settings→models | `/models` (colonne/toggle sur carte) | fusion |
| Config RAG | Settings→rag | `/admin`→RAG (ou `/knowledge` onglet config) | déplacement de section |
| Serveurs MCP | Settings→mcp | `/tools` onglet « Serveurs MCP » | absorption par ToolsWorkspace |
| Memory facts/search/events | onglet Workspace seulement | section pleine `/workspace` (ou route dédiée) | promotion |
| Exécutions d'agents | nulle part | `/agents` onglet exécutions (API prête) | ajout UI |
| Cartes modèles custom | nulle part | `/models` dialog création/édition (`/models` CRUD API prête) | ajout UI |
| Gestion utilisateurs | `/security` mélangé 2FA+users | `/admin`→Users ; 2FA reste `/settings` | scission |
| Sélecteur modèle | 2 slots `compact` discrets | hero chat (variant full) | relocalisation visuelle |
| Sélection agent | menu "+" composer | popover top bar chat (+ conservé au composer) | promotion |

## 9. À NE SURTOUT PAS réimplémenter

1. **Aucune logique métier dans le WebUI** : pas d'appels directs Ollama/OpenAI/MCP/Postgres depuis le navigateur — tout passe par l'API ETHAN (règle AGENTS.md).
2. **Pas de deuxième brain** : ne pas recréer providers/RAG/memory côté frontend ni dupliquer les stores Svelte d'Open-WebUI.
3. **Pas de copie du code Open-WebUI** : patterns seulement (Svelte ≠ React), pas de dépendance à Bits UI/Tiptap sans décision préalable.
4. **Ne pas casser** : contrats `lib/api/*`, arbre de messages Core, format SSE (`content/done/error/tool_call/tool_result/status/history/names`) descripteurs dans `use-chats.ts`.
5. **Pas de fonctionnalités fantômes** : archivage/tags de chats, partage, ACL fines nécessitent d'abord des endpoints Core — ne pas fabriquer d'UI localStorage-only pour ça.
6. **Ne pas migrer Socket.IO/PersistedTree indexing** ou toute autre brique backend d'Open-WebUI sans RFC.

## 10. Risques de régression

| # | Risque | Impact | Mitigation |
|---|---|---|---|
| R1 | Le bouton rail Search mort vs palette Ctrl+K : brancher sans créer un 2e moteur de recherche | bas | openCommandPalette() |
| R2 | Route `/c/[id]` : la sidebar affiche l'historique via le pont page→shell ; une nouvelle route doit re-registrer le même pont ou centraliser dans le shell | moyen | élever les handlers chat au niveau shell (useChats en provider) |
| R3 | Scission Settings : les 10 sections vivent dans un seul fichier (~900 lignes) ; extraction imparfaite = régression CRUD dupliquée encore pire | élevé | refactor mécanique : chaque section devient un composant importé ; tests RTL avant/après |
| R4 | Sélecteur full au top bar : surface cliquable plus grande, risque de sélections orphelines (model sans provider) | faible | valider couple (provider_id, model) envoyé, cf. useActiveModel |
| R5 | Absorption MCP par /tools : Settings→mcp avait ses propres query keys (`settings-mcp-servers`) — conflits d'invalidation | moyen | unifier sur `['tool-servers']` |
| R6 | Suppression sections Settings métier : utilisateurs habitués perdent leurs points d'entrée | faible | redirections + liens depuis Admin + release notes |
| R7 | `PUT /providers/{id}/default` déclenché à chaque changement de provider dans useActiveModel — effet de bord multi-onglets | faible | documenter le comportement plutôt que le changer |
| R8 | Performance : catalogue modèles peut être volumineux — dropdown plein doit rester virtualisé/léger | faible | pagination/fuse local déjà prévu |
| R9 | WS status provider : les overlays globaux dépendent du WebSocketProvider ; ne pas remonter ces providers pendant la refonte shell | moyen | ne pas toucher à `app/layout.tsx` providers en Phase A |

## 11. Ordre recommandé des modifications

> Chaque phase est livrable/testable indépendamment. Les P0 de robustesse (préflight, healthchecks NATS) du plan Boot ne sont pas impactés.

- **Phase A — Collage shell** (sans changement de comportement)
  1. Brancher Search rail → palette ; UserBar → menu `useAuth`.
  2. Extraire les sections Settings en composants autonomes (préparation à la scission).
- **Phase B — Chat**
  3. Montée du ModelSelector variant full en hero top bar.
  4. Popover sélection d'agent dans le top bar (+ conservé composer).
  5. Route `/c/[id]` (migration interne progressive).
  6. Slash commands riches + chips nommées.
- **Phase C — Navigation unique**
  7. Rail afféral épuré ; AppSidebar taxinomie unique alignée §5.2.
  8. WorkspaceMemory promotion (`/workspace`), suppression tabs redondants.
- **Phase D — Registres & Admin**
  9. `/tools` absorbe MCP servers ; `/models` gagne les cartes custom.
  10. Scission Settings → `/settings` user + `/admin` système (garde par rôle `Permission.*` existante côté API).
  11. `/agents` onglet exécutions.
- **Phase E — Finitions UX Open-WebUI**
  12. Menus ⋮ génériques lists (confirmation delete déjà présente).
  13. États processing documents ; refresh onFocus React Query global.
  14. Arbre de messages navigable si priorisé avec le Core.

## 12. Critères d'acceptation de la future refonte

1. Changer de modèle : **≤ 2 clics depuis le chat**, avec recherche et badges visibles.
2. Changer d'agent : visible en permanence dans le top bar du chat, état « piloté par » explicite.
3. **Une seule taxinomie de navigation** : toute capacité accessible depuis exactement un endroit canonique (+ liens).
4. Zéro doublon CRUD : providers/models/skills/agents/tools/MCP gérés une fois, réutilisés partout (hooks features).
5. Toute liste open-webui-like (chats, knowledge, skills) a : recherche, menu item, confirmation destructive, états loading/error/empty.
6. Memory disposera d'une surface dédiée lisant `/v1/memory/*`.
7. `tsc --noEmit`, `next lint`, `npm run test`, e2e Playwright chat → verts après chaque phase.
8. Aucun appel réseau hors proxy `/api/*` ; aucune clé/secret côté frontend (règle secret).

---

## Annexe A — Fichiers de référence Open-WebUI consultés

| Pattern | Source |
|---|---|
| Shell authentifié / sidebar / overlays | `src/routes/(app)/+layout.svelte`, `src/lib/components/layout/Sidebar.svelte` (+ `Sidebar/{ChatItem,ChatMenu,PinnedModelList,Folders,UserMenu…}`), `layout/SearchModal.svelte`, `Navbar/Menu.svelte`, stores `src/lib/stores/index.ts` (`showSidebar`, `sidebarWidth`, `mobile`) |
| Sélecteur de modèles | `src/lib/components/chat/ModelSelector/{Selector,ModelItem,ModelItemMenu}.svelte` — popover ancré, recherche, pins, capabilities |
| Chat & composer | `chat/MessageInput.svelte` (+ InputMenu, Commands, voice), `chat/Messages.svelte`, `chat/Chat.svelte` (owner état conversationnel) |
| Workspace registres | `routes/(app)/workspace/{models,knowledge,skills,tools,prompts,functions}/+page.svelte`, nav secondaire par onglets |
| Admin | `routes/(app)/admin/settings/+page.svelte` + `lib/components/admin/Settings/*.svelte` (General, Interface, Connections, Models, Documents, Evaluations, Users…) |
| Knowledge cycle | `workspace/Knowledge.svelte`, `Knowledge/KnowledgeBase.svelte`, `Files`, `AddContentMenu` — upload → processing → disponible |

> Ces éléments servent de spécification comportementale. La transposition reste React/Tailwind/Zustand, tokens ETHAN, AtmosphereLayer.

## Annexe B — Carte rapide fichiers WebUI clés

```
interfaces/webui/src/
├─ middleware.ts                     garde auth cookie
├─ app/layout.tsx                    providers + rail/sidebar + overlays
├─ app/page.tsx                      page chat (runStream, pont sidebar)
├─ app/api/[...path]/route.ts        proxy FastAPI (SSE ok)
├─ app/{workspace,knowledge,skills,tools,agents,providers,models,
│        settings,security,missions,calendar,notes,inbox,research,
│        cookbook}/page.tsx
├─ components/layout/sidebar.tsx     IconRail + AppSidebar(Chats|Nav)+UserBar
├─ components/shared/model-selector.tsx   variant full jamais monté
├─ components/features/assistant/    top-bar · input · chat · hooks(use-chats, use-active-model)
├─ components/features/providers/    models·providers workspace + hooks
├─ components/features/settings/     settings-workspace (~10 sections)
├─ lib/api/*                         clients fins (source de vérité contrats)
└─ store/{ui.store, chat-sidebar.store}.ts
```

*Fin de l'audit — document de cartographie, aucune modification fonctionnelle réalisée à ce stade.*








