# Implémentation — Refonte Shell WebUI (inspiration Open-WebUI)

> **Date** : 26 août 2026 · **Portée** : shell frontend uniquement (`interfaces/webui/src/components/layout/*`, layout racine, globals.css).
> **Conformité** : aucun changement Core/Runtime/API/modèles de données. Aucune fonctionnalité supprimée. Aucun code Open-WebUI importé.
> **Prérequis** : `Obsidian/Engineering/Audits/ui-openwebui-refactor-audit.md` · `Obsidian/Engineering/Audits/ui-openwebui-target-architecture.md`

## Structure obtenue

```
┌────────────────────────────────────────────────────────────┐
│ AppHeader (44px) : Ethan › {page}      • état WS temps réel│
├──────┬─────────────┬───────────────────────────────────────┤
│ Rail │ AppSidebar  │  Main content (routes existantes)     │
│ ⛭    │ Chat | Nav  │  — top bars métier inchangées         │
│ 🔍   │ sections via│                                       │
│ ＋    │ nav-config  │                                       │
│ ⚙    │ UserBar auth│                                       │
└──────┴─────────────┴───────────────────────────────────────┘
```

- **Rail** (affordances globales) : toggle volet · recherche → palette Ctrl+K (**bouton mort réparé**) · nouveau chat (`/`) · Paramètres.
- **AppSidebar unique** : sur `/` → vue Chats (pont `chat-sidebar.store` intact : épinglés, périodes, rename, pin/delete, ModelSelector compact) ; ailleurs → vue Navigation alimentée par **`nav-config.ts`** (Pilotage / Capacités / Système).
- **AppHeader global** : fil `Ethan › Page courante` calculé depuis `NAV_ITEMS_FLAT` + dot état WebSocket (`useWebSocket`). Masqué sur `/` (le chat garde sa top bar modèle/agent — pas de redondance).
- **UserBar réelle** : initiale + nom issus de `useAuth()` (fini « User » statique), tooltip email.

## Fichiers modifiés (liste exacte)

| Fichier | Type | Contenu |
|---|---|---|
| `interfaces/webui/src/components/layout/nav-config.ts` | créé | Taxinomie de navigation unique (3 sections, 14 routes existantes), export `NAV_SECTIONS`/`NAV_ITEMS_FLAT`. Référencé par AppSidebar et utilisable par la palette. |
| `interfaces/webui/src/components/layout/sidebar.tsx` | modifié | `IconRail` refondu (search→palette) ; `NavigationContent` branché sur `NAV_SECTIONS` (suppression listes en dur divergentes) ; `UserBar` authentifiée ; imports nettoyés. Vue Chats et logique store **inchangées**. |
| `interfaces/webui/src/components/layout/app-header.tsx` | créé | Composant présentation pur : breadcrumb page active + indicateur WS coloré. Aucune logique métier (AGENTS.md). |
| `interfaces/webui/src/app/layout.tsx` | modifié | Montage `<AppHeader />` dans `<main>` avant `AnimatePresence` ; import. Le reste des providers/overlays intacts. |
| `interfaces/webui/src/app/globals.css` | modifié | Bloc `.app-header*` + `.ws-dot/.ws-{status}` (~60 lignes) avec les tokens existants (`--bg`, `--border`, `--fg-3`, `--bg-2`, `--green/--amber/--red`) ; styles rail/sidebar/user-bar réutilisés à l'identique. |

Aucun autre fichier touché : pages, features, hooks, clients API, stores = zéro diff.

## Ce qui a été délibérément conservé

- Pont chat→sidebar (`chat-sidebar.store.ts`) et toutes ses actions.
- `ModelSelector` compact en pied de sidebar chats.
- Auto-repli responsive <768px (comportement mobile).
- Palette Ctrl+K, raccourcis globaux, Inspector, Mission Control, Atmosphere.
- Toutes les top bars métier des workspaces (Providers/Models/Agents…).
- Middleware auth, proxy API, SSE pipeline.

## Vérifications exécutées

1. `npx tsc --noEmit` → **EXIT 0**.
2. `npx next lint` → *No ESLint warnings or errors*.
3. `npm test` (Jest) → **5 suites / 7 tests PASS**.
4. Dev server `localhost:3000` :
   - sans cookie : `/login`,`/register` = 200 ; 16 routes protégées = 307→login ✔ middleware intact ;
   - avec cookie : les **16 routes protégées rendent toutes 200**, aucune erreur compile dans le log ;
   - grep DOM SSR : `.app-header` présent sur `/settings`, absent sur `/` ✔ ;
   - sidebar rendering contient Pilotage/Capacités/Système ✔.

## Suivi (prochaines étapes hors périmètre)

Étape suivante du plan cible : promouvoir `model-selector` variant `full` + `agent-selector-popover`/`use-active-agent` dans le header chat (§3–4 target-architecture), puis route `/c/[id]`.
