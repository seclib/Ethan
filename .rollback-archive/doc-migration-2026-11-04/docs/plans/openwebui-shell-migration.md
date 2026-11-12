# ETHAN WebUI — Migration du shell vers Open WebUI

> **Portée** : refonte visuelle du shell frontend (tokens CSS, sidebar, header, composer).
> **Aucune modification** backend / API / stores / hooks / logique métier — les services ETHAN existants sont réutilisés tels quels.

---

## Objectif

Transformer la perception du WebUI : d'un dashboard « ETHAN historique » vers **« un Open WebUI personnalisé pour ETHAN »**.

- **Référence** : `examples/open-webui` (checkout réel — nota bene : le dossier est `open-webui`, avec tiret, *pas* `openwebui`).
- **Identité ETHAN conservée** : logo `LogoSquare`, nom ETHAN, accent rouge (`--accent`), terminologie (Agents, Missions, Skills, Cookbook…), 4 groupes de navigation (`build`/`operate`/`configure`/`admin`).

---

## Ce qui a changé (fichiers)

### 1. `src/app/globals.css` (+~1,9 Ko)

| Élément | Avant | Après (Open WebUI) |
|---|---|---|
| Fond sidebar | `--panel` (identique au main) | **`--sidebar-bg` distinct** : light `#f9f9f9` (main `#fff` pur), dark `rgb(18 18 20)` (main `#17171b`) |
| Bordure sidebar | `1px solid var(--border)` | `0.5px` + `--sidebar-border` quasi invisible (light `0/5%`, dark `255/6%`) |
| Largeur | 220 px fixe | **`var(--sidebar-width, 260px)`** + `transition width .25s` ; `.sidebar-collapsed` = 60 px |
| Header sidebar | bordure basse | sans bordure, padding 10/12/4 |
| New Chat | bouton accent plein (rail) | **`.sidebar-new-chat`** pleine largeur, bordé, radius 12, label + `SquarePen` (OWUI *PencilSquare*) |
| Recherche | absente | **`.sidebar-search`** ouvrant la palette Ctrl+K via `openCommandPalette()` du `ui.store` existant |
| Rail replié | tailwind inline h-9/rounded-lg | **`.sidebar-collapsed-btn`** : ghost 36px, radius 12 (OWUI *rounded-xl hover:bg-gray-100/850*), état `.active` accent-soft |
| Items (list/nav) | padding 7px, radius 8 | min-height **32px** (OWUI `#sidebar-chat-item`), radius 10 |
| Avatar user | carré 8px | **rond 50%** 28px (OWUI `rounded-full`) |
| Composer | radius 20px | **radius 24px** + `:focus-within` bordure accent mixée |
| Modales | radius 10px | radius **16px** |
| App-header crumb | uppercase 12px letter-spacé | 13px neutre, sans uppercase (fin du look dashboard) |

> Signatures visuelles Open WebUI obtenues : **deux plans de fond** (sidebar vs zone principale), bordures hairline, items 32px arrondis, New Chat bordé prominent, barre de recherche placeholder, composer flottant arrondi.

### 2. `src/components/layout/sidebar.tsx`

- Imports : `useUIStore` (palette), `SquarePen`, `PanelLeftClose` ; retrait `Menu`.
- Handlers centralisés : `handleNewChat` (réutilise `chatState.onNewChat`, sinon `/`), `openCommandPalette`.
- **Mode étendu** : header `[LogoSquare ETHAN] … [PanelLeftClose]` → bloc `.sidebar-actions` (New Chat + Rechercher) → `ChatSection` (conversations, inchangé) → `NavigationSection` (4 groupes collapsibles, inchangé) → `UserBar`.
- **Mode replié (60px)** : logo (toggle) en tête → New Chat (`SquarePen`) → Recherche → rail d'icônes `NAV_SECTIONS` (tooltips natifs conservés) → `UserBar` compacte.

### 3. Non touché (volontaire)

- `layout.tsx`, `app-header.tsx`, `page.tsx`, `assistant-*`, stores, hooks, API : héritent automatiquement des nouveaux tokens via les classes partagées.
- Logique métier : aucune. AGENTS.md respecté (présentation uniquement).

---

## Mapping Open WebUI ↔ ETHAN

| Open WebUI | ETHAN |
|---|---|
| `Sidebar.svelte` (`bg-gray-50/70 dark:bg-gray-950/70`, `--sidebar-width` 220–480) | `.sidebar` (`--sidebar-bg`, `--sidebar-width` 260) |
| Bouton `New Chat` (PencilSquare, bordé) | `.sidebar-new-chat` (SquarePen, bordé) |
| `SearchModal` / bouton Search | `.sidebar-search` → `GlobalCommandPalette` (Ctrl+K) |
| `ChatItem` 32px hover gray-100/850 | `.list-item` / `.sidebar-nav-item` 32px `fg/8%` |
| Rail replié icônes `size-9 rounded-xl` | `.sidebar-collapsed-btn` 36px radius 12 |
| `UserMenu` avatar rond | `.user-bar-avatar` rond |
| Composer `MessageInput` rounded-[24px] | `.chat-input-bar` radius 24 + focus accent |
| Body `#fff` / dark `#171717` | `--bg` `#fff` / `#17171b` (accent rouge ETHAN conservé) |

---

## Validation exécutée

| Contrôle | Commande | Résultat |
|---|---|---|
| TypeScript | `npx tsc --noEmit` | ✅ exit 0 |
| ESLint | `npx next lint` | ✅ No warnings/errors |
| Jest | `CI=1 npm test -- --watchAll=false` | ✅ 6 suites / 12 tests PASS |
| Build production | `npx next build` | voir §Build |
| Routes | curl ×18 sur :3001 | ✅ login/register 200, protégées 307→/login |
| SSR DOM | grep HTML `/workspace` | ✅ `sidebar-new-chat`×1, `sidebar-search`×1, «Nouveau chat»×2, «Rechercher…»×1, `Ctrl K`×1 |
| Thème | `--sidebar-bg`/`--sidebar-border` définis pour `dark` **et** `light` (hc/oled héritent) | ✅ |
| Responsive | `<768px` → repli automatique (conservé), rail 60px | ✅ |

## Build

`npx next build` — ✅ terminé sans erreur (0 error) : toutes les 17 routes compilées, `First Load JS shared` 102 kB, middleware 34,2 kB. Le CSS (Tailwind/PostCSS) compile sans avertissement — preuve indirecte de validité des nouveaux tokens.

Après le build, le serveur de dev a été relancé sur 3001 (`./ethan webui`) : `/login` 200, 18 routes re-vérifiées, sonde `/workspace` (cookie) 200 avec les classes OWUI dans le SSR.

---

## Dette / suite possible

- Redimensionnement draggable de la sidebar (OWUI 220–480px) — non implémenté.
- Sidebar mobile en overlay avec backdrop (OWUI `bg-black/60`) — actuellement rail 60px conservé sur mobile.
- Restyler page par page les listes de cards (Agents/Models/Knowledge) vers des « workspace lists » OWUI (tokens prêts, shell aligné).

*Document de conception — migration shell Open WebUI, frontend uniquement.*
