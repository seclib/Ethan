# QUANTAR_REBUILD_INVENTORY

Date : 2026-11-03

## Répertoires inspectés

- Source : `/home/fatsio/AI/TradingAgents`.
- Destination : `/home/fatsio/AI/Ethan/examples/quantar`.

## Décision

Migration contrôlée avec `rsync`, sans modification du dépôt source.
Copie sans `.git`, sans caches, sans environnements virtuels, sans secrets.
`vendor/` sera retiré une fois la nouvelle image construite avec succès.
