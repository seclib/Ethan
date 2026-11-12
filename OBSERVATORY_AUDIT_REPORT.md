# Observatory Workspace — Phase 1 Audit Report

**Date**: 2026-11-10  
**Status**: Complete  
**Scope**: Read-only audit of existing WebUI, Core services, and Ethan.Obsidians documentation

---

## 1. État des lieux vérifiable

### 1.1 WebUI — Architecture existante

| Élément | Localisation | Statut |
|---------|--------------|--------|
| Sidebar & Navigation | `interfaces/webui/src/components/layout/sidebar.tsx` | ✅ Opérationnel |
| Configuration nav | `interfaces/webui/src/components/layout/nav-config.ts` | ✅ Taxinomie v5 |
| Page Workspaces | `interfaces/webui/src/app/workspaces/page.tsx` | ✅ Existe (MCP seulement) |
| Route MCP Workspace | `interfaces/webui/src/app/workspaces/mcp/page.tsx` | ✅ Implémentée |

**Pattern Workspaces actuel** : Une page index `/workspaces` qui liste les workspaces disponibles (actuellement seulement MCP). Chaque workspace a sa propre route sous `/workspaces/*`.

### 1.2 Knowledge / RAG / Memory — Services Core existants

| Service | Core Module | API Router | WebUI Component |
|---------|-------------|------------|-----------------|
| Knowledge Collections | `core/knowledge/collections.py` | `/v1/knowledge/collections` | `KnowledgeWorkspace` |
| Knowledge Tree | `core/knowledge/collections.py` | `/v1/knowledge/collections/tree` | `KnowledgeHub` (onglet) |
| RAG Engine | `core/rag/pipeline.py` | `/v1/rag/config`, `/v1/rag/strategies` | `KnowledgeWorkspace` (dialog RAG) |
| Search Unifié | `core/search/__init__.py` | `/v1/search` | `KnowledgeHub` (barre recherche) |
| Memory (Facts) | `core/facts/store.py` | `/v1/memory/facts` | Non exposé en UI dédié |
| Engineering Memory | `core/engineering_memory/` | `/v1/memory/events` | Non exposé en UI dédié |

**Observation clé** : Tous les services métier existent dans le Core. Le WebUI ne fait que les exposer via des composants React qui appellent l'API. Aucune logique métier dans le frontend.

### 1.3 Ethan.Obsidians — Inventaire documentaire

**Localisation** : `/home/fatsio/AI/Ethan/Obsidian` (767 fichiers, 106 répertoires)

| Couche | Répertoires principaux | Volume | Formats |
|--------|------------------------|--------|---------|
| **Archives** | `Archives/Conversations/{cline,codex,copilot}/` | ~95 fichiers | Markdown (brut) |
| **Events** | `Archives/Events/` | ~30 fichiers | Markdown + YAML frontmatter |
| **Knowledge/Architecture** | `Knowledge/Architecture/` | 8 fichiers | Markdown + YAML |
| **Knowledge/Syntheses** | `Knowledge/Syntheses/by-agent/` | 6 fichiers | Markdown |
| **Operational-Memory** | `Operational-Memory/` | 10 fichiers | Markdown + YAML |
| **Engineering** | `Engineering/{Audits,Specs,Plans,Tests-Validation,...}/` | ~200+ fichiers | Markdown, JSON, CSV |
| **Métadonnées** | `_meta/` | ~150 fichiers | CSV, JSON, Markdown, NDJSON |

**Formats identifiés** :
- **Markdown + YAML frontmatter** : Documents structurés (events, decisions, components)
- **Markdown pur** : Archives brutes, synthèses, rapports
- **CSV** : `FILE_MANIFEST.csv` (467 KB), `LINK_MANIFEST.csv` (367 KB)
- **NDJSON** : `MEMORY_EVENT_LOG.ndjson` (audit trail)
- **JSON** : `application-manifest.schema.json`, `sync-state.json`

**Schémas documentaires** (définis dans `Knowledge/Architecture/MEMORY_DATA_MODEL.md`) :
- `Component`, `Decision`, `EngineeringEvent`, `Incident`, `Repair`
- `Verification`, `TestResult`, `Dependency`, `TechnicalDebt`
- `Evidence`, `AgentReport`
- IDs stables : `CMP-YYYY-NNN`, `DEC-YYYY-NNN`, `EVT-YYYY-NNN`, `INC-YYYY-NNN`, etc.
- Statuts par catégorie (ex: Decision → PROPOSED/APPROVED/REJECTED/SUPERSEDED)

### 1.4 API Engineering Memory — Déjà implémentée

**Router** : `interfaces/api/routers/engineering_memory.py`

| Endpoint | Méthode | Permission | Description |
|----------|---------|------------|-------------|
| `/v1/memory/health` | GET | READ | Intégrité du vault |
| `/v1/memory/events` | POST | RECORD | Enregistrer un événement |
| `/v1/memory/events/validate` | POST | RECORD | Valider sans persister |
| `/v1/memory/events/{id}` | GET | READ | Récupérer un événement |
| `/v1/memory/events` | GET | READ | Rechercher (filtres: component, type, status) |
| `/v1/memory/components/{component}/history` | GET | READ | Historique par composant |

**Service Core** : `core/engineering_memory/service.py` → `EngineeringMemoryService`
- Persistance atomique dans `Obsidian/` (Markdown + YAML)
- Registre de types avec destinations, statuts, naming conventions
- Validation stricte (schémas, statuts, provenance, secrets)
- Audit log NDJSON automatique

### 1.5 MCP REA — Capacités vérifiées

**Résultat `opencode.list_mcp_resources`** : Aucune ressource MCP exposée actuellement.

**Outils REA disponibles** (via `tools.rea.*`) :
- Sessions Frida/GDB/Rizin pour reverse engineering
- Navigation contextuelle (document, adresse, procédure)
- **Pas d'outils de lecture/écriture de fichiers locaux, pas de recherche documentaire, pas d'indexation**

**Conclusion** : Le MCP REA est orienté *reverse engineering de binaires*, pas *knowledge management*. Il ne peut pas remplacer les services Core existants pour l'Observatory.

---

## 2. Architecture et mécanismes existants

### 2.1 Flux de données actuel

```
User Action (WebUI)
       │
       ▼
React Component (ex: KnowledgeWorkspace)
       │
       ▼
API Client (lib/api/knowledge.ts, memory.ts, search.ts, rag.ts)
       │
       ▼
HTTP /v1/knowledge, /v1/rag, /v1/search, /v1/memory
       │
       ▼
FastAPI Router (interfaces/api/routers/*.py)
       │
       ▼
Core Service (core/knowledge, core/rag, core/search, core/engineering_memory)
       │
       ▼
Persistance (Obsidian/, PostgreSQL, ChromaDB, mémoire)
```

### 2.2 Conventions d'intégration Workspace

1. **Route** : `/workspaces/{name}/page.tsx` sous `app/workspaces/`
2. **Entrée sidebar** : Ajout dans `WORKSPACE_SECTIONS` (nav-config.ts) ou `WORKSPACES` (workspaces/page.tsx)
3. **Composant principal** : `{Name}Workspace` dans `components/features/{name}/components/`
4. **Hooks** : `use{Name}` dans `components/features/{name}/hooks/`
5. **API** : `lib/api/{name}.ts` pour les appels Core
6. **Permissions** : Via `require_permission(Permission.READ/RECORD/ADMIN)` côté API

### 2.3 Composants UI réutilisables identifiés

| Composant | Localisation | Usage pour Observatory |
|-----------|--------------|------------------------|
| `PageHeader` | `components/shared/page-header.tsx` | En-tête pages |
| `Dialog`, `ConfirmDialog` | `components/ui/dialog.tsx` | Modales |
| `Input`, `Textarea`, `Select` | `components/ui/input.tsx` | Formulaires |
| `Button`, `Badge` | `components/ui/button.tsx` | Actions |
| `Card` | `components/ui/card.tsx` | Conteneurs |
| `Tabs` (compound) | Pattern dans `nav-config.ts` | Navigation interne |
| `CommandPalette` | `components/ui/command-palette.tsx` | Recherche globale |
| `SidebarNavSections` | `components/layout/sidebar-nav-sections.tsx` | Navigation latérale |
| `VirtualMarketList` | Pattern dans `frontend-patterns` | Listes virtualisées |
| `DataLoader` | Pattern dans `frontend-patterns` | Fetch + loading/error |

---

## 3. Lacunes et risques

| Lacune | Impact | Mitigation |
|--------|--------|------------|
| **Pas de composant graphe interactif** | Graph/Canvas vides | Utiliser `react-force-graph` ou `cytoscape` (nouvelle déps) |
| **Pas d'éditeur Markdown WYSIWYG** | Vault read-only | `@uiw/react-md-editor` ou `monaco-editor` (nouvelle déps) |
| **Pas de visualisation timeline** | Timeline vide | Composant custom avec `recharts` ou SVG natif |
| **Pas de canvas libre** | Canvas vide | `reactflow` ou `d3-force` (nouvelle déps) |
| **Engineering Memory API non exposée en UI** | onglet Engineering inopérant | Créer composants de lecture/écriture |
| **Search unifié non testé sur memory** | Search incomplet | Étendre `/v1/search` type=memory |
| **Permissions Engineering Memory** | WRITE nécessite `RECORD` | Vérifier mapping roles/permissions |

---

## 4. Conventions ADR/ESR constatées

### ADR (Architecture Decision Records)
- **Localisation** : `engineering/adr/ADR-*.md` (9 fichiers) + `Obsidian/Architecture/ADR/` (40+ fichiers)
- **Format** : Markdown avec en-tête `Statut`, `Date`, `Contexte`, `Décision`, `Conséquences`, `Compliance`, `References`
- **Numérotation** : ADR-001, ADR-1001+, ADR-3000+, ADR-4000+, ADR-EM-001, ADR-MEM-014
- **Audit trail** : Colonne « État audité » datée confrontant décision vs code réel

### ESR (Engineering Specifications & Requirements)
- **Localisation** : `Obsidian/Architecture/ESR/` (14 fichiers)
- **Lien ADR** : Chaque ESR référence son ADR parent (ex: ESR-001 → ADR-4001)
- **Statut** : Implémenté / Partiel

### ASR (Architecture Security Requirements)
- **Localisation** : `Obsidian/Architecture/ASR/` (1 fichier : ASR-EM-001)
- **Contenu** : Exigences sécurité (Auth, RBAC, Secrets, Redaction, Audit, Publication)

### Memory Data Model
- **Fichier** : `Knowledge/Architecture/MEMORY_DATA_MODEL.md`
- **Entités** : 11 types avec schémas YAML complets
- **Statuts** : Par catégorie (voir §1.3)

---

## 5. Architecture cible proposée pour Observatory

### 5.1 Structure de routes

```
/workspaces/observatory/                    → Page d'index (Overview)
/workspaces/observatory/vault               → Vault (explorateur + éditeur)
/workspaces/observatory/graph               → Graph interactif
/workspaces/observatory/canvas              → Canvas libre
/workspaces/observatory/timeline            → Timeline
/workspaces/observatory/search              → Recherche unifiée
/workspaces/observatory/engineering         → Engineering (ADR, ESR, Components, etc.)
/workspaces/observatory/ai-insights         → AI Insights (rapports agents)
```

### 5.2 Intégration technique

| Fonctionnalité | Service Core existant | Nouveaux composants WebUI |
|----------------|----------------------|---------------------------|
| **Vault** | Engineering Memory API (`/v1/memory/events`) + Knowledge Collections | `VaultExplorer`, `MarkdownEditor`, `MarkdownPreview`, `BacklinksPanel` |
| **Graph** | Search API (`/v1/search`) + Knowledge Collections tree | `GraphView` (react-force-graph) |
| **Canvas** | Engineering Memory (relations) | `CanvasView` (reactflow) |
| **Timeline** | Engineering Memory events + Memory events | `TimelineView` (custom) |
| **Search** | `/v1/search` (étendre type=memory) | `UnifiedSearch` |
| **Engineering** | Engineering Memory API + ADR/ESR files | `EngineeringHub` (tabs) |
| **AI Insights** | Engineering Memory (AgentReport type) | `AIInsightsPanel` |

### 5.3 Modèle de données unifié

L'**Engineering Memory** (`core/engineering_memory/`) est la source unique pour :
- Events techniques (EVT-*)
- Décisions (DEC-*)
- Composants (CMP-*)
- Incidents/Réparations (INC-*/REP-*)
- Vérifications/Tests (VER-*/TST-*)
- Dépendances/Dette (DEP-*/DEBT-*)
- Preuves (EVD-*)
- Rapports agents (RPT-*)

Le **Knowledge** (`core/knowledge/`) reste pour :
- Collections utilisateur (documents RAG)
- Arborescence dossiers
- Recherche sémantique

---

## 6. Plan d'implémentation priorisé

### Phase 1 — Audit ✅ TERMINÉE
- [x] Cartographie WebUI, Core, Ethan.Obsidians
- [x] Identification services réutilisables
- [x] Vérification MCP REA
- [x] Proposition architecture technique

### Phase 2 — Interface de base (Semaine 1)
- [ ] Route `/workspaces/observatory/page.tsx` (Overview)
- [ ] Entrée dans `WORKSPACE_SECTIONS` (nav-config.ts) + `WORKSPACES` (workspaces/page.tsx)
- [ ] Layout principal avec navigation interne (tabs latéraux ou header)
- [ ] Composant `ObservatoryOverview` (récents, stats, actions rapides)
- [ ] **Vault Read** : Explorateur arborescence (réutiliser `listCollectionTree` + Engineering Memory search)

### Phase 3 — Fonctionnalités Vault (Semaine 2)
- [ ] **Markdown Editor** : `@uiw/react-md-editor` (éditeur + preview split)
- [ ] **Liens internes** : `[[wiki-links]]` parsing + navigation
- [ ] **Backlinks** : Query `/v1/memory/events` par `related_components` + liens dans contenu
- [ ] **Tags/Propriétés** : YAML frontmatter editing
- [ ] **Recherche documentaire** : Étendre `/v1/search` type=memory

### Phase 4 — Graph, Timeline, Canvas (Semaine 3)
- [ ] **Graph** : `react-force-graph-2d` ou `cytoscape` — nœuds = documents/composants, arêtes = relations
- [ ] **Timeline** : Composant custom SVG/Canvas — événements triés par date
- [ ] **Canvas** : `reactflow` — nœuds déplaçables, edges, regroupements

### Phase 5 — Engineering & AI Insights (Semaine 4)
- [ ] **Engineering Hub** : Tabs ADR/ESR/ASR/Components/Incidents/Runbooks/Dependencies/Tests/Debt/Archives
- [ ] **AI Insights** : Liste `AgentReport` (RPT-*) avec filtres agent/date/statut, distinction provenance

### Phase 6 — Search Unifié & Validation (Semaine 5)
- [ ] Étendre `/v1/search` pour inclure `type=memory` (Engineering Memory)
- [ ] Composant `UnifiedSearch` avec filtres type/date/composant
- [ ] Tests d'intégration (routes, permissions, API)
- [ ] Vérification non-régression Workspaces existants (MCP, Knowledge, etc.)

---

## 7. Tests et critères d'acceptation

### Phase 2 — Interface de base
| Test | Critère de réussite |
|------|---------------------|
| Route `/workspaces/observatory` accessible | HTTP 200, page rendue |
| Entrée sidebar "Observatory" visible | Clic → navigation vers `/workspaces/observatory` |
| Overview affiche stats | Collections count, Events count, Docs count depuis API |
| Navigation interne fonctionnelle | Tabs/links → routes correspondantes |

### Phase 3 — Vault
| Test | Critère de réussite |
|------|---------------------|
| Explorateur arborescence | Affiche dossiers/collections Obsidian + Engineering Memory |
| Clic document → ouverture éditeur | Éditeur affiche contenu Markdown |
| Édition + sauvegarde | POST `/v1/memory/events` ou PUT collection → persistence |
| Liens `[[wiki]]` cliquables | Navigation vers document cible |
| Backlinks visibles | Panel affiche documents référençant le courant |

### Phase 4 — Graph/Timeline/Canvas
| Test | Critère de réussite |
|------|---------------------|
| Graph affiche nœuds/arêtes | >0 nœuds, interactions (zoom, pan, clic) |
| Clic nœud → navigation | Ouvre document/composant correspondant |
| Timeline affiche événements | Ordonnés chronologiquement, filtres par type |
| Canvas permet création nœuds | Drag-drop, edges, sauvegarde relations |

### Phase 5 — Engineering/AI
| Test | Critère de réussite |
|------|---------------------|
| Engineering Hub tabs | Chaque tab affiche données depuis API/files |
| AI Insights liste rapports | Filtres agent/date/statut fonctionnels |
| Distinction provenance | Badge "Agent Report" vs "Verified State" |

### Phase 6 — Validation globale
| Test | Critère de réussite |
|------|---------------------|
| Search unifié | Résultats knowledge + memory + conversation |
| Permissions | READ/RECORD respectées selon role |
| Non-régression | MCP, Knowledge, Tools workspaces inchangés |
| Build + Typecheck | `pnpm build` && `pnpm typecheck` réussis |

---

## 8. Cinq premières actions concrètes recommandées

1. **Créer la route Overview** : `/interfaces/webui/src/app/workspaces/observatory/page.tsx` avec `ObservatoryOverview` component
2. **Ajouter l'entrée sidebar** : Dans `nav-config.ts` → `WORKSPACE_SECTIONS` + `workspaces/page.tsx` → `WORKSPACES`
3. **Créer le layout Observatory** : Composant `ObservatoryLayout` avec navigation interne (tabs: Overview, Vault, Graph, Canvas, Timeline, Search, Engineering, AI Insights)
4. **Implémenter Vault Explorer (lecture)** : Réutiliser `listCollectionTree` + `/v1/memory/events` search pour afficher l'arborescence complète
5. **Étendre l'API Search** : Ajouter `type=memory` dans `/v1/search` (router + SearchManager) pour recherche unifiée

---

## 9. Preuves et limites de l'audit

**Preuves vérifiées** :
- Code source WebUI (sidebar, nav-config, workspaces, knowledge components)
- Code source API routers (knowledge, memory, search, rag, engineering_memory)
- Code source Core services (engineering_memory, knowledge, rag, search, facts)
- Dossier Obsidian (structure, formats, schémas, manifests)
- MCP REA resources list (vide)

**Limites** :
- Pas d'exécution des tests applicatifs (build, typecheck, unit tests)
- Pas de vérification runtime des permissions Engineering Memory
- Pas d'analyse de performance sur gros volumes (767 fichiers Obsidian)
- MCP REA capacités limitées au reverse engineering (pas de file search/indexing)

---

**Prochaine étape** : Validation de ce rapport → Lancement Phase 2 (Interface de base)