# Stratégie de Maintenance — Fork Open-WebUI → ETHAN WebUI

**Date** : 11/08/2026  
**Statut** : Stratégie — document de référence  
**Basé sur** : OPENWEBUI_FORK_FEASIBILITY.md, ETHAN_WEBUI_UX_ANALYSIS.md, OPENWEBUI_TO_ETHAN_API_MIGRATION.md, ETHAN_WEBUI_V2_ARCHITECTURE.md

---

## Objectif

Transformer Open-WebUI en ETHAN WebUI **sans perdre la capacité de suivre upstream**.

ETHAN WebUI v2 reprend les **patterns UX et composants UI** d'Open-WebUI (chat, éditeur, terminal, thèmes, i18n), mais **remplace entièrement le backend** par ETHAN Core/API. La WebUI devient un **client léger** qui communique uniquement via l'API ETHAN.

---

## 1. Organisation Git

### 1.1 Remotes

| Remote | URL | Rôle |
|--------|-----|------|
| `origin` | `git@github.com:seclib/Ethan.git` | Dépôt principal ETHAN |
| `upstream` | `git@github.com:owui/ETHAN-WebUI.git` | Fork Open-WebUI (source des patterns UX) |
| `owui-upstream` | `https://github.com/open-webui/open-webui.git` | Upstream Open-WebUI original |

### 1.2 Structure du dépôt

```
Ethan/
├── interfaces/webui/          # ETHAN WebUI (fork Open-WebUI)
│   ├── src/
│   │   ├── app/               # Next.js App Router
│   │   ├── components/        # Composants UI (inspirés d'Open-WebUI)
│   │   ├── core/              # Stores, API client, providers
│   │   ├── features/          # Features par domaine ETHAN
│   │   ├── lib/               # Utils, constants, types
│   │   ├── styles/            # CSS, thèmes
│   │   └── types/             # Types TypeScript
│   ├── package.json           # Next.js 15 + React 19
│   ├── tailwind.config.js     # Tailwind CSS 3
│   └── ...
├── core/                      # ETHAN Core (source de vérité)
│   ├── state/                 # Stores (chats, files, channels, notes)
│   ├── auth/                  # Auth (users, groups, oauth, ldap, api_keys, scim)
│   ├── llm/                   # Providers (tts, images)
│   ├── scheduler/             # Automations, calendar
│   ├── tools/                 # Servers, functions
│   ├── learning/              # Evaluations
│   ├── metrics/               # Analytics
│   └── ...
├── interfaces/api/            # API Gateway (FastAPI)
│   ├── routers/               # Routers (message, state, providers, config, domains, v1)
│   └── ...
├── docs/
│   ├── audit/                 # Audits (OPENWEBUI_FORK_FEASIBILITY.md)
│   ├── design/                # Design (ETHAN_WEBUI_UX_ANALYSIS.md)
│   ├── architecture/          # Architecture (OPENWEBUI_TO_ETHAN_API_MIGRATION.md)
│   ├── plans/                 # Plans (ETHAN_WEBUI_V2_ARCHITECTURE.md)
│   └── development/           # Développement (ETHAN_WEBUI_FORK_STRATEGY.md)
├── tests/
│   ├── core/                  # Tests Core
│   └── webui/                 # Tests WebUI
└── ...
```

---

## 2. Branches

### 2.1 Stratégie de branches

| Branche | Description |
|---------|-------------|
| `main` | Branche principale — code stable et testé |
| `develop` | Branche de développement — intégration continue |
| `feature/webui-v2` | Branche de développement ETHAN WebUI v2 |
| `feature/webui-openwebui-sync` | Branche de synchronisation avec Open-WebUI upstream |
| `release/v2.x.x` | Branches de release |
| `hotfix/*` | Branches de correctifs urgents |

### 2.2 Branches de synchronisation

| Branche | Description |
|---------|-------------|
| `owui/main` | Suivi de `open-webui/open-webui` (branche principale) |
| `owui/develop` | Suivi de `open-webui/open-webui` (branche develop) |
| `owui/frontend` | Suivi de la partie frontend uniquement |

### 2.3 Workflow de synchronisation

```bash
# 1. Fetch upstream Open-WebUI
git fetch owui-upstream main:owui/main

# 2. Créer une branche de sync
git checkout -b feature/webui-openwebui-sync

# 3. Extraire les composants UI d'Open-WebUI
# (scripts de migration Svelte → React)

# 4. Appliquer les changements sur la WebUI ETHAN
git checkout develop
git merge feature/webui-openwebui-sync

# 5. Nettoyer
git branch -d feature/webui-openwebui-sync
```

---

## 3. Gestion des Modifications ETHAN

### 3.1 Principe

**Toute modification ETHAN est documentée et isolée du code Open-WebUI.**

### 3.2 Stratégie de modification

| Type de modification | Stratégie |
|----------------------|-----------|
| **UI/UX** (patterns, thèmes, composants) | Copier depuis Open-WebUI → migrer vers React → adapter au design system ETHAN |
| **Backend** (logique métier) | **Supprimer** — remplacer par ETHAN Core/API |
| **Auth** | **Remplacer** — utiliser core/auth (JWT, OAuth, LDAP, API keys, SCIM) |
| **Providers** | **Remplacer** — utiliser core/llm/provider_manager.py |
| **RAG** | **Remplacer** — utiliser core/rag/ |
| **Mémoire** | **Remplacer** — utiliser core/memory/ |
| **Stockage** | **Remplacer** — utiliser core/state/ |
| **WebSocket** | **Remplacer** — utiliser NATS + socket.io |

### 3.3 Marquage des modifications

Chaque fichier modifié depuis Open-WebUI doit inclure un en-tête :

```typescript
/**
 * ETHAN WebUI v2 — Migrated from Open-WebUI
 * Original: src/lib/components/chat/Chat.svelte
 * Migration: Svelte → React (Next.js 15)
 * ETHAN Core integration: core/state/chats.py, core/llm/provider_manager.py
 * Last sync: 2026-08-11
 */
```

### 3.4 Scripts de migration

```bash
# scripts/migrate-owui-components.sh
# Script automatisé pour extraire et migrer les composants Open-WebUI

# 1. Extraire les composants UI d'Open-WebUI
# 2. Convertir Svelte → React
# 3. Adapter les stores Svelte → Zustand
# 4. Brancher sur l'API ETHAN
# 5. Appliquer le design system ETHAN
```

---

## 4. Documentation

### 4.1 Structure de la documentation

```
docs/
├── audit/                    # Audits d'architecture
│   ├── OPENWEBUI_FORK_FEASIBILITY.md
│   └── ...
├── design/                   # Analyse UX
│   ├── ETHAN_WEBUI_UX_ANALYSIS.md
│   └── ...
├── architecture/             # Architecture
│   ├── OPENWEBUI_TO_ETHAN_API_MIGRATION.md
│   ├── api-core-boundary-refactoring.md
│   └── ...
├── plans/                    # Plans de développement
│   ├── ETHAN_WEBUI_V2_ARCHITECTURE.md
│   └── ...
├── development/              # Stratégie de développement
│   ├── ETHAN_WEBUI_FORK_STRATEGY.md
│   └── ...
├── getting-started/          # Démarrage
├── tutorials/                # Tutoriels
├── user-guide/               # Guide utilisateur
└── ...
```

### 4.2 Documentation par composant

Chaque composant migré depuis Open-WebUI doit inclure :

1. **Source** : fichier Open-WebUI original
2. **Migration** : transformations apportées (Svelte → React, stores, API)
3. **ETHAN Core** : capacités Core utilisées
4. **Tests** : liens vers les tests

---

## 5. Licence

### 5.1 Licence Open-WebUI

Open-WebUI est sous licence **MIT**.

### 5.2 Licence ETHAN

ETHAN est sous licence **MIT** (voir `LICENSE`).

### 5.3 Compatibilité

La licence MIT est compatible — ETHAN peut incorporer du code Open-WebUI sous licence MIT, à condition de **conserver l'attribution**.

### 5.4 Attribution

Toute utilisation de code Open-WebUI doit inclure :

```
This file incorporates components from Open-WebUI (https://github.com/open-webui/open-webui)
Copyright (c) 2024 Open-WebUI

Licensed under the MIT License.
```

---

## 6. Attribution

### 6.1 Attribution dans le code

Chaque fichier migré depuis Open-WebUI doit inclure :

```typescript
// Source: Open-WebUI (https://github.com/open-webui/open-webui)
// Copyright (c) 2024 Open-WebUI
// License: MIT
```

### 6.2 Attribution dans la documentation

Le fichier `docs/development/ETHAN_WEBUI_FORK_STRATEGY.md` (celui-ci) sert d'attribution officielle.

### 6.3 Attribution dans les commits

Les commits qui incorporent du code Open-WebUI doivent inclure :

```
Source: open-webui/open-webui@<commit-hash>
License: MIT
```

---

## 7. Synchronisation Future

### 7.1 Cadence de synchronisation

| Type de changement | Fréquence |
|---------------------|-----------|
| **Security patches** | Immédiate (dès publication upstream) |
| **Bug fixes** | Hebdomadaire |
| **Features UI** | Mensuelle |
| **Features backend** | Non synchronisé (ETHAN Core est la source de vérité) |

### 7.2 Processus de synchronisation

```bash
# 1. Identifier les changements upstream
git fetch owui-upstream main
git diff owui/main..owui-upstream/main --name-only

# 2. Filtrer les changements UI
# (ignorer les changements backend, auth, providers, RAG, mémoire)

# 3. Appliquer les changements UI
# (migrer Svelte → React si nécessaire)

# 4. Tester
npm test
npm run test:e2e

# 5. Commit
git commit -m "chore(webui): sync UI components from Open-WebUI v0.9.2"
```

### 7.3 Outils de synchronisation

- **git-subtree** : pour extraire des sous-répertoires d'Open-WebUI
- **patch** : pour appliquer des correctifs ciblés
- **scripts de migration** : pour automatiser la conversion Svelte → React

### 7.4 Gestion des conflits

| Type de conflit | Stratégie |
|-----------------|-----------|
| **Conflit UI** | Résoudre en faveur d'ETHAN (design system, patterns ETHAN) |
| **Conflit backend** | Ignorer (ETHAN Core est la source de vérité) |
| **Conflit auth** | Ignorer (ETHAN Core/auth est la source de vérité) |
| **Conflit providers** | Ignorer (ETHAN Core/llm est la source de vérité) |

---

## 8. Règles de Contribution

### 8.1 Principes

1. **ETHAN Core est la source de vérité** — aucune logique métier dans la WebUI
2. **La WebUI ne fait que afficher et envoyer des actions** — pas de stockage, pas de logique
3. **Toute modification UI doit être documentée** — source Open-WebUI, migration, ETHAN Core
4. **Toute synchronisation upstream doit être filtrée** — UI only, pas de backend
5. **Les tests sont obligatoires** — unit, e2e, storybook

### 8.2 Processus de contribution

```bash
# 1. Fork du dépôt ETHAN
git clone git@github.com:seclib/Ethan.git
cd Ethan

# 2. Créer une branche feature
git checkout -b feature/webui-<nom>

# 3. Développer
# - UI : inspiré d'Open-WebUI, migré vers React
# - API : branché sur ETHAN Core/API
# - Tests : obligatoires

# 4. Tester
npm test
npm run test:e2e

# 5. Commit (format conventional commits)
git commit -m "feat(webui): add chat streaming with Tiptap editor"

# 6. Push + PR
git push origin feature/webui-<nom>
# Créer une PR sur GitHub
```

### 8.3 Revue de code

- **UI** : vérifier l'inspiration Open-WebUI, la migration React, le design system ETHAN
- **API** : vérifier l'utilisation des capacités ETHAN Core (pas de logique métier)
- **Tests** : vérifier la couverture
- **Documentation** : vérifier l'attribution Open-WebUI

---

## 9. Bonnes Pratiques

### 9.1 Code

- **TypeScript strict** — types complets pour tous les composants
- **Composants réutilisables** — shadcn/ui + composants ETHAN
- **Hooks personnalisés** — logique métier dans les hooks, pas dans les composants
- **Services API centralisés** — un seul point d'accès à l'API ETHAN
- **Stores Zustand** — state client minimal, pas de logique métier

### 9.2 Architecture

- **Séparation UI / Logique** — la WebUI ne gère jamais de logique métier
- **API Gateway** — proxy unique vers ETHAN API
- **WebSocket** — événements temps réel via NATS
- **Cache** — TanStack Query pour le cache serveur, Zustand pour le state client

### 9.3 Tests

- **Unit** : Jest pour les composants et hooks
- **E2E** : Playwright pour les flux utilisateur
- **Storybook** : composants isolés
- **Couverture** : 80% minimum

### 9.4 Performance

- **Code splitting** : lazy loading par page
- **Image optimization** : next/image
- **Bundle analysis** : webpack-bundle-analyzer
- **Caching** : TanStack Query cache + localStorage

### 9.5 Sécurité

- **JWT HttpOnly** : cookie sécurisé
- **CORS** : restrictif (ETHAN_API_URL uniquement)
- **CSP** : Content Security Policy
- **Audit** : dépendances régulièrement mises à jour

---

## 10. Conclusion

ETHAN WebUI v2 est un **fork stratégique** d'Open-WebUI qui :

1. **Garde** les patterns UX et composants UI d'Open-WebUI
2. **Remplace** le backend par ETHAN Core/API
3. **Maintient** la capacité de suivre upstream (UI only)
4. **Respecte** la licence MIT et l'attribution Open-WebUI
5. **Documente** toutes les modifications et synchronisations

La stratégie repose sur :
- Une **organisation Git claire** (remotes, branches, workflow)
- Une **gestion documentée** des modifications ETHAN
- Une **synchronisation filtrée** (UI only, pas de backend)
- Des **règles de contribution** strictes (Core = source de vérité)
- Des **bonnes pratiques** de code, tests et sécurité
