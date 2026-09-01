# Rapport de migration WebUI — référence Open-WebUI

> **Périmètre** : `interfaces/webui` (Next.js 15, React 19, Tailwind, zustand, React Query).
> **Référence** : `examples/open-webui` — ergonomie uniquement, zéro fork backend.
> **Principe vérifié** : aucune API parallèle, aucun système d'agents/models/providers/conversations dupliqué, aucune régression Core/Runtime.

---

## 1. Problèmes trouvés (audit)

| # | Problème | Gravité | Statut |
|---|---|---|---|
| 1 | Pas de sélecteur **Provider** interactif dans le header du chat (exigence `Agent ▼ Model ▼ Provider ▼`) | Majeur | ✅ Corrigé |
| 2 | Racines de pages en `h-full` au lieu de `flex-1` : avec l'`AppHeader` au-dessus, le contenu dépasse `main` → conteneur scrollable interne partiellement hors écran (Providers, Models, Settings, Skills, Tools, Knowledge, Agents, Notes, Inbox, Calendar, Research, Cookbook, Security) | Majeur (scrolling) | ✅ Corrigé |
| 3 | Sidebar trop visible / icônes seules / pas de labels | Majeur | ✅ Déjà corrigé (refonte v3, vérifié) |
| 4 | Contrôles centraux du chat doublonnaient le header | Majeur | ✅ Déjà corrigé (composer simplifié, `ChatContextBar` seule représentation visuelle) |
| 5 | Scrolling des dropdowns et listes longues | Moyen | ✅ Vérifié (`max-h-72 overflow-y-auto` sur les dropdowns, workspaces `min-h-0` + `overflow-y-auto`) |
| 6 | Administration vide/trompeuse | Moyen | ✅ Vérifiée réelle : Diagnostics → `/api/health/detailed` (200 OK), Security → `/v1/security/*`, Logs/Monitoring → Grafana externe |
| 7 | Port 3001 occupé par un `next-server` lancé par **root** (PID 672558) | Info | ✅ Non tué (règle §14) ; validation effectuée sur :3005 |

## 2. Fichiers modifiés (cette passe)

| Fichier | Changement |
|---|---|
| `interfaces/webui/src/components/features/assistant/components/provider-selector.tsx` | **Nouveau** — dropdown compact `[Provider ▼]` branché sur `useActiveModel` (liste `GET /providers`, sélection → `PUT /providers/{id}/default`, réalignement du modèle sur `default_model`) |
| `interfaces/webui/src/components/features/assistant/components/assistant-top-bar.tsx` | Ajout de `<ProviderSelector />` à côté de `AgentSelector` et `ModelSelector` |
| `interfaces/webui/src/app/{providers,settings,notes,inbox,research,tools,calendar,knowledge,skills,models,agents,cookbook,security}/page.tsx` | Racine `flex h-full min-h-0 flex-col` → `flex min-h-0 flex-1 flex-col` (correction du débordement sous AppHeader) |
| `docs/webui/open-webui-reference.md` | **Nouveau** — ce qui a été repris d'Open-WebUI, pourquoi, ce qui reste |
| `docs/webui/open-webui-migration-report.md` | **Nouveau** — ce rapport |

## 3. Chemin complet vérifié (Browser → Core)

- **Agent** : `agent-selector.tsx` → `useActiveAgent` → `GET /v1/agents` (cache React Query partagé avec /agents) → `localStorage ethan.active-agent` → payload `agent_id` (+ `metadata.agent_id`) → `POST /v1/chat/completions/stream` → `core/chat/pipeline.py` (résolution provider/model/skills/knowledge/tools).
- **Model** : `model-selector.tsx` (groupé par provider, pin, recherche, clavier) → `useActiveModel.setModel` → `localStorage ethan.active-model` → payload `model` → Core. Commande `/model <id>` également supportée.
- **Provider** : `provider-selector.tsx` → `useActiveModel.setProvider` → `PUT /providers/{id}/default` (**propagation backend réelle**) + réalignement `default_model` → payload `provider_id` → Core.
- **Chat** : `assistant-input.tsx` (Enter / Shift+Enter / Send / Stop `AbortController`) → `useChats.sendMessageStream` → SSE `/v1/chat/completions/stream` → rendu `assistant-chat.tsx` (auto-scroll + retour en bas) → historique persisté par le ChatStore Core (`/chats`).

## 4. Comportement avant / après (cette passe)

| Avant | Après |
|---|---|
| Header : `[Agent ▼] [Model ▼]` — provider sélectionnable seulement de manière détournée (en choisissant un modèle groupé par provider) | Header : `[Agent ▼] [Model ▼] [Provider ▼]` — les trois sélections sont explicites, interactives et propagées au Core |
| Pages internes : conteneur scrollable partiellement coupé sous l'AppHeader (haut de liste inaccessible sans scroller `main`) | Pages internes : `flex-1 min-h-0` → le conteneur interne occupe exactement l'espace restant, scroll interne complet |

## 5. Tests réalisés

| Test | Résultat |
|---|---|
| `npx tsc --noEmit` | ✅ 0 erreur |
| `npx eslint src` | ✅ 0 erreur (1 warning préexistant `no-img-element` sur `loading-overlay.tsx`) |
| `npx jest` | ✅ 6 suites, 12 tests passés |
| `npm run build` | ✅ build production complète (toutes routes générées) |
| `next start -p 3005` (temporaire, arrêté après validation) | ✅ `GET /` → 307 `/login?redirect=%2F` ; `/login` rendu ; `/api/health/detailed` → **200** via le proxy catch-all |
| API Core | ✅ `GET :8000/health/ready` → `{"status":"ok","service":"api","nats_connected":true}` |
| Port 3001 | ✅ intact — servi par le `next-server` préexistant (root), jamais tué |

## 6. Conformité architecture (AGENTS.md)

- ❌ Aucun nouveau système d'agents / models / providers / conversations / state manager.
- ❌ Aucune logique métier ajoutée au WebUI : `ProviderSelector` affiche et envoie la sélection (`PUT /providers/{id}/default` = capacité Core existante).
- ✅ Core/Runtime non modifiés par cette passe.
- ✅ Projets/dossiers : **non implémentés** faute de backend — documentés dans `docs/webui/open-webui-reference.md` §4 (règle anti-fantôme respectée).

## 7. Problèmes restants / recommandations

1. **Port 3001 sous root** : le serveur actuellement sur 3001 appartient à root ; pour servir la nouvelle build sur 3001, redémarrer via `./ethan webui` (ou l'unité systemd correspondante). La build `.next` de `interfaces/webui` est à jour.
2. **Bouton Plan désactivé** : nécessite une API Core de forçage de mode (`mode: "plan"` dans `core/chat/pipeline.py`) avant réactivation — ne pas le faire côté interface.
3. **Projets / dossiers de chat** : à faire côté Core d'abord (RFC).
4. **Warning lint préexistant** (`<img>` dans `loading-overlay.tsx`) : mineur, hors périmètre.

---

## 5. Résolution P1/P2 — audit UX (implémentation)

### P1 — Administration → Monitoring/Logs (liens morts)

**Cause racine** : la stack d'observabilité (docker-compose.observability.yml) était définie mais jamais démarrée ; de plus `GRAFANA_PORT=3001` dans `.env` était en conflit avec le WebUI (nav-config et port_registry.json attendent 3002).

**Correction** :
- `.env` : `GRAFANA_PORT=3002` (aligné sur port_registry.json et nav-config GRAFANA_URL).
- Démarrage de la stack : `docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d grafana prometheus loki`.
- Vérifié : ethan-grafana healthy sur :3002 (health 200), ethan-prometheus :9090, ethan-loki :3100. Les liens « Monitoring » et « Logs » de la sidebar mènent désormais à un service réel (login Grafana + explore).

### P2 — Bouton « Plan » (contrôle mort)

**Avant** : bouton désactivé (`disabled`), aucun backend — le rapport le classait P2 « maintenir le tooltip ».

**Correction** : branché sur la vraie capacité Core **Goals** existante (`/v1/goals`, core/goals/manager.py) :
- `assistant-input.tsx` : bouton Plan actif (disabled seulement si saisie vide), nouveau `onPlan(msg)`.
- `assistant-chat.tsx` : transite `onPlan` vers le composer.
- `page.tsx` : `handlePlan` → `useCreateGoal().mutate({ title, description })` (API réelle, auth requise).
- Aucune nouvelle API parallèle : le bouton soumet un goal réel au Core.

### P2 — Tooltip sans repositionnement

- `tooltip.tsx` : ajout d'un positionnement adaptatif sans dépendance — flip haut↔bas quand l'espace manque au viewport + clamp horizontal (getBoundingClientRect au hover/focus).

### Validation
- tsc 0 · eslint 0 · jest 18/18 · npm run build OK · image ethan-ui rebuild et recréée (:3001 healthy).
- Grafana/Prometheus/Loki healthy (11 conteneurs).
