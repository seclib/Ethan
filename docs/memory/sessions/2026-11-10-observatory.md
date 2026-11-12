# Session 2026-11-10 — Workspace ETHAN Observatory

## Objectif

Créer le workspace **Observatory** dans le WebUI ETHAN — environnement de
mémoire et de connaissances (Obsidian-like + graphe + timeline), natif,
sans doublon Knowledge/RAG/Engineering Memory.

## Changements effectués

**Core**
- `core/engineering_memory/vault.py` (nouveau) : service lecture seule
  `VaultService` sur le vault canonique (`Obsidian/`) — arborescence,
  lecture de fichiers (allowlist d'extensions, 20 Mo max, chemins bornés
  `Archives/` protégé contre l'écriture), recherche plein texte, backlinks
  wikiliens, graphe wikiliens (priorisation liens → documents, archives en
  dernier), résolution de wikiliens, écriture bornée hors `Archives/`.
- `interfaces/api/routers/engineering_memory.py` : nouvelles routes
  `GET /v1/memory/vault/{tree,file,search,backlinks,graph,resolve}`,
  `POST /v1/memory/vault/file` (RECORD + Archives/ refusé),
  `GET /v1/memory/records`. Toutes protégées par RBAC existant. Le GET
  `/v1/memory/events` reste porté par v1.py (route plus fiable dans l'ordre
  d'inclusion) — le vault évite toute collision de routes.
- `tests/core/test_engineering_memory_vault.py` : 15 tests.
- `tests/interfaces/test_engineering_memory_vault_router.py` : 7 tests
  (TestClient + overrides de permission).

**WebUI**
- `app/workspaces/observatory/` : page Overview + layout interne + 8 routes
  (overview, vault, graph, canvas, timeline, search, engineering, ai-insights).
- `components/features/observatory/` : composants VaultWorkspace (explorateur
  redimensionnable, éditeur Markdown + aperçu, wikiliens, backlinks,
  propriétés YAML, recherche plein texte), GraphView (SVG maison, force
  layout déterministe, pan/zoom/drag), TimelineView, SearchView (plein texte
  vault + /v1/search), EngineeringView (ADR/ESR/ASR du vault + records EM),
  AiInsightsView (synthèses agents du vault + reports RPT-*, provenance
  explicite), CanvasWorkspace (arrangement local localStorage), composants
  partagés (frontmatter parser, wikilinks réécriture, layout).
- `lib/api/observatory.ts` : client fin des routes vault/records.
- `app/workspaces/page.tsx`, `components/layout/sidebar.tsx`,
  `components/layout/nav-config.ts` : entrée Observatory dans Workspaces +
  sidebar déployée + palette Ctrl+K. `locales/*.json` : clé
  `navigation.observatory` (6 langues).
- `__tests__/` : 3 suites jest (wikilinks, frontmatter, layout) — 11 tests.
- `OBSERVATORY_AUDIT_REPORT.md` : rapport de l'audit Phase 1 (existant).

## Tests exécutés

- `.venv/bin/python -m pytest tests/core/test_engineering_memory_vault.py
  tests/interfaces/test_engineering_memory_vault_router.py
  tests/core/test_engineering_memory*.py tests/interfaces/test_engineering_memory_router.py`
  → 37 passed (dont 22 nouveaux).
- `npm run typecheck` (tsc --noEmit) → OK.
- `npm test` (jest) → 72 suites, 421 passed (dont 3 nouvelles).
- `eslint …/observatory …/observatory --max-warnings 0` → propre.
- `next build` → OK ; les 8 routes `/workspaces/observatory*` sont
  prérendues statiquement (61 pages).
- Smoke réel read-only sur le vault (`/home/fatsio/AI/Ethan/Obsidian`) :
  tree 764 fichiers en 0,06 s ; recherche « engineering memory » 10 hits en
  0,12 s ; backlinks MEMORY_DATA_MODEL.md 10 entrées en 1,9 s ; graphe
  wikiliens 155 nœuds / 10 arêtes en 0,5 s (198 wikiliens bruts présents ;
  seules les cibles résolubles deviennent des arêtes).

## Résultats vérifiés

- Build de production génère et prérend les 8 routes Observatory.
- Routes protégées par l'auth WebUI (307 → /login hors session).
- Archives du vault immutables depuis l'interface (refus Core explicite,
  testé).
- Les données dérivées (graphes, wikiliens) sont recalculées à la demande —
  rien n'est persisté en cache disque par l'interface.
- Les workspaces existants inchangés (diff limité aux fichiers listés).

## Hypothèses / limites

- Le MCP REA (sessions Frida/GDB/Rizin) ne lit pas les fichiers : il n'entre
  pas dans l'architecture Observatory ; les agents ETHAN accéderont à la
  mémoire via Engineering Memory + l'API Core (routes vault), comme tout
  autre service commun.
- L'éditeur permet l'écriture uniquement hors `Archives/` (documents
  gérés). Les archives brutes sont immutables depuis l'interface.
- Canvas = arrangement local navigateur (localStorage), volontairement non
  persisté côté serveur ; aucun lien n'est écrit dans le vault.
- Pas de navigateur automatisé avec session opérateur : vérification visuelle
  non effectuée ; preuve par build statique + tests + smoke read-only.
- L'API servie sur :8000 (préexistante) n'a pas été redémarrée — les routes
  vault ne sont actives qu'après redémarrage du service par l'opérateur.
- Le graphe préfère les documents avec wikiliens et exclut les archives de
  la priorité ; 198 wikiliens bruts, 10 arêtes résolubles constatées.

## Tâches non terminées

- Redémarrage du service API par l'opérateur pour activer les routes vault.
- Édition assistée par agent (extraction RPT-* + relecture) non branchée.
- Timeline alimentée uniquement par les events actuels (28) ; les événements
  historiques des archives ne sont pas ingérés (hors périmètre).
