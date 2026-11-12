# ETHAN — Runbook P1 (installation, sauvegarde, restauration, diagnostic, rollback)

## Installation (audit/socle parallèle)
1. Vérifier prérequis: Python 3.10-3.13, Node, Rust toolchain, Docker.
2. Ne pas changer de port existant.
3. Préserver Ollama hôte.
4. Travailler sur branche dédiée (déjà `refactor/ethan-rebuild-p0`).
5. Valider état Git sans écraser.

## Sauvegarde
- Backup PostgreSQL (`backup.sh`), Redis snapshot, NATS stream, core data dirs, .env/.secrets.
- Export checksums.
- Conserver `.rollback-archive`.

## Restauration
- Restaurer DB + volumes + data dirs.
- Vérifier migrations et counts.
- Lancer health checks.

## Diagnostic
- `lint-imports`, pytest, ruff, npm typecheck.
- Docker daemon logs.
- `/health/detailed`.
- provider health checks.

## Rollback
- Toggle feature flags Rust vers Python.
- Restaurer backup pré-migration.
- Conserver mapping anciens/nouveaux IDs.
- Ne pas supprimer données.
