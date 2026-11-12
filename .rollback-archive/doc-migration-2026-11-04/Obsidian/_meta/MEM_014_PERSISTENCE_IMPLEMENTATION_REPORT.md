# MEM_014_PERSISTENCE_IMPLEMENTATION_REPORT

Date : 2026-11-03
Phase : MEM-014 Phase 8 — Persistance durable
Statut : implémenté et testé localement

## État initial et constats

Les registres de permissions, événements, conformité et cycle de vie étaient en mémoire. L'audit global a signalé la perte d'état au redémarrage.

## Architecture retenue

SQLite standard, mode WAL, stockage SQLite avec migrations versionnées, exposé par `ApplicationStateStore`.

## Composants modifiés

- `core/applications/persistence.py` (nouveau)
- `core/applications/permissions.py`
- `core/applications/compliance.py`
- `core/applications/observability.py`
- `core/applications/resilience.py`
- `core/applications/__init__.py`

## Tests exécutés

- `tests/core/test_application_persistence_phase8.py` : 7 passed
- Régression complète complémentaire à exécuter par le pipeline global

## Garanties

- Enregistrement et relecture après redémarrage.
- Transactions SQLite.
- Migrations versionnées.
- Aucun ALLOW fondé uniquement sur la présence d'un enregistrement.
- Preuves HROT restent obligatoires.

## Limites restantes

- mono-processus / pas de réplication ;
- cryptographie de production encore absente ;
- adaptateurs externes non créés.

## Risques non résolus

- accès complet à la base par un attaquant n'est pas détectable sans mécanisme cryptographique externe.
