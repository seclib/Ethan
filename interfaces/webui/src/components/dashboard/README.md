# Dashboard Vivant

## Vue d'ensemble

Le Dashboard est une interface temps réel qui affiche 14 cartes métriques dynamiques.

## Cartes

| Carte | Icône | Source | Fréquence |
|-------|-------|--------|-----------|
| Core | ⚙️ | Kernel status | 5s |
| CPU | ⚡ | psutil / /proc/stat | 1s |
| RAM | 💾 | psutil.virtual_memory() | 2s |
| GPU | 🎮 | nvidia-ml-py / rocm-smi | 2s |
| Providers | 🔌 | API health check | 5s |
| Tokens | 🔤 | Telemetry aggregator | 1s |
| Agents | 🤖 | Orchestrator | 3s |
| Planner | 📋 | Goals manager | 2s |
| Knowledge | 🧠 | Context/Skills | 5s |
| Memory | 💾 | Redis/PostgreSQL | 3s |
| MCP | 🔧 | Tools registry | 5s |
| Plugins | 🧩 | Plugin loader | 10s |
| Events | 📡 | Event bus | 1s |
| Network | 🌐 | System metrics | 2s |

## États

- **Normal** (vert) : valeur dans la plage attendue
- **Warning** (jaune) : valeur élevée mais acceptable
- **Critical** (rouge) : valeur critique, action requise
- **Loading** (bleu) : chargement initial
- **Error** (rouge) : impossible de récupérer la donnée
- **N/A** (gris) : non applicable

## Architecture

```
DashboardPage
  └── DashboardGrid
        ├── CoreCard
        ├── CpuCard
        ├── RamCard
        ├── GpuCard
        ├── ProvidersCard
        ├── TokensCard
        ├── AgentsCard
        ├── PlannerCard
        ├── KnowledgeCard
        ├── MemoryCard
        ├── McpCard
        ├── PluginsCard
        ├── EventsCard
        └── NetworkCard
```

## Hooks

- `useLiveMetric<T>(endpoint, interval)` : connexion SSE avec retry exponentiel
- `usePollingMetric<T>(fetchFn, interval)` : polling avec fallback

## Prochaines étapes

- [ ] Connecter les cartes aux endpoints API réels
- [ ] Ajouter le drill-down vers les pages détaillées
- [ ] Implémenter le drag & drop pour la personnalisation
- [ ] Ajouter les sparklines et graphiques historiques
- [ ] Persister les préférences dans localStorage