# ETHAN WebUI — Plan de Migration Complet v2.0
> **Rôle** : Lead Frontend / UX Architect / Software Architect  
> **Date** : 2026-07-23  
> **Statut** : Analyse terminée — aucun fichier source modifié

---

## ÉTAPE 1 — ANALYSE COMPARATIVE

### Contexte réel

> **Jarvis-OS (`/jarvis-OS/`)** : dossier **entièrement vide** au moment de l'audit.  
> Son héritage est déjà présent dans ETHAN via :
> - `src/styles/jarvis-tokens.css` — palette cyan `#00d4ff`, typographie, radius, shadows
> - `src/styles/_legacy-jarvis.css` — `top-nav`, `rooms-pages` (pills), `rooms-mc`, `rooms-chapter` (archivé, commenté)
> - `src/styles/atmosphere.css` — vignette, grain, aurora, spotlight, mode-glow
> - `src/styles/components.css` — `detail-panel`, `mission-overlay`, `approval-modal`, `kpi-card`, `tasks-widget`

L'interface actuelle **est déjà une fusion** ETHAN + influences Jarvis-OS. La migration n'est pas un remplacement mais une **consolidation et modernisation progressive**.

### Corrections par rapport au plan v1

Le plan v1 (daté du 8 juillet) a été rédigé avant plusieurs implémentations. L'audit réel révèle que **certaines actions sont déjà réalisées** :

| Action v1 | Statut réel | Détails |
|---|---|---|
| B3 — Double client API | ✅ **Résolu** | `lib/api-client.ts` est désormais un simple re-export de `core/api/api-client.ts` (20 lignes, `@deprecated`) |
| B2 — Double ThemeProvider | ✅ **Résolu** | `topbar.tsx` importe `useTheme` depuis `@/core/providers/theme-provider`, pas `next-themes` |
| B4 — Atmosphere non activée | ✅ **Résolu** | `AtmosphereLayer` (`components/layout/atmosphere-layer.tsx`) existe et est monté dans `layout.tsx` |
| 3.1 — Command Palette | ✅ **Résolu** | `GlobalCommandPalette` + `CommandPalette` UI implémentés, intégrés dans `dashboard/layout.tsx` |
| 3.2 — Mission Control | ✅ **Résolu** | `MissionControlOverlay` (`components/layout/mission-control-overlay.tsx`) existe, déclenché via `⌘M` |
| 3.3 — Inspector Panel | ✅ **Résolu** | `GlobalInspector` (`components/layout/global-inspector.tsx`) existe, déclenché via `⌘J` |
| 1.1 — CSS legacy nettoyé | ✅ **Partiellement résolu** | `_legacy-jarvis.css` archivé, commenté dans `globals.css` |
| B5 — WebSocket heartbeat | ⚠️ **Partiellement résolu** | Heartbeat (ping/pong 30s) + exponential backoff implémentés, mais pas de buffer d'événements pendant déconnexion |
| B6 — Framer Motion inutilisé | ❌ **Toujours ouvert** | `framer-motion` dans `dependencies` mais 0 utilisation dans le code |
│   │       ├── documents/     Docs
│   │       ├── planner/       Goals
│   │       ├── missions/      Missions
│   │       ├── tools/         Lab
│   │       ├── plugins/       Plugins
│   │       ├── models/        LLMs
│   │       ├── providers/     API keys
│   │       ├── terminal/      Terminal
│   │       ├── logs/          Flux events
│   │       └── settings/      Config
│   ├── components/
│   │   ├── layout/            sidebar, topbar, command-palette, inspector, shortcuts
│   │   ├── ui/                17 composants atomiques (shadcn-style)
│   │   └── shared/            event-stream, metric-card
│   ├── features/              10 domaines métier
│   ├── core/
│   │   ├── api/               api-client
│   │   ├── providers/         auth, theme, query, websocket
│   │   └── store/             ui.store (Zustand)
│   ├── styles/                8 fichiers CSS (tokens, base, navigation, atmosphere, etc.)
│   ├── types/                 index.ts (372 lignes, types complets)
│   └── lib/                   utils, api-client, logger, env, animations.css
├── Stack: Next.js 15 / React 19 / TypeScript 5 / Tailwind 3
├── State: Zustand + TanStack Query
├── Animations: Framer Motion (installé, peu utilisé)
```

### Stack technique

| Couche | Technologie | Statut |
|--------|-------------|--------|
| Framework | Next.js 15 + App Router | ✅ Moderne |
| UI | React 19 + TypeScript 5 | ✅ Moderne |
| Style | Tailwind 3 + CSS Modules custom | ⚠️ Hybride (incohérent) |
| State | Zustand + TanStack Query | ✅ Solide |
| Animations | Framer Motion (installé) | ❌ Quasi inutilisé |
| Thème | ThemeProvider custom + next-themes | ⚠️ Double système |
| WS | WebSocketProvider custom | ⚠️ Partiel (pas de heartbeat) |
| Tests | Jest + Playwright | ⚠️ Squelette (peu de tests réels) |
| Auth | AuthProvider custom (JWT localStorage) | ⚠️ Non sécurisé prod |

---

## ÉTAPE 2 — MATRICE DE CORRESPONDANCE JARVIS-OS → ETHAN

### Palette & Design Tokens

| Élément Jarvis-OS | Équivalent ETHAN | Statut |
|---|---|---|
| `--j-primary: #00d4ff` (cyan) | `--accent: #60a5fa` (blue) | ⚠️ **Couleur différente** — Jarvis cyan vs ETHAN blue |
| `--j-bg-0: #05070f` (ultra dark) | `--bg-0: #0f172a` (slate-900) | ⚠️ **Plus lumineux** dans ETHAN |
| `--j-font-mono: JetBrains Mono` | `font-mono: JetBrains Mono` | ✅ Identique |
| `--j-font-sans: Inter` | `font-sans: Inter` | ✅ Identique |
| `--j-radius-*` (6/10/16/24px) | Tailwind defaults | ❌ **Non mappé** — Tailwind gère les radius |
| `--j-shadow-lg` (cyan glow) | `accent-line` sur hover | ⚠️ Partiel |
| `--j-border-*` (cyan tinted) | `--line-1/2/3` (white alpha) | ⚠️ **Esthétique différente** |
| Tokens `--j-green: #00ff88` | `--green: #34d399` | ⚠️ Légèrement différent |

**Décision** : Les deux palettes coexistent via `jarvis-tokens.css`. La migration doit **choisir une palette principale** (ETHAN blue ou Jarvis cyan).

---

### Navigation & Layout

| Élément Jarvis-OS | Équivalent ETHAN | Adaptation | Statut |
|---|---|---|---|
| `top-nav` centré (top bar) | `Topbar` (left-aligned, sticky) | Navigation différente | ⚠️ **Incompatible** |
| `rooms-pages` (pills bas de page) | `Sidebar` (colonne gauche) | Paradigme opposé | ❌ **Remplacer ou fusionner** |
| `rooms-mc` (bouton Mission Control bas-gauche) | Command Palette (⌘K) | Même concept | ⚠️ Réutilisable |
| `rooms-chapter` (indicateur section) | Breadcrumbs dans Topbar | Même concept | ✅ Réutilisable |
| Sidebar fixe/collapsible (ETHAN) | N/A (Jarvis = pills) | — | ETHAN-natif |

---

### Composants UI

| Composant Jarvis-OS | Équivalent ETHAN | Statut |
|---|---|---|
| `detail-panel` (slide-in droite) | `GlobalInspector` | ✅ Présent |
| `approval-modal` | `Dialog` (ui/dialog.tsx) | ✅ Présent |
| `mission-overlay` | `MissionCreatorDialog` | ✅ Présent |
| `kpi-card` | `MetricCard` (shared) | ✅ Présent + sparkline |
| `flux-stream` / `flux-row` | `EventStream` (shared) | ✅ Présent |
| `tasks-widget` | Aucun | ❌ **Manquant** |
| Command Palette | `GlobalCommandPalette` + `CommandPalette` UI | ✅ Implémenté |
| `atmo--vignette/grain/aurora` | `atmosphere.css` | ✅ Présent (inutilisé en JSX) |
| `spotlight` | `atmosphere.css` | ✅ Présent (inutilisé en JSX) |
| `mode-glow` | `atmosphere.css` | ✅ Présent (inutilisé en JSX) |

---

### Pages & Fonctionnalités

| Page Jarvis-OS | Page ETHAN | Adaptation | Statut |
|---|---|---|---|
| Dashboard (cockpit) | `(dashboard)/page.tsx` | KPI + EventStream + Missions | ✅ Base solide |
| Chat / Assistant | `assistant/page.tsx` | Version très basique | ⚠️ **À enrichir** |
| Memory graph | `memory/page.tsx` | Liste facts simple | ⚠️ **À moderniser** |
| Mission Control | `missions/page.tsx` | Page missions basique | ⚠️ **À enrichir** |
| Agents | `agents/page.tsx` | Page agents basique | ⚠️ **À enrichir** |
| Terminal | `terminal/page.tsx` | Présent | ⚠️ État inconnu |
| Knowledge | `knowledge/page.tsx` | Présent | ⚠️ État inconnu |
| Settings | `settings/page.tsx` | Présent | ⚠️ État inconnu |

---

### Services & Data Layer

| Couche Jarvis-OS | Couche ETHAN | Statut |
|---|---|---|
| Auth service | `auth-provider.tsx` (JWT localStorage) | ⚠️ Basique, pas httpOnly cookies |
| WebSocket | `websocket-provider.tsx` | ⚠️ Partiel, pas heartbeat |
| API client | `core/api/api-client.ts` + `lib/api-client.ts` | ❌ **Doublon** (2 clients API) |
| Feature services | `features/*/services/*.service.ts` | ✅ Structuré |
| Feature hooks | `features/*/hooks/use-*.ts` | ✅ Structuré |
| State global | `core/store/ui.store.ts` (Zustand) | ✅ Complet |

---

## ÉTAPE 3 — BLOCAGES ACTUELS

### 🔴 Blocages Critiques (empêchent une interface moderne)

#### B1 — Double système de design (Tailwind + CSS custom)
- **Problème** : Tailwind gère les classes utilitaires ET 8 fichiers CSS custom définissent des styles redondants. `components.css` redefine `.animate-fade-in` identique à `animations.css`. `navigation.css` contient des styles (`.top-nav`, `.rooms-pages`) **jamais utilisés dans le JSX actuel** (legacy Jarvis-OS).
- **Impact** : Conflits de specificity, maintenance impossible, bundle CSS gonflé.

#### B2 — Double ThemeProvider
- **Problème** : `core/providers/theme-provider.tsx` (custom, `data-theme` attribute) coexiste avec `next-themes` (importé dans `topbar.tsx` via `useTheme` from `next-themes`). Les deux systèmes se battent pour contrôler le thème.
- **Impact** : Hydration mismatches, comportement imprévisible en SSR.

#### B3 — Double client API
- **Problème** : `src/lib/api-client.ts` (2279 bytes) ET `src/core/api/api-client.ts` (6746 bytes). Deux implémentations différentes pour la même chose.
- **Impact** : Inconsistance dans les features, erreurs silencieuses.

#### B4 — Styles d'atmosphère (vignette, aurora, spotlight) non activés
- **Problème** : `atmosphere.css` est importé mais les classes `.atmo`, `.spotlight`, `.mode-glow` ne sont **jamais rendues dans le JSX** (aucun composant les utilise).
- **Impact** : L'esthétique "Jarvis-OS night" n'apparaît pas — l'interface est plate.

#### B5 — WebSocket sans heartbeat ni exponential backoff
- **Problème** : Reconnexion fixe à 5s/10s. Pas de ping/pong. Pas de gestion des messages perdus pendant reconnexion. En production, connexions zombie.
- **Impact** : Dashboard "live" qui ne l'est pas vraiment.

#### B6 — Framer Motion installé, inutilisé
- **Problème** : `framer-motion` est dans `dependencies` (package.json) mais aucune animation Framer n'est utilisée dans le code. Les transitions sont en CSS pur.
- **Impact** : +50KB bundle pour rien. WEBUI_ROADMAP cite Framer Motion pour "Phase 5" mais la dépendance est déjà payée maintenant.

#### B7 — Pages squelettes (contenu statique/mock)
- **Problème** : `assistant/page.tsx` a des messages hardcodés. Plusieurs pages n'utilisent pas les hooks/services disponibles dans `features/`.
- **Impact** : UI déconnectée du backend réel.

---

### 🟡 Dettes Techniques (dégradent l'expérience)

| Dette | Description | Priorité |
|---|---|---|
| D1 | Auth par JWT en localStorage (XSS vulnérable) | Haute |
| D2 | `Sidebar` collapsible mais default `false` (toujours réduite) | Moyenne |
| D3 | Topbar a deux icônes `Search` (bug ligne 92) | Haute |
| D4 | `useTheme` dans Topbar importe de `next-themes` mais ThemeProvider est custom | Haute |
| D5 | Types `any` dans WebSocketProvider et `page.tsx` (mission casting) | Moyenne |
| D6 | Navigation CSS legacy (`top-nav`, `rooms-*`) orpheline | Basse |
| D7 | `jarvis-tokens.css` défini mais aucune var `--j-*` utilisée dans JSX/Tailwind | Basse |
| D8 | Storybook v7 avec React 19 (incompatibilité connue) | Moyenne |

---

## ÉTAPE 4 — ROADMAP DE MIGRATION

> **Règle d'or** : Ne jamais casser ce qui fonctionne. Migration incrémentale. Chaque étape est réversible.

---

### PHASE 0 — RESTAURATION (Semaine 1)
> **Objectif** : ETHAN doit démarrer proprement, sans erreurs console, sans conflits.

#### 0.1 — Unifier ThemeProvider (Critique)
- **Action** : Supprimer l'import de `next-themes` dans `topbar.tsx`. Utiliser uniquement `useTheme` du `core/providers/theme-provider.tsx` custom.
- **Fichiers** : `topbar.tsx`, `layout.tsx`
- **Effort** : 1h

#### 0.2 — Corriger le bug double icône Search dans Topbar
- **Action** : Remplacer la 2ème icône `Search` (ligne 92 topbar.tsx) par `SlidersHorizontal` pour le toggle Inspector.
- **Fichiers** : `topbar.tsx`
- **Effort** : 15min

#### 0.3 — Fusionner les deux clients API
- **Action** : Faire pointer tous les services vers `core/api/api-client.ts` (le plus complet). Supprimer `lib/api-client.ts` ou le transformer en ré-export.
- **Fichiers** : `lib/api-client.ts`, tous les `features/*/services/`
- **Effort** : 2h

#### 0.4 — Connecter les pages aux features existantes
- **Action** : `assistant/page.tsx` → utiliser les composants de `features/assistant/components/`. Vérifier chaque page vs son feature folder.
- **Fichiers** : Pages dashboard, vérification feature-par-feature
- **Effort** : 4h

**Livrable Phase 0** : ETHAN démarre sans erreur. Toutes les pages affichent des données réelles (ou skeleton si API down).

---

### PHASE 1 — STABILISATION (Semaines 2–3)
> **Objectif** : Architecture solide, WebSocket fiable, styles cohérents.

#### 1.1 — Nettoyer le CSS legacy
- **Action** : Supprimer de `navigation.css` les classes orphelines (`.top-nav`, `.rooms-pages`, `.rooms-mc`, `.rooms-chapter`) qui ne sont pas utilisées dans le JSX. Les archiver dans `styles/_legacy-jarvis.css` (commenté, pour référence).
- **Effort** : 2h

#### 1.2 — Unifier le design system : choisir une seule stratégie CSS
- **Décision à prendre** : Tailwind-first ou CSS custom-first ?
- **Recommandation** : **Tailwind-first** avec CSS custom pour les tokens uniquement.
  - Conserver `tokens.css` (variables CSS custom)
  - Conserver `atmosphere.css` (effets visuels uniques)
  - Migrer `components.css` vers composants Tailwind
  - Supprimer les redondances entre `animations.css` et `components.css`
- **Effort** : 6h

#### 1.3 — WebSocket robuste
- **Action** : Ajouter heartbeat (ping/pong toutes les 30s), exponential backoff (1s → 2s → 4s → max 30s), buffer d'événements pendant déconnexion.
- **Fichiers** : `core/providers/websocket-provider.tsx`
- **Effort** : 4h

#### 1.4 — Supprimer Framer Motion ou l'utiliser
- **Décision** : Si Framer Motion reste dans deps, l'utiliser pour les transitions de page (layout animations). Sinon, le retirer du `package.json` et économiser 50KB.
- **Recommandation** : L'utiliser — wraper `<main>` dans `<AnimatePresence>` avec une transition douce.
- **Effort** : 3h (si utilisé) | 30min (si supprimé)

#### 1.5 — Activer les effets d'atmosphère
- **Action** : Créer un composant `<AtmosphereLayer />` qui rend les `.atmo--vignette`, `.atmo--aurora`, `.spotlight` et `.mode-glow`. L'intégrer dans `layout.tsx`.
- **Effort** : 2h

**Livrable Phase 1** : Interface visuellement cohérente, WebSocket fiable, 0 style orphelin.

---

### PHASE 2 — MODERNISATION (Semaines 4–6)
> **Objectif** : Élever l'expérience visuelle au niveau "cognitive OS cockpit".

#### 2.1 — Enrichir la page Assistant
- Intégrer `features/assistant/components/` complets (AssistantChat, AssistantInput, AssistantMessage, SidePanel avec reasoning/memory/tools/documents)
- Streaming de tokens (SSE ou WS)
- Effort : 8h

#### 2.2 — Dashboard cockpit amélioré
- Activer les sparklines sur MetricCard (données réelles)
- EventStream branché sur WebSocket live
- Ajout d'un graphique de tendance (via recharts — optionnel)
- Effort : 6h

#### 2.3 — Inspector Panel complet
- `GlobalInspector` : afficher les détails d'un agent/mission/goal au clic
- Slide-in animé (CSS existant dans `components.css`)
- Actions rapides : pause, kill, view logs
- Effort : 6h

#### 2.4 — Pages missions/agents enrichies
- Cartes avec status live (polling ou WS)
- Actions inline (start/pause/kill)
- Lien Inspector
- Effort : 8h

#### 2.5 — Tokens Jarvis-OS : décision palette
- **Choix** : Adopter l'accent cyan `#00d4ff` (Jarvis) ou rester sur blue `#60a5fa` (ETHAN) ?
- **Recommandation** : **Garder blue ETHAN** pour l'identité propre. Utiliser cyan uniquement pour les effets glow (aurora, spotlight), jamais comme couleur primaire.
- **Action** : Mettre à jour `jarvis-tokens.css` pour refléter cette décision. Documenter dans `tokens.css`.
- Effort : 2h

**Livrable Phase 2** : Interface "cockpit" fonctionnelle et visuellement impressionnante.

---

### PHASE 3 — INTÉGRATION DES IDÉES JARVIS-OS (Semaines 7–10)
> **Objectif** : Adopter les patterns UX Jarvis-OS qui améliorent ETHAN sans le dénaturer.

#### 3.1 — Navigation hybride (optionnelle)
- **Concept Jarvis** : pills de navigation en bas de page (`rooms-pages`) pour les sous-vues
- **Adaptation ETHAN** : Garder la sidebar. Ajouter des pills internes sur les pages qui ont des sous-onglets (planner: goals/steps, logs: flux/system, tools: lab/installed)
- La classe `.subpages-pills` est déjà dans `components.css` — l'activer
- Effort : 4h par page

#### 3.2 — Mode Mission Control
- **Concept Jarvis** : overlay `mission-overlay` avec grille de cartes de mission
- **Adaptation ETHAN** : Trigger via Command Palette ("Launch Mission Control") ou shortcut `⌘M`
- Styles déjà dans `pages.css` (`.mission-overlay`, `.mission-grid`, `.mission-card`)
- Effort : 6h

#### 3.3 — Ambient atmosphere temps réel
- Aurora qui change de couleur selon le statut kernel (bleu = normal, amber = warning, rouge = error)
- Spotlight qui suit le curseur
- Mode glow animé selon l'activité des agents
- Effort : 8h

#### 3.4 — Sidebar étendue avec preview
- Hover sur item sidebar → preview flottante avec stats rapides
- Inspiration : VS Code sidebar hovers
- Effort : 5h

#### 3.5 — Accessibilité & Performance
- `prefers-reduced-motion` : désactiver toutes les animations
- Lighthouse > 90 sur toutes les pages
- WCAG 2.1 AA sur les contrastes
- First Load JS < 150KB
- Effort : 8h

---

## RÉSUMÉ DES PRIORITÉS

```
PHASE 0 — Restauration    [S1]      ~7h   🔴 URGENT
  ├── Unifier ThemeProvider
  ├── Corriger bug Topbar
  ├── Fusionner clients API
  └── Connecter pages ↔ features

PHASE 1 — Stabilisation   [S2-S3]   ~17h  🔴 HAUTE
  ├── CSS cleanup (legacy Jarvis nav)
  ├── Design system unifié
  ├── WebSocket heartbeat + backoff
  ├── Framer Motion (utiliser ou supprimer)
  └── AtmosphereLayer activé

PHASE 2 — Modernisation   [S4-S6]   ~30h  🟡 MOYENNE
  ├── Assistant enrichi (streaming)
  ├── Dashboard cockpit
  ├── Inspector complet
  ├── Pages missions/agents
  └── Décision palette tokens

PHASE 3 — Jarvis-OS UX    [S7-S10]  ~31h  🟢 PROGRESSIVE
  ├── Pills sous-navigation
  ├── Mission Control overlay
  ├── Atmosphere réactive
  ├── Sidebar enrichie
  └── A11y + Performance
```

---

## RÈGLES DE CONDUITE

1. **Jarvis-OS n'est pas copié** — ses patterns sont adaptés à l'identité ETHAN
2. **Jamais de breaking change** — chaque PR est testée et réversible
3. **Un seul ThemeProvider** — custom, pas next-themes
4. **Un seul client API** — `core/api/api-client.ts`
5. **Tailwind-first** — les styles custom sont réservés aux effets non-réalisables en Tailwind
6. **Atmosphère = opt-in** — `AtmosphereLayer` peut être désactivé via settings
7. **Types stricts** — bannir `any` dans les nouveaux fichiers
8. **Sidebar ETHAN** — ne pas remplacer par les pills Jarvis (paradigmes incompatibles)

---

## MÉTRIQUES DE VALIDATION

| Métrique | Phase 0 | Phase 1 | Phase 2 | Phase 3 |
|---|---|---|---|---|
| Erreurs console | 0 | 0 | 0 | 0 |
| Clients API | 1 | 1 | 1 | 1 |
| ThemeProviders | 1 | 1 | 1 | 1 |
| CSS orphelins | ↓ | 0 | 0 | 0 |
| Framer Motion utilisé | — | ✅ | ✅ | ✅ |
| WebSocket heartbeat | — | ✅ | ✅ | ✅ |
| Atmosphere active | — | ✅ | ✅ | ✅ |
| Lighthouse score | — | — | >85 | >90 |
| First Load JS | — | — | <200KB | <150KB |
