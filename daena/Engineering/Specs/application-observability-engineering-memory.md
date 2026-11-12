# Spécification — Observabilité et Engineering Memory (MEM-014 Phase 7)

## Schéma d'événement

Version courante : `1.0.0`.

Champs obligatoires : `event_id`, `schema_version`, `app_id`, `instance_id`, `timestamp`, `event_type`, `operation`, `status`, `provenance`.

## Provenance et preuves

Les références de preuve sont conservées ; les secrets sont rejetés ou masqués.

## Filtrage Engineering Memory

Seuls les événements significatifs avec preuves et origine vérifiée sont promus.
Les logs opérationnels ne sont pas copiés automatiquement.
