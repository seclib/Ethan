# QUANTAR — Normalisation de l'image Docker

Date : 2026-11-04
Statut : implémenté et partiellement validé

## 1. Dockerfiles identifiés

- `examples/quantar/Dockerfile` : runtime actuel, point d'entrée `python quantar_task_runner.py`, utilisateur `1000:1000`.
- `examples/quantar/docker-compose.security.yml` : configuration de sécurité ancienne, pas de point d'entrée propre.

## 2. Modifications

- `core/applications/quantar_service.py` utilise désormais `quantar-runtime:latest` par défaut.
- `examples/quantar/compose.yaml` et `docker-compose.security.yml` pointent vers `quantar-runtime:latest`.
- Construction unique : `docker build -t quantar-runtime:latest examples/quantar`.

## 3. Images

- anciennes images conservées sans suppression :
  - `quantar-runtime:phase39`
  - `quantar-runtime:real-task`
- image canonique construite :
  - `quantar-runtime:latest`

## 4. Validation

- point d'entrée vérifié : `python quantar_task_runner.py`
- UID/GID vérifié : `1000:1000`
- TradingAgents importe correctement (version 0.7.1)
- le runner expose correctly les événements et gère un échec sans données financières réelles
- tests Quantar concernés : 23 passés

## 5. Risques résiduels

- l'image nécessite un répertoire home accessible en écriture pour le cache TradingAgents (`/home/quantar/.tradingagents`) lors de l'exécution réelle ;
- Ollama ou réseau externe peut être requis par la contrainte data provider, mais `quantar_service.py` utilise `network: none` par défaut ;
- anciennes images demeurent et attendent décision humaine avant nettoyage ;
- aucun object `latest` remote n'est maintenu.

## 6. Conclusion

La normalisation est en place. Le mécanisme de build est centralisé et la référence canonique est utilisée. Le statut Quantar reste PARTIALLY_VALIDATED.
