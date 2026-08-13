# 📋 Rapport Complet — Audit Fonctionnel WebUI Dashboard (PLAN MODE)

## 1. Vue d'Ensemble Exécutive

L'audit révèle **60% des fonctionnalités WebUI sont des placeholders frontend-only**. Le frontend appelle des API endpoints (`/api/v1/agents`, `/api/v1/goals`, `/api/v1/memory`, etc.) qui **n'existent pas** dans le backend FastAPI. L'authentification est cassée : le frontend appelle `/api/v1/auth/login` mais le backend expose `/auth/login`. Le WebUI ne peut pas démarrer via `./ethan webui` car le healthcheck vérifie `/api/v1/version` qui n'existe pas.

---

## 2. Dead Features Report

### Dashboard (`page.tsx`)
| Élément | Action | Backend | Statut |
|---------|--------|---------|--------|
| 4× MetricCard KPI | Hook useAgents/useGoals/useFacts/useFlux | 0 API routes existantes | 🔴 **404 partout** |
| Quick Actions "New Mission" | Aucun onClick | — | 🔴 **Dead button** |
| Quick Actions "Start Agent" | Aucun onClick | — | 🔴 **Dead button** |
| Quick Actions "Search Memory" | Aucun onClick | — | 🔴 **Dead button** |
| Quick Actions "Open Terminal" | Aucun onClick | — | 🔴 **Dead button** |
| Mission Pause/Kill/View | Aucun onClick | — | 🔴 **Dead buttons** |
| EventStream Pause/Resume | Appelle onPause/onResume avec `() => {}` | — | 🟡 **Noop handlers** |

### Assistant (`assistant/page.tsx`)
| Élément | Action | Backend | Statut |
|---------|--------|---------|--------|
| Chat input submit | `apiClient.request("/api/v1/chat")` | Aucun route `/api/v1/chat` | 🔴 **404** |
| Comment code | "Temporary fallback call until real backend is mapped" | — | 🟡 **Consciemment brisé** |

### Agents (`agents/page.tsx`)
| Élément | Action | Backend | Statut |
|---------|--------|---------|--------|
| useAgents hook | `agentsService.getAll()` → `/api/v1/agents` | Aucun route | 🔴 **404** |
| AgentEditorDialog | `createAgent` → `/api/v1/agents` | Aucun route | 🔴 **404** |
| Pause/Play/Kill buttons | Aucun onClick | — | 🔴 **Dead buttons** |
| Refresh button | `refetch()` | — | 🔴 **Dead button** |

### Missions (`missions/page.tsx`)
| Élément | Action | Backend | Statut |
|---------|--------|---------|--------|
| useMissions hook | `missionsService.getAll()` → `/api/v1/missions` | Aucun route | 🔴 **404** |
| Pause/Kill/Play buttons | Aucun onClick | — | 🔴 **Dead buttons** |
| MissionCreatorDialog | `createMission` → `/api/v1/missions` | Aucun route | 🔴 **404** |

### Providers (`providers/page.tsx`)
| Élément | Action | Backend | Statut |
|---------|--------|---------|--------|
| Toute la page | `useState` durci, **aucun hook** | — | 🔴 **Frontend-only** |
| "Configure" button | Aucun onClick | — | 🔴 **Dead button** |
| Status "Connected" | Durci | — | 🔴 **Fake status** |
| `features/providers/hooks/` | N'existe pas | — | 🔴 **Manquant** |
| `features/providers/services/` | N'existe pas | — | 🔴 **Manquant** |

### Settings (`settings/page.tsx`)
| Élément | Action | Backend | Statut |
|---------|--------|---------|--------|
| 4 cards (LLM, Permissions, Budget, System) | Texte descriptif statique, aucune interaction | — | 🔴 **Placeholder pur** |
| `settingsService.get/update` | `/api/v1/settings` | Aucun route | 🔴 **404** |

### Models (`models/page.tsx`)
| Élément | Action | Backend | Statut |
|---------|--------|---------|--------|
| Toute la page | `useState` durci (3 modèles) | — | 🔴 **Frontend-only** |

### Plugins (`plugins/page.tsx`)
| Élément | Action | Backend | Statut |
|---------|--------|---------|--------|
| togglePlugin | State local uniquement | — | 🟡 **No-op persistance** |
| "Install" button | Aucun onClick | — | 🔴 **Dead button** |

### Terminal (`terminal/page.tsx`)
| Élément | Action | Backend | Statut |
|---------|--------|---------|--------|
| Form submit | Mise à jour d'état local (`setHistory`) | Aucune connexion WebSocket | 🔴 **Simulation client uniquement** |

### Logs (`logs/page.tsx`)
| Élément | Action | Backend | Statut |
|---------|--------|---------|--------|
| Toute la page | `DEMO_LOGS` durci | — | 🔴 **Frontend-only** |
| Filtre | Client-side seulement | — | 🟡 **No-op** |

### Planner (`planner/page.tsx`)
| Élément | Action | Backend | Statut |
|---------|--------|---------|--------|
| Pause/Run buttons | Aucun onClick | — | 🔴 **Dead buttons** |
| Tasks | `useState` durci | — | 🔴 **Frontend-only** |

### Memory (`memory/page.tsx`)
| Élément | Action | Backend | Statut |
|---------|--------|---------|--------|
| useFacts hook | `memoryService.getFacts()` → `/api/v1/memory/facts` | Aucun route | 🔴 **404** |
| Search input | Durci, pas de filtration réelle | — | 🟡 **No-op** |
| Export button | Aucun onClick | — | 🔴 **Dead button** |

### Knowledge (`knowledge/page.tsx`)
| Élément | Action | Backend | Statut |
|---------|--------|---------|--------|
| useKnowledge hook | `knowledgeService.getAll()` → `/api/v1/knowledge` | Aucun route | 🔴 **404** |
| Search | Fonctionne côté client uniquement | — | 🟡 **No-op API** |

### Login (`login/page.tsx`)
| Élément | Action | Backend | Statut |
|---------|--------|---------|--------|
| Login form | `fetch("/api/v1/auth/login")` via auth-provider | `/auth/login` (sans /v1) | 🔴 **404 route** |
| StatusPanel | Durci (NETWORK:ONLINE, AI CORE:READY) | — | 🔴 **Fake status** |
| "Forgot credentials" | Aucun onClick | — | 🔴 **Dead button** |

---

## 3. Missing Routes Report

### Frontend → Backend Route Mismatch (via `next.config.js` rewrite `/api/*` → `localhost:8000/*`)

| Frontend calls | Backend has | Statut |
|---------------|-------------|--------|
| `/api/v1/auth/login` | `/auth/login` | 🔴 **Mismatch prefix** |
| `/api/v1/auth/me` | (n/a) | 🔴 **Missing** |
| `/api/v1/auth/logout` | (n/a) | 🔴 **Missing** |
| `/api/v1/auth/refresh` | (n/a) | 🔴 **Missing** |
| `/api/v1/agents` | (n/a) | 🔴 **Missing** |
| `/api/v1/goals` | (n/a) | 🔴 **Missing** |
| `/api/v1/missions` | (n/a) | 🔴 **Missing** |
| `/api/v1/memory/*` | (n/a) | 🔴 **Missing** |
| `/api/v1/skills` | (n/a) | 🔴 **Missing** |
| `/api/v1/knowledge` | (n/a) | 🔴 **Missing** |
| `/api/v1/flux` | (n/a) | 🔴 **Missing** |
| `/api/v1/settings` | (n/a) | 🔴 **Missing** |
| `/api/v1/chat` | (n/a) | 🔴 **Missing** |
| `/api/v1/version` | `/v1/version` in PUBLIC_PATHS mais absent du backend | 🔴 **Missing** |
| `/api/internal/*` | `/internal/*` | 🟡 **Prefix mismatch** |
| `/api/v1/message` | `/v1/message` | 🟡 **Prefix mismatch** |

**Backend routes existantes** (dans `interfaces/api/`):
```
GET  /health            (main.py)
GET  /health/live       (main.py)
GET  /health/ready      (main.py)
GET  /health/detailed   (main.py)
POST /auth/login        (main.py)  ← pas /v1 prefix
GET  /metrics           (main.py)
GET  /v1/health         (message router)
POST /v1/message        (message router)
POST /v1/intent         (message router)
GET  /internal/audit*   (internal router)
GET  /internal/budget*  (internal router)
GET  /internal/facts/*  (internal router)
POST /internal/approval/* (internal router)
POST /internal/skilllab/* (internal router)
```

---

## 4. Provider Configuration Report

### Pourquoi les providers apparaissent comme "Connected" mais ne peuvent pas être configurés

1. **`providers/page.tsx`** utilise `React.useState` avec données durcies :
```tsx
const [providers] = React.useState<Provider[]>([
    { id: "openai", name: "OpenAI", type: "LLM", status: "connected" },
    // ...
]);
```

2. **Aucun hook** : `features/providers/hooks/` — **n'existe pas**
3. **Aucun service** : `features/providers/services/` — **n'existe pas**
4. **Aucun composant** : `features/providers/components/` — **n'existe pas**
5. **"Configure" button** : `<Button>Configure</Button>` — **aucun onClick**
6. **Pas de routes API** pour providers dans le backend
7. **Pas de persistance DB** pour les configurations de providers

### Trace du flux brisé :
```
UI: "Configure" button → (aucun onClick) → [ARRÊT]
```
→ **Étape 1 cassée : le bouton n'appelle même rien**

Même si un onClick était ajouté :
```
UI hook (manquant) → API route (manquante) → Backend handler (manquant) → DB schema (manquant)
```

---

## 5. WebUI Startup Mechanism Report

### Comment `./ethan webui` démarre actuellement :
1. `ethan` → `scripts/cmd-webui.sh`
2. `cmd-webui.sh` source `ethan-lib.sh` (définit `WEBUI_DIR`, `require_node`)
3. Vérifie `node_modules` → `npm install` si absent
4. Vérifie API backend : `curl -sf http://localhost:8000/api/v1/version`
   - **BUG** : `/api/v1/version` n'existe pas sur le backend → retourne 404
   - Le script continue malgré l'échec (le `if` est `if ! curl -sf ...`)
   - Tente de démarrer l'API via `cmd-api.sh` si healthcheck échoue
5. Lance `npx next dev -p "$PORT"` (mode développement)

### Problèmes de startup :
- **Healthcheck cassé** : `cmd-webui.sh` vérifie `/api/v1/version` mais le backend n'a que `/auth/login`, `/v1/health`, `/v1/message`, `/metrics`
- **Mode dev** : `npx next dev` au lieu de `npm run start` — pas de production build
- **Pas de proxy dans Docker** : Le `next.config.js` rewrite `/api/` → `localhost:8000`, mais dans Docker Compose, la UI tourne dans un conteneur séparé. `localhost:8000` ne fonctionne pas cross-containers.
- **Auth cassé** : `auth-provider.tsx` appelle `/api/v1/auth/login` → rewrite → `localhost:8000/v1/auth/login` → **404**

### Que démarre actuellement (Docker Compose) :
- **nats** : port 4222 (bind 127.0.0.1)
- **redis** : port 6379 (bind 127.0.0.1)
- **postgres** : port 5432 (bind 127.0.0.1)
- **api** : port 8000 (bind 127.0.0.1)
- **kernel** : port 8080 (bind 127.0.0.1)
- **modules** : port 8081
- **pg_backup** : service
- **ui** : port 3000 (bind 127.0.0.1) — **mais le proxy `/api/` ne fonctionne pas car `ETHAN_API_URL` n'est pas défini dans docker-compose.yml pour le service `ui`**

### Pas de processus actuellement en cours :
- Pas de PM2
- Pas de processus Next.js en cours d'exécution
- Le service systemd `ethan-core.service` gère le Docker Compose mais n'existe peut-être pas comme service installé

---

## 6. Fix Plan Priorisé

### 🔴 P0 — Corrigé (session ACT précédente)
- [x] Sparkline Memory Facts normalisé (100-320 → 31-100)
- [x] EventStream pause/resume logique inversée corrigée
- [x] Empty state missions ajouté
- [x] Guard division par zéro
- [x] Emojis → lucide-react
- [x] Badge "Live" conditionnel
- [x] border-line-2 uniformisé
- [x] Buttons variants uniformisés
- [x] variant="outlined" redondant supprimé (4 occurrences)
- [x] Separator supprimé
- [x] aria-label ajoutés sur tous les boutons

### 🔴 P0 — À corriger (nécessite ACT MODE)
| Action | Fichiers | Effort |
|--------|----------|--------|
| Corriger le mismatch `/auth/login` vs `/api/v1/auth/login` | `auth.py`, `auth-provider.tsx`, `api-client.ts` | 10 min |
| Corriger `cmd-webui.sh` healthcheck `/api/v1/version` → `/v1/health` | `scripts/cmd-webui.sh` | 5 min |
| Ajouter `ETHAN_API_URL` dans docker-compose.yml pour le service `ui` | `docker-compose.yml` | 2 min |

### 🟡 P1 — Routes API manquantes
| Action | Backend route à ajouter | Frontend appel existant | Effort |
|--------|------------------------|------------------------|--------|
| Agents CRUD | `GET/POST/PUT/DELETE /v1/agents` | `/api/v1/agents` | 4h |
| Goals CRUD | `GET/POST/PUT/DELETE /v1/goals` | `/api/v1/goals` | 4h |
| Missions CRUD | `GET/POST/PUT/DELETE /v1/missions` | `/api/v1/missions` | 6h |
| Memory facts | `GET /v1/memory/facts`, `GET /v1/memory/search` | `/api/v1/memory/*` | 3h |
| Skills CRUD | `GET/POST/PUT/DELETE /v1/skills` | `/api/v1/skills` | 4h |
| Knowledge nodes | `GET /v1/knowledge` | `/api/v1/knowledge` | 3h |
| Flux events | `GET /v1/flux` | `/api/v1/flux` | 3h |
| Settings | `GET/PUT /v1/settings` | `/api/v1/settings` | 3h |
| Chat | `POST /v1/chat` | `/api/v1/chat` | 2h |
| Auth logout/refresh/me | `POST /auth/logout`, `POST /auth/refresh`, `GET /auth/me` | `/api/v1/auth/*` | 2h |

### 🟡 P1 — Provider Configuration
| Action | Fichier | Effort |
|--------|---------|--------|
| Créer `features/providers/hooks/` + `services/` | Nouveau | 3h |
| Ajouter route `/internal/providers/*` au backend | `internal.py` | 2h |
| Ajouter onClick au bouton "Configure" | `providers/page.tsx` | 1h |
| Connecter status réel via API | `providers/page.tsx` | 1h |

### 🟡 P2 — Pages statiques à connecter
| Page | Problème | Effort |
|------|----------|--------|
| Terminal | Simulation client — pas de WebSocket kernel | 4h |
| Plugins | Toggle local — pas de persistance | 2h |
| Logs | Données durcies — utiliser `useFlux` | 1h |
| Planner | Tâches durcies — utiliser `useGoals` | 2h |
| Models | Données durcies — API à créer | 2h |

### 🟢 P3 — Améliorations UX
| Action | Effort |
|--------|--------|
| Ajouter search filtre réel sur Memory page | 1h |
| Ajouter search filtre réel sur Knowledge page | 1h |
| Connecter Export button sur Memory page | 30 min |
| Connecter "Forgot credentials" sur Login | 30 min |

---

## 7. Fichiers clés à examiner pour les corrections

```
interfaces/webui/src/app/(dashboard)/page.tsx         — Dashboard principal
interfaces/webui/src/components/shared/event-stream.tsx — Stream d'événements
interfaces/webui/src/components/layout/sidebar.tsx      — Sidebar (déjà corrigée)
interfaces/webui/src/styles/components.css              — CSS (doublon tooltip supprimé)
interfaces/webui/src/core/api/api-client.ts             — Client API frontend
interfaces/webui/src/next.config.js                     — Proxy rewrite /api/*
interfaces/webui/src/core/providers/auth-provider.tsx   — Auth provider
interfaces/webui/src/app/(dashboard)/providers/page.tsx — Pages providers
interfaces/webui/src/app/(dashboard)/settings/page.tsx  — Pages settings
interfaces/api/main.py                                — Backend API routes
interfaces/api/auth.py                                  — Backend auth
interfaces/api/routers/                                 — Backend routers
docker-compose.yml                                      — Docker services
scripts/cmd-webui.sh                                    — Script webui startup
scripts/ethan-lib.sh                                    — Lib commune
infrastructure/systemd/ethan-core.service               — Service systemd
deploy/Dockerfile.ui                                    — Docker WebUI build
```
</arg_value>
<task_progress>
- [x] Explorer la structure du WebUI et du Dashboard
- [x] Analyser le composant Dashboard (page.tsx) — cartes, widgets, sections, titres, espacements, responsive
- [x] Analyser MetricCard, Card, EventStream, Progress
- [x] Identifier les problèmes de design/UI
- [x] Corriger les bugs UI (P0-P3) — terminé en session ACT précédente
- [x] Auditer toutes les routes frontend → backend
- [x] Identifier toutes les routes manquantes
- [x] Identifier tous les boutons dead (sans onClick)
- [x] Identifier tous les composants frontend-only (durced state)
- [x] Analyser le système de providers
- [x] Analyser le mécanisme de startup WebUI
- [x] Produire le rapport d'audit complet
- [ ] Corriger le mismatch route auth (`/auth/login` vs `/api/v1/auth/login`)
- [ ] Corriger le healthcheck `cmd-webui.sh` (`/api/v1/version` → `/v1/health`)
- [ ] Ajouter `ETHAN_API_URL` dans docker-compose.yml pour service `ui`
- [ ] Implémenter les routes API backend manquantes (agents, goals, missions, memory, skills, knowledge, flux, settings, chat)
- [ ] Créer le système de providers complet (hooks + services + backend routes)
- [ ] Connecter Terminal à WebSocket kernel
- [ ] Connecter Plugins à backend
- [ ] Connecter Logs à useFlux
- [ ] Connecter Planner à useGoals
- [ ] Connecter Models à API
</task_progress>
</plan_mode_respond>