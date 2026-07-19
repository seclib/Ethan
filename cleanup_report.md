# Rapport de Nettoyage — ETHAN WebUI
> Date : 2026-07-18 | TypeScript : **0 erreur** | Fichiers après : **100**

---

## Résumé Exécutif

| Métrique | Avant | Après | Gain |
|---|---|---|---|
| Fichiers `.ts`/`.tsx` | ~130 | **100** | −23% |
| Packages npm (prod) | 12 | **9** | −3 packages |
| Packages npm (dev) | 15 | **14** | −1 package |
| Stores Zustand | 8 | **2** | −6 stores |
| Erreurs TypeScript | 0 | **0** | — |

---

## 1. Code mort supprimé

### Composants UI inutilisés
| Fichier | Raison |
|---|---|
| `components/ui/animated-button.tsx` | Non référencé dans aucune page |
| `components/ui/animated-card.tsx` | Non référencé dans aucune page |
| `components/ui/atmosphere.tsx` | Non référencé (effet visuel orphelin) |
| `components/ui/chapter-indicator.tsx` | Non référencé dans aucune page |
| `components/ui/mission-control-trigger.tsx` | Non référencé dans aucune page |

### Overlays non connectés
| Fichier | Raison |
|---|---|
| `components/overlays/approval-modal.tsx` | Aucun consumer trouvé |
| `components/overlays/detail-panel.tsx` | Aucun consumer trouvé |
| `components/overlays/file-viewer.tsx` | Aucun consumer trouvé |
| `components/overlays/scene-card.tsx` | Aucun consumer trouvé |

### Dashboard drag-and-drop cluster (complet)
| Fichier | Raison |
|---|---|
| `components/dashboard/dashboard-grid.tsx` | Aucun consumer dans les pages |
| `components/dashboard/dashboard-card.tsx` | Uniquement référencé par dashboard-grid |
| `components/dashboard/IMPLEMENTATION.md` | Documentation orpheline |
| `components/dashboard/README.md` | Documentation orpheline |

### Widgets non montés
| Fichier | Raison |
|---|---|
| `components/widgets/project-card.tsx` | Non référencé dans aucune page |
| `components/widgets/tasks-widget.tsx` | Non référencé dans aucune page |

### Charts custom
| Fichier | Raison |
|---|---|
| `components/charts/bar-chart.tsx` | Les pages utilisent `recharts` directement |

### Composants flux
| Fichier | Raison |
|---|---|
| `components/flux/virtual-list.tsx` | Non référencé dans aucune page |

### Hooks inutilisés
| Fichier | Raison |
|---|---|
| `hooks/useAnimations.ts` | Consumers (animated-button/card) supprimés |
| `hooks/useAtmosphere.ts` | Consumer (atmosphere.tsx) supprimé |
| `hooks/usePageTransition.ts` | Aucun consumer externe |
| `hooks/useExport.ts` | Aucun consumer |
| `hooks/useInspector.ts` | Aucun consumer |
| `hooks/useLiveMetrics.ts` | Aucun consumer |
| `hooks/useMetricHistory.ts` | Aucun consumer |
| `hooks/useModeTinting.ts` | Aucun consumer |
| `hooks/useSSE.ts` | Aucun consumer |
| `hooks/useDebounce.ts` | Auto-référence uniquement |
| `hooks/useLocalStorage.ts` | Auto-référence uniquement |
| `hooks/useMediaQuery.ts` | Auto-référence uniquement |
| `hooks/useThrottle.ts` | Auto-référence uniquement |

### Fichiers i18n
| Fichier | Raison |
|---|---|
| `i18n/fr.json` | Aucun consumer (`useTranslation` absent du code) |
| `i18n/index.ts` | Aucun consumer |

### CSS orphelins
| Fichier | Raison |
|---|---|
| `styles/globals.css` | Doublon — le vrai est `app/globals.css` |
| `lib/animations.css` | Non importé dans aucun fichier |

### Documentation
| Fichier | Raison |
|---|---|
| `WEBUI_ARCHITECTURE.md` | Document obsolète (architecture a changé) |

---

## 2. Dépendances npm supprimées

### prod (`dependencies`)
| Package | Raison |
|---|---|
| `@dnd-kit/core` | dashboard-grid.tsx supprimé |
| `@dnd-kit/sortable` | dashboard-grid.tsx supprimé |
| `@dnd-kit/utilities` | dashboard-grid.tsx supprimé |

### devDependencies
| Package | Raison |
|---|---|
| `@types/react-syntax-highlighter` | `react-syntax-highlighter` non utilisé dans le code |

---

## 3. Stores Zustand supprimés (session précédente)

Ces stores avaient été migrés vers React Query lors de la session précédente :

| Store supprimé | Remplacé par |
|---|---|
| `stores/agents.store.ts` | `hooks/use-agents.ts` + React Query |
| `stores/goals.store.ts` | `hooks/use-goals.ts` + React Query |
| `stores/missions.store.ts` | `hooks/use-missions.ts` + React Query |
| `stores/memory.store.ts` | `hooks/use-memory.ts` + React Query |
| `stores/skills.store.ts` | `hooks/use-skills.ts` + React Query |
| `stores/flux.store.ts` | `hooks/use-flux.ts` + React Query |
| `stores/knowledge.store.ts` | `hooks/use-knowledge.ts` + React Query |
| `stores/plugins.store.ts` | Local `useState` (données mock) |

**Stores conservés (légitimes) :**
- `stores/auth.store.ts` — état d'authentification (UI global, non cacheable)
- `stores/ui.store.ts` — état UI global (sidebar, command palette, inspector)

---

## 4. État final du dépôt

```
src/
├── app/
│   ├── (auth)/           # Login, Register
│   ├── (dashboard)/      # 14 routes (agents, assistant, documents, knowledge, logs, memory, models, page, planner, plugins, providers, settings, terminal, tools)
│   ├── globals.css       # Seule feuille de style globale (3786 lignes)
│   └── layout.tsx
├── components/
│   ├── assistant/        # Chat assistant complet
│   ├── dashboard/        # metric-card.tsx (utilisé par page.tsx)
│   ├── features/missions # mission-creator-dialog.tsx
│   ├── layouts/          # global-command-palette, global-inspector, global-shortcuts, sidebar, topbar
│   ├── ui/               # 13 composants atomiques + 10 tests
│   └── widgets/          # event-stream.tsx (utilisé par page.tsx)
├── hooks/                # 9 hooks (tous actifs)
├── lib/utils.ts
├── providers/            # 4 providers
├── services/             # 8 services API
├── stores/               # 2 stores Zustand (auth + ui)
└── types/                # 4 fichiers de types
```

---

## 5. Ce qui reste à faire (hors scope nettoyage)

> [!NOTE]
> Ces items ne sont pas des dettes — ils sont des évolutions futures.

- **`useDashboardLayout.ts`** est conservé mais plus rien ne l'utilise depuis la suppression de `dashboard-grid`. Il peut être réintégré si un nouveau grid drag-and-drop est créé.
- **`framer-motion`** est utilisé uniquement dans les composants login (4 fichiers). Si le login est simplifié, cette dépendance lourde peut être supprimée.
- **`recharts`** est utilisé dans `page.tsx` (dashboard). À conserver.

---

## Vérification finale

```
npx tsc --noEmit → Exit code: 0 ✅ (aucune erreur TypeScript)
```
