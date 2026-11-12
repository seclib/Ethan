# État courant — ETHAN

> Date : 2026-11-10
> Branche : `refactor/ethan-rebuild-p0`
> Dernier commit référencé : `9e57d1c0` — `feat(knowledge): implement TechnicalMemoryWorker for background synchronization` (2026-10-29)

## Mise à jour — 2026-11-12 (DAĒNĀ P2.8.2 — Consolidation fonctionnelle des Project Anchors)

- **Mission** : consolidation complète des Project Anchors (Mission 02 —
  Stabilisation fonctionnelle), **sans** engager P2.8.3.
- **Défauts corrigés (12)** : réactivation ignorant l'exclusivité (A1) ;
  absence d'atomicité contrôle-puis-écriture (A2) ; existence des cibles
  jamais vérifiée (B1) ; panne du store transformée en « projet
  introuvable » (C1) ; inventaire inaccessible rendu par une liste vide
  (C2) ; `detach()` sans validation (D1) ; métadonnées d'origine effacées
  (E1) ; pas d'historique des cycles (E2) ; filtrage quadratique (F1) ;
  filtrage accepté pour un projet inexistant (F2) ; erreurs non traduites
  dans les routes (G1, G2).
- **Correction du socle** : `CoreRecordStore` ne fournissait **aucune**
  garantie de concurrence ni distinction « absent » / « inconnu ». Ajout
  de `get_strict`, `list_strict`, `save_strict` et de la section critique
  `atomic(guard)` — transaction PostgreSQL + `pg_advisory_xact_lock`,
  repli `asyncio.Lock` sans PostgreSQL. **Aucune base nouvelle, aucun
  daemon, aucune migration, aucun changement de schéma.**
- **Existence des cibles** : trois verdicts — `verified` (source
  alimentée, cible présente), `not_found` (source alimentée, cible absente
  → rattachement **refusé**), `unresolvable` (source non alimentée ou
  inaccessible → rattachement accepté mais **existence non prétendue**).
  Sources réelles : `knowledge`, `resources`, `missions`, et le vault
  documentaire pour les documents d'ingénierie (résolveur injecté).
- **Historique** : l'ancre porte ses **cycles** (`history`) — date,
  auteur, métadonnées, détachement, verdict d'existence. Rétrocompatible
  (une ancre sans `history` est reconstituée).
- **Erreurs** : `ProjectAnchorStoreUnavailable` (technique → **503**) est
  distinct de `ProjectAnchorError` (règle métier → **422**).
- **Routes** : 5 routes (4 d'origine + `anchors/global` qui expose
  `status: ok | unavailable`). Permissions `READ` (lecture) et `MEMORY`
  (écriture).
- **Tests** : `tests/core/test_project_anchors.py` **48** (26 + 22) ;
  `interfaces/api/tests/test_project_anchors_api.py` **17**. Les deux
  tests de régression de défaut ont été **vérifiés détecteurs** (section
  critique et contrôle de réactivation neutralisés → tests en échec).
  Non-régression : `tests/core/` = **960 passés** (938 + 22), 27 failed +
  8 errors **pré-existants inchangés** ; `interfaces/api/tests/` = **373
  passés**, 1 ignoré.
- **Runtime** : instance **isolée** (store mémoire, aucun accès PG ni
  corpus) → les 5 routes exercées en HTTP réel, tous codes de statut
  conformes ; conteneur `ethan-api` reconstruit → 5 routes exposées et
  **401** sans jeton.
- **Statut** : IMPLEMENTED + TESTED + RUNTIME_VALIDATED ; **PARTIAL** sur
  l'isolation (testée dans le service, **non appliquée** aux managers
  Core) ; **NOT_VERIFIED** pour l'E2E production authentifié (aucun
  identifiant opérateur autorisé — non contourné).
- **Documentation** : `docs/architecture/dana-p2-8-2-project-anchors.md`
  §12 à §17 (ajout chronologique) ; ADR **D-008 complément** dans
  `docs/memory/DECISIONS.md` ; session P2.8.2 complétée.
- **Hors périmètre, documenté** : 119 suppressions `daena/` staged par un
  processus externe (fichiers présents sur le disque) ; rôle `api-key`
  sans permission RBAC ; résolveur du vault ≈ 0,5 s ; `ResourceRegistry`
  non branché (P2.8.6) ; sessions non persistées (P2.8.7) ; branchement
  `KnowledgeManager`/RAG (P2.8.3 → P2.8.8).
- **⚠ ANOMALIE CRITIQUE (constatée pendant la mission, hors périmètre)** :
  à 13:57, un **processus externe a supprimé puis recréé `.git`** — branche
  `master` **sans commit**, `refs/heads/` vide, reflog vide, commits
  `57e254b0` / `95a4765b` / `9ae9744f` **absents de la base d'objets**,
  stash `audit-pre-refactoring-state` **perdu**, 4172 fichiers indexés
  comme nouveaux. `git ls-remote origin` ne renvoie aucune référence :
  l'historique n'est pas récupérable depuis le remote. **Aucun commit,
  reset, clean, stash ou checkout n'a été exécuté par cette session** et
  **aucune réparation n'a été tentée** (opération Git interdite par la
  mission ; décision réservée à l'opérateur). **Aucun travail perdu** :
  tous les fichiers de travail sont intacts et les tests passent. Rapport
  détaillé : `docs/memory/sessions/2026-11-12-daena-p2-8-2-project-anchors.md`
  §11.1.
- Session : `docs/memory/sessions/2026-11-12-daena-p2-8-2-project-anchors.md`.

## Mise à jour — 2026-11-12 (DAĒNĀ P2.8.3 — Traçabilité automatique des interventions)

- **Objectif** : toute intervention technique laisse une trace documentaire
  persistante, consultable et cumulative dans DAĒNĀ.
- **Modèle** : `core/engineering_memory/traceability.py` — `InterventionReport`
  (rubriques A→J), `TraceabilityService` (écriture, transitions, contrôle de
  fin), `report_from_payload()` (coercion des interfaces), `redact()` /
  `redact_structure()` (12 motifs de secrets).
- **Source documentaire unique** : le vault `daena/` via l'Engineering
  Memory. **Aucun type d'enregistrement nouveau** — rapport = `ENGINEERING_EVENT`,
  anomalie = `INCIDENT`, dette = `TECHNICAL_DEBT`. **Aucune base nouvelle.**
- **Immuabilité** : un document n'est jamais réécrit ; un changement d'état
  est un **événement corrélé** (`correlation_id`). Conflit d'identifiant →
  `409`, jamais d'écrasement.
- **Extension rétrocompatible** : champ `metadata` optionnel sur
  `MemoryRecord` (structure interrogeable) ; comparaison d'idempotence
  canonique JSON.
- **Contrôle de fin** : 8 conditions vérifiées (`complete`, `persisted`,
  `missing`, `unresolved_anomalies`). Un rapport non persisté ne peut pas
  être déclaré documenté. Échec → trace de secours rejouable hors corpus.
- **API** : 7 routes `/v1/memory/traceability/*` ; autorisation par **portée
  machine** `memory:traceability` (`require_memory_scope`, nouveau) ou
  permission RBAC pour les sessions humaines.
- **OpenCode** : plugin `.opencode/plugins/daena-traceability.ts` (capture
  automatique sur `session.execution.succeeded` + outil `daena_traceability`).
  `session.idle` **n'est pas émis** en v2.2.6 — vérifié en exécution réelle.
- **Tests** : `tests/core/test_traceability.py` (28) +
  `interfaces/api/tests/test_traceability_api.py` (12) = **40 tests, 40
  passent**. Persistance **réelle** (fichiers écrits, relus par une
  nouvelle instance de service). Non-régression : `tests/core/` = **938
  passés** (910 + 28), 27 échecs + 8 erreurs **pré-existants** inchangés ;
  `interfaces/api/tests/` = 356 passés, 1 ignoré.
- **Runtime** : validée en exécution réelle — rapport créé dans
  `daena/Archives/Events/`, anomalie dans `daena/Knowledge/Incidents/`,
  contrôle de fin à 8/8 via l'API conteneurisée.
- **Correctifs apportés au socle** (indispensables à la fonctionnalité) :
  - `persistence._read` : découpage du frontmatter **ligne par ligne** — le
    découpage sur la chaîne `---` rendait illisible tout document dont le
    corps contient un tableau Markdown ;
  - `persistence._read` : un document **illisible** (permissions) est isolé
    au lieu d'interrompre la lecture du corpus ;
  - `persistence.write` : comparaison canonique JSON (le YAML relit
    certaines chaînes comme des dates → faux conflits) ;
  - `security` : contrôle des secrets dans la charge utile structurée ;
    marqueur `[REDACTE…]` accepté.
- **Documentation** : `docs/architecture/dana-p2-8-3-traceability.md` ;
  ADR **D-009** dans `docs/memory/DECISIONS.md`.
- **Limites** : vault `daena/` **non inscriptible par l'utilisateur hôte**
  (uid 1000) — l'écriture passe par le conteneur `ethan-api` (uid 10001) ;
  granularité automatique = tour d'agent (capture `NOT_VERIFIED`) ;
  promotion des décisions en documents `Decision` hors périmètre (P2.8.4) ;
  `ResourceRegistry` non branché (P2.8.6) ; missions/sessions non
  persistées (P2.8.7) ; rapports non indexés par le `VaultService`.
- Session : `docs/memory/sessions/2026-11-12-daena-p2-8-3-traceability.md`.

## Mise à jour — 2026-11-12 (DAĒNĀ P2.8.2 — Ancrages projet)

- **Modèle** : `core/projects/anchors.py` — `ProjectAnchor` (relation
  dediee), `ProjectAnchorService` (Core-owned), domaine
  `core_domain_records[project-anchors]`.
- **Choix d'architecture** : **relation dediee** plutot qu'un `project_id`
  identique sur les 5 modeles concernes (`MemoryRecord`, `KnowledgeNode`,
  `ResourceRecord`, `Mission`, `ArchivedSession`). Motifs : multi-projet
  natif, provenance portee par la relation, **aucune migration de schema ni
  de donnees**, chemin de requete et regle d'isolation uniques.
- **Portee derivee, jamais stockee** : `GLOBAL` (0 ancre), `PROJECT` (1),
  `MULTI_PROJECT` (>1). `Mission` et `ArchivedSession` sont **exclusifs**
  (0..1) ; les autres categories sont partageables.
- **Validation** : projet inexistant, inactif ou identifiant vide refuses ;
  identifiant d'ancre UUIDv5 deterministe (rattachement idempotent) ;
  projet inactif refuse pour un **nouveau** rattachement, ancres existantes
  valides.
- **API** : 4 routes sous `/v1/projects/{id}/anchors`, permissions `READ` /
  `MEMORY`, **aucune logique metier** dans l'interface ; service cable dans
  `main.py` sur le `domain_store` partage.
- **Tests** : `tests/core/test_project_anchors.py` — 26 tests, 26 passent.
  Non-regression : 151 tests (P2.8.2 + P2.8.1 + P2.7 + P2.8.0 + EM) ; suite
  `tests/core/` = **910 passes** (884 + 26), 27 echecs + 8 erreurs
  **pre-existants** inchanges.
- **Donnees historiques** : aucun projet invente, aucun rattachement deduit —
  les 100 KnowledgeNode, 118 MemoryRecord et 536 ResourceRecord restent
  `GLOBAL`. **Aucune migration** : la relation est additive.
- **Documentation** : `docs/architecture/dana-p2-8-2-project-anchors.md` ;
  ADR **D-008** dans `docs/memory/DECISIONS.md`.
- **Limites** : `ResourceRegistry` non branche sur le store partage
  (P2.8.6) ; `missions` non persiste ; sessions hors store (P2.8.7) ;
  routes non validees en conditions authentifiees.
- Session : `docs/memory/sessions/2026-11-12-daena-p2-8-2-project-anchors.md`.

## Mise à jour — 2026-11-12 (DAĒNĀ P2.8.1 — Unification de la persistance)

- **Problème central résolu** : `ResourceRegistry` construisait son
  `KnowledgeManager` **sans store** → les 145 `KnowledgeNode` produits par
  P2.7 (déclarés `knowledge_state: indexed`) étaient **perdus au
  redémarrage**. L'affirmation était fausse.
- **Nouvelle couche** : `core/resources/repository.py` — `ResourceRepository`
  sur `CoreRecordStore`, domaine `resources`. Sérialisation seulement, aucune
  logique métier.
- **Registre unifié** : `ResourceRegistry` accepte `store` ; `persist()` écrit
  la source de vérité **puis** l'export portable ; `load_from_repository()`
  relit la source de vérité. `mark_stale` / `mark_disappeared` /
  `mark_deprecated` / `restore_resource` sont devenues `async` (elles
  persistent).
- **Défauts corrigés** : chemin explicite faisant foi (le fallback ignorait un
  `registry_meta_path` explicite et chargeait le registre global) ; fidélité du
  round-trip (`discovered_at` / `last_verified` relus) ; double comptage des
  statuts ; `_reconstitute_pending_nodes` désormais appelé.
- **Tests** : `tests/core/test_resource_persistence_unification.py` — 25 tests,
  25 passent. Non-régression : 100 tests EM/P2.7/P2.8.0 passent ; suite
  `tests/core/` = **884 passés** (859 + 25), 27 échecs + 8 erreurs
  **pré-existants** inchangés.
- **Migration** : `scripts/migrate_registry_to_pg.py` — dry-run par défaut.
  Vérifié : 536 enregistrements détectés, **0 écriture** sur le PG réel
  (domaine `resources` toujours à 0). Le `--apply` a été validé sur store
  mémoire isolé (536 écrits). **Non exécutée** sur les données réelles :
  autorisation opérateur requise.
- **Documentation** : `docs/architecture/dana-p2-8-1-persistence-unification.md`
  (cartographie, architecture, contrat, modèle, limites, preuves) ; ADR
  **D-007** dans `docs/memory/DECISIONS.md`.
- **Limite assumée** : le câblage runtime du `ResourceRegistry` sur le store
  partagé relève de **P2.8.6** (intégration fonctionnelle), hors périmètre de
  P2.8.1. Aucune migration n'a été exécutée sur les données réelles.
- Session : `docs/memory/sessions/2026-11-12-daena-p2-8-1-persistence-unification.md`.

## Mise à jour — 2026-11-12 (DAĒNĀ P2.8.0 — Correspondance documentaire)

- **Corrections appliquées** dans `core/engineering_memory/registry.py` : 4 mappings
  de destination corrigés vers le corpus réel — `COMPONENT`
  `Knowledge/Components` → `Knowledge/Composants` ; `VERIFICATION` et
  `TEST_RESULT` `Knowledge/Tests` → `Knowledge/Tests-et-Preuves` ; `DEPENDENCY`
  `Knowledge/Dependencies` → `Knowledge` (couche, aucun sous-répertoire dédié
  n'existe dans le corpus).
- **Justification** : les 3 chemins anglais n'existent nulle part dans le corpus
  (zéro occurrence de `Knowledge/Components` dans les 849 documents) ; ils ne
  figuraient que dans `daena/Metadata/REGISTRY.md` (PROPOSED, 2026-11-03,
  antérieur à la migration vers les noms français). Sources canoniques :
  `daena/INDEX.md`, `daena/AGENTS.md`, `daena/README.md` (2026-11-11).
- **7 mappings vérifiés corrects** et inchangés : `DECISION`, `ENGINEERING_EVENT`,
  `INCIDENT`, `REPAIR`, `TECHNICAL_DEBT`, `EVIDENCE`, `AGENT_REPORT`.
- **Protection du corpus** : 3 aides en lecture seule ajoutées
  (`destination_exists`, `resolve_destination`, `corpus_mapping`) + garde-fou
  opt-in `require_existing_destination` sur `ObsidianPersistence` et
  `EngineeringMemoryService` (l'écriture refuse de créer un répertoire absent ;
  défaut inchangé pour ne pas casser les appels existants).
- **Tests** : `tests/core/test_engineering_memory_destination_mapping.py` —
  34 tests, 34 passent. Non-régression : 28 tests Engineering Memory existants
  passent, 11 tests API memory/knowledge passent, suite `tests/core/` = 859
  passés (825 + 34), 27 échecs + 8 erreurs **pré-existants** inchangés.
- **Corpus intact** : 868 fichiers, 116 répertoires, manifeste SHA256 identique
  avant/après — aucun document déplacé, renommé, supprimé, copié ou modifié,
  aucun répertoire créé.
- **Runtime** : valid�� en exécution réelle sur le corpus (11/11 destinations
  existantes). L'API `/health` reste à 200 ; uvicorn tourne sans `--reload`,
  donc le processus en mémoire porte encore le code précédent — la correction
  sera prise au prochain redémarrage de l'API.
- **Documentation** : section « Correspondance documentaire Engineering Memory »
  ajoutée à `docs/architecture/dana-p2-7-knowledge-discovery.md`.
- **Anomalie restante** : `daena/Metadata/REGISTRY.md` (dans le corpus) reste
  périmé — il annonce `Knowledge/Tests` et `Knowledge/Components`. Sa
  correction relève d'une mission documentaire dédiée, car §5 de P2.8.0
  interdit de modifier un contenu du corpus.
- Session : `docs/memory/sessions/2026-11-12-daena-p2-8-0-document-correspondence.md`.

## Mise à jour — 2026-11-12 (DAĒNĀ P2.7 — Knowledge Discovery natif)

- **P2.7 implémenté dans ETHAN Core** : découverte documentaire native sur
  `AI/Ethan/docs/` et `AI/Ethan/docs/user-guide/` (`.md` + `.rst`), classification
  déterministe et justifiée, référencement dans le Resource Registry, extraction
  de contenu, indexation RAG réelle, relations objectives documents↔Skills.
- **Architecture** : `core/resources/discovery.py` devient un *scan pur*
  (`discover_documents`, `classify_document`) ; `core/resources/registry.py`
  orchestre (`discover_documents`, `index_documents`, `link_documents_to_skills`,
  `attach_pending_nodes`). Le cycle d'import `discovery ⇄ registry` est **éliminé
  à la source** : `discovery.py` n'importe plus `registry.py`.
- **Trois blocages levés** : (1) échappement de chaînes — `content.split(chr(92)+"n")`
  découpait sur la séquence littérale `\n` et non sur le saut de ligne ; (2) `await`
  hors fonction `async` — `discover_knowledge`/`discover_all_knowledge` déclarés
  `async` mais leurs appelants ne l'étaient pas ; (3) import circulaire — résolu
  par inversion de la direction de dépendance.
- **Deux bugs pré-existants corrigés** : double comptage des statuts dans
  `discover_skills` ; lien `ResourceRecord ↔ KnowledgeNode` rompu (`km.create()`
  générait un `uuid4()`) — corrigé par l'extension rétrocompatible
  `KnowledgeManager.create(..., node_id=None)`, qui aligne l'identité du nœud sur
  le `stable_id` et rend la création idempotente.
- **Identité documentaire** : UUIDv5 ancré sur le chemin canonique seul
  (`_compute_document_stable_id`) — un document dont le titre ou le contenu
  évolue conserve son identité, ce qui rend la détection de modification
  opérationnelle.
- **Résultats réels** : 391 Skills préservés, 145 documents découverts, 145
  KnowledgeNodes créés, 536 documents indexés dans le RAG (memory backend), 2
  relations documents↔Skills justifiées, registre à 536 ressources actives,
  idempotence stable sur 3 passes, persistance JSON validée après redémarrage.
- **Tests** : `tests/core/test_dana_p2_7_document_discovery.py` — 38 tests, 38
  passent. Non-régression `tests/core/` : 825 passent, 27 échecs + 8 erreurs
  **pré-existants** (bridge Rust, modèles, applications, imports interdits dans
  des fichiers non modifiés).
- **Documentation** : `docs/architecture/dana-p2-7-knowledge-discovery.md`
  (contrats, formats, catégories, états, relations, limites, points d'entrée
  WebUI/MCP).
- **Limites assumées** : aucune validation PostgreSQL/Redis ; `auth_proof` vérifie
  la présence, pas une signature cryptographique ; un déplacement de fichier
  change l'identité documentaire.

## Mise à jour — 2026-11-10 (Phase 3 — Intégration Knowledge / DAĒNĀ)

- Audit réel du corpus généalogique `daena/Knowledge/genealogie/` : 7 fichiers (stubs d'en-têtes, 125 car. au total), 7 sous-dossiers vides, 1 fichier avec anomalie de nommage `README.md,` (0 octet). Dossier non suivi par Git.
- Navigation WebUI : suppression du doublon « Toutes les Skills » dans `knowledge-hub.tsx`, `Workspaces → Skills` intégralement préservé.
- Audit Core & DAĒNĀ : absence de découverte automatique entre filesystem et bases Core (KnowledgeManager, RAGPipeline). Visible dans Vault, mais inexploitable pour les agents (pas de contenu probant).
- Session : `docs/memory/sessions/2026-11-10-phase3-knowledge-daena.md`.

## Mise à jour — 2026-11-10 (Observatory)

- Nouveau workspace **Observatory** dans le WebUI (Workspaces) — environnement
  de mémoire/connaissances ETHAN : Overview, Vault (explorateur redimensionnable,
  éditeur Markdown + aperçu, wikiliens, backlinks, propriétés YAML, recherche
  plein texte), Graph (SVG maison), Canvas (arrangement local), Timeline,
  Search (plein texte vault + /v1/search), Engineering (ADR/ESR/ASR + records
  Engineering Memory), AI Insights (synthèses agents vs preuves, provenance
  explicite).
- Core : nouveau service `core/engineering_memory/vault.py` (lecture seule,
  Archives/ immutables depuis l'interface) + routes vault dans le router
  Engineering Memory RBAC. Tests : 22 nouveaux (core + router).
- Vérifié : typecheck, eslint (0 warning), 421 tests WebUI, build Next OK
  (8 routes prérendues), smoke read-only réel sur le vault (tree 0,06 s,
  graph 155 nœuds / 10 arêtes).
- L'API sur :8000 n'est pas redémarrée : les routes vault requièrent un
  restart par l'opérateur.
- Session : `docs/memory/sessions/2026-11-10-observatory.md`.



## Objectif de la session courante

Mettre en place une mémoire persistante inter-sessions pour Codex, sans modification du comportement applicatif.

## Faits vérifiés

- Au moment de la création de ce fichier, le dépôt contient de nombreuses modifications, ajouts, suppressions et fichiers non suivis (compte approximatif, incluant le dossier `docs/memory/` créé par cette session).
- La lecture condensée du statut ne constitue pas une preuve d'intégrité du dépôt.
- La branche courante est `refactor/ethan-rebuild-p0`.
- Aucune migration ni code applicatif n'a été modifié par cette session documentaire.
- Aucun test applicatif n'a été exécuté dans cette session documentaire.

## Priorités documentaires observées

1. Conserver la WebUI Next.js existante comme base et l'enrichir avec les concepts UX Open WebUI sans abandonner la base existante (décision documentée le 2026-08-17).
2. Phase C settings en cours de consolidation via `Obsidian/Engineering/Audits/03-PHASE-C-SETTINGS.md`.
3. Phase 3D sécurité : proposition de conception rédigée dans la session actuelle (non versionnée) ; aucun changement applicatif validé ni test exécuté.

## Mise à jour — 2026-11-11 (MISSION 01 — DAĒNĀ Global Architecture & Capability Audit)

- Rapport créé : `docs/memory/DAENA_GLOBAL_ARCHITECTURE_AUDIT.md` (15 sections).
- Audit en lecture seule : aucune modification de code, aucune migration, aucun commit.
- Croisement des sources : documents d'architecture, mémoire opérationnelle, code réel, API, interfaces, tests.
- Distinction des états pour chaque capacité : Fonctionnel et vérifié / Implémenté mais non vérifié / Partiellement implémenté / Absent / Bloqué par dépendance.
- Proposition d'architecture cible argumentée (sans implémentation).
- Session : `docs/memory/sessions/2026-11-11-daena-global-architecture-audit.md`.

## Mise à jour — 2026-11-11 (MISSION 09 — Real Core Runtime Validation, phases A et B)

- Rapport créé : `docs/memory/MISSION_09_REAL_CORE_RUNTIME_VALIDATION.md`.
- Stack Docker démarrée avec autorisation explicite (`./ethan up`) : 10/10 services, 9/10 healthy.
- API Core disponible : `GET /health` → 200, `nats_connected: true`, OpenAPI accessible.
- API non authentifiée (401) : aucun token ni credentials.json ; opérateur a refusé la création d'admin.
- Commandes CLI non authentifiées vérifiées (version, status, doctor, daemon, aide, JSON).
- Sous-systèmes protégés bloqués par l'authentification (pas de bypass, pas d'escalation).
- Aucune modification de code, aucune opération destructive.
- Statut final : BLOCKED BY CORE/API (authentification requise).

## Mise à jour — 2026-11-11 (MISSION 09 — Reprise phases C à G)

- Tentative de reprise des phases C à G après authentification.
- Vérification de `ETHAN_TOKEN` : absent. `~/.config/ethan/credentials.json` : absent. Aucun `.env*` ne contient `ETHAN_TOKEN`.
- `ethan auth status` : `Not logged in` (exit 1).
- Aucune création d'admin, aucun contournement de HROT.
- Phases C à G non exécutées : bloquées par l'absence de token authentifié.
- Rapport mis à jour : `docs/memory/MISSION_09_REAL_CORE_RUNTIME_VALIDATION.md` (section 11).
- Statut final maintenu : BLOCKED BY CORE/API.

## Prochaine tâche probable

- Fournir un token via `ETHAN_TOKEN` (sans le coller dans le prompt ni dans un fichier du dépôt) ou autoriser `ethan auth create-admin`/`login` pour débloquer les phases C à G.

## Blocages / risques

- Grand volume de changements locaux non commités : risque de confusion entre travail documentaire et travail applicatif.
- Mémoire historique présente dans plusieurs documents, dont certains peuvent être contradictoires ; uniquement les décisions marquées « validées » doivent être considérées comme fermes.
- Les rapports de session peuvent décrire des intentions qui n'ont pas été implémentées.

## Action de prudence

Ne jamais écraser un changement existant pour produire une sortie Codex.

## Mise à jour — 2026-11-02

- Implémentation de l'ETHAN Response Renderer dans `interfaces/webui`.
- Rendu Markdown renforcé, blocs de code, callouts, graphiques, KPI, badges, détails et diagrammes via blocs enrichis validés.
- Intégration dans `assistant-message.tsx`.
- Tests ciblés et build WebUI réussis.

Prochaine étape probable : affiner le style compact selon les retours et étendre la compatibilité des messages historiques.

## Mise à jour — 2026-11-03 (MEM-014 Phase 1)

- Implémentation du socle d'identité applicative et de validation contractuelle dans `core/applications/`.
- Ajout du schéma JSON `Obsidian/Engineering/Specs/application-manifest.schema.json`, de la documentation et d'un exemple de manifeste.
- Tests ciblés ajoutés/existants passent.
- Module non intégré aux interfaces ; Odin, Frame et TradingAgents restent inchangés.

## Mise à jour — 2026-11-03 (audit Phase 1)

- Audit de robustesse réalisé dans le périmètre `core/applications/`.
- Corrections ciblées validées par 19 tests réussis.

## Mise à jour — 2026-11-03 (Phase 3)

- Permissions et HROT implémentés dans `core/applications/permissions.py`.
- 9 tests ciblés réussis, 38 régressions réussies.

## Mise à jour — 2026-11-03 (Phase 4)

- Contrats d'intégration applicative implémentés dans `core/applications/contracts.py`.
- 7 tests ciblés et 45 tests cumulés réussis.

## Mise à jour — 2026-11-03 (Phase 5)

- Moteur de conformité implémenté dans `core/applications/compliance.py`.
- 13 tests ciblés et 58 tests cumulés réussis.

## Mise à jour — 2026-11-03 (Phase 6)

- Résilience et cycle de vie implémentés dans `core/applications/resilience.py`.
- 9 tests ciblés et 67 tests cumulés réussis.

## Mise à jour — 2026-11-03 (Phase 7)

- Observabilité implémentée dans `core/applications/observability.py`.
- 12 tests ciblés et 79 tests cumulés réussis.

## Mise à jour — 2026-11-03 (audit global MEM-014)

- Audit global en lecture seule produit dans `Obsidian/_meta/MEM_014_GLOBAL_ARCHITECTURE_AUDIT.md`.
- Roadmap d'intégration produite dans `Obsidian/_meta/MEM_014_INTEGRATION_READINESS_ROADMAP.md`.
- 79 tests MEM-014 passent.

## Mise à jour — 2026-11-03 (HROT hardening + E2E tests)

- `HumanAuthority` obligatoire pour toute autorisation positive.
- Mapping permission/capacité strict.
- 5 tests transversaux et 84 tests cumulés réussis.

## Mise à jour — 2026-11-03 (Phase 8)

- Persistance durable SQLite implémentée dans `core/applications/persistence.py`.
- Services MEM-014 intègrent un stockage optionnel.
- 7 tests de persistance passent.

## Mise à jour — 2026-11-03 (Phase 9)

- Capability Registry implémenté dans `core/applications/capabilities.py`.
- 11 tests ciblés passent.
- HROT et mappings exacts préservés.

## Mise à jour — 2026-11-03 (Phase 10)

- HROT cryptographique Ed25519 implémenté dans `core/applications/hrot_crypto.py`.
- Intégration optionnelle avec `PermissionService`.
- Vérification réelle et anti-rejeu testés.
- 102 tests cumulés passent.

## Mise à jour — 2026-11-03 (Phase 11)

- HROT operational readiness implémenté dans `core/applications/hrot_operations.py`.

## Mise à jour — 2026-11-10 (Mission C1 — ETHAN CLI/TUI)

- Nouveau paquet `interfaces/cli/tui/` : TUI plein écran (thème sombre,
  conversation centrale, streaming, appels Tools, HROT, barre de statut,
  commandes slash, navigation clavier) construit sans nouvelle dépendance
  lourde (rich + stdlib).
- Point d'entrée `ethan cli` (sans argument) et `ethan tui` lancent le TUI ;
  `ethan cli <commande>` conserve la compatibilité.
- Client typé `TuiCoreClient` projetant les contrats Core
  (`/v1/agents`, `/models`, `/providers`, `/v1/tools`, `/chats`,
  `/v1/chat/completions/stream`, `/internal/approval/*`,
  `/internal/hrot/*`).
- `stream_sse` gagne le paramètre optionnel `abort_event` (rétro-compatible).
- `get_token()` valide l'expiration du token legacy avant adoption.
- 44 tests dédiés dans `tests/cli/ethan/tui/` (tous verts).
- Limitation documentée : approbation in-stream non supportée par le Core
  (voir ADR-4010).
- 7 tests phase 11 passent.

## Mise à jour — 2026-11-03 (Phase 12)

- Audit transversal de sécurité produit dans `Obsidian/_meta/MEM_014_PHASE_12_SECURITY_AUDIT.md`.
- 109 tests passent, 1 avertissement non bloquant.
- Consommation cryptographique des preuves durcie dans PermissionService.

## Mise à jour — 2026-11-03 (Phase 13)

- Registre d'intégration applicative implémenté dans `core/applications/application_registry.py`.
- 6 tests phase 13 passent, 115 tests cumulés passent.

## Mise à jour — 2026-11-03 (Phase 14)

- Validation end-to-end implémentée avec 7 tests.
- 122 tests cumulés passent.

## Mise à jour — 2026-11-03 (Phase 15)

- Préparation Odin réalisée sans lancement.
- Manifeste `examples/odin/ethan-application-manifest.yaml` validé.
- 3 tests Odin et 125 tests cumulés passent.

## Mise à jour — 2026-11-03 (Phase 16)

- Adaptateur Odin non exécutant implémenté.
- 3 tests phase 16 passent.

## Mise à jour — 2026-11-03 (Phase 17)

- Vérification build WebUI réussie; entrée Odin déjà présente sous Tools.
- Aucune opération Docker réelle lancée.

## Mise à jour — 2026-11-03 (Phase 18)

- Validation opérationnelle préparatoire documentée.
- Aucune opération Odin destructive exécutée.
- 128 tests passent.

## Mise à jour — 2026-11-03 (Phase 19)

- Validation runtime Odin non démontrée : backend bloqué par NATS.
- Build WebUI et 128 tests passent.

## Mise à jour — 2026-11-03 (Phase 19.1)

- Diagnostic NATS terminé.
- Blocage confirmé: URL/token et disponibilité de l'environnement non alignés.
- Aucune correction destructive appliquée.

## Mise à jour — 2026-11-03 (Phase 19.3)

- Phase reportée en attente d'authentification manuelle.
- Aucune session artificielle créée.

## Mise à jour — 2026-11-03 (Phase 20)

- Préparation Frame réalisée sans lancement.
- 1 test Frame phase 20 passe.

## Mise à jour — 2026-11-03 (Phase 21)

- Validation runtime Frame non effectuée (aucun démarrage, aucune capture).
- HROT reste non activé.

## Mise à jour — 2026-11-03 (Phase 22)

- Diagnostic backend/auth effectué.
- Correctif d'import dans `interfaces/api/main.py`.
- NATS et auth runtime non validés.

## Mise à jour — 2026-11-03 (Phase 23)

- Instance NATS locale validée avec token partagé.
- Connexion et publication backend réussies.
- Phase 19 reste à compléter avec authentification et capture navigateur réelles.

## Mise à jour — 2026-11-03 (Phase 24)

- Validation WebUI/Auth refusée faute d'authentification opérateur réelle.
- Aucune session artificielle créée.

## Mise à jour — 2026-11-03 (Phase 25)

- Audit Plugins UI documenté.
- Aucune modification de code appliquée dans cette phase.

## Mise à jour — 2026-11-03 (Phase 26)

- Moteur de réponses riches vérifié par build et typage.
- Aucune modification destructive.

## Mise à jour — 2026-11-03 (Phase 27)

- Rich Response UI build, typecheck et tests passent.
- Aucune validation navigateur réelle.

## Mise à jour — 2026-11-03 (Phase 28)

- Diagnostic Plugins UI documenté.
- Build et tests frontend passent, mais cause exacte du chargement non confirmée sans session.

## Mise à jour — 2026-11-03 (Phase 29)

- Page Plugins isolée de la section Odin.
- ErrorBoundary locale ajoutée.
- Build et typecheck réussis.

## Mise à jour — 2026-11-03 (Phase 30)

- Validation runtime dépend toujours d'une session authentifiée manuelle.

## Mise à jour — 2026-11-03 (Phase 30 Plugins Recovery)

- Page Plugins isolée de la section Odin.
- ErrorBoundary locale ajoutée.
- Typecheck, build et 378 tests passent.

## Mise à jour — 2026-11-03 (Phase 31)

- Build, typecheck et tests frontend passent.
- Validation visuelle réelle non obtenue.

## Mise à jour — 2026-11-03 (Phase 32)

- Validation runtime Frame non démontrée faute de session authentifiée et de démarrage contrôlé.

## Mise à jour — 2026-11-03 (Phase 34)

- Manifeste Quantar validé.
- 1 test phase 34 passe.

## Mise à jour — 2026-11-03 (Phase 36)

- Aucune implémentation fonctionnelle ajoutée.
- Phase conservée en préparation jusqu'à validation des dépendances et secrets.

## Mise à jour — 2026-11-03 (Phase 36 minimum)

- Quantar service backend minimal, routes API et page WebUI ajoutés.
- Typecheck et build réussis.
- Aucune exécution réelle de TradingAgents.

## Mise à jour — 2026-11-03 (Phase 37A)

- Configuration Docker hardened créée dans `examples/quantar/docker-compose.security.yml`.
- Validation `docker compose config` réussie.

## Mise à jour — 2026-11-03 (Phase 37)

- Configuration statique hardened validée.
- Aucune exécution runtime démontrée.

## Mise à jour — 2026-11-03 (Phase 37B)

- Tests runtime Docker hardened réussis sur image Python disponible.
- Réseau egress non encore contrôlé au niveau fin.

## Mise à jour — 2026-11-03 (Phase 38)

- Frontière runtime non démontrée.
- Aucune image Quantar dédiée construite.

## Mise à jour — 2026-11-03 (Phase 39)

- Aucune image dédiée construite.
- Aucun conteneur Quantar exécuté.

## Mise à jour — 2026-11-03 (Phase 39)

- Image Quantar dédiée construite et testée avec restrictions Docker.
- Digest : sha256:1825cfaf0a92f29da82e977d91f64d81b7ecd51b55e4357b561e402b5e933803.

## Mise à jour — 2026-11-03 (Phase 41)

- Catalogue applicatif local implémenté.
- 1 test phase 41 passe; HROT fail-closed préservé.


---

> Emplacement canonique de l’état opérationnel après réconciliation : `Obsidian/Operational-Memory/PROJECT_STATE.md`.
> La fusion détaillée est conservée dans ce fichier canonique (annexe).

## Mise à jour — DTAI-03F (2026-11-06)

- Cause réelle identifiée : l'onglet "Applications" de ToolsHub était déclaré mais son composant `ApplicationCatalog` n'était pas rendu (import sans usage effectif), ce qui empêchait de démontrer le parcours API → WebUI.
- Correction : ajout du rendu conditionnel `{tab === "applications" && <ApplicationCatalog />}`.
- Preuves ajoutées :
  - core : persistance manifeste puis rechargement + retrouver dans le catalogue (`tests/core/test_dta3f_integration_closure.py`) ;
  - API live (TestClient) : les deux endpoints retournent ComfyUI avec statut valide (`tests/interfaces/test_application_integration_catalog_api.py`) ;
  - WebUI (Jest/RTL) : affichage de ComfyUI à partir de la réponse API (`tests/unit/tools/application-catalog.test.tsx`).
- Non-régression : tests DTAI cibles + typecheck WebUI OK.
- Verdict : DTAI-03F validé pour la démonstration disponible dans l'environnement standard ; la démonstration navigateur live complète reste tributaire de Postgres/NATS/auth en environnement réel.

## Mise à jour — 2026-11-11 (Library Navigation / Final Validation)
- Finalisation de la palette Ctrl+K (`interfaces/webui/src/components/ui/command-palette.tsx`) : destinations issues de `NAV_ITEMS_FLAT`, filtrage par requête, routes et libellés traduits, navigation via Next.js `Link`, fermeture + réinitialisation de la recherche après sélection, navigation clavier et accessibilité. Library apparaît avec son libellé FR/EN.
- Spec Playwright de validation navigateur : `interfaces/webui/tests/e2e/library-navigation.spec.ts`.
- Tests : Jest ciblé command-palette-library 2/2 vert ; Jest UI 16 suites / 56 tests verts ; `tsc --noEmit` OK ; eslint OK ; `next build` OK (`/library` statique) ; Playwright Chromium sur le serveur de développement :3005 vert (13 étapes : desktop, sidebar réduite, mobile, i18n FR/EN, KnowledgeHub, Ctrl+K).
- Screenshots et rapport erreurs dans `/tmp/opencode/library-nav/` (identifiants non affichés).
- Non modifiés : Core/API/RAG, Skills, Skills Lab, DAĒNĀ, Motion Design. Aucune dépendance ajoutée. Aucune opération Git destructive, aucun commit.
- Blocage sécurité (Mission 4) : le compte temporaire `obs-audit-1794359036` n'a pas pu être supprimé de la base faute de voie propre (pas d'accès aux identifiants de la base de données, pas de droit admin sur ce compte via l'API). Suppression non effectuée pour ne pas contourner les permissions. Fichier `/tmp/opencode/obs-audit-creds.txt` supprimé.
- Session : `docs/memory/sessions/2026-11-11-library-navigation.md`.

## Mise à jour — 2026-11-11 (DAĒNĀ Architecture & Integration Assessment — MISSION 01)

Mission exclusivement d'investigation : aucun fichier de code de production modifié, aucun nouveau service, aucune dépendance installée, aucune migration, aucune opération Git destructive, aucun commit.

- Rapport d'évaluation produit dans `docs/memory/assessments/daena-dtai/` (8 fichiers, sans écrasement de documents existants) :
  1. `CURRENT_STATE.md` — état réel des composants, opérationnel / partiel / absent, preuves, 10 problèmes identifiés.
  2. `DAENA_ARCHITECTURE.md` — architecture actuelle, dépendances, flux de données, diagramme Mermaid.
  3. `KNOWLEDGE_RAG_ASSESSMENT.md` — analyse Knowledge et RAG, capacités et lacunes, parcours document complet avec ruptures.
  4. `AGENT_INTEGRATION.md` — niveau réel d'intégration des agents (Knowledge/RAG/Engineering Memory), tests et couverture.
  5. `DTAI_ASSESSMENT.md` — état réel du système d'intégration (DTAI), cas d'application Odin/Frame/Quantar/TradingAgents, endpoints, duplications.
  6. `DAENA_DTAI_ARCHITECTURE.md` — architecture cible, contrats DAĒNĀ ↔ DTAI, 5 diagrammes Mermaid, responsabilités.
  7. `IMPLEMENTATION_ROADMAP.md` — missions P0/P1/P2/P3, ordre d'exécution, dépendances, risques, critères d'acceptation mesurables.
  8. `EXECUTIVE_SUMMARY.md` — synthèse des constats, 5 problèmes prioritaires, recommandation de première mission.

- Cinq problèmes prioritaires :
  1. Pas de mécanisme commun d'accès Knowledge pour les agents (pas de retrieval autonome, mémoire cognitive `core/memory/` non branchée).
  2. Pas de citation formelle dans les réponses LLM (provenance uniquement dans le prompt).
  3. Pas de comptage de tokens / adaptation à la fenêtre de contexte (borne 8000 caractères bruts).
  4. HROT non appelé dans le flux d'exécution agent (service autonome non intégré).
  5. TradingAgents absent (proposition de manifest dans un test uniquement).

- Recommandation de toute première mission d'implémentation : P0-1 — Nettoyage des routeurs orphelins (`knowledge.py`, `engineering_memory.py` non montés dans `main.py`).

- Aucun test n'a été exécuté dans le cadre de cette mission (consigne : investigation uniquement, pas de modification de code). Les tests cités dans les rapports sont ceux existants dans le dépôt.

- Session : `docs/memory/sessions/2026-11-11-daena-dtai-assessment.md`.

## Mise à jour — 2026-11-11 (DAĒNĀ & DTAI — Architecture Roadmap Reprioritization — MISSION 02)

Mission exclusivement de planification et de documentation. Aucun code de production modifié, aucune API modifiée, aucune écriture en base, aucune migration, aucune dépendance installée, aucun nouveau service, aucune suppression/relocalisation de fichier, aucune opération Git destructive, aucun commit. Working tree et modifications préexistantes préservés.

### Priorités architecturales approuvées (nouvel ordre)

- **P0 — Sécurité et accès unifié aux capacités des agents (Critique)** : intégration réelle de l'autorisation HROT dans le cycle d'exécution agent, point d'entrée canonique d'autorisation, mécanisme commun contrôlé d'accès des agents à Knowledge/RAG/Engineering Memory, autorisation avant exécution protégée, fail-closed, auditabilité, pas de contournement.
- **P1 — Intelligence opérationnelle de DAĒNĀ (Haute)** : connecter l'exécution agent à Knowledge/RAG (sous autorisation P0), réutiliser Engineering Memory et Vault, stratégie de récupération cohérente, provenance des sources et citations formelles, gestion de contexte consciente des tokens, distinguer information récupérée et conclusions du modèle.
- **P2 — Intégration DAĒNĀ ↔ DTAI (Haute)** : contrats de métadonnées canoniques, stratégie d'événements et de synchronisation, versioning et provenance, gestion des erreurs et cohérence, propriété des entités, prévention des dépendances circulaires. DTAI reste propriétaire du cycle de vie ; DAĒNĀ reste propriétaire de la connaissance et de la mémoire.
- **P3 — Consolidation de l'architecture et fiabilité (Consolidation)** : routeurs API orphelins (identification du canonique, pas de montage aveugle), duplication Odin/ComposeService, opérations du cycle de vie des manifests, observabilité et tests d'intégration, suppression des composants obsolètes après analyse de dépendances.

### Documentation révisée (dans `docs/memory/assessments/daena-dtai/`)

- `IMPLEMENTATION_ROADMAP.md` : réécrite selon le nouvel ordre P0/P1/P2/P3 avec pour chaque mission : objectif, état actuel et preuves, périmètre, exclusions, prérequis, stratégie technique, fichiers affectés, sécurité, contrats API/données, tests, critères d'acceptation, risques/rollback, DoD, et séparation faits confirmés / recommandations / hypothèses non vérifiées / questions pour le propriétaire.
- `EXECUTIVE_SUMMARY.md` : constats factuels préservés, ordre de priorité révisé, recommandation de première mission (P0-1 HROT), constats secondaires reclassés en P3.
- Les six autres rapports (`CURRENT_STATE.md`, `DAENA_ARCHITECTURE.md`, `KNOWLEDGE_RAG_ASSESSMENT.md`, `AGENT_INTEGRATION.md`, `DTAI_ASSESSMENT.md`, `DAENA_DTAI_ARCHITECTURE.md`) sont préservés sans modification (aucune incohérence factuelle n'a nécessité de correction).

### Recommandation de toute première mission d'implémentation

**P0-1 — Intégration de l'autorisation HROT dans le cycle d'exécution agent** (point d'entrée canonique, fail-closed, auditabilité, pas de contournement). Aucune implémentation n'a été commencée ; la roadmap attend une validation explicite du responsable du projet.

### Aucun test exécuté

Aucun test n'a été exécuté dans le cadre de cette mission (consigne : investigation et planification uniquement). Les tests cités dans les rapports sont ceux existants dans le dépôt.

### Session

- `docs/memory/sessions/2026-11-11-daena-dtai-assessment.md` (MISSION 01 — investigation).
- `docs/memory/sessions/2026-11-11-daena-dtai-roadmap-reprioritization.md` (MISSION 02 — roadmap).
- `docs/memory/sessions/2026-11-11-daena-dtai-p0-1r-security-audit.md` (MISSION P0-1R — audit de sécurité indépendant).
- `docs/memory/sessions/2026-11-11-library-navigation.md` (bibliothèque, préexistante).

## Mise à jour — 2026-11-11 (DAĒNĀ & DTAI — P0-1R HROT Security Audit — MISSION P0-1R)

Mission exclusivement d'audit de sécurité indépendante, lecture seule. Aucun fichier de code de production modifié, aucun test modifié, aucune API modifiée, aucune écriture en base, aucune migration, aucune dépendance installée, aucun nouveau service, aucune suppression/relocalisation de fichier, aucune opération Git destructive, aucun commit. Working tree et modifications préexistantes préservés.

### Priorités architecturales approuvées (confirmées, inchangées)

- **P0 — Sécurité et accès unifié aux capacités des agents (Critique)** : P0-1 — Intégration de l'autorisation HROT dans le cycle d'exécution agent.
- **P1 — Intelligence opérationnelle de DAĒNĀ (Haute)**.
- **P2 — Intégration DAĒNĀ ↔ DTAI (Haute)**.
- **P3 — Consolidation de l'architecture et fiabilité (Consolidation)**.

### Documentation produite (dans `docs/memory/assessments/daena-dtai/p0-1r/`)

8 fichiers d'audit, création uniquement (aucun document existant modifié) :

1. `EXECUTION_PATH_INVENTORY.md` — inventaire des 12 chemins d'exécution, matrice d'autorisation, distinction capacités applicatives (HROT) vs exécution agent/capability manager (non HROT).
2. `HROT_SECURITY_REVIEW.md` — audit des 10 étapes de `CapabilityAuthorizationService.authorize()`, 6 faiblesses identifiées (HROT-01 à HROT-06).
3. `IDENTITY_AND_TRUST_REVIEW.md` — chaîne d'identité `Authenticated Principal → ExecutionContext → Agent Identity → Capability Invocation → HROT Decision`, faiblesse HROT-02 (pas de `verify_trusted_principal`).
4. `PERSISTENCE_AND_AUDIT_REVIEW.md` — persistance des grants (PermissionService en mémoire par défaut), piste d'audit en mémoire, pas de dépendance DurableHrotStore ↔ PermissionService.
5. `TEST_COVERAGE_REVIEW.md` — 53 tests existants (58 avec command API), scénarios manquants identifiés (11).
6. `INDEPENDENT_REVIEW.md` — revue indépendante confirmant l'architecture, 3 limites architecturales identifiées.
7. `REMEDIATION_PLAN.md` — plan de remédiation 8 éléments, ordre recommandé, critères d'acceptation, risques.
8. `FINAL_VERDICT.md` — **APPROVED WITH LIMITATIONS**, conditions pour promotion à APPROVED.

### Verdict final

**APPROVED WITH LIMITATIONS** : aucune vulnérabilité critique ou haute exploitable via l'API HTTP publique. Limitations architecturales (HROT-01, HROT-02, HROT-03, PERSIST-01, PERSIST-03) documentées, à remédier avant P1.

### Recommandation de toute première mission d'implémentation

**P0-1 — Intégration de l'autorisation HROT dans le cycle d'exécution agent** est validée comme prête à implémenter, sous réserve de la remédiation des limitations listées dans `REMEDIATION_PLAN.md` avant début de P1.

### Tests exécutés

- 58 tests passés (commande : `pytest tests/interfaces/test_application_capability_execution_api.py tests/interfaces/test_application_capability_contract_api.py tests/test_ethan_core/test_capability_registry.py tests/test_hrot_approval_flow.py tests/core/test_approval_hrot_integration.py tests/core/test_application_hrot_operations_phase11.py tests/core/test_hrot_provider_gateway.py`).
- Aucun test modifié ni créé. Échecs pré-existants non liés à P0-1 confirmés sur le code original (`git stash`).

## Mise à jour — 2026-11-11 (DAĒNĀ & DTAI — P0-1S HROT Security Hardening — MISSION P0-1S)

Mission d'implémentation de sécurité (P0-1S) — remédiation des limitations identifiées lors de l'audit P0-1R. Aucune opération Git destructive, aucun commit. Working tree et modifications préexistantes préservés.

### Fichiers modifiés (application)

| Fichier | Modifications |
|---------|---------------|
| `core/applications/capability_execution.py` | HROT-03 (suppression `enforce_hrot`), HROT-06 (suppression code mort lignes 272-299) |
| `core/hrot/capability_authorization.py` | HROT-01 (`permission_service` obligatoire + validation `authorize`), HROT-02 (`verify_trusted_principal()` dans `_evaluate()`), HROT-05 (`_record()` loggue les échecs) |

### Fichiers créés (application)

| Fichier | Contenu |
|---------|-----------|
| `tests/interfaces/test_application_capability_execution_p01s.py` | 17 tests de régression P0-1S |

### Documentation créée (dans `docs/memory/assessments/daena-dtai/p0-1s/`)

| Fichier | Contenu |
|---------|-----------|
| `IMPLEMENTATION_REPORT.md` | Rapport d'implémentation complet avec fichiers modifiés, détails par mission, dépendances, considérations de sécurité |
| `EXECUTIVE_SUMMARY.md` | Synthèse des constats, problèmes identifiés, recommandations, verdict final |
| `PERSISTENCE_AND_AUDIT.md` | Persistance des grants, piste d'audit, limitations et recommandations |
| `TEST_RESULTS.md` | Résultats des 75 tests (58 existants + 17 nouveaux), détails par test |
| `INDEPENDENT_REVIEW.md` | Revue indépendante par subagent, 6 constatations (1 HIGH, 1 MEDIUM, 3 INFO) |
| `FINAL_VERDICT.md` | **APPROVED WITH LIMITATIONS**, conditions pour promotion à APPROVED |

### Verdict final

**APPROVED WITH LIMITATIONS** : aucune vulnérabilité critique ou haute exploitable via l'API HTTP publique. Limitations architecturales (HROT-01, HROT-02, HROT-03, PERSIST-01, PERSIST-03) documentées, à remédier avant P1.

### Tests exécutés

**75 tests passés** (commande : `pytest tests/interfaces/test_application_capability_execution_api.py tests/interfaces/test_application_capability_contract_api.py tests/test_ethan_core/test_capability_registry.py tests/test_hrot_approval_flow.py tests/core/test_approval_hrot_integration.py tests/core/test_application_hrot_operations_phase11.py tests/core/test_hrot_provider_gateway.py tests/interfaces/test_application_capability_execution_p01s.py`).

- 58 tests existants (régression) : tous passés
- 17 nouveaux tests P0-1S : tous passés
- Échecs pré-existants non liés à P0-1S : confirmés sur le code original

### Session

- `docs/memory/sessions/2026-11-11-daena-dtai-assessment.md` (MISSION 01 — investigation)
- `docs/memory/sessions/2026-11-11-daena-dtai-roadmap-reprioritization.md` (MISSION 02 — roadmap)
- `docs/memory/sessions/2026-11-11-daena-dtai-p0-1r-security-audit.md` (MISSION P0-1R — audit de sécurité)
- `docs/memory/sessions/2026-11-11-daena-dtai-p0-1s-security-hardening.md` (MISSION P0-1S — implémentation, ce fichier)
- `docs/memory/sessions/2026-11-11-library-navigation.md` (bibliothèque, préexistante)

## Mise à jour — 2026-11-11 (DAĒNĀ & DTAI — P2 DAĒNĀ Knowledge Access for OpenCode & Cline — Architecture & Security Contract)

Mission de conception et de validation technique (P2 — Phase 2). Aucun fichier de code de production modifié, aucun test modifié, aucune API modifiée, aucune écriture en base, aucune migration, aucune nouvelle dépendance, aucun nouveau service, aucune suppression/relocalisation de fichier, aucune opération Git destructive, aucun commit. Working tree et modifications préexistantes préservés.

### Livrables créés (documentation uniquement)

| Fichier | Contenu |
|---------|-----------|
| `docs/memory/assessments/daena-mcp/P2_INVESTIGATION_REPORT.md` | Rapport consolidé des quatre investigations (Agent 1: Core & Lifecycle, Agent 2: Identity & Security, Agent 3: Retrieval & Provenance, Agent 4: MCP & Clients) |

### Verdict de la phase 2

**READY WITH CONDITIONS**

L'architecture est validée, le modèle d'identité MCP est défini, les autorisations sont compatibles avec HROT, les contrats des outils sont documentés, les risques non résolus sont identifiés, la stratégie de tests est définie, et le plan d'implémentation est suffisamment précis pour commencer la phase 3.

### Conditions à remplir avant la phase 3 (implémentation du serveur MCP DAĒNĀ)

1. Implémenter un serveur MCP autonome (processus séparé de l'API FastAPI), transport Streamable HTTP recommandé.
2. Câbler l'authentification client MCP vers `AgentPrincipal` (JWT/API key → `verify_trusted_principal`).
3. Câbler l'autorisation des appels MCP vers `CapabilityAuthorizationService.authorize()` / `PermissionService.evaluate()`.
4. Persister durablement les décisions d'autorisation (actuellement mémoire volatile uniquement).
5. Rendre l'audit MCP obligatoire (pas de `_audit_store = None` silencieux).
6. Exposer uniquement des outils MCP read-only (7 outils proposés : knowledge_search, knowledge_get, rag_retrieve, rag_build_context, collections_list, engineering_memory_search, engineering_memory_get).

### Prochaine mission autorisée

P1-0 — Knowledge Access Security & Integration Audit (après résolution des conditions C1 à C5 ci-dessus).

### Session

- Rapport consolidé : `docs/memory/assessments/daena-mcp/P2_INVESTIGATION_REPORT.md`


---

## Mise à jour — 2026-11-11 (démarrage ETHAN / python-base / modules)

### Cause racine

`modules` déclarait `python-base: condition: service_healthy`, mais
`python-base` est un conteneur utilitaire (`CMD sleep infinity`, aucun
healthcheck) qui ne peut donc jamais atteindre l'état `healthy`. Compose
refusait de démarrer `modules` (« container ethan-python-base has no
healthcheck configured »), puis `ethan up` poursuivait le boot et attendait
120 s la santé de `modules` avant d'échouer — alors que `modules` devenait
en fait `healthy` via son propre healthcheck.

### Correction appliquée

- `docker-compose.yml` : `modules.depends_on.python-base` passé de
  `service_healthy` à `service_started` (la disponibilité de `python-base`
  se résume à « le processus tourne »). Les autres dépendances
  (`nats`, `postgres`, `redis`, `api`, `kernel`) restent en
  `service_healthy`.
- `interfaces/cli/commands/up.py` : `_wait_for_services` fail-fast sur tout
  service sorti (`exited`/`dead`/`restarting`) au lieu de rester bloqué
  jusqu'au timeout ; délai par défaut ramené de 60 s à 30 s.
- `docker-compose.yml` : commentaire explicatif sur le réseau
  `ethan_ethan-core` (artefact manuellement créé lors de tests antérieurs,
  subnet 172.28.0.0/16 sans label Compose ; non déclaré `external`,
  non supprimé).

### Réseau `ethan_ethan-core`

Réseau créé manuellement pendant des tests antérieurs (subnet erroné
172.28.0.0/16, aucun label `com.docker.compose.*`), distinct du réseau
déclaré par Compose (172.20.0.0/16). Non supprimé (contrainte mission) ;
non déclaré `external: true` (propriété et cycle de vie non confirmés).
Le warning Compose reste attendu tant que cet artefact existe.

### Validations

- `docker compose config --quiet` : OK (exit 0).
- `sudo ethan up` : boot complet en ~4.6 s, 10/10 démarrés, 9/10 healthy
  (le dernier service en cours d'initialisation).
- `ethan-modules` : `running` / `healthy`.
- `ethan-python-base` : `running` (sans healthcheck, attendu).
- `ethan status` : OK.
- `ruff check interfaces/cli/commands/up.py` : All checks passed.

### Git

- Branche : `refactor/ethan-rebuild-p0`, HEAD `57e254b0` (aucun commit).
- Modifications préexistantes préservées.
