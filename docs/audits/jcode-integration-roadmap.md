# Feuille de route d'intégration JCode -> ETHAN / Atreus

Date : 9 novembre 2026
Mode : proposition uniquement. Aucune implémentation lancée. Validation explicite requise avant toute modification.

---

## 1. Stratégie générale

- JCode est une **source d'inspiration**, pas une dépendance.
- Toute capacité doit être réimplémentée dans le **Core ou Runtime ETHAN** avant exposition CLI/WebUI.
- Atreus n'est pas implémenté : préparer son Harness via des capacités Core réutilisables.
- Approche progressive : P0 sécurité, puis P1 structurant, puis P2 fonctionnel, puis P3 optionnel.

---

## 2. Propositions détaillées

### P0 — Sécurité / blocage critique

#### P0.1 Classification déterministe des commandes shell

- Ce que fait JCode : `jcode-command-risk` classe les commandes par blast radius (Safe/Low/Confirm/Catastrophic), gère wrappers, redirections, substitutions, cibles protégées, refus absolu.
- Implémentation JCode : `crates/jcode-command-risk/src/lib.rs`, `gate.rs`, `paths.rs`, `tokenize.rs`.
- Intérêt ETHAN : éviter destruction massive et ajouter une défense déterministe avant HROT.
- Composants concernés : `core/security/*`, `core/approval/engine.py`, `core/human_root/*`, outils d'exécution (`system_exec`).
- Adaptations : réimplémenter en Python ou service Rust isolé ; intégrer HROT comme autorité finale ; ne pas remplacer l'approbation humaine.
- Risques/coûts : complexité de parsing shell ; faux positifs/négatifs ; maintenance.
- Intégration progressive : d'abord mode shadow (log only), puis gate sur commandes à risque, puis blocage.
- Tests : corpus de commandes sûres/dangereuses, obfuscation, wrappers, redirections, substitutions, chemins home/root/credentials, tests de non-régression.

#### P0.2 Expiration des permissions de sessions mortes

- Ce que fait JCode : `expire_dead_session_requests` supprime les requêtes dont la session n'est plus active.
- Implémentation JCode : `crates/jcode-base/src/safety.rs`.
- Intérêt ETHAN : éviter accumulation et décisions obsolètes.
- Composants : `core/approval/engine.py`, `core/human_root/audit_log.py`.
- Adaptations : ajouter état de session active et expiration automatique.
- Tests : requêtes expirées/non expirées, audit trail.

#### P0.3 Validation déclarative des extensions (skills/plugins/MCP)

- Ce que fait JCode : applets validés avant rendu, MCP config fusionnée, OAuth explicite.
- Intérêt ETHAN : renforcer `core/plugins/*` et `core/skills/*`.
- Composants : `core/plugins/validator.py`, `core/skills/store.py`, `interfaces/api/routers/skills*.py`, `mcp`.
- Tests : imports interdits, schémas invalides, credentials non affichés.

### P1 — Amélioration structurante

#### P1.1 Compaction de contexte

- Ce que fait JCode : seuils 80/95%, conservation des 10 derniers tours, estimation tokens, gestion images/payloads, récupération 413.
- Implémentation : `crates/jcode-compaction-core/src/lib.rs`.
- Intérêt ETHAN : stabiliser les agents longs, éviter erreurs de taille.
- Composants : `core/memory/*`, agent executor, LLM providers.
- Adaptations : service Core de compaction, métriques, tests.
- Risques : perte d'information, coût LLM pour résumé.
- Intégration : d'abord métriques/estimation, puis compaction manuelle, puis automatique.
- Tests : seuils, images, payloads volumineux, récupération 413.

#### P1.2 Session leases et migration sûre

- Ce que fait JCode : epoch monotone, blocage des copies périmées, merge 3-way.
- Implémentation : `crates/jcode-storage/src/session_lease.rs`.
- Intérêt ETHAN : préparer des agents mobiles/reprises et éviter écrasements.
- Composants : sessions, state store, API.
- Adaptations : modèle de lease dans Core, pas de cloud propriétaire initialement.
- Tests : blocage moved-away, stale copy, ids invalides.

#### P1.3 Provider doctor / coverage / context audit

- Ce que fait JCode : diagnostic strict des checkpoints, coverage live, audit context window.
- Implémentation : `src/cli/args.rs` (`ProviderDoctor`, `AuthTest`, `ProviderTestCoverage`), `jcode-provider-doctor`.
- Intérêt ETHAN : améliorer diagnostic provider et onboarding.
- Composants : `core/providers/*`, CLI `provider`, `auth`, `model`.
- Adaptations : commandes CLI + endpoints Core.
- Tests : provider non configuré, clé invalide, context window.

#### P1.4 Ratchets CI et budgets qualité

- Ce que fait JCode : checks fmt, clippy, lockfile, warning budget, code/test size, panic/swallowed errors, boundaries, SDK parity.
- Intérêt ETHAN : réduire dette et régressions.
- Composants : `.github/workflows`, scripts, pyproject/ruff/pytest.
- Adaptations : ruff/mypy/pytest coverage, limites de taille, audit dépendances Python (`pip-audit`).
- Tests : CI verte.

### P2 — Amélioration fonctionnelle

#### P2.1 Ergonomie CLI avancée

- Sorties JSON/NDJSON systématiques, aliases, suggestions de commandes, `--read-only`, `--sandbox`.
- Composants : `interfaces/cli/*`.
- Tests : parsing, exit codes, JSON schema.

#### P2.2 Replay et inspection de sessions

- Replay timeline, export JSON/video, recherche dans historique.
- Composants : sessions, CLI, WebUI.
- Tests : replay d'une session réelle, export.

#### P2.3 Swarm / coordination multi-agents (Core-first)

- Swarm comme capacité Core (pas seulement CLI) : messages, rôles, statuts, limites.
- Composants : `core/agents/*`, futur Atreus Harness.
- Tests : coordination, conflits de fichiers, messages.

#### P2.4 MCP OAuth et test de connexion CLI

- Reprendre `mcp test/login/logout` pour ETHAN.
- Composants : `interfaces/cli/commands/mcp.py`, Core MCP.
- Tests : connexion, OAuth, credentials non affichés.

### P3 — Amélioration facultative

#### P3.1 Applets déclaratifs

- UI déclarative validée, placement, fallback.
- Composants : WebUI, application integration.
- Risque : complexité et dépendance à l'hôte.

#### P3.2 TUI riche (images inline, LaTeX, diff modes)

- Amélioration UX CLI.
- Composants : renderer CLI.

#### P3.3 Hibernation/reload serveur

- Handoff de sessions lors d'upgrade.
- Composants : daemon, runtime.

---

## 3. Composants ETHAN concernés (synthèse)

- `core/agents/manager.py`, `core/agents/executor.py`, `core/agents/types.py`
- `core/approval/engine.py`, `core/approval/types.py`
- `core/human_root/*`, `core/security/*`
- `core/memory/*`, `core/providers/*`
- `core/plugins/*`, `core/skills/*`
- `interfaces/cli/*`
- `interfaces/api/routers/*`
- tests `tests/core`, `tests/interfaces`, `tests/cli`

---

## 4. Risques transverses

- Ne pas casser l'architecture Core-first.
- Ne pas introduire de dépendance Rust sans décision ADR.
- Ne pas afficher de secrets.
- Ne pas automatiser des actions destructives sans HROT.
- Ne pas promettre de validation sans tests.

---

## 5. Critères de validation par phase

- P0 : tests de contournement shell, permissions, extensions ; audit trail ; pas de régression tests existants.
- P1 : métriques de contexte, compaction manuelle puis auto ; leases ; provider doctor.
- P2 : CLI JSON/NDJSON, replay, swarm, MCP OAuth.
- P3 : applets, TUI, reload.

---

## 6. Synthèse exécutive

### Les cinq meilleures idées à reprendre

1. Classification déterministe des commandes shell par blast radius + gate de justification.
2. Compaction de contexte avec seuils, conservation des tours récents et récupération 413.
3. Session leases à epoch monotone pour migration/reprise sûre.
4. Provider doctor / coverage / context audit.
5. Ratchets CI pour qualité, sécurité et taille.

### Les composants à ne surtout pas reproduire

1. Self-dev / rebuild et reload du binaire en production.
2. Surface CLI interne exposée comme commandes publiques.
3. Cloud move propriétaire avec transfert de credentials.
4. Applets host-specific sans isolation processus robuste.
5. Télémétrie par défaut non contrôlée.

### Améliorations prioritaires du CLI ETHAN

1. Sorties JSON/NDJSON systématiques et stables.
2. Diagnostic provider live (`doctor`, `coverage`, `context audit`).
3. Test de connexion MCP et OAuth CLI.
4. Suggestions de commandes et aide contextuelle.
5. Replay/inspection de sessions.

### Changements recommandés pour Atreus et son Harness

1. Implémenter Atreus comme capacité Core, pas comme CLI.
2. Ajouter un Harness de compaction et de gestion de contexte.
3. Intégrer la classification shell dans HROT.
4. Prévoir la coordination multi-agents (swarm) comme service Core.
5. Ajouter des leases pour la reprise/migration de sessions.

### Prochaines étapes et critères de validation

1. Valider cette feuille de route avec le mainteneur.
2. Créer des ADR pour P0.1 et P1.1.
3. Prototyper en mode shadow (sans blocage) et mesurer.
4. Ajouter les tests de contournement et de non-régression.
5. Ne passer en blocage qu'après validation E2E et revue sécurité.

Aucune implémentation ne doit commencer sans validation explicite.
