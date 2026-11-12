# ETHAN — Audit factuel P0 avant refonte (hybride Rust + Python, Open WebUI)

- **Date d'audit** : 2026-10-29 (environnement local, branche `refactor/ethan-rebuild-p0`)
- **Révision Git inspectée** : `9e57d1c0` (commit `feat(knowledge): implement TechnicalMemoryWorker for background synchronization`)
- **Dépôt** : `/home/fatsio/AI/Ethan`, remote `origin git@github.com:seclib/Ethan.git`
- **Rapport** : `Obsidian/Engineering/Audits/ETHAN_REBUILD_P0_AUDIT.md`
- **Matrice** : `Obsidian/Engineering/Audits/ETHAN_REBUILD_P0_TRACEABILITY_MATRIX.csv`
- **Registre données** : `Obsidian/Engineering/Audits/ETHAN_PERSISTENT_DATA_REGISTRY_P0.md`
- **Inventaire interfaces** : `Obsidian/Engineering/Audits/ETHAN_COMPONENT_INTERFACE_INVENTORY_P0.md`

> Aucun code fonctionnel n'a été modifié, aucune migration exécutée, aucun fichier/volume/conteneur supprimé pendant cet audit. Les deux modifications Git non commitées et les fichiers non suivis ont été préservés.

## 0. Verdict synthétique

- **ETHAN n'est pas une simple WebUI**. Le dépôt contient un noyau Python substantiel (`core/`, 452 fichiers) et une API FastAPI (`interfaces/api`, 48 routers), avec des dépendances d'architecture déjà encodées (`importlinter`) et maintenues.
- **Il n'existe pas de dossier `runtime/` racine**. Le "runtime" est composé par Docker Compose (`ethan-kernel`, `ethan-modules`, `ethan-api`, NATS, Redis, PostgreSQL). Cela doit être pris en compte dans le cadrage "Core hybride Rust + Python".
- **Open WebUI v0.9.1 est déjà vendored** dans `examples/open-webui` et son dépôt Git pointe vers `open-webui/open-webui`; toutefois il contient **des modifications de travail locales** (5 fichiers modifiés + répertoire `services/` non suivi + compose supprimé/re créé). L'audit factuel de l'amont doit partir d'un clone propre, pas de cet arbre modifié sans traçabilité.
- **Risque juridique élevé de marque** : la licence Open WebUI interdit l'altération/suppression du branding sauf exception documentée (≤ 50 utilisateurs finaux sur 30 jours ou permission écrite/licence enterprise). Une reprise "marque ETHAN" sans conformité est un blocage P0.
- **La stratégie "Core hybride Rust + Python" est déjà amorcée** par des prototypes non fonctionnels : `core/rust/ethan_health/`, `core/bus/backends/rust_event_store/` (`lib.rs` avec `write/read/save_checkpoint/replay` en `TODO`). Le contrat Rust/PyO3 est documenté (`interfaces/bridge/openwebui/event_bus_contract.md`) et marque explicitement ces fichiers comme non modifiables pendant l'expérimentation.
- **Les backends d'événements Rust/Python ne sont pas opérationnels** pour la lecture/rejeu : implémentation `read` existante mais fragile (NATS: abonnement éphémère sans pagination ni bornage durable ; Redis: boucle `while True` bloquante, pattern matching approximatif), checkpoints/snapshot non implémentés.
- **Tests en état mitigé** :
  - import-linter : 5 contrats conservés, 0 cassés (`Analyzed 1518 files, 7094 dependencies`);
  - import Python racine : `pytest tests/test_python_imports.py` = 5 passed;
  - API FastAPI/TestClient : collection bloquée par un décalage `typing_extensions` (module 4.15.0 installé avec dist-info 4.15.0 + 4.16.0, alors que anyio 4.x exige `sentinel`);
  - WebUI Next.js : `npm run typecheck` échoue (`src/app/plugins/page.tsx` erreurs TypeScript).
- **Codage de travail non commité actif** : 2 modifications (`core/plugins/odin.py`, `interfaces/webui/src/app/odin/page.tsx`) et 17 fichiers non suivis, dont `core/rust` (≈182 Mo de cible de build) et `core/bus/backends/rust_event_store`.

## 1. Dépôts, branches, worktrees

| Élément | Résultat |
|---|---|
| Branche active | `refactor/ethan-rebuild-p0` |
| Worktree unique | `/home/fatsio/AI/Ethan  9e57d1c0 [refactor/ethan-rebuild-p0]` (commande `git worktree list`) |
| Branches locales | `main`, `refactor/ethan-rebuild-p0` |
| Branche distante | `remotes/origin/main` |
| Remote | `origin git@github.com:seclib/Ethan.git` (fetch/push) |
| Open WebUI nested repo | `examples/open-webui` → remote `open-webui/open-webui`, branche `main`, commit sommet `0a8a620fb` |
| Derniers commits | voir section 2 |

## 2. État Git et modifications non commitées

Modifications suivies (non commitées) :
- `core/plugins/odin.py` : clarification des messages d'erreur (dépôt/compose introuvables), aucune logique métier ajoutée observée.
- `interfaces/webui/src/app/odin/page.tsx` : passage de `<details>` natifs à des blocs pilotés par React state; ajout tutoriel; refactor UI Odin.

Fichiers non suivis (17) :
- `core/bus/backends/rust_event_store/`
- `core/knowledge/agent_traces/__main__.py`
- `core/rust/`
- `core/skills/anthropic_importer.py`
- `core/skills/import_manager.py`
- `Obsidian/Engineering/API/contract-v1.md`
- `docs/operations/` (dont procédure backup volumes)
- `interfaces/api/routers/health.py`
- `interfaces/api/routers/knowledge.py`
- `interfaces/api/routers/plugins.py`
- `interfaces/api/routers/skills.py`
- `interfaces/api/routers/skills_import.py`
- `interfaces/bridge/`
- `tests/test_anthropic_cyber_importer.py`
- `tests/test_secret_redaction.py`
- `tests/test_skill_validation.py`

Règle de sécurité appliquée : aucune commande `git clean`, `git reset`, `git checkout` ou suppression n'a été lancée.

## 3. Architecture observée (réalité code)

- Racine sans dossier `runtime/`. Le runtime est orchestration Docker (voir README + compose).
- Règles d'architecture encodées : `importlinter` dans `pyproject.toml`, contrats 1 à 5, all `KEPT` lors de l'exécution `lint-imports`.
- Documentation d'architecture présente et volumineuse : ADR (`docs/architecture/adr`, `docs/adr`, `engineering/adr`), ESR (`docs/engineering/esr`), plans de migration Core/WebUI.
- Conventions de ports via `docker-compose.yml` et `docker-compose.ports.yml`; ne pas modifier.

### Cartographie répertoires de premier niveau (utile migration)

| Dossier | Rôle constaté |
|---|---|
| `core/` | Bibliothèques/intelligence métier (452 fichiers Python) |
| `interfaces/` | WebUI (Next.js), API (FastAPI), CLI, desktop, shell, canaux, outils bridge |
| `plugins/` | plugins système et packages |
| `deploy/` | Dockerfiles, compose, migrations PG, init SQL |
| `docs/` | documentation architecture, audits, API, sécurité |
| `engineering/` | ADR/ESR/standards |
| `tests/` | 753 fichiers `test*.py` (tests racine) |
| `examples/` | nombreux exemples, dont `open-webui` candidat |
| `models/`, `infrastructure/`, `sdk/` | stockage/modèles, observabilité, SDK |
| `core/rust/` | prototype Rust non versionné (artefacts build ~182 Mo) |

## 4. Matrice fonctionnelle synthétique

Détail ligne par ligne : `ETHAN_REBUILD_P0_TRACEABILITY_MATRIX.csv`.

Domaines clés :

| Domaine | Emplacement principal | État vérifié | Tests observés | Stratégie proposée |
|---|---|---|---|---|
| Auth / JWT / RBAC | `core/auth/`, `interfaces/api/auth.py`, `main.py` auth routes, migrations `003`/`006` | Présent + partiellement intégré | tests API parties | conserver Core, réutiliser pour interfaces |
| Providers LLM | `core/llm/provider_manager.py`, `core/llm/store.py`, `interfaces/api/routers/providers.py` | Présent, testé partiellement | contract tests providers | conserver, exposer une agrégation unique |
| Modèles | `core/llm/types.py` (`ModelInfo`), routers `models.py`/`model_router.py` | Présent mais fiche custom à préciser | `test_models_provider_boundary_api.py` | adapter plutôt que réimplémenter |
| Knowledge | `core/knowledge/manager.py`, router `v1.py` + `knowledge.py` (untracked) | Présent + évolution en cours | `test_knowledge_tree.py`, API tests | conserver Core, étendre notion collection |
| RAG | `core/rag/pipeline.py`, `core/rag/*`, API | Présent + tests stratégies | `test_rag_strategies.py` | conserver, stabiliser upload/processing |
| Memory / Facts | `core/memory/manager.py`, `core/facts/store.py`, API memory | Présent + doublon possible via `CoreWebUIStore` facts | API memory tests | gateway vers vrai manager, retirer doublon |
| Skills | `core/skills/manager.py`, `SkillStore`, SkillLab, nouveaux importers (untracked) | Présent + en évolution critique | `test_skill_validation.py` (untracked), API tests skills | conserver Core, stabiliser import/validation |
| Tools / MCP | `core/tools/*`, routers connections/integrations | Présent partiel | `test_tools_crud.py`, `test_mcp_servers.py` | conserver; étendre MCP |
| Agents | `core/agents/`, router `v1.py` agents | Présent | tests agent domains/resources | conserver; vérifier disponibilité exécution |
| Missions / Tasks | `core/missions/`, router missions/v1 | Présent | `test_mission_domains.py` | conserver |
| Chat pipeline | `core/chat/`, `CoreWebUIStore` chats, router `message.py`/`v1.py` | Présent | chat scope tests | stabiliser persistance et contracts |
| Files/Folders/Projects | `core/state/files.py`, `core/folders`, `core/projects`, routers | Présent | tests folders/projects | conserver avec stratégies de données |
| Event bus | `core/bus/*`, `core/events/*` | Présent mais stubs dans backends | pas de test évident de replay | corriger Python, puis Rust shadow mode |
| Plugins | `core/plugins/*`, `CoreWebUIStore`, routers plugins (untracked) | Présent + tests contrat | `test_plugins.py`, `test_skills_phases.py` | conserver Core source de vérité |
| Automations/Extensions | `core/scheduler/`, extensions routers | Présent partiel | `test_extensions_rbac_api.py`, `test_components_lifecycle_api.py` | adapter API manquante |
| Desktop/Voice | non implémenté dans repo | absent (docs mention planned) | aucune preuve | pas de migration à cette phase |
| Open WebUI candidate | `examples/open-webui` (v0.9.1) | Présent, modified checkout | upstream test suite | fork conditionnel sous réserve licence/marque |

## 5. Données persistantes et configuration

Détail dans `ETHAN_PERSISTENT_DATA_REGISTRY_P0.md`.

- Stores : PostgreSQL (users, providers custom, files metadata, memory, conversations, password reset, TOTP), Redis (live state/cache), NATS JetStream (events), CoreRecordStore composite, fichiers locaux (`/var/lib/ethan/*`), archives, backups PG, Qdrant/Chroma (optionnel).
- Env : `.env` + `.env.v2.example` incohérent (deux générations de config); `.secrets` existant; `OLLAMA_BASE_URL` pointe par défaut vers `host.docker.internal`; aucune reinstall d'Ollama requise ni lancée.
- Migrations : `deploy/postgres/migrations/001..009`, plus Alembic.
- Secrets : JWT, NATS token, Postgres/Redis passwords, API keys. L'audit n'a pas affiché de valeurs; seule la présence/clés a été inspectée.
- Volumes Docker : non visibles (permission daemon refusée). Aucune suppression tentée.

## 6. Tests, builds, erreurs connues

| Vérification | Commande | Résultat |
|---|---|---|
| Tests import racine | `pytest tests/test_python_imports.py` via `.venv` | 5 passed |
| Import-linter | `.venv/bin/lint-imports` | 5 kept, 0 broken, 1518 fichiers, 7094 dépendances |
| Ruff | non exécuté complet dans cet audit | succès partiel à confirmer par CI; code style line-length 100 documenté |
| Typecheck WebUI | `npm run typecheck` dans `interfaces/webui` | échec : `src/app/plugins/page.tsx` (3 erreurs signalées) |
| Collection tests API | `pytest interfaces/api/tests` | bloquée par `typing_extensions` (module 4.15.0, dist-info 4.15+4.16, anyio exige `sentinel`) |
| Docker | `docker ps` / `docker info` | permission refusée sur socket (utilisateur non docker group) |
| `npm run lint` WebUI | non exécuté (audit borné) | inconnu courant |

Important : ne pas interpréter l'existence de `.next/` comme une webapp fonctionnelle : c'est un artefact de build stale, incompatible avec le typecheck courant.

## 7. ADR / ESR et règles respectées

- ADR actifs relatifs à rebuild : `ADR-4004 core source of truth`, Cap manager, install on demand, data lifecycle, extension trust model. Principe essentiel : interfaces sont remplaçables.
- ESR existants : capability model, installation engine, Docker provisioning, local provisioning, WebUI capability manager, security model. Statuts `Implémenté`/`Partiel`. Ils ne doivent pas être réécrits, mais complétés pour hybride Rust/Python.
- `AGENTS.md` première loi : toute capacité intelligente appartient au Core. Toute modification refonte doit respecter.

## 8. Open WebUI — candidate d'interface

- Version inspectée : `0.9.1` (package.json).
- Remote : `https://github.com/open-webui/open-webui` ; commit sommet `0a8a620fb`.
- Licence : Open WebUI License + historique MIT/BSD selon commit. Clause de marque restrictive : pas de rebrand sans exception (≤50 utilisateurs sur 30 j.) ou permission écrite/licence enterprise. **Blocage si objectif = distribution ETHAN sous marque propre.**
- Upstream monitoring : projet actif (merge PR récents dans le checkout); maintenance d'un fork implique conflits réguliers. Évaluer "backend shim" vs "frontend rewrite" vs maintenir WebUI Next actuelle.
- Le checkout local Open WebUI n'est **pas propre** (modifications non documentées). Ne pas utiliser comme baseline de décision sans extraire un commit propre.

## 9. Risques bloquants identifiés

1. **Licence/marque Open WebUI** (P0) : rebrand potentiellement interdit.
2. **Décalage dépendances Python** (`typing_extensions`) : empêche la validation API via TestClient en local; risque CI/local.
3. **WebUI TypeScript cassé** : plugins page.
4. **Backends EventBus incomplets** : checkpoints/read durable non implémentés; lecture NATS/Redis fragile.
5. **Rust prototypes non fonctionnels** (`TODO`) : ne pas les présenter comme composants validés; 182 Mo d'artefacts non versionnés.
6. **Doublons API/CoreWebUIStore** pour memory/facts/skills/events/settings/providers/plugins : la refonte doit établir gateway vers managers réels.
7. **Configurations env incohérentes** (`.env.example` vs `.env.v2.example`) : risque de migration et confusion.
8. **État Git non propre** : travail en cours doit être commité/conservé avant toute bascule de socle.
9. **Docker inaccessible** à l'agent : pas de preuve d'état réel des conteneurs/volumes sur cette machine. Audit ops à faire avec permissions adéquates.

## 10. Composants : conserver / adapter / remplacer / retirer

- **Conserver** : `core/*` metabolique (managers réels), règles import-linter, migrations PostgreSQL, interfaces API gateway, CLI et ses tests.
- **Adapter** : API `/v1/*` pour brancher les gateways vers managers réels; modèles de données WebUI; upload/processing RAG; scripts CI Python 3.11.
- **Remplacer (cible)"** : backend Open WebUI par Core API si fork Open WebUI retenu; `CoreWebUIStore` doublon pour memory/skills/providers/plugins.
- **Retirer (plus tard, après tests)** : WebUI legacy React/Next si socle Open WebUI choisi; prototypes Rust TODO si non retenus; artefacts build.
- **Aucune action maintenant** : cette phase est audit uniquement.

## 11. Plan post-audit recommandé (P1/P2)

1. Nettoyer/committé l'état Git actuel (sans écraser) et retirer `core/rust/**/target` du suivi si ajouté (artefacts).
2. Résoudre dépendances Python (`typing_extensions`) et typecheck WebUI.
3. Extraire Open WebUI propre (commit sommet ou tag), valider licence/marque avec décision produit.
4. Établir un tableau de correspondance API par endpoint et runner de tests de non-régression.
5. Implémenter event store Python (read durable + checkpoints) avant Rust.
6. Shadow mode Rust seulement après critères de tests/perf documentés.
7. Ne pas migrer de données pendant P0.

## 12. Inconnues restantes (à résoudre)

- État réel des conteneurs/volumes et données production sur cette machine (Docker daemon non accessible).
- Disponibilité réelle des providers Ollama/OpenAI (aucune vérification live lancée).
- Couverture exacte des tests (pas de rapport de couverture exécuté dans cet audit).
- Statut d'exécution agents et schedulers (présence de code ≠ opérationnel).
- Choix business/licence pour marque Open WebUI.
- Backends particuliers (migrations appliquées ? index vector stores existants ?).
- Déduplication complète : quels éléments de `CoreWebUIStore` sont déjà remplacés par managers réels (inspection router v1 trop longue pour P0; la matrice cite l'évidence disponible).
