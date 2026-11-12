# Spécification — Persistance durable MEM-014 (Phase 8)

## Technologie retenue

SQLite standard, mode WAL, accès via `ApplicationStateStore`.

## Tables principales

- `permission_requests`
- `permission_grants`
- `authorization_decisions`
- `compliance_reports`
- `lifecycle_states`
- `observability_events`
- `schema_migrations`

## Interfaces

- `save_record`, `load_records`, `delete_record`
- `save_lifecycle_state`, `load_lifecycle_states`
- `transaction` (connexion SQLite sous-jacente)

## Règles

- Aucune autorisation automatique fondée sur la seule présence d'un enregistrement.
- Toute reprise doit repasser par HROT et les contrôles de conformité nécessaires.
- Les autorisations expirées ou révoquées restent refusées après redémarrage.
