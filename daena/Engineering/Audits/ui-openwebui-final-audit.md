# Audit final — WebUI ETHAN post-refonte (cohérence Open-WebUI)

> **Date** : 27 août 2026 · **Branche** : `main` · **Portée** : interface frontend uniquement.
> **Conformité** : aucun changement Core/Runtime/API/backend pendant cet audit ; diagnostics et recommandations uniquement.
> **Base de vérification** : code `interfaces/webui/src`, `tsc`, `next lint`, Jest, `next build`, SSR des routes.

---

## Synthèse

La WebUI est désormais **cohérente avec la philosophie Open-WebUI tout en restant ETHAN**, et
**fonctionnellement saine** : `tsc` ✅ · `next lint` ✅ · Jest 6 suites / 12 tests ✅ ·
`next build` réussi (toutes routes + middleware) ✅.

Le chat est un véritable « cockpit » : sélecteurs **Agent** + **Model**, barre de **contexte actif**
(chips réels, anti-chips fantômes), **composer** moderne (toolbar caps + stopper), sidebar unique +
**taxinomie unique** `nav-config`. Toutes les pages de configuration existantes restent actives.

Il reste essentiellement de la **dette de cohérence** (palette en dur, doublons Settings↔pages,
CSS mort `.icon-rail`) et quelques **écarts vs structure ADMIN cible**.

---

## 1. Vérifications effectuées

### CHAT
| Point | État |
|---|---|
| Agent visible | ✅ `agent-selector.tsx` monté dans `AssistantTopBar` |
| Model visible | ✅ `ModelSelector` (variant full semi-contrôlable) en header |
| Changement d'agent rapide | ✅ popover + recherche + « Sans agent » + Récents, `use-active-agent` (localStorage) |
| Changement de modèle rapide | ✅ popover + recherche + pins, `PUT /providers/{id}/default` |
| Capabilities compréhensibles | ✅ `chat-context-bar.tsx` : Agent·Model·Outils·Skills·Connais·Mémoire (chips réels) |
| Composer clair | ✅ `assistant-input.tsx` : toolbar 📎 Skills Tools Knowledge Agent + Send/Stop, Enter / Shift+Entrée |
| Streaming / arrêt | ✅ streaming SSE piloté par le parent ; bouton ⊓ stop ; bannière d'erreur |
| Conversations accessibles | ✅ chat-sidebar (chat-sidebar.store) affiche Chats sur `/` |
| Nouveau chat évident | ✅ groupe CONVERSATIONS → New Chat → `/` |

### NAVIGATION

- Sidebar unique **repliable** (`sidebar.tsx`), état persisté (Zustand/localStorage), chiffrement user (auth).
- Taxinomie **unique** `nav-config.ts` (Pilotage / Capacités / Système) consommée par la **AppSidebar** et le **breadcrumb** `app-header.tsx`.
- Toutes les routes listées existent (`agents skills tools providers models knowledge …`) ✅.
- ⚠️ Divergence : `global-command-palette.tsx` recopie des routes en dur (9) au lieu de consommer `NAV_SECTIONS` (14).

### AGENTS — ✅ refonte card-grid
Liste (grille) · recherche · création (`AgentEditorDialog`) · configuration · menu ⋮ (éditer / exécuter / dupliquer / supprimer) · sélection depuis le chat (header + composer).

### MODELS — ✅ refonte card-grid
Liste (grille) · recherche · favoris (localStorage) · badge provider/local · badge **Indisponible** (non-dispo grisé) · sélection depuis le chat.

### CAPABILITIES
- Skills : page `/skills` + menu composer.
- Tools : page `/tools` (builtin + mcp) + menu composer.
- MCP : page `/tools` (serveurs) + section MCP dans `/settings`.
- Knowledge : page `/knowledge` (collections ↔ documents) + chips composer.
- Memory : ⚠️ pas de page dédiée — onglet Mémoire dans `/workspace`. Écart mineur vs cible.

### CONFIGURATION
- Providers : page `/providers` CRUD + test/toggle + popover de modèles.
- Settings : 10 sections **utilisateur/système mélangés** ; plusieurs sections **réimplémentent des pages dédiées** (Models, Providers, Skills, Agents, Tools, MCP, Knowledge).
- **Admin / Diagnostics / Logs / Monitoring** : absents (aucun écran dédié).

### TECHNIQUE
| Contrôle | Résultat |
|---|---|
| `tsc --noEmit` | ✅ exit 0 |
| `next build` | ✅ laiteries écurité des routes + middleware |
| `next lint` | ✅ No ESLint warnings/errors |
| Jest | ✅ 6 suites / 12 tests PASS |
| Routes | ✅ 20+ routes compilent / pre-render |
| API calls | ✅ clients modulaires `lib/api/*` via proxy Next.js, SSE préservé |
| Loading / Error | ✅ skeletons & empty states par page, toasts, bannière chat |
| Responsive | ⚠️ repli sidebar <768px via JS ; design mobile à confirmer sur écran |
| Persistance | ✅ sidebar, active Model/Agent, pinned-models, thème (localStorage) |
| Refresh navigateur | ✅ routes profondes servables |

---

## 2. Problèmes restants

### P1 — Cohérence navigation
1. `global-command-palette.tsx` ne consomme pas `NAV_SECTIONS` : doublons de routes en dur (9), entrées manquantes (calendrier, research…).

### P2 — Doublons Settings ↔ pages dédiées
1. `/settings` 10 sections dont plusieurs ré-implémentent les CRUD des pages dédiées :
   - settings→models ↔ `/models` ; settings→providers ↔ `/providers` ; settings→skills ↔ `/skills`
   - settings→agents ↔ `/agents` ; settings→tools ↔ `/tools` ; settings→mcp ↔ `/tools` MCP; settings→knowledge ↔ `/knowledge`
   → risque de divergence réelle entre deux rendus du même état.
2. CSS mort : blocs `.icon-rail*` encore dans `app/globals.css` (IconRail supprimé, styles de l'ancien rail désormais inutilisés) — `app-header` refait. Supprimable sans risque.

### P3 — Écart structure ADMIN cible
- `ADMIN : System / Diagnostics / Logs / Monitoring` — **absents** ; à définir côté runtime/API puis UI.

---

## 3. Fichiers modifiés / créés lors de la refonte (rappel)

**Nouveaux composants**
- `components/layout/nav-config.ts` (NAV_SECTIONS) ; `components/layout/app-header.tsx` (bandeau + breadcrumb + websocket)
- `components/assistant/agent-selector.tsx` ; `components/assistant/chat-context-bar.tsx` ; `hooks/use-active-agent.ts`
- `lib/accent.ts`, `lib/api/rag.ts`, `tests/unit/assistant/`.

**Modifications principales**
- `app/layout.tsx`, `app/page.tsx`, `app/globals.css`
- `assistant-top-bar.tsx`, `assistant-input.tsx` ; `agents/*/agents-workspace.tsx`, `providers/*/models-workspace.tsx`
- `sidebar.tsx`, `shared/model-selector.tsx` ; `settings/skills/knowledge/*`.

---

## 4. Composants supprimables (audités)

| Composant / classe | État | Action conseillée |
|---|---|---|
| CSS `.icon-rail*` dans `globals.css` (≈l.353+) | orphelin, plus référencé | Supprimer proprement (CSS) |
| Liste de routes en dur dans `global-command-palette.tsx` | duplique `NAV_SECTIONS` | Remplacer par `NAV_ITEMS_FLAT` |
| (Aucun grand composant UI n'est répliqué entre chat/sidebar) | — | Rien à supprimer |

## 5. Composants conservés (atouts)

`AppSidebar`, `AgentSelector`, `ChatContextBar`, `AssistantTopBar`, `AssistantInput` (toolbar), `ModelSelector` semi-contrôlable, `AgentsWorkspace` (grid), `ModelsWorkspace` (grid), `AgentEditorDialog`, `nav-config`, `AppHeader`, `UserBar` (user réel + logout).

## 6. Dette UX restante (priorisée)

1. **(P1)** Harmoniser la palette avec `NAV_SECTIONS`.
2. **(P2)** Recentrer `/settings` sur préférences utilisateur (General/Appearance/Compte/RAG) et renvoyer en liens vers les pages opérationnelles ; préparer `/admin`.
3. **(P3)** Page Memory dédiée (ajoutée à la section Capacités) au lieu d'un onglet dans Workspace.
4. **(P3)** Les écrans Admin/Diagnostics/Logs/Monitoring (feuille de route en fonction de l'API disponible).
5. **(P3)** Options globales : toggle de thème en sidebar, « reset chat », raccourcis.

## 7. Recommandations finales

1. Générer la Navigation de la palette depuis `NAV_SECTIONS` (+ commandes en dur) — impact nul.
2. Purger le CSS `.icon-rail` mort — audit évidence, sans risque.
3. Reorganiser Settings : liens vers pages dédiées (WorkSpaceLink existant), garder General/Apparence/Compte/RAG ; ouvrir une route `/admin` protégée (gated par rôle) pour le système.
4. Exposer Mémoire accessible depuis la section Capacités.
5. Feuille de route Admin/Diagnostics sur la base des endpoints `/v1/settings` + `/flux` (sans contrainte technique bloquante).

## 8. Conformité règle absolue

Aucune modification Core/Runtime/API pendant cet audit — diagnostics chiffrés uniquement. Frontière « interface vs système » (AGENTS.md) respectée : toute capacité (providers, memories, RAG, agents) demeure dans Core/Runtime, la UI (re)présente et contrôle.

*— Fin audit final —*
