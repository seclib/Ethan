# Audit CTO — Revue Indépendante WebUI ETHAN

> **Date :** 14 août 2026  
> **Auteur :** CTO / Architecte en Chef  
> **Source de Vérité :** Code source réel (`interfaces/webui`), Routeurs API (`interfaces/api/routers`), Tests (`tsc`, `eslint`).

---

## 1. Principes d'Évaluation & Méthodologie

Cette revue indépendante évalue l'alignement strict de l'interface WebUI avec l'architecture **ETHAN Cognitive OS** et le maintien de la parité UX avec **Open-WebUI**.

### Hiérarchie des preuves :
1. **Code réel** (`interfaces/webui/src/app`, `src/lib/api`, `interfaces/api/routers`)
2. **Validation des types et linter** (`tsc --noEmit` EXIT 0, `eslint` 0 erreur)
3. **Flux de données & Proxy HTTP** (`src/app/api/[...path]/route.ts`)
4. **Documentation**

---

## 2. Évaluation des Capacités P0 & P1 (Système & Registres)

| Capacité / Module | Statut | Preuve Code & Implémentation | Conformité Architecture ETHAN | Parité Open-WebUI |
| :--- | :--- | :--- | :--- | :--- |
| **API Proxy Layer** | `VERIFIED DONE` | `src/app/api/[...path]/route.ts` intercepte `/api/*`, convertit le cookie JWT `ethan_token` en header `Authorization: Bearer`, et délègue au backend FastAPI. | **Conforme** — La WebUI est un client léger. | **Parfait** |
| **Models Registry** | `VERIFIED DONE` | `app/(dashboard)/models/page.tsx` + `lib/api/models.ts`. CRUD complet : listing découvert/custom, création de fiches custom, suppression, activation/désactivation (toggle). | **Conforme** — Délégué à `ProviderManager` et `ModelStore` Core. Aucune logique locale. | **Supérieur** (supporte fiches custom & découverts) |
| **Providers Registry** | `VERIFIED DONE` | `app/(dashboard)/providers/page.tsx` + `lib/api/providers.ts`. Formulaire d'enregistrement, mise à jour clés API, test de connexion healthcheck, définition du provider par défaut, suppression. | **Conforme** — Délégué à `ProviderManager` Core via `/providers/*`. Clés API masquées. | **Parfait** |
| **Knowledge / RAG** | `VERIFIED DONE` | `app/(dashboard)/knowledge/page.tsx` + `lib/api/knowledge.ts`. Collections, création/suppression, ingestion RAG, liaison documents-collections. | **Conforme** — Utilise `core/knowledge` et `core/rag`. Chunking/Embeddings 100% Core. | **Parfait** |
| **Documents / Files** | `VERIFIED DONE` | `app/(dashboard)/documents/page.tsx` + `lib/api/knowledge.ts`. Ingestion RAG direct, liste paginée avec chunks, recherche et suppression. | **Conforme** — Migré vers `lib/api/knowledge.ts`. Monolithe éliminé. | **Parfait** |
| **Skills Registry** | `VERIFIED DONE` | `app/(dashboard)/skills/page.tsx` + `lib/api/skills.ts`. Visualisation des skills, création, toggle actif/inactif, suppression et exécution. | **Conforme** — Délégué à `core/skills/store.py` (`SkillStore`). | **Supérieur** |
| **Tools / MCP** | `VERIFIED DONE` | `app/(dashboard)/tools/page.tsx` + `lib/api/tools.ts`. Enregistrement de serveurs MCP, bascule d'état (enable/disable), suppression. | **Conforme** — Délégué au registry MCP backend. | **Parfait** |
| **Prompts Template** | `VERIFIED DONE` | `app/(dashboard)/prompts/page.tsx` + `lib/api/prompts.ts`. CRUD complet des templates de prompts avec recherche et confirmation. | **Conforme** — Délégué aux endpoints `/v1/prompts`. | **Parfait** |

---

## 3. Évaluation des Capacités P2 (Workflows & Administration)

| Capacité / Module | Statut | Preuve Code & Implémentation | Conformité Architecture ETHAN |
| :--- | :--- | :--- | :--- |
| **Memory Management UI** | `VERIFIED DONE` | `app/(dashboard)/memory/page.tsx` + `lib/api/memory.ts`. Utilise les types canoniques `Fact`, filtre par catégorie/recherche, suppression avec mutation React Query. | **Conforme** — Délégué à `core/memory`. |
| **Planner & Goals** | `VERIFIED DONE` | `app/(dashboard)/planner/page.tsx` + `lib/api/goals.ts`. Dialog de création de goals, suivi des tâches, contrôle d'exécution (pause/run/status). | **Conforme** — Délégué au Planner Core. |
| **Terminal & Flux Logs** | `VERIFIED DONE` | `app/(dashboard)/logs/page.tsx` + `lib/api/flux.ts`. Streaming d'événements bus NATS/Flux en temps réel avec filtres par type et source. | **Conforme** — Délégué au routeur Flux. |
| **Settings & Governance** | `VERIFIED DONE` | `app/(dashboard)/settings/page.tsx` + `lib/api/settings.ts`. Configuration LLM, gouvernance, budgets et logs système. | **Conforme** — Délégué au store Settings backend. |
| **Plugin Manager** | `VERIFIED DONE` | `app/(dashboard)/plugins/page.tsx` + `lib/api/plugins.ts`. Toggle en ligne, installation et supervision des plugins. | **Conforme** — Délégué au Plugin Registry. |

---

## 4. Contrôle Anti-Violation Architecturale

1. **Aucun appel direct Frontend → Providers/Ollama** :
   - TOUTES les requêtes HTTP passent par `/api/*`, relayées de manière transparente par le proxy App Router (`src/app/api/[...path]/route.ts`) vers `ETHAN_API_URL`.
2. **Aucune duplication de registres ou de stockage métier** :
   - Le frontend ne garde aucun état métier en `localStorage` (hormis les préférences de mise en page et les modèles épinglés).
   - Les Providers, Modèles, Skills, Memory, et Documents sont 100% stockés et gérés par le Core ETHAN.
3. **Indépendance des interfaces** :
   - Si la WebUI est arrêtée, le Core ETHAN continue de fonctionner de manière autonome (conformément à la Première Loi d'ETHAN dans `AGENTS.md`).

---

## 5. Matrice Parité Open-WebUI

| Élément UI / UX | Statut Parité | Note de Mise en Œuvre |
| :--- | :--- | :--- |
| **Sidebar Navigation** | `VERIFIED DONE` | Ergonomie repliable avec tooltips, groupes thématiques, raccourcis et profil utilisateur. |
| **Assistant / Chat Interface** | `VERIFIED DONE` | Support streaming SSE, panneau latéral d'inspection (tools, memory, docs), historique des conversations. |
| **Model Selector** | `VERIFIED DONE` | Modèle actif connecté au ProviderManager backend, commande `/model` intégrée. |
| **Workspace & Knowledge** | `VERIFIED DONE` | Navigation par collections, ingestion RAG multi-sources. |
| **Settings & Configuration** | `VERIFIED DONE` | Section AI Providers unifiée, gestion du provider par défaut et tests de connexion. |

---

## 6. Travaux Restants Priorisés (Post-P2)

1. **[P3-01] Optimisation du Streaming SSE en faible bande passante** : Ajouter un buffer anti-jitter sur les tokens SSE de `streamEvents()`.
2. **[P3-02] Websocket Reconnection Backoff** : Implémenter une stratégie d'exponential backoff sur `WebSocketProvider`.
3. **[P3-03] Visualisation Graphique des Fact Relations** : Ajouter une vue Mermaid/Graph3D pour la mémoire cognitive.
