# Open-WebUI comme référence d'implémentation — WebUI ETHAN

> **Statut** : document de référence — migration UX WebUI ETHAN.
> **Référence analysée** : `examples/open-webui` (frontend SvelteKit + backend FastAPI).
> **Règle cardinale** : Open-WebUI est une référence d'*ergonomie et de structure*, jamais un fork backend. ETHAN conserve son Core, son Runtime, ses providers, agents, tools, MCP, RAG et memory.

---

## 1. Ce qui a été étudié dans Open-WebUI

Analyse des composants réels (pas seulement le CSS) :

| Concept Open-WebUI | Emplacement de référence | Transposition ETHAN |
|---|---|---|
| Sidebar repliable (rail compact → clic → développée) | `src/lib/components/layout/Sidebar.svelte` | `sidebar.tsx` + `ui.store.ts` (`sidebarExpanded`) |
| Navigation conversation-centric (chats épinglés/récents) | `Sidebar.svelte` + routes `(app)` | `chat-sidebar.store.ts` (état publié par la page chat vers le shell) |
| Sélecteur de modèle : recherche, épinglage, groupement par provider | `src/lib/components/chat/ModelSelector/` | `components/shared/model-selector.tsx` (`full`/`compact`) |
| Navigation clavier dropdowns (flèches + Enter + Escape) | `src/lib/components/common/Selector.svelte` | `model-selector.tsx`, `agent-selector.tsx` (`data-arrow-selected`) |
| Header chat avec sélecteurs de premier niveau | `src/lib/components/chat/Chat.svelte` | `assistant-top-bar.tsx` → `AgentSelector` + `ModelSelector` + `ProviderSelector` |
| Composer minimal (textarea + actions essentielles) | `MessageInput.svelte` | `assistant-input.tsx` (Act / Plan / Send uniquement) |
| Auto-resize, Enter = envoyer, Shift+Enter = nouvelle ligne | `MessageInput.svelte` | `assistant-input.tsx` (`handleKeyDown`, `handleInput`) |
| Auto-scroll intelligent + bouton « retour en bas » | `Chat.svelte` | `assistant-chat.tsx` (`autoScrollRef`, `BOTTOM_THRESHOLD`) |
| Settings à sections | Settings d'Open-WebUI | `settings-workspace.tsx` (sections + hash URL `#general`…) |
| Administration réelle | Admin Settings + `/health` | `nav-config.ts` `NAV_SECTIONS_ADMIN` (Diagnostics, Grafana, Security) |
| Message tree (branches, régénération, édition) | backend `chats` Open-WebUI | déjà présent : `core/state/chats.py` + `parent_id`/`children_ids` |
| Streaming SSE avec arrêt (Stop) | `chat/completions` streaming | `use-chats.ts` (`sendMessageStream`, `AbortController`) |

## 2. Ce qui a été repris — et pourquoi

1. **Sidebar unique, repliable, conversation-centric** — la liste de conversations est l'élément central de la navigation ; les entrées techniques vivent en second niveau. ETHAN applique la même hiérarchie : sidebar = Conversations + Assistants + Pilotage + Administration compacte ; Providers/Models/Knowledge/Skills/Tools/MCP passent par Settings et la palette Ctrl+K (`nav-config.ts` v5).
2. **Sélecteurs de premier niveau dans le header du chat** — changer d'agent/modèle/provider ne quitte jamais le chat. Un seul emplacement par sélecteur (anti-doublon) : le composer n'expose ni Agent ni Model ni Provider.
3. **Dropdowns avec recherche + groupement + clavier** — modèles groupés par provider, épinglage (pin), états « indisponible » grisés (pattern `ModelSelector.svelte`).
4. **Composer minimal** — `Act` (mode réel, envoi direct Core), `Plan` (désactivé volontairement : la planification est gérée par le module planner du Core, aucune API « mode » n'existe — cf. `docs/plans/chat-composer-simplification.md`), Send/Stop.
5. **Auto-scroll + Stop réel** — Stop = `AbortController` sur le flux SSE ; le contenu partiel est conservé.
6. **Settings à sections avec hash URL** — navigation directe `/settings#appearance` depuis la sidebar.

## 3. Ce qui a été volontairement conservé d'ETHAN

- **Aucune logique métier dans le WebUI** : toutes les données viennent des APIs Core (`/v1/agents`, `/providers`, `/models`, `/chats`, `/v1/chat/completions/stream`, `/health/detailed`).
- **Thème ETHAN** (variables CSS `--bg`, `--fg`, `--panel`, accent, `globals.css`) — pas de copie des couleurs Open-WebUI.
- **Agents, models, providers du Core** : `useActiveAgent` et `useActiveModel` sont des clients d'API, pas des systèmes parallèles. La sélection de provider est propagée au backend via `PUT /providers/{id}/default`.
- **Chat pipeline Core** (`core/chat/pipeline.py`) : résolution agent → provider/model/skills/knowledge/tools côté Core uniquement ; le payload chat porte `agent_id`, `provider_id`, `model`.
- **ChatContextBar** (exclusivité ETHAN) : affichage du contexte résolu (skills/knowledge/tools/mémoire) — absent d'Open-WebUI, conservé car il répond à « pourquoi ETHAN répond comme ça ? ».

## 4. Ce qui reste à implémenter (backend manquant documenté)

| Fonctionnalité Open-WebUI | État backend ETHAN | Action requise |
|---|---|---|
| Dossiers de conversations (`folders/`) | ❌ aucun module Core | Créer un store Core (`core/state/folders.py` ou champ `folder_id` sur `chats`) avant toute UI |
| Projects (conversations groupées + fichiers projet) | ❌ aucun module Core | Idem — ne pas créer d'UI fantôme (règle anti-fantôme de `nav-config.ts`) |
| Mode « Plan » manuel dans le composer | planner Core automatique, pas d'API de forçage | Exposer un paramètre chat (ex. `mode: "plan"`) dans `core/chat/pipeline.py`, puis réactiver le bouton |
| Partage de conversations | ❌ | Hors périmètre immédiat |
| Réglages par modèle (system prompt par chat) | partiel (agents) | Passer par les agents ETHAN plutôt que dupliquer |

## 5. Ports et exécution

- `./ethan webui` → dev server Next.js sur **:3001** (`scripts/cmd-webui.sh`).
- Attention : le port 3001 peut être occupé par un `next-server` préexistant lancé par un autre utilisateur (root) — ne jamais le tuer brutalement ; valider sur un port temporaire (`npx next start -p 3005`) puis laisser `./ethan webui` gérer 3001.
