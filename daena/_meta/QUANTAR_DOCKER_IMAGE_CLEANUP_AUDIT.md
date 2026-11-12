# QUANTAR — Audit des images Docker et préparation du nettoyage

Date : 2026-11-04
Statut : audit terminé, aucune suppression effectuée

## 1. Références applicatives

- Service Quantar utilise `quantar-runtime:latest` ;
- Compose actuel (`examples/quantar/compose.yaml`, `docker-compose.security.yml`) utilise `quantar-runtime:latest` ;
- L'ancienne référence `quantar-runtime:real-task` a été supprimée des fichiers actifs ;
- `quantar-runtime:phase39` et `main.py` ne sont plus référencés par le service actuel.

## 2. État des images

| Image | ID | Création | Utilisateur | Commande |
|---|---|---|---|---|
| `quantar-runtime:latest` | `75bed746e1c1` | 2026-11-04 | `1000:1000` | `python quantar_task_runner.py` |
| `quantar-runtime:real-task` | `8c3fb2a42299` | 2026-11-04 | `1000:1000` | `python quantar_task_runner.py` |
| `quantar-runtime:phase39` | `4999dad937e9` | 2026-11-03 | `1000:100` | `python main.py` |

Note : `real-task` est techniquement équivalent à `latest` selon les vérifications d'entrée. `phase39` n'est pas compatible avec l'exécution actuelle car point d'entrée `main.py`.

## 3. Conteneurs associés

Aucun conteneur référencé par les filtres d'ancêtres Docker (`docker ps -a --filter ancestor=...`) au moment de l'audit.

## 4. Cohérence image canonique

`quantar-runtime:latest` :
- UID/GID : `1000:1000`
- commande : `python quantar_task_runner.py`
- image basée sur `python:3.12-slim`
- dépendances TradingAgents installées
- conforme aux contraintes de durcissement existantes.

## 5. Recommandations de nettoyage (non exécutées)

- `quantar-runtime:real-task` : candidat au nettoyage manuel après confirmation, car références applicatives absentes.
- `quantar-runtime:phase39` : candidat à l'archivage ou suppression après validation humaine, car non compatible sans reroot.
- `quantar-runtime:latest` : conserver absolument.

Aucune commande de suppression n'a été lancée. Aucun impact sur le reste du système ETHAN.

## 6. risque

- suppression accidentelle de l'image active ;
- perte d'une revue/rollback implicite si les tags de phase sont retirés ;
- mismatch si `compose.yaml` est modifié indépendamment.

## Conclusion

Audit terminé, aucune suppression effectuée, rollback préservé.
