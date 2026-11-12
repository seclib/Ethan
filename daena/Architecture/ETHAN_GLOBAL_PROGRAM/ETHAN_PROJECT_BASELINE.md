# ETHAN_PROJECT_BASELINE

Date de mise à jour : 2026-11-05

## État Git initial

- Branche : `refactor/ethan-rebuild-p0`
- Dernier commit : `9e57d1c0efb6aaaf33a778b5ccaf3f97fb3ef118`
- Date commit : 2026-10-29 09:09:56 +0400
  - Message : `feat(knowledge): implement TechnicalMemoryWorker for background synchronization`
- Statut : `git status --short` = 615 lignes (modifications, ajouts, suppressions et non suivis).
- Classification : dépôt en état très sale/migration documentaire majeure en cours. Les modifications non commitées et non suivies doivent être préservées.

## Répertoires documentaires

- Obsidian présent et principal.
- `docs/` partiellement déplacé/retiré au profit d’Obsidian; plusieurs anciens fichiers apparaissent supprimés dans le statut.
- Rapports récents ajoutés : global audit, mission 19, mission 20.
- Anciennes archives non migrées apparaissent en `D` (`Odsidian/...`).

## Vérifications connues

- `tests/core/test_hrot_provider_gateway.py` : 14 passed (test réel) — batch gateway.
- Certaines parties runtime WebUI/API non exécutées complètement pendant cette mission.

## Inconnues

- État exact de fonctionnement de tous les menus et lifecycle app.
- État de tout le dépôt dans plusieurs environnements (Docker/machine distants).
- Statut final de migration Rust et migration docs.
