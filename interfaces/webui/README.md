# ETHAN WebUI — Interface de Pilotage Cognitif

> **Cockpit de contrôle pour assistant IA autonome**
> Inspiré de Raycast, VS Code, Grafana, Linear, et Home Assistant

---

## 🚀 Démarrage Rapide

```bash
# Installation des dépendances
cd interfaces/webui
npm install

# Développement
npm run dev

# Build production
npm run build

# Tests E2E
npm run test:e2e
```

Ouvrir [http://localhost:3000](http://localhost:3000)

---

## 📁 Architecture

```
interfaces/webui/
├── src/
│   ├── app/                      # Pages (App Router)
│   │   ├── (dashboard)/          # Dashboard V2 avec sidebar
│   │   │   ├── page.tsx         # Dashboard home (KPI + Charts + Event Stream)
│   │   │   ├── agents/page.tsx
│   │   │   ├── missions/page.tsx
│   │   │   ├── goals/page.tsx
│   │   │   ├── flux/page.tsx
│   │   │   ├── memory/facts/page.tsx
│   │   │   ├── skills/lab/page.tsx
│   │   │   └── settings/page.tsx
│   │   ├── (auth)/               # Pages d'authentification
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   └── layout.tsx            # Root layout
│   │
│   ├── components/
│   │   ├── ui/                   # Composants atomiques (shadcn-style)
│   │   │   ├── command-palette.tsx  # ⭐ Ctrl+K recherche globale
│   │   │   ├── inspector.tsx        # ⭐ Panel détails (Ctrl+J)
│   │   │   ├── badge.tsx
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── input.tsx
│   │   │   ├── textarea.tsx
│   │   │   ├── skeleton.tsx        # Loading states
│   │   │   └── toast.tsx
│   │   │
│   │   ├── layouts/              # Layouts
│   │   │   ├── sidebar.tsx       # Navigation principale
│   │   │   └── topbar.tsx        # Header avec command palette
│   │   │
│   │   ├── features/             # Features métier
│   │   │   └── missions/
│   │   │       └── mission-creator-dialog.tsx  # Formulaire création mission
│   │   │
│   │   └── widgets/              # Widgets dashboard
│   │       ├── kpi-card.tsx      # ⭐ KPI avec sparklines
│   │       └── event-stream.tsx  # ⭐ Flux d'événements temps réel
│   │
│   ├── hooks/                    # Custom hooks
│   │   ├── use-websocket.ts      # ⭐ WebSocket avec reconnection
│   │   ├── use-flux.ts           # Events temps réel
│   │   ├── use-agents.ts
│   │   ├── use-goals.ts
│   │   ├── use-missions.ts
│   │   ├── use-memory.ts
│   │   └── use-skills.ts
│   │
│   ├── stores/                   # State management (Zustand)
│   │   ├── ui.store.ts           # UI state (sidebar, inspector, theme)
│   │   ├── auth.store.ts
│   │   ├── agents.store.ts
│   │   ├── goals.store.ts
│   │   ├── missions.store.ts
│   │   ├── flux.store.ts
│   │   └── memory.store.ts
│   │
│   ├── services/                 # API clients
│   │   ├── api-client.ts
│   │   ├── agents.service.ts
│   │   ├── missions.service.ts
│   │   ├── goals.service.ts
│   │   ├── flux.service.ts
│   │   └── memory.service.ts
│   │
│   ├── types/                    # TypeScript definitions
│   │   └── index.ts              # Agent, Goal, Mission, Fact, Skill, FluxEvent
│   │
│   ├── i18n/                     # Internationalisation
│   │   └── index.ts              # FR/EN (120+ clés)
│   │
│   └── lib/
│       └── utils.ts              # Utility functions
│
├── tests/
│   ├── e2e/
│   │   ├── dashboard-v2.spec.ts  # 10 tests Playwright
│   │   ├── app.spec.ts
│   │   └── chat.spec.ts
│   └── unit/
│       └── hooks.test.ts
│
├── WEBUI_ROADMAP.md              # ⭐ Document de référence
├── package.json
└── next.config.ts
```

---

## ✨ Fonctionnalités Implémentées

### 🎯 Composants Signature

#### 1. Command Palette (`Ctrl+K`)
- Recherche globale (pages, agents, missions, goals)
- Actions rapides (toggle sidebar, toggle inspector)
- Historique des commandes (10 dernières)
- Navigation au clavier (↑↓ + Enter + Esc)

#### 2. Inspector Panel (`Ctrl+J`)
- Panel rétractable à droite (w-80)
- Détails contextuels (clic droit sur agent/goal/mission)
- Métadonnées + actions rapides
- Animation slide-in (300ms)

#### 3. KPI Cards avec Sparklines
- Mini graphiques SVG
- Indicateurs de tendance (↑ ↓ →)
- Tooltips au survol
- Clic → navigation

#### 4. Event Stream Widget
- Flux temps réel avec WebSocket
- Filtres par type + recherche
- Pause/Reprise
- Export JSON
- Color coding par severity

### 🔌 WebSocket Temps Réel

**Hook générique** : `useWebSocket`
- Connexion/déconnexion
- Reconnexion automatique (exponential backoff)
- Gestion des erreurs
- États de connexion

**Intégré dans** : `useFlux`
- Buffer de 100 événements
- Fallback sur polling API
- États de connexion

### 📝 Formulaires Avancés

**Mission Creator Dialog**
- Création de mission avec étapes
- Ajout/suppression dynamique de steps
- Validation des champs
- Formulaire réutilisable (Input, Textarea)

### 🎨 Animations & Polish

**Skeleton Loaders**
- `Skeleton` (base)
- `SkeletonText` (lignes de texte)
- `SkeletonCard` (cards)
- `SkeletonTable` (tableaux)

### 🌍 Internationalisation

**i18n FR/EN**
- 120+ clés de traduction
- Utilisation : `import { t } from "@/i18n"`
- Support de 2 locales (fr, en)

### 🔐 Authentification

**Pages Auth**
- `/login` — Connexion
- `/register` — Inscription
- Layout dédié `(auth)`

---

## 🎨 Design System

### Couleurs ETHAN

```
ETHAN Blue      #3b82f6  — Primary, brand, actions
ETHAN Cyan      #06b6d4  — Information, data
ETHAN Green     #10b981  — Success, running, active
ETHAN Yellow    #f59e0b  — Warning, pending, attention
ETHAN Red       #ef4444  — Error, failed, critical
ETHAN Purple    #8b5cf6  — Thinking, reasoning, meta
ETHAN Dim       #64748b  — Secondary text, metadata
```

### Typographie

- **UI** : Inter
- **Code** : JetBrains Mono
- **Sizes** : 12px (small), 14px (body), 16px (h3), 20px (h2), 24px (h1)

### Composants UI

- **Base** : shadcn/ui + Tailwind CSS 4
- **State** : Zustand (global) + TanStack Query (server)
- **Charts** : Recharts
- **Animations** : CSS transitions (Framer Motion ready)

---

## 📊 Routes Disponibles

| Route | Page | Layout |
|-------|------|--------|
| `/` | Dashboard (SPA legacy) | Sidebar legacy |
| `/login` | Login | `(auth)` |
| `/register` | Register | `(auth)` |
| `/agents` | Agents V2 | Sidebar V2 |
| `/missions` | Missions V2 | Sidebar V2 |
| `/goals` | Goals V2 | Sidebar V2 |
| `/flux` | Event Flux V2 | Sidebar V2 |
| `/memory/facts` | Memory Facts V2 | Sidebar V2 |
| `/skills/lab` | Skills Lab V2 | Sidebar V2 |
| `/settings` | Settings V2 | Sidebar V2 |

---

## 🧪 Tests

### E2E (Playwright)

```bash
# Lancer les tests E2E
npm run test:e2e

# Interface UI
npm run test:e2e:ui
```

**Tests existants** :
- `tests/e2e/dashboard-v2.spec.ts` — 10 tests (navigation, sidebar, loading, error, empty states)

### Unit (Jest)

```bash
# Lancer les tests unitaires
npm run test
```

---

## 🔧 Scripts Disponibles

```json
{
  "dev": "next dev",
  "build": "next build",
  "start": "next start",
  "lint": "next lint",
  "test": "jest",
  "test:watch": "jest --watch",
  "test:e2e": "playwright test",
  "test:e2e:ui": "playwright test --ui",
  "test:all": "npm run test && npm run test:e2e",
  "typecheck": "tsc --noEmit",
  "validate": "npm run typecheck && npm run lint && npm run test"
}
```

---

## 📦 Stack Technique

| Couche | Technologie | Version |
|--------|-------------|---------|
| **Framework** | Next.js | 15.5.20 |
| **UI** | React | 19.0.0 |
| **Language** | TypeScript | 5.7.0 |
| **Styling** | Tailwind CSS | 4.0.0 |
| **State** | Zustand + TanStack Query | 5.0.0 + 5.60.0 |
| **Charts** | Recharts | 2.15.4 |
| **Tests E2E** | Playwright | 1.61.1 |
| **Tests Unit** | Jest | 30.4.2 |
| **i18n** | Custom (FR/EN) | — |

---

## 🎯 Prochaines Étapes

### Action 7 : Animations & Polish (7-9h)
- [ ] Transitions de page (Framer Motion)
- [ ] Micro-interactions (hover, click)
- [ ] Skeleton loaders sur toutes les listes
- [ ] Toast notifications animées
- [ ] Respect `prefers-reduced-motion`

### Action 8 : Tests & Qualité (13-18h)
- [ ] Tests unitaires des hooks (Jest)
- [ ] Tests E2E Playwright (auth, navigation, création)
- [ ] CI/CD GitHub Actions
- [ ] Lighthouse CI

### Action 9 : Docker & Déploiement (7-8h)
- [ ] Dockerfile multi-stage
- [ ] Docker Compose (webui + kernel + db)
- [ ] Scripts de déploiement automatisé
- [ ] Rollback
- [ ] Healthcheck post-deploy

---

## 📖 Documentation

- **WEBUI_ROADMAP.md** — Document de référence complet
  - Vision produit
  - Actions immédiates
  - Phases de développement
  - Recommandations
  - Points de décision
  - Checklist de validation
  - Métriques de succès

---

## 🤝 Contribution

Voir `WEBUI_ROADMAP.md` pour les guidelines de contribution.

---

## 📄 License

MIT

---

**Dernière mise à jour** : 2026-07-08
**Version** : 0.1.0
**Status** : ✅ 6/9 actions complétées (67%)