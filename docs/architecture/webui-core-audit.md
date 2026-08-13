# ETHAN — Audit WebUI / Core Boundary

**Date** : 2026-03-08  
**Auteur** : WebUI Interface Refactoring Agent  
**Statut** : Audit complet — plan de refactoring  
**Portée** : `interfaces/webui/src/app/(dashboard)/`, `interfaces/webui/src/features/`, `core/`

---

## 1. Résumé Exécutif

L'audit du WebUI couvre **11 pages** du dashboard. Résultat :

- **7 pages** sont des clients API purs ✅
- **4 pages** contiennent de la **logique métier in-memory** ❌

Les 4 pages problématiques utilisent `useState` pour stocker des données qui devraient être gérées par le Core.

---

## 2. Audit par Page

### 2.1 Pages correctes (client API pur) ✅

| Page | Hook/Service | Endpoint API | Core associé |
|---|---|---|---|
| `agents/page.tsx` | `useAgents` → `agentsService` | `/api/v1/agents` | `core/agents/` |
| `documents/page.tsx` | `ragService` | `/api/v1/rag/documents` | `core/rag/` |
| `knowledge/page.tsx` | `useKnowledge` | (via hook) | `core/knowledge/` |
| `missions/page.tsx` | `useMissions` | (via hook) | `core/missions/` |
| `settings/page.tsx` | `apiClient.request` | `/api/v1/settings` | `core/config/` |
| `memory/page.tsx` | `useFacts` | (via hook) | `core/facts/` |
| `tools/page.tsx` | — (navigation) | — | — |

### 2.2 Pages problématiques (logique métier in-memory) ❌

| # | Page | Problème | Core associé |
|---|---|---|---|
| 1 | `models/page.tsx` | Modèles hardcodés dans `useState` | `core/llm/` |
| 2 | `plugins/page.tsx` | Plugins hardcodés dans `useState`, toggle local | `plugins/` |
| 3 | `planner/page.tsx` | Tâches hardcodées dans `useState` | `core/planner/` |
| 4 | `terminal/page.tsx` | Historique hardcodé, commande simulée | `core/tools/` |

---

## 3. Détails des Pages Problématiques

### 3.1 `models/page.tsx` — Modèles hardcodés

**Problème** : Les modèles sont définis en dur dans `useState` :

```typescript
const [models, setModels] = React.useState([
  { id: "gpt4", name: "GPT-4", provider: "OpenAI", status: "active", latency: 1200 },
  { id: "claude3", name: "Claude 3", provider: "Anthropic", status: "active", latency: 800 },
  { id: "llama3", name: "Llama 3", provider: "Meta", status: "inactive", latency: 0 },
]);
```

**Capacité Core** : `core/llm/provider_manager.py` — `ProviderManager.list_models()`

**Solution** :
1. Ajouter `getModels()` à `api-client.ts` → `/api/v1/models`
2. Créer `useModels` hook → `modelsService`
3. Remplacer `useState` par `useQuery`

### 3.2 `plugins/page.tsx` — Plugins hardcodés

**Problème** : Les plugins sont définis en dur dans `useState` et le toggle est local :

```typescript
const [plugins, setPlugins] = React.useState([
  { id: "docker", name: "Docker Builder", version: "1.0.0", enabled: true },
  { id: "k8s", name: "Kubernetes Deploy", version: "0.9.0", enabled: true },
  { id: "web", name: "Web Scraper", version: "2.1.0", enabled: false },
  { id: "slack", name: "Slack Notifier", version: "1.2.0", enabled: false },
]);

const togglePlugin = (id: string) => {
  setPlugins((prev) =>
    prev.map((p) => (p.id === id ? { ...p, enabled: !p.enabled } : p))
  );
};
```

**Capacité Core** : `plugins/manager.py` — `PluginManager`

**Solution** :
1. Ajouter `getPlugins()`, `togglePlugin()` à `api-client.ts` → `/api/v1/plugins`
2. Créer `usePlugins` hook → `pluginsService`
3. Remplacer `useState` par `useQuery` + `useMutation`

### 3.3 `planner/page.tsx` — Tâches hardcodées

**Problème** : Les tâches sont définies en dur dans `useState` :

```typescript
const [tasks] = React.useState<Task[]>([
  { id: "1", name: "Analyze requirements", status: "done", progress: 100 },
  { id: "2", name: "Design solution", status: "running", progress: 60 },
  { id: "3", name: "Implement", status: "pending", progress: 0 },
  { id: "4", name: "Test", status: "pending", progress: 0 },
]);
```

**Capacité Core** : `core/planner/` — `Planner`

**Solution** :
1. Ajouter `getTasks()` à `api-client.ts` → `/api/v1/planner/tasks`
2. Créer `usePlannerTasks` hook → `plannerService`
3. Remplacer `useState` par `useQuery`

### 3.4 `terminal/page.tsx` — Historique hardcodé

**Problème** : L'historique est défini en dur et la commande est simulée :

```typescript
const [history, setHistory] = React.useState<string[]>([
  "ETHAN Shell v1.0",
  "Type 'help' for available commands",
]);

const handleSubmit = (e: React.FormEvent) => {
  e.preventDefault();
  if (!input.trim()) return;
  setHistory((prev) => [...prev, `$ ${input}`, `[${input}]: executed`]);
  setInput("");
};
```

**Capacité Core** : `core/tools/` ou `interfaces/shell/`

**Solution** :
1. Ajouter `executeCommand()` à `api-client.ts` → `/api/v1/terminal/execute`
2. Créer `useTerminal` hook → `terminalService`
3. Remplacer `useState` par `useQuery` + `useMutation`

---

## 4. Plan de Refactoring

### Phase 1 — API Endpoints (P0)

Pour chaque page problématique, ajouter les endpoints API manquants dans `interfaces/api/routers/v1.py` :

| Page | Endpoint | Méthode | Core associé |
|---|---|---|---|
| models | `/api/v1/models` | GET | `core/llm/provider_manager.py` |
| plugins | `/api/v1/plugins` | GET, PUT | `plugins/manager.py` |
| planner | `/api/v1/planner/tasks` | GET | `core/planner/` |
| terminal | `/api/v1/terminal/execute` | POST | `core/tools/` |

### Phase 2 — API Client (P1)

Ajouter les services à `interfaces/webui/src/core/api/api-client.ts` :

```typescript
// Models
export const modelsService = {
  getAll: () => apiClient.request<any[]>("/api/v1/models"),
};

// Plugins
export const pluginsService = {
  getAll: () => apiClient.request<any[]>("/api/v1/plugins"),
  toggle: (id: string) => apiClient.request<any>(`/api/v1/plugins/${id}/toggle`, { method: "PUT" }),
};

// Planner
export const plannerService = {
  getTasks: () => apiClient.request<any[]>("/api/v1/planner/tasks"),
};

// Terminal
export const terminalService = {
  execute: (command: string) => apiClient.request<any>("/api/v1/terminal/execute", {
    method: "POST",
    body: JSON.stringify({ command }),
  }),
};
```

### Phase 3 — Hooks (P1)

Créer les hooks correspondants :

| Hook | Fichier | Service |
|---|---|---|
| `useModels` | `features/models/hooks/use-models.ts` | `modelsService` |
| `usePlugins` | `features/plugins/hooks/use-plugins.ts` | `pluginsService` |
| `usePlannerTasks` | `features/planner/hooks/use-planner.ts` | `plannerService` |
| `useTerminal` | `features/terminal/hooks/use-terminal.ts` | `terminalService` |

### Phase 4 — Pages (P2)

Remplacer `useState` par `useQuery`/`useMutation` dans chaque page :

| Page | Avant | Après |
|---|---|---|
| `models/page.tsx` | `useState([...])` | `useModels()` |
| `plugins/page.tsx` | `useState([...])` + `togglePlugin` local | `usePlugins()` + `pluginsService.toggle` |
| `planner/page.tsx` | `useState([...])` | `usePlannerTasks()` |
| `terminal/page.tsx` | `useState([...])` + `handleSubmit` local | `useTerminal()` + `terminalService.execute` |

---

## 5. Règles de Non-Régression

1. **Ne pas supprimer les pages existantes** — les transformer en clients purs.
2. **Conserver l'expérience utilisateur** — même layout, même interactions.
3. **Validation HTTP conservée dans l'API** — le Core ne gère pas le HTTP.
4. **Sérialisation conservée dans l'API** — le Core retourne des objets métier.
5. **Tests existants** — `pytest tests/` doit passer après chaque migration.
6. **Migration progressive** — chaque page est migrée indépendamment.

---

## 6. Résultat Attendu

Après refactoring, **toutes les pages du WebUI** seront des clients API purs :

```
WebUI (React/Next.js) — UI pure
    ↓ (proxy /api/*)
interfaces/api/ (FastAPI) — Gateway pure
    ↓
core/ — Source de vérité
    ├── agents/     ← AgentManager
    ├── missions/   ← MissionManager
    ├── knowledge/  ← KnowledgeManager
    ├── rag/        ← RAGIngestion, RAGRetrieval, RAGContext
    ├── llm/        ← ProviderManager, LLMClient
    ├── planner/    ← Planner
    ├── memory/     ← MemoryManager
    ├── facts/      ← FactStore
    ├── config/     ← SettingsManager
    └── tools/      ← ToolManager
```

**Aucune logique métier, aucun stockage, aucune règle dans le WebUI.**
</arg_value><arg_key>task_progress</arg_key><arg_value>- [x] Analyser les modules Core existants
- [x] Créer `core/agents/` (4 fichiers)
- [x] Ajouter les événements AGENT_*, MISSION_*, KNOWLEDGE_* à `core/ethan_types/event.py`
- [x] Créer `core/missions/` (3 fichiers)
- [x] Créer `core/knowledge/` (3 fichiers)
- [x] Créer `core/rag/` (5 fichiers)
- [x] Vérifier que les imports des 4 domaines fonctionnent
- [x] Vérifier que les imports cassés (core.executive, core.cognition) sont réparés
- [x] Auditer les pages WebUI pour identifier la logique métier in-memory
- [x] Créer le plan d'audit WebUI (`docs/architecture/webui-core-audit.md`)</arg_value></tool_call>