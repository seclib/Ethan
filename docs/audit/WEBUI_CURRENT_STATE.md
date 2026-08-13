# ETHAN WebUI — État Actuel (Audit CTO)

**Date** : 12/08/2026
**Auteur** : CTO / Principal Engineer
**Portée** : Architecture ETHAN, WebUI, Open-WebUI, Core, Runtime, API, documentation
**Méthode** : Inspection du code réel (source de vérité), vérification de chaque document existant

---

## 1. Architecture actuelle

```
                    ETHAN
        ┌────────────┼────────────┐
        │            │            │
   interfaces/   core/       services/
   (WebUI, CLI,  (intelligence)  (NATS, Postgres,
    Desktop,      runtime/        Redis, Traefik,
    Channels,     kernel)         Vault, observabilité)
    Shell, API)
```

### Flux réel des requêtes WebUI

```
Navigateur (Next.js :3000)
   │  fetch("/api/...")  [credentials: include]
   ▼
Route Handler catch-all  src/app/api/[...path]/route.ts
   │  réécriture /api/* → ETHAN_API_URL/* (défaut http://localhost:8000)
   │  cookie HttpOnly "ethan_token" → header "Authorization: Bearer"
   │  gestion Set-Cookie (login/refresh/logout)
   ▼
API Gateway FastAPI  interfaces/api/main.py (:8000)
   │  auth_middleware (JWT), rate_limit (slowapi), CORS
   │  injection des managers Core au startup (lifespan)
   ▼
Routers  /v1, /providers, /config, /chats, /internal, /state, /message
   │  passerelles HTTP → managers Core
   ▼
Core  core/agents, core/missions, core/knowledge, core/rag,
      core/llm (ProviderManager), core/state (ChatStore, FileStore),
      core/auth (UserManager, GroupManager), core/config
```

### Stack WebUI (vérifiée dans package.json)

| Technologie | Version |
|---|---|
| Next.js | 15.4 (App Router, Turbopack) |
| React | 19 |
| TypeScript | 5.4 |
| Tailwind CSS | 3.4 |
| Zustand | 4.5 |
| TanStack Query | 5.101 |
| Framer Motion | 11.15 |
| Storybook | 8.6 |
| Jest + Playwright | 29 / 1.61 |

### Pages réelles (14 pages dashboard + auth)

`agents`, `assistant`, `documents`, `knowledge`, `logs`, `memory`, `missions`, `models`, `planner`, `plugins`, `providers`, `settings`, `terminal`, `tools` + `login`, `register`.

### Features WebUI

`agents`, `assistant`, `flux`, `goals`, `knowledge`, `memory`, `missions`, `plugins`, `providers`, `settings`, `skills`.

---

## 2. État réel de la WebUI

### Points forts (vérifiés dans le code)

- **Architecture propre** : App Router, route groups `(dashboard)`/`(auth)`, séparation `core/` (API client, providers, store) / `features/` / `components/`.
- **Auth sécurisée** : cookie HttpOnly `ethan_token`, middleware Next.js protège les routes, proxy convertit cookie → Bearer. Le bug P0 de stale closure documenté dans `docs/frontend_auth_audit.md` est **corrigé** (login immédiat, overlay cosmétique).
- **Proxy fonctionnel** : le route handler catch-all `/api/[...path]/route.ts` remplace les rewrites (absents de `next.config.js`). Gère les cookies, les headers de sécurité (CSP, X-Frame-Options, etc.).
- **Client API centralisé** : `src/core/api/api-client.ts` avec `credentials: "include"`, gestion 401/204, services métier (auth, agents, goals, memory, rag, skills, flux, settings, providers, chats).
- **Assistant fonctionnel** : page assistant avec chat, sélecteur de modèle (inspiré Open-WebUI : recherche, épinglage localStorage, capabilities), side panel (documents, mémoire, outils, MCP, actions), persistance via `useChats` → `/api/chats`.
- **Sélecteur de modèles** : `useModels` (TanStack Query) + `ModelSelector` (variants full/compact), épinglage localStorage, filtrage par provider.
- **Qualité** : build 22 pages 0 erreur, lint 0, typecheck 0, tests unitaires UI (5 suites, 7 tests), e2e Playwright (login, chat, dashboard).

### Points faibles

- **Doublon `ModelSelector`** : `features/providers/components/model-selector.tsx` (sans variant) et `components/shared/model-selector.tsx` (avec variant full/compact) coexistent.
- **README WebUI obsolète** : référence des chemins qui n'existent plus (`goals/page.tsx`, `flux/page.tsx`, `memory/facts/page.tsx`, `skills/lab/page.tsx`, `components/features/`, `components/widgets/`, `hooks/`).
- **i18n incomplet** : structure prête, traductions à finaliser.
- **Couverture de tests faible** : < 20% (documenté dans TECHNICAL_DEBT).
- **Storybook** : à remettre à niveau pour React 19.

---

## 3. État réel d'Open-WebUI (référence)

### Localisation

`examples/open-webui/` — **non suivi par git** (absent de `git ls-files`). Référence v0.9.1 complète.

### Backend (Python FastAPI + SQLAlchemy)

- **29 routers** : auths, chats, models, ollama, openai, knowledge, memories, files, tools, functions, skills, users, groups, configs, retrieval, terminals, automations, channels, calendar, notes, prompts, tasks, analytics, audio, images, evaluations, pipelines, scim, utils.
- **23 modèles SQLAlchemy** : User, Chat, ChatMessage, Model, Knowledge, Memory, File, Tool, Function, Skill, Group, Config, Prompt, Tag, Folder, Channel, Note, Automation, Calendar, Task, Evaluation, OAuthSession, AccessGrant.
- **Services** : retrieval, socket, storage, tools, utils, internal (db, migrations).

### Frontend (SvelteKit)

- `src/lib/apis/` (clients API), `src/lib/components/`, `src/lib/stores/`, `src/lib/types/`, `src/routes/` (app, auth, error, s, watch).
- i18n, pyodide, workers, thèmes.

### Verdict de l'étude de faisabilité (docs/audit/OPENWEBUI_FORK_FEASIBILITY.md)

Le fork est **techniquement faisable** mais représente un changement architectural majeur (React → SvelteKit, aucun composant réutilisable). Recommandé **uniquement** si l'objectif UX est un "near-clone" d'Open-WebUI.

---

## 4. Différences WebUI ETHAN vs Open-WebUI

| Aspect | WebUI ETHAN (actuelle) | Open-WebUI (référence) |
|---|---|---|
| **Framework** | Next.js 15 / React 19 | SvelteKit / Svelte |
| **Backend** | Aucun (proxy → ETHAN API) | FastAPI intégré (SQLAlchemy) |
| **Source de vérité** | ETHAN Core/Runtime | Backend Open-WebUI (DB locale) |
| **Auth** | Cookie HttpOnly + JWT ETHAN | JWT + OAuth + LDAP + API keys |
| **Chat** | `/api/v1/chat` → ProviderManager | Proxy Ollama/OpenAI intégré |
| **Modèles** | `/api/providers` → ProviderManager | CRUD modèles + accès par groupe |
| **RAG** | `/api/v1/rag` → core/rag | Knowledge + retrieval intégrés |
| **Mémoire** | `/api/v1/memory` → core/memory | Memories utilisateur |
| **Skills/Tools** | `/api/v1/skills` → core/skills | Tools + Functions + Pipelines |
| **Groupes** | `/api/groups` → core/auth/groups | Groupes + permissions |
| **Pipelines/Valves** | ❌ Absent | ✅ Présent |
| **Analytics** | ❌ Non exposé (core/metrics existe) | ✅ Présent |
| **Audio/Images** | ❌ Non exposé (core/llm/tts, images existent) | ✅ Présent |
| **Automatisations** | ❌ Non exposé (core/scheduler existe) | ✅ Présent |
| **Canaux/Notes/Calendrier** | ❌ Non exposé (core/state existe) | ✅ Présent |

---

## 5. Fonctionnalités déjà présentes

### Côté WebUI (interface pure)

- ✅ Login/Register ETHAN (overlay animé, status panel)
- ✅ Dashboard cockpit (KPI, charts, event stream, tasks widget)
- ✅ Assistant chat (messages, side panel documents/mémoire/outils/MCP/actions)
- ✅ Sélecteur de modèles (recherche, épinglage, capabilities)
- ✅ Pages agents, missions, goals, knowledge, memory, documents, models, providers, plugins, settings, logs, planner, terminal, tools
- ✅ Command palette (Ctrl+K), Inspector (Ctrl+J), mission control overlay
- ✅ WebSocket temps réel (heartbeat 30s, backoff exponentiel)
- ✅ Thème unifié, atmosphere (vignette, grain, aurora, spotlight), dark mode
- ✅ i18n structure FR/EN (120+ clés)

### Côté Core/API (capacités ETHAN exposées)

- ✅ Agents : `core/agents/` (AgentManager) → `/v1/agents` (CRUD + execute + executions)
- ✅ Missions : `core/missions/` (MissionManager) → `/v1/missions` (CRUD + steps verify/approve)
- ✅ Knowledge : `core/knowledge/` (KnowledgeManager) → `/v1/knowledge` (CRUD + connections + RAG ingest)
- ✅ RAG : `core/rag/` (RAGPipeline) → `/v1/rag` (documents, retrieve, context)
- ✅ Providers LLM : `core/llm/` (ProviderManager, 8 providers) → `/providers` (CRUD, models, test, default)
- ✅ Chats : `core/state/chats.py` (ChatStore) → `/chats` (CRUD, messages, share)
- ✅ Fichiers : `core/state/files.py` (FileStore) → `/files`
- ✅ Utilisateurs/Groupes : `core/auth/` (UserManager, GroupManager) → `/users`, `/groups`
- ✅ Configuration : `core/config/` (ConfigurationService) → `/config` (CRUD, import/export, validate)
- ✅ Auth : `core/auth/` (RBAC, oauth, ldap, api_keys, scim) + JWT API
- ✅ Audit/Budget/Facts/Approval/SkillLab : `core/audit`, `core/cost`, `core/facts`, `core/approval`, `core/skills/lab` → `/internal/*`

---

## 6. Fonctionnalités manquantes

### Manquantes côté API (logique Core existante non exposée)

| Capacité Core | Module Core | Router API manquant |
|---|---|---|
| Automatisations | `core/scheduler/automations.py` | `/v1/automations` |
| Calendrier | `core/scheduler/calendar.py` | `/v1/calendar` |
| TTS/STT | `core/llm/tts.py` | `/v1/audio` |
| Génération d'images | `core/llm/images.py` | `/v1/images` |
| Évaluations | `core/learning/evaluations.py` | `/v1/evaluations` |
| Analytics | `core/metrics/analytics.py` | `/v1/analytics` |
| Canaux | `core/state/channels.py` | `/v1/channels` |
| Notes | `core/state/notes.py` | `/v1/notes` |
| Prompts | `core/config/` | `/v1/prompts` |
| Tool servers | `core/tools/servers.py` | `/v1/tools` |
| Fonctions/Pipelines | `core/tools/functions.py` | `/v1/functions` |
| SCIM | `core/auth/scim.py` | `/v1/scim` |

### Manquantes côté WebUI (UI)

- ❌ Pipelines / Valves (équivalent Open-WebUI)
- ❌ Pages Automations, Canaux, Notes, Calendrier, Audio, Images, Évaluations, Analytics
- ❌ Traductions i18n complètes
- ❌ Tests e2e étendus, coverage > 80%
- ❌ Storybook à jour React 19

---

## 7. Dette technique

### P0 — Bloquant

- **Aucun** (le login est corrigé, le proxy fonctionne, le build passe)

### P1 — Haute priorité

- **`interfaces/api/routers/v1.py` : logique métier in-memory persistante** — goals, memory/facts, skills, flux, settings, providers, plugins restent dans des stores in-memory (`MemoryStore`, `_default_settings`, `_default_providers`, `_default_plugins`). **Violation directe du principe ETHAN** (la logique métier doit être dans le Core). Perdu au redémarrage.
- **Doublon Core `core/providers/`** : legacy (ReasoningProvider, ProviderRegistry) non importé nulle part — code mort à supprimer ou shim.
- **Doublons planner/goals** : `core/planner/` + `core/modules/planner/` + `core/executive/` (planner), `core/goals/` + `core/planner/goal_manager.py` + `core/executive/goal_manager.py` (goals).
- **Capacités Core non exposées** : automations, analytics, audio, images, évaluations, canaux, notes, prompts, tools, functions, scim (voir section 6).
- **Tests** : coverage < 20%, e2e à étendre.

### P2 — Priorité normale

- **Doublon `ModelSelector`** : `features/providers/components/` vs `components/shared/`.
- **README WebUI obsolète** : chemins erronés.
- **i18n** : traductions manquantes.
- **Types `any` résiduels** dans les hooks features.
- **Storybook** : mise à jour React 19.

### P3 — Basse

- Optimisation bundle (lazy loading, tree-shaking)
- Skeletons par page
- Timeouts API + error boundaries
- SEO (sitemap, OpenGraph, robots)

---

## 8. Incohérences

### Documentation obsolète (ne correspond plus au code)

| Document | Incohérence |
|---|---|
| `docs/frontend_auth_audit.md` | Bugs P0 (stale closure, LoadingOverlay) **corrigés** — le login appelle `login()` immédiatement, l'overlay est cosmétique |
| `docs/audit/WEBUI_IMPLEMENTATION_STATUS.md` | Prétend que le proxy n'est pas implémenté — **faux** : le route handler `/api/[...path]/route.ts` fait le proxy |
| `docs/audit/ETHAN_WEBUI_GAP_ANALYSIS.md` | Prétend que les groupes utilisateurs sont "Missing" — **faux** : `core/auth/groups.py` + `/groups` existent |
| `docs/audit/OPENWEBUI_TO_ETHAN_API_MIGRATION.md` | Prétend que les phases 2-4 sont "implémentées (Core)" mais "non exposées (API)" — partiellement vrai, mais les routers `/chats`, `/files`, `/users`, `/groups` existent dans `domains.py` |
| `interfaces/webui/docs/WEBUI_ROADMAP.md` | Phases 2-7 marquées "À commencer" — **faux** : command palette, inspector, event stream, WebSocket, formulaires, animations sont implémentés (audit final) |
| `interfaces/webui/docs/API_CLIENTS.md` | Décrit 2 clients avec auth Bearer localStorage — **faux** : `lib/api-client.ts` est un ré-export déprécié, auth par cookie HttpOnly |
| `interfaces/webui/docs/FRONTEND_COMPONENTS.md` | Référence `components/dashboard/`, `components/charts/` — **n'existent pas** (les vrais sont `components/shared/metric-card.tsx`, `event-stream.tsx`) |
| `interfaces/webui/README.md` | Référence des pages/chemins obsolètes (`goals/page.tsx`, `flux/page.tsx`, `memory/facts/page.tsx`, `skills/lab/page.tsx`, `components/features/`, `components/widgets/`, `hooks/`) |
| `Audit Architecture — WebUI vs Core Runtime.md` (racine) | Note de travail antérieure : décrit `core/rag`, `core/agents`, `core/missions`, `core/knowledge` comme "manquants" — **tous créés depuis** |
| `Plan de Consolidation Architecture ETHAN.md` (racine) | Note de travail antérieure : le plan a été exécuté (phases 0-3) mais les doublons planner/goals/providers persistent |

### Incohérences de code

- **`core/providers/`** : legacy non importé (code mort) — le plan prévoyait un shim, il n'y en a pas.
- **`core/llm/__init__.py`** : types dupliqués avec `core/llm/types.py` (documenté dans le plan, non vérifié en détail).
- **Doublon `ModelSelector`** : deux implémentations coexistent.
- **`v1.py`** : mélange de passerelles Core (agents, missions, knowledge, rag) et de stores in-memory (goals, memory, skills, flux, settings, providers, plugins).

---

## 9. Risques

### Risque 1 — Violation d'architecture persistante (v1.py in-memory)

**Impact** : Élevé. La logique métier (goals, memory, skills, flux, settings, providers, plugins) vit dans l'interface API, pas dans le Core. Données perdues au redémarrage. Contredit `.clinerules/Principe.md` et `AGENTS.md`.

**Mitigation** : Migrer vers `core/goals`, `core/memory`, `core/skills`, `core/state`, `core/config`, `core/llm`, `plugins/` — comme fait pour agents/missions/knowledge/rag.

### Risque 2 — Doublons Core non résolus (planner, goals, providers)

**Impact** : Moyen. Trois implémentations de planner/goals coexistent. Risque de divergence de comportement et de confusion.

**Mitigation** : Unifier vers `core/planner/` et `core/goals/` (le plan de consolidation le prévoit), supprimer `core/providers/`.

### Risque 3 — Capacités Core non exposées

**Impact** : Moyen. Automations, analytics, audio, images, évaluations, canaux, notes, prompts, tools, functions, scim existent dans le Core mais sont inaccessibles via l'API. La WebUI ne peut pas les afficher.

**Mitigation** : Créer les routers manquants (section 6) — travail purement d'exposition, pas de nouvelle logique.

### Risque 4 — Documentation obsolète

**Impact** : Moyen. 10+ documents décrivent un état antérieur. Risque de mauvaises décisions basées sur des informations fausses (ex : "proxy non implémenté", "groups missing").

**Mitigation** : Mettre à jour ou archiver les documents obsolètes. Ce document (`WEBUI_CURRENT_STATE.md`) devient la référence.

### Risque 5 — Open-WebUI non suivi par git

**Impact** : Faible. `examples/open-webui/` est une référence externe (v0.9.1) non versionnée. Pas de risque de divergence de code, mais la référence peut être perdue.

**Mitigation** : Documenter la version de référence et la source d'acquisition.

### Risque 6 — Tests insuffisants

**Impact** : Moyen. Coverage < 20%, e2e limités. Risque de régression lors des migrations.

**Mitigation** : Étendre les tests (P1 de la dette technique).

---

## 10. Prochaines étapes

### Phase A — Consolider l'architecture (P0/P1)

1. **Migrer la logique in-memory de `v1.py` vers le Core** :
   - Goals → `core/goals/manager.py` (existe déjà)
   - Memory/Facts → `core/memory/` + `core/facts/` (existent déjà)
   - Skills → `core/skills/` (existe déjà)
   - Flux/Events → `core/bus/` + `core/events/` (existent déjà)
   - Settings → `core/config/` (existe déjà)
   - Providers → `core/llm/provider_manager.py` (existe déjà, router `/providers` dédié)
   - Plugins → `plugins/` (existe déjà)
2. **Supprimer `core/providers/`** (legacy non importé) ou créer un shim de compatibilité.
3. **Unifier les doublons planner/goals** vers `core/planner/` et `core/goals/`.

### Phase B — Exposer les capacités Core manquantes (P1)

4. Créer les routers : `/v1/automations`, `/v1/calendar`, `/v1/audio`, `/v1/images`, `/v1/evaluations`, `/v1/analytics`, `/v1/channels`, `/v1/notes`, `/v1/prompts`, `/v1/tools`, `/v1/functions`, `/v1/scim`.
5. Étendre l'API client WebUI (`api-client.ts`) et les features correspondantes.

### Phase C — Aligner la WebUI sur Open-WebUI (UX)

6. **Décision stratégique** : fork Open-WebUI (SvelteKit) vs évolution de la WebUI React actuelle. L'étude de faisabilité recommande le fork **uniquement** si l'objectif est un near-clone. La WebUI actuelle est déjà validée (81/100, production-ready).
7. Si évolution : ajouter les pages manquantes (automations, canaux, notes, etc.) et les composants inspirés d'Open-WebUI (déjà partiellement fait : ModelSelector).
8. Si fork : suivre `docs/development/ETHAN_WEBUI_FORK_STRATEGY.md` et `docs/architecture/OPENWEBUI_TO_ETHAN_API_MIGRATION.md`.

### Phase D — Assainir la documentation (P2)

9. Mettre à jour ou archiver les 10+ documents obsolètes identifiés en section 8.
10. Mettre à jour `interfaces/webui/README.md` avec les chemins réels.
11. Supprimer le doublon `ModelSelector` (garder `components/shared/` avec variants).
12. Finaliser i18n, étendre les tests, mettre à jour Storybook.

### Phase E — Qualité (P3)

13. Optimisation bundle, skeletons, timeouts API, SEO.
14. CI/CD (lint + test + build sur chaque PR), Lighthouse CI.

---

## Annexe — Inventaire des documents vérifiés

| Document | Statut | Verdict |
|---|---|---|
| `docs/architecture/OPENWEBUI_TO_ETHAN_API_MIGRATION.md` | ⚠️ Partiellement à jour | Phases 1-4 Core implémentées ; routers partiellement exposés |
| `docs/audit/OPENWEBUI_FORK_FEASIBILITY.md` | ✅ À jour | Fork faisable, recommandé seulement si near-clone |
| `docs/audit/WEBUI_IMPLEMENTATION_STATUS.md` | ❌ Obsolète | Proxy "not implemented" — faux |
| `docs/audit/ETHAN_WEBUI_GAP_ANALYSIS.md` | ❌ Obsolète | Groups "missing" — faux |
| `docs/audit/WEBUI_PRIORITIES.md` | ⚠️ Partiellement à jour | P0 proxy/auth corrigés |
| `docs/audit/WEBUI_DOCUMENTARY_INVENTORY.md` | ✅ À jour | Inventaire correct |
| `docs/audit/ETHAN_WEBUI_INITIAL_ARCHITECTURE_AUDIT.md` | ⚠️ Partiellement à jour | Stack correcte, proxy via route handler |
| `docs/frontend_auth_audit.md` | ❌ Obsolète | Bugs P0 corrigés |
| `interfaces/webui/docs/ETHAN_WEBUI_AUDIT_FINAL.md` | ✅ À jour | Build 22 pages, 0 erreur |
| `interfaces/webui/docs/ETHAN_WEBUI_MIGRATION_STATUS.md` | ✅ À jour | Origine OpenJarvis, phases 0-3 complétées |
| `interfaces/webui/docs/ETHAN_WEBUI_SCORECARD.md` | ✅ À jour | 81/100, validé production |
| `interfaces/webui/docs/ETHAN_WEBUI_TECHNICAL_DEBT.md` | ✅ À jour | P0 aucun, P1 tests/i18n |
| `interfaces/webui/docs/WEBUI_ROADMAP.md` | ❌ Obsolète | Phases 2-7 "à commencer" — implémentées |
| `interfaces/webui/docs/API_CLIENTS.md` | ❌ Obsolète | 2 clients, localStorage — faux |
| `interfaces/webui/docs/FRONTEND_COMPONENTS.md` | ❌ Obsolète | Chemins dashboard/charts inexistants |
| `interfaces/webui/README.md` | ❌ Obsolète | Chemins de pages erronés |
| `Audit Architecture — WebUI vs Core Runtime.md` (racine) | ❌ Obsolète | Modules "manquants" créés depuis |
| `Plan de Consolidation Architecture ETHAN.md` (racine) | ⚠️ Partiellement à jour | Plan exécuté, doublons persistent |