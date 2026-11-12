# ETHAN — Architecture cible P1 (hybride Rust + Python, socle Open WebUI étudié)

- **Date** : 2026-10-29
- **Prérequis** : `docs/audit/ETHAN_REBUILD_P0_AUDIT.md`
- **Statut** : proposition documentée, aucun code implémenté
- **Légende** :
  - **Fait observé** : vérifié dans le dépôt ou par commande.
  - **Hypothèse** : à confirmer par tests/document.
  - **Choix proposé** : décision cible proposée par cet architecte.

## 1. Principes non négociables (faits/propositions)

1. **Fait observé** : `AGENTS.md` impose que Core et Runtime soient la source de vérité ; les interfaces révèlent sans définir.
2. **Fait observé** : import-linter impose Core indépendant de interfaces/plugins/examples/tests.
3. **Choix proposé** : construire le nouveau socle en parallèle, sans supprimer l'existant jusqu'à équivalence prouvée.
4. **Choix proposé** : ne pas déplacer de ports; WebUI reste prévu sur 3001, API 8000, kernel 8080.
5. **Choix proposé** : Odin reste externe; ETHAN déclenche/supervise seulement son cycle de vie.
6. **Fait observé/proposé** : le Human Root of Trust existe dans `core/human_root`; la clé privée d'autorisation ne doit pas être transmise aux agents/modèles/skills/plugins/MCP.

## 2. Composants et frontières

| Composant | Responsabilité | Dépendances autorisées | Interdictions |
|---|---|---|---|
| Core Python | Intelligence métier, managers, stores, règles | stdlib, libs Python déclarées, DB/cache, bus | import interfaces/plugins/examples/tests |
| Core Rust (expérimental) | services natifs performance/sûreté via FFI | contrat JSON, PyO3 | modifier contrats Core par côté, code métier |
| API FastAPI | contrat HTTP, auth context, delegation | Core uniquement | logique métier, accès direct providers |
| Event runtime | NATS/Redis/Postgres orchestration | services versionnés | logique métier |
| WebUI adapter | rendu/UX/config/déclenchement | API HTTP | accès DB/infra ou logique métier |
| CLI/Desktop | mêmes capacités | API HTTP | idem |
| CapsManager/Odin lifecycle | cycles de vie externes | Core services autorisés | implémentation d'Odin dans ETHAN |

### 2.1 Human Root of Trust

- **Fait observé** : `ApprovalEngine` et `HumanRootOfTrust` existent.
- **Proposition** :
  - La clé d'autorisation privée ou secret racine reste dans un composant humain/gardé (`core/human_root` + secret manager/env).
  - Agents/skills/plugins reçoivent des capacités dérivées révocables (tokens scoppés/minimales), jamais la racine.
  - Toute action destructrice/privilegiée passe par approval/catégorisation et audit log append-only (`core/human_root/audit_log.py`).
  - Accès MCP/stdio sandbox selon env allowlist/policy déjà documentée.

## 3. Core Hybride Rust + Python

### 3.1 Faits observés
- Un prototype Rust health utilise le port par défaut 8080 (`core/rust/ethan_health`).
- Le crate event store expose `write/read/save_checkpoint/replay`, mais toutes ces fonctions contiennent `TODO`; il renvoie des valeurs factices.
- Contrat bridge interdit de modifier `nats_bus.py`, `router.py`, `interface.py`, `kernel.py` pendant l'expérimentation.

### 3.2 Stratégie proposée

- **Phase A (Python parity)** : corriger le backend Python `read` durable, checkpoints et bornage.
- **Phase B (shadow mode)** : Rust écrit/lit en parallèle et compare hash/count/latence.
- **Phase C (feature flag)** : bascule échangeable par configuration, retour arrière possible.
- **Phase D (benchmark gates)** : bascule uniquement si zéro perte et ≥30-50% gain avec budget SLO.
- **Hypothèse** : Rust d'abord pour event store uniquement, pas pour logique métier.
- **Choix** : ne pas inclure Rust dans le chemin critique tant que checkpoints et rétention ne sont pas parity-testés.

### 3.3 Frontières FFI
- Format canonique JSON (events `{id,type,timestamp,payload,context}`).
- PyO3-friendly, sans shared mutable state non contrôlé.
- Interface Rust doit rester non-bloquante et testée unitairement.
- Retour arrière par configuration backend.

## 4. API contrats versionnés

### 4.1 Principes

- Contrat HTTP canonique ETHAN = `/v1/*` et `/v2/*` uniquement par évolution explicite; pas de duplication.
- Invariant de réponse : structure documentée `docs/api/contract-v1.md` (nouveau fichier non suivi, à relire/valider).
- Erreur JSON uniforme:
  ```json
  { "code": "string", "message": "human-readable", "details": {}, "request_id": "uuid", "retryable": false }
  ```
- Idempotence pour tâches longues et mutations.
- Auth par JWT Bearer validé au gateway. Pas de clé racine.
- Pagination cursor-based pour listes volumineuses.
- Audit trail pour changements sensibles.

### 4.2 Contrats proposés par capacité

| Capacité | Route canonique | Manager Core |
|---|---|---|
| Auth | `/auth/*` | core auth |
| Providers | `/providers` | ProviderManager |
| Models catalog | `/models` | ProviderManager + modèles custom store |
| Knowledge | `/v1/knowledge` | KnowledgeManager / collection |
| RAG documents/retrieve/context | `/v1/rag/*` | RAGPipeline |
| Memory | `/v1/memory/*` | MemoryManager |
| Skills | `/v1/skills/*` | SkillManager/SkillStore |
| Tools/MCP | `/v1/tools/*` | ToolManager |
| Missions | `/v1/missions/*` | MissionManager |
| Agents | `/v1/agents/*` | AgentManager |
| Files | `/files` | FileStore |
| Events/jobs | `/v1/jobs/*` | orchestration Core |
| Health | `/health/*` | diagnostics |

- **Choix** : toutes les interfaces passent par API HTTP; pas d'accès direct internals.
- **A éviter** : conserver doublon `/v1/providers` et records `webui_*` non liés aux managers réels.

### 4.3 Identifiants et erreurs

- UUID v4/v7 pour entités, tenant/user scoping explicite.
- Codes erreur stables `ETHAN_*` versionnés.
- HTTP statuses alignés à la sémantique (`401`, `403`, `404`, `409`, `422`, `503`).
- Pour états non initialisés, `503 service not ready`.
- Timeout standard pour tâches longues et `Retry-After`.

### 4.4 Tâches longues et progression

- Création de job idempotent avec `Idempotency-Key`.
- États : `queued`, `running`, `succeeded`, `failed`, `cancelled`.
- Événements de progression via SSE/WebSocket gateway (pas de logique métier UI).
- Cancel scopes et retries bornés.
- Journalisation sans secrets.

### 4.5 Observabilité et audit

- logs JSON `text/json/dual`.
- traces OTLP optionnelles.
- métriques Prometheus.
- audit events append-only pour actions auth/permissions/data destructive.
- redaction patterns présents dans `core/security`.

## 5. Persistance, migrations et sauvegardes

### 5.1 Stratégie cible

- PostgreSQL reste source durable pour auth/providers/knowledge/metas/messages.
- Redis pour live/state/cache.
- NATS JetStream pour events.
- CoreRecordStore composite pour compatibilité progressive.
- Migrations versionnées et testées; rollback scripté.
- Backup Postgres quotidien (`pg_backup` déjà dans compose) + archive locale + checksum.
- Restauration documentée en runbook (`docs/operations/backup-volumes-procedure.md`).

### 5.2 Migration progressive sans perte

- Ne pas copier de données hors procédure.
- Shadow reads/writes pour nouvelles structures.
- Table de correspondance anciens IDs -> nouveaux IDs.
- Feature flags et temps de bascule.
- Plan de reprise et validation par checksum/comptage/tests.

### 5.3 Retour arrière

- Snapshot pré-migration.
- Toggle config pour revenir à l'implémentation Python d'event store.
- Pas de destructif pendant phase parallèle.
- Retour arrière documenté avant bascule.

## 6. Open WebUI comme frontend candidat

### 6.1 Faits observés

- version `0.9.1`.
- remote upstream actif.
- worktree local modifié.
- licence Open WebUI + historique MIT/BSD.
- branding clause restrictive.

### 6.2 Comparaison proposée

| Critère | Open WebUI | WebUI ETHAN actuelle (Next.js) |
|---|---|---|
| UX richesse | élevée (chat, RAG, tools, functions, settings) | présente, modulaire, tests unitaires |
| Stack | SvelteKit (migration TS/React -> Svelte) | Next.js/React/Tailwind actuel |
| Coût maintenance fork | élevé (divergence upstream) | contrôle interne |
| Licence/marque | contrainte majeure | Apache 2.0 projet |
| Backend | à remplacer/proxier vers ETHAN Core | déjà branché sur Core |
| Intégration Core | à adapter massivement | déjà aligné |
| Tests existants | upstream e2e | tests unitaires ciblés |

### 6.3 Recommandation proposée (choix, pas fait)

- **Option proposée** : ne pas rebrander un fork Open WebUI comme produit final sans décision juridique.
- Pister une voie hybride :
  1. Valider juridiquement usage/marque et nombre utilisateurs;
  2. Sinon conserver WebUI Next.js actuelle et importer uniquement composants UX/adaptations;
  3. Si Open WebUI retenu, adopter backend shim vers ETHAN Core + plan de divergence upstream explicite.
- **Décision bloquante** : licence/marque doit être documentée avant implémentation.

### 6.4 Gouvernance fork (si retenu)

- pin commit/tag;
- changes isolés dans couche d'adaptation;
- automated sync tests;
- documented conflicts resolution.

## 7. Sécurité, skills, tools, plugins, agents, MCP

### 7.1 Frontières de confiance

- Human root: validation et signature d'actions sensibles.
- Core: politique et exécution.
- Runners: MCP/tool executors via allowlist/sandbox.
- Interfaces: uniquement déclenchement et visualisation.
- Agents/modèles: capacités dérivées, pas de secrets racines.

### 7.2 Politique d'exécution

- Skills importées validées (`core/skills/validation.py`, importer an-th (untracked)).
- Tools exécutés côté Core, pas navigateur.
- MCP types manquants à définir côté Core (auth, headers, ACL).
- Plugins versionnés, activation/inactivation, seed defaults.
- Destructive actions: approval exact et confirmation.
- Audit trail obligatoire.
- Secret redaction déjà présent (`tests/test_secret_redaction.py` nouveaux tests).

### 7.3 Auth et permissions

- RBAC par verbes/modes selon ESR-006.
- JWT secret sécurisé, rotation planifiée.
- API keys scoppées, expiration.
- Pas d'administrative bypass silencieux.
- Audit log append-only.

## 8. Stratégie de tests

| Niveau | Cible | Preuve | Gate |
|---|---|---|---|
| Unit | managers, stores,-policy | pytest unit | bloquant CI |
| Contract API | routes/response shapes/errors | tests directes + TestClient | bloquant |
| Integration | DB/cache/bus, import/exports | pytest avec services test | bloquant |
| E2E | parcours WebUI/API | Playwright/Cypress | nightly/release |
| Security | injection, RBAC, secrets, destructive confirm | tests ciblés | bloquant |
| Non-régression | comparaison P0 endpoints | golden snapshots | release |
| Performance | latence/throughput/retry | benchmarks | SLO |
| Rust parity | Python vs Rust event store | shadow tests | migration |

### 8.1 Environnement

- Résoudre dépendance Python (`typing_extensions`) avant tests API.
- CI versions Python 3.10-3.13 comme déclaré.
- Node/TypeScript gate pour WebUI.
- Docker daemon permis dans CI pour tests d'intégration.

## 9. Indicateurs performance/fiabilité (avant/après)

- Latence p95 message complet.
- throughput événements bus (msgs/s).
- latence publication event.
- taux d'erreur API (%).
- taux retry successful.
- temps restore backup.
- memory RSS stable sous charge.
- zéro perte d'événements.
- test couverture minimale et regression pass count.
- temps boot services p95.
- temps réponse health détaillé.

Baseline doit être capturée avec scripts existants (CLI benchmarks) avant toute bascule.

## 10. Migration ordonnée (P2+)

1. Normaliser état Git et artifacts.
2. Corriger dépendances/tests.
3. Stabiliser Python event store.
4. Établir API contract v1 validé et tests.
5. Brancher doublons vers managers réels (memory/skills/providers/plugins) via gateways.
6. Stabiliser knowledge/RAG upload et collections.
7. Implémenter MCP type/auth.
8. Odin lifecycle adapter (pas Odin lui-même).
9. Shadow Rust event store + parity tests.
10. Candidat UI décision licence et migration UX.
11. Basculer sous flag + retour arrière.
12. Retirer legacy progressivement seulement après preuves.

Critères d'acceptation par étape: tests verts, contract tests, migration rollback validé, zéro perte données, metrics SLO, review ADR.

## 11. Risques (registre)

| ID | Risque | Gravité | Mitigation |
|---|---|---|---|
| R1 | Licence/marque Open WebUI | critique | décision juridique/documentée |
| R2 | event store perte données | critique | parity/shadow/rollback |
| R3 | doublons silencieux | élevé | gateway + dépréciation |
| R4 | auth secret faible | critique | secret management + audit |
| R5 | UI incompatible | élevé | contract tests |
| R6 | test environment drift | moyen | pin deps + CI |
| R7 | port conflicts | moyen | config immutable |
| R8 | données locales perdues | critique | backup/restore runbooks |

## 12. Décisions documentées mais non implémentées

- ADR-4006 propose cette cible.
- ADR-4007 pose le gate licence Open WebUI.
- Aucune implémentation de fonctionnalité ne commence avant validation des blocants.
