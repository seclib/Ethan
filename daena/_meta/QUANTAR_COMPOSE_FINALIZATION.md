# QUANTAR — Finalisation du déploiement Docker Compose

Date : 2026-11-04

## Modification

- `core/plugins/quantar.py` : `QuantarService.get_status` surclasse l'état `not_installed` en `installed_stopped` lorsque l'image `quantar-runtime:latest` est présente.
- Aucune migration massive, aucun nouveau conteneur.

## Comportement

- L'instance Compose reste optionnelle et pilotée par le backend.
- L'API lifecycle Quantar reflète `installed_stopped` au lieu de `not_installed`.
- Aucune analyse réelle n'est démarrée automatiquement.
- `network: none` et les restrictions Docker conservées.

## Tests

- `test_quantar_service_phase36.py` : passés ;
- `test_quantar_pilot_phase35.py` : passés.
