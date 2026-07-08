# ETHAN WebUI — Roadmap & Code de Conduite

> **Document de référence** pour le développement du WebUI ETHAN.
> Ce fichier est la source de vérité pour les priorités, décisions et actions.

---

## Table des Matières

1. [Vision Produit](#vision-produit)
2. [Actions Immédiates](#actions-immédiates)
3. [Questions à l'Utilisateur](#questions-à-lutilisateur)
4. [Phases de Développement](#phases-de-développement)
5. [Recommandations](#recommandations)
6. [Points de Décision](#points-de-décision)
7. [Checklist de Validation](#checklist-de-validation)

---

## Vision Produit

### Philosophie

**ETHAN n'est pas un chatbot. C'est un système cognitif autonome.**

Le WebUI doit refléter cette philosophie :
- **Transparence cognitive** : l'utilisateur voit *ce que l'IA pense*, pas juste *ce qu'elle dit*
- **Pilotage, pas conversation** : interface de contrôle comme un cockpit d'avion
- **Temps réel permanent** : flux d'événements, états des modules, métriques live
- **Confiance par l'observabilité** : chaque action est tracée, vérifiable, explicable
- **Puissance accessible** : experts ont des raccourcis, débutants ont des guides

### Analogie

> Si ChatGPT est un assistant personnel, ETHAN est un **centre de mission spatial** — il planifie, exécute, vérifie, apprend.

### Identité Visuelle

```
◆  ETHAN  ◇  Cognitive Runtime

◆ = Diamond (brand marker)
◇ = Lozenge (separator)
```

**Palette** :
- ETHAN Blue `#3b82f6` — Primary, brand, actions
- ETHAN Cyan `#06b6d4` — Information, data
- ETHAN Green `#10b981` — Success, running, active
- ETHAN Yellow `#f59e0b` — Warning, pending, attention
- ETHAN Red `#ef4444` — Error, failed, critical
- ETHAN Purple `#8b5cf6` — Thinking, reasoning, meta
- ETHAN Dim `#64748b` — Secondary text, metadata
- ETHAN White `#f8fafc` — Primary text
- ETHAN Dark `#0f172a` — Background (dark mode)

**Typographie** :
- Font: Inter (UI) + JetBrains Mono (code)
- Sizes: 12px (small), 14px (body), 16px (h3), 20px (h2), 24px (h1)
- Weights: 400 (normal), 500 (medium), 600 (semibold), 700 (bold)

---

## Actions Immédiates

### Action 1 : Créer la Command Palette
**Priorité** : 🔴 HAUTE
**Effort** : 3-4h
**Fichier** : `components/ui/command-palette.tsx`
**Inspiration** : Raycast, VS Code

**Fonctionnalités** :
- [ ] Recherche globale (pages, agents, missions, goals)
- [ ] Actions rapides (créer mission, nouveau goal, toggle sidebar)
- [ ] Navigation instantanée
- [ ] Historique des commandes
- [ ] Raccourci `Ctrl+K`

**Critères d'acceptation** :
- `Ctrl+K` ouvre la palette en < 100ms
- Recherche fuzzy sur tous les éléments navigables
- Affichage des 10 dernières commandes
- Navigation au clavier (↑↓ + Enter)

---

### Action 2 : Créer l'Inspector Panel
**Priorité** : 🔴 HAUTE
**Effort** : 4-5h
**Fichier** : `components/layouts/inspector.tsx`
**Inspiration** : VS Code

**Fonctionnalités** :
- [ ] Panel rétractable à droite (toggle `Ctrl+J`)
- [ ] Affiche détails contextuels (clic droit sur agent/mission/goal)
- [ ] Métadonnées, actions rapides, historique
- [ ] Responsive (masqué sur mobile)
- [ ] Largeur configurable (300-500px)

**Critères d'acceptation** :
- Clic droit sur un élément → ouvre l'inspector
- Inspector affiche les détails de l'élément
- Actions rapides fonctionnelles (edit, delete, etc.)
- Animation slide-in fluide (300ms)

---

### Action 3 : Améliorer le Event Stream Widget
**Priorité** : 🔴 HAUTE
**Effort** : 3-4h
**Fichier** : `components/widgets/event-stream.tsx`
**Inspiration** : Grafana Loki, Home Assistant logs

**Fonctionnalités** :
- [ ] Flux temps réel avec WebSocket
- [ ] Filtres par type, module, priorité
- [ ] Pause/Reprise du flux
- [ ] Export JSON
- [ ] Color coding par severity

**Critères d'acceptation** :
- Affichage des événements en temps réel (< 500ms latency)
- Filtres fonctionnels (par type, module)
- Pause/Reprise sans perte de données
- Export JSON des événements filtrés

---

### Action 4 : Améliorer les KPI Cards
**Priorité** : 🟡 MOYENNE
**Effort** : 2h
**Fichier** : `components/widgets/kpi-card.tsx`
**Inspiration** : Grafana

**Fonctionnalités** :
- [ ] Sparklines (mini graphiques)
- [ ] Tooltips détaillés
- [ ] Liens vers les pages concernées
- [ ] Indicateurs de tendance (↑ ↓ →)

**Critères d'acceptation** :
- Affichage d'un sparkline sur chaque KPI
- Tooltip au survol avec détails
- Click sur KPI → navigation vers la page concernée

---

### Action 5 : Connecter WebSocket Temps Réel
**Priorité** : 🔴 HAUTE
**Effort** : 6-9h
**Fichiers** : `providers/websocket-provider.tsx`, `hooks/use-flux.ts`

**Fonctionnalités** :
- [ ] Connexion auto au kernel WebSocket
- [ ] Reconnection exponentielle
- [ ] Heartbeat / ping-pong
- [ ] Gestion des erreurs réseau
- [ ] Subscription aux événements kernel
- [ ] Buffer d'événements (last 100)
- [ ] Filtrage par type
- [ ] Callbacks onEvent

**Critères d'acceptation** :
- Connexion WebSocket établie en < 1s
- Reconnexion automatique après coupure (max 3 tentatives)
- Affichage des événements en temps réel dans le dashboard
- Pas de perte d'événements pendant la reconnexion

---

### Action 6 : Créer les Formulaires Avancés
**Priorité** : 🟡 MOYENNE
**Effort** : 9-12h
**Fichiers** :
- `components/features/mission/mission-creator.tsx`
- `components/features/goal/goal-creator.tsx`
- `components/features/agents/agent-editor.tsx`

**Fonctionnalités** :
- [ ] Dialogue création mission (avec étapes)
- [ ] Formulaire création goal (avec tâches)
- [ ] Édition inline des agents
- [ ] Validation budgétaire avant exécution
- [ ] Drag & drop pour réorganiser les steps

**Critères d'acceptation** :
- Création de mission en 3 étapes max
- Validation des champs obligatoires
- Preview avant soumission
- Feedback utilisateur (toast notifications)

---

### Action 7 : Ajouter les Animations & Polish
**Priorité** : 🟡 MOYENNE
**Effort** : 7-9h
**Fichiers** : divers composants

**Fonctionnalités** :
- [ ] Transitions de page (Framer Motion)
- [ ] Micro-interactions (hover, click)
- [ ] Skeleton loaders
- [ ] Toast notifications animées
- [ ] Respect `prefers-reduced-motion`

**Critères d'acceptation** :
- Transitions fluides (200ms)
- Animations respectent `prefers-reduced-motion`
- Skeleton loaders sur toutes les listes
- Toasts avec animation slide-in

---

### Action 8 : Tests & Qualité
**Priorité** : 🟡 MOYENNE
**Effort** : 13-18h
**Fichiers** : `tests/unit/*.test.ts`, `tests/e2e/*.spec.ts`

**Fonctionnalités** :
- [ ] Tests unitaires des hooks (Jest)
- [ ] Tests E2E Playwright (auth, navigation, création)
- [ ] CI/CD GitHub Actions
- [ ] Lighthouse CI

**Critères d'acceptation** :
- 80% de couverture de tests (hooks + components)
- CI/CD fonctionnelle (lint + test + build sur chaque PR)
- Lighthouse score > 90

---

### Action 9 : Docker & Déploiement
**Priorité** : 🟢 BASSE
**Effort** : 7-8h
**Fichiers** : `Dockerfile`, `docker-compose.yml`, `deploy/`

**Fonctionnalités** :
- [ ] Dockerfile multi-stage
- [ ] Docker Compose (webui + kernel + db)
- [ ] Scripts de déploiement automatisé
- [ ] Rollback
- [ ] Healthcheck post-deploy

**Critères d'acceptation** :
- Image Docker < 200MB
- Déploiement en 1 commande : `docker compose up`
- Healthcheck fonctionnel
- Rollback en < 30s

---

## Questions à l'Utilisateur

### Question 1 : Priorités
**Question** : Les phases 2 et 3 (composants signature + WebSocket) sont-elles bien les priorités ?

**Impact** : Détermine l'ordre d'implémentation des 6 prochaines semaines.

**Recommandation** : Oui, commencer par les composants signature (Command Palette, Inspector) car ce sont les éléments les plus visibles et les plus différenciants.

---

### Question 2 : Design
**Question** : Faut-il créer un mockup Figma avant de coder les composants ?

**Impact** : Gain de temps sur le design, mais ajoute une étape de validation.

**Recommandation** : Oui, créer un mockup Figma basique du dashboard et de la Command Palette pour valider le design avec l'équipe avant de coder.

---

### Question 3 : WebSocket
**Question** : Le kernel a-t-il déjà un endpoint WebSocket, ou faut-il l'implémenter côté backend ?

**Impact** : Si le kernel n'a pas de WebSocket, il faut l'implémenter en Go avant de pouvoir connecter le frontend.

**Recommandation** : Vérifier l'existant côté kernel (`core/bus/`, `core/events/`). Si pas de WebSocket, implémenter un endpoint simple en Go avec NATS JetStream.

---

### Question 4 : Tests
**Question** : Voulez-vous que je commence immédiatement les tests E2E, ou d'abord les composants visuels ?

**Impact** : Les tests E2E prennent du temps mais sécurisent le code. Les composants visuels sont plus visibles mais moins critiques.

**Recommandation** : Commencer par les composants visuels (Phase 2) pour avoir quelque chose de visible rapidement, puis ajouter les tests E2E en parallèle.

---

### Question 5 : Docker
**Question** : Faut-il inclure le kernel Go dans le Docker Compose, ou déployer le webui séparément ?

**Impact** : Si le kernel est inclus, le déploiement est plus simple mais moins flexible. Si séparé, plus de flexibilité mais plus de complexité.

**Recommandation** : Inclure le kernel dans le Docker Compose pour simplifier le déploiement en dev/prod. Permettre un déploiement séparé en production si besoin.

---

## Phases de Développement

### Phase 1 : Fondations ✅ COMPLÉTÉE

**Statut** : Terminé
**Durée** : ~40h
**Livrable** : WebUI fonctionnelle avec navigation, auth, dashboard avec graphiques Recharts.

**Réalisations** :
- [x] Next.js 15 + React 19 + TypeScript 5
- [x] Architecture App Router avec route groups `(dashboard)` et `(auth)`
- [x] Stores Zustand (8 stores)
- [x] Services API (api-client + 5 services)
- [x] Hooks métier (6 hooks)
- [x] Composants UI de base (shadcn-style)
- [x] Layouts (Sidebar + Topbar + Auth layout)
- [x] i18n FR/EN (120+ clés)
- [x] Tests E2E Playwright (10 tests)
- [x] Build réussi (14 pages, 0 erreur)

---

### Phase 2 : Composants Signature 🔴 HAUTE PRIORITÉ

**Statut** : À commencer
**Durée** : 12-15h
**Dépendances** : Aucune

**Objectif** : Créer les composants qui font l'identité ETHAN.

**Livrables** :
- [ ] Command Palette (`Ctrl+K`)
- [ ] Inspector Panel (`Ctrl+J`)
- [ ] Event Stream Widget
- [ ] KPI Cards améliorées

**Critères de succès** :
- Command Palette : recherche globale en < 100ms
- Inspector : affichage détails contextuels en < 200ms
- Event Stream : affichage temps réel < 500ms latency
- KPI Cards : sparklines fonctionnels

---

### Phase 3 : WebSocket Temps Réel 🔴 HAUTE PRIORITÉ

**Statut** : En attente de Phase 2
**Durée** : 6-9h
**Dépendances** : Phase 2 (Event Stream Widget)

**Objectif** : Remplacer le polling par du vrai temps réel.

**Livrables** :
- [ ] WebSocket Provider (connexion, reconnection, heartbeat)
- [ ] useFlux Hook refactorisé (WebSocket)
- [ ] Event Stream dans Dashboard (live)
- [ ] Gestion des erreurs réseau

**Critères de succès** :
- Connexion WebSocket en < 1s
- Reconnexion automatique (max 3 tentatives)
- Pas de perte d'événements pendant reconnexion
- Affichage live dans dashboard

---

### Phase 4 : Formulaires Avancés 🟡 MOYENNE PRIORITÉ

**Statut** : En attente de Phase 3
**Durée** : 9-12h
**Dépendances** : Phase 3

**Objectif** : Permettre la création/édition d'entités via des dialogues intuitifs.

**Livrables** :
- [ ] Mission Creator Dialog
- [ ] Goal Creator Dialog
- [ ] Agent Editor Dialog
- [ ] Validation budgétaire

**Critères de succès** :
- Création de mission en 3 étapes max
- Validation des champs obligatoires
- Preview avant soumission
- Feedback utilisateur (toast notifications)

---

### Phase 5 : Animations & Polish 🟡 MOYENNE PRIORITÉ

**Statut** : En attente de Phase 4
**Durée** : 7-9h
**Dépendances** : Phase 4

**Objectif** : Rendre l'interface fluide et agréable.

**Livrables** :
- [ ] Transitions de page (Framer Motion)
- [ ] Micro-interactions (hover, click)
- [ ] Skeleton loaders
- [ ] Toast notifications animées

**Critères de succès** :
- Transitions fluides (200ms)
- Animations respectent `prefers-reduced-motion`
- Skeleton loaders sur toutes les listes
- Toasts avec animation slide-in

---

### Phase 6 : Tests & Qualité 🟡 MOYENNE PRIORITÉ

**Statut** : En attente de Phase 5
**Durée** : 13-18h
**Dépendances** : Phase 5

**Objectif** : Atteindre 80% de couverture de tests.

**Livrables** :
- [ ] Tests unitaires des hooks (Jest)
- [ ] Tests E2E Playwright (auth, navigation, création)
- [ ] CI/CD GitHub Actions
- [ ] Lighthouse CI

**Critères de succès** :
- 80% de couverture de tests
- CI/CD fonctionnelle
- Lighthouse score > 90

---

### Phase 7 : Docker & Déploiement 🟢 BASSE PRIORITÉ

**Statut** : En attente de Phase 6
**Durée** : 7-8h
**Dépendances** : Phase 6

**Objectif** : Faciliter le déploiement en production.

**Livrables** :
- [ ] Dockerfile multi-stage
- [ ] Docker Compose (webui + kernel + db)
- [ ] Scripts de déploiement automatisé
- [ ] Rollback
- [ ] Healthcheck post-deploy

**Critères de succès** :
- Image Docker < 200MB
- Déploiement en 1 commande
- Healthcheck fonctionnel
- Rollback en < 30s

---

## Recommandations

### Recommandation 1 : next-intl vs i18n custom

**Décision** : Garder le i18n custom pour l'instant.

**Justification** :
- Fonctionne bien (120+ clés FR/EN)
- Pas de dépendance supplémentaire
- Pas de besoin de pluralisation complexe
- Pas de besoin de locales dynamiques

**Condition de changement** : Migrer vers `next-intl` seulement si :
- Pluralisation complexe nécessaire
- Extraction automatique des clés nécessaire
- Support de plus de 2 locales

---

### Recommandation 2 : WebSocket vs SSE

**Décision** : WebSocket pour le flux d'événements, SSE pour les métriques.

**Justification** :
- WebSocket : bidirectionnel, basse latence, idéal pour event flux
- SSE : unidirectionnel, plus simple, idéal pour métriques (KPI, stats)

**Implémentation** :
- WebSocket : `wss://kernel:8080/events` (event flux)
- SSE : `https://kernel:8080/metrics` (KPI, stats)

---

### Recommandation 3 : Docker vs bare metal

**Décision** : Docker Compose pour dev/prod.

**Justification** :
- Déploiement du stack complet en 1 commande
- Isolation des services
- Facile à reproduire en dev
- Facile à scaler en prod

**Structure** :
```yaml
services:
  webui:
    build: ./interfaces/webui
    ports:
      - "3000:3000"
    depends_on:
      - kernel
      - redis
      - postgres

  kernel:
    build: ./core
    ports:
      - "8080:8080"
    depends_on:
      - redis
      - postgres
      - nats

  redis:
    image: redis:7-alpine

  postgres:
    image: postgres:16-alpine

  nats:
    image: nats:2-alpine
```

---

### Recommandation 4 : Architecture des Composants

**Décision** : Structure modulaire avec séparation UI / Features / Widgets.

**Justification** :
- Réutilisabilité des composants UI
- Isolation des features (mission, goal, agent)
- Widgets indépendants pour le dashboard
- Facile à tester et maintenir

**Structure** :
```
components/
├── ui/                    # Composants atomiques (shadcn-style)
│   ├── button.tsx
│   ├── card.tsx
│   ├── dialog.tsx
│   ├── command-palette.tsx  # Signature ETHAN
│   └── ...
├── layouts/               # Layouts (sidebar, topbar, inspector)
│   ├── sidebar.tsx
│   ├── topbar.tsx
│   └── inspector.tsx       # Signature ETHAN
├── features/              # Features métier
│   ├── mission/
│   ├── goal/
│   ├── agent/
│   └── ...
└── widgets/               # Widgets dashboard
    ├── kpi-card.tsx
    ├── event-stream.tsx   # Signature ETHAN
    └── ...
```

---

### Recommandation 5 : State Management

**Décision** : Zustand pour global state, TanStack Query pour server state.

**Justification** :
- Zustand : simple, léger, pas de boilerplate
- TanStack Query : caching, background refetch, optimistic updates
- Séparation claire entre UI state et data state

**Usage** :
- Zustand : sidebar, theme, auth, inspector
- TanStack Query : agents, goals, missions, memory, skills, flux

---

## Points de Décision

### Décision 1 : next-intl vs i18n custom

**Décision** : Garder le i18n custom.

**Raison** : Fonctionne bien, pas de dépendance supplémentaire, pas de besoin de fonctionnalités avancées.

**Condition de changement** : Migrer vers `next-intl` seulement si besoin de pluralisation complexe, extraction automatique des clés, ou support de plus de 2 locales.

---

### Décision 2 : WebSocket vs SSE

**Décision** : WebSocket pour event flux, SSE pour métriques.

**Raison** : WebSocket bidirectionnel pour temps réel, SSE unidirectionnel pour métriques simples.

---

### Décision 3 : Docker vs bare metal

**Décision** : Docker Compose pour dev/prod.

**Raison** : Déploiement simple, isolation, reproductibilité.

---

### Décision 4 : Architecture des composants

**Décision** : Structure modulaire (ui / layouts / features / widgets).

**Raison** : Réutilisabilité, isolation, testabilité.

---

### Décision 5 : State management

**Décision** : Zustand + TanStack Query.

**Raison** : Simplicité, performance, séparation des concerns.

---

## Checklist de Validation

### Avant de commencer chaque phase

- [ ] Lire la documentation de la phase
- [ ] Vérifier les dépendances
- [ ] Créer les tests d'acceptation
- [ ] Valider avec l'équipe

### Après chaque phase

- [ ] Tests passent (unit + E2E)
- [ ] Build réussi (0 erreur)
- [ ] Lighthouse score > 90
- [ ] Documentation à jour
- [ ] Code review effectué
- [ ] Déployé en staging

### Avant le déploiement en production

- [ ] Toutes les phases complétées
- [ ] Tests E2E passent (100%)
- [ ] Lighthouse score > 90
- [ ] Performance : First Load JS < 150KB
- [ ] Accessibilité : WCAG 2.1 AA
- [ ] Sécurité : audit des dépendances
- [ ] Documentation complète
- [ ] Rollback testé

---

## Métriques de Succès

| Métrique | Target | Mesure |
|----------|--------|--------|
| **Performance** | First Load JS < 150KB | Lighthouse |
| **Accessibilité** | WCAG 2.1 AA | Lighthouse + axe-core |
| **Tests** | 80% coverage | Jest + Playwright |
| **Build** | < 10s | `npm run build` |
| **Lighthouse** | > 90 | Performance, A11y, Best Practices |
| **Browser support** | Chrome, Firefox, Safari, Edge | Playwright |
| **Uptime** | 99.9% | Monitoring |
| **Error rate** | < 0.1% | Sentry / LogRocket |

---

## Glossaire

| Terme | Définition |
|-------|------------|
| **KPI** | Key Performance Indicator (indicateur clé de performance) |
| **WebSocket** | Protocole de communication bidirectionnel temps réel |
| **SSE** | Server-Sent Events (événements serveur → client) |
| **RSC** | React Server Components |
| **SSR** | Server-Side Rendering |
| **SSG** | Static Site Generation |
| **CVA** | Class Variance Authority (pour variants de composants) |
| **Zustand** | Bibliothèque de state management React |
| **TanStack Query** | Bibliothèque de gestion de state serveur (anciennement React Query) |
| **Recharts** | Bibliothèque de graphiques React |
| **Framer Motion** | Bibliothèque d'animations React |
| **Playwright** | Framework de tests E2E |
| **Jest** | Framework de tests unitaires |

---

## Ressources

### Documentation
- [Next.js 15](https://nextjs.org/docs)
- [React 19](https://react.dev)
- [Tailwind CSS 4](https://tailwindcss.com/docs)
- [Zustand](https://docs.pmnd.rs/zustand)
- [TanStack Query](https://tanstack.com/query/latest/docs/framework/react/overview)
- [Recharts](https://recharts.org)
- [Framer Motion](https://www.framer.com/motion)
- [Playwright](https://playwright.dev)
- [shadcn/ui](https://ui.shadcn.com)

### Inspirations
- [Raycast](https://raycast.com) — Command palette
- [VS Code](https://code.visualstudio.com) — Inspector panel
- [Grafana](https://grafana.com) — Dashboards, KPIs
- [Linear](https://linear.app) — Mission tracking
- [Notion](https://notion.so) — Goal tree
- [Obsidian](https://obsidian.md) — Knowledge graph
- [Home Assistant](https://home-assistant.io) — Event stream
- [Portainer](https://portainer.io) — System management

---

## Historique des Modifications

| Date | Version | Auteur | Description |
|------|---------|--------|-------------|
| 2026-07-08 | 1.0.0 | Claude | Création initiale du roadmap |

---

## Contact

Pour toute question sur ce roadmap :
- **GitHub** : [seclib/Ethan](https://github.com/seclib/Ethan)
- **Issues** : [GitHub Issues](https://github.com/seclib/Ethan/issues)

---

**Dernière mise à jour** : 2026-07-08
**Prochaine révision** : 2026-07-15 (après Phase 2)