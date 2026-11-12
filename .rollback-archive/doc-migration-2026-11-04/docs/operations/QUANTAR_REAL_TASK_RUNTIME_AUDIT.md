# QUANTAR_REAL_TASK_RUNTIME_AUDIT

Date : 2026-11-04
Statut global : `PARTIALLY_VALIDATED`

## Contrôles

| Contrôle | Résultat | Preuve | Limitation |
|---|---|---|---|
| Service Core | IMPLEMENTED / UNIT_TESTED | `tests/core/test_quantar_real_task_runtime.py` | TradingAgents mocké |
| Task Runner | IMPLEMENTED / UNIT_TESTED / DOCKER_VALIDATED | sortie Docker `ticker is required`, `result.json` FAILED | Échec contrôlé uniquement |
| Propagate | IMPLEMENTED / UNIT_TESTED | `QuantarTaskService.run_task()` | Pas de fournisseur LLM configuré |
| Docker | IMPLEMENTED / DOCKER_VALIDATED | `docker build` image `quantar-runtime:real-task`, runtime inspect | Pas de bout en bout réel |
| Sécurité | IMPLEMENTED / DOCKER_VALIDATED | `docker inspect`: `User=1000:1000`, `ReadOnly=true`, `SecurityOpt=[no-new-privileges]`, `CapDrop=[ALL]`, limites appliquées | Réseau `bridge` sauf conteneurs lancés par le service avec `--network none` |
| Résultat JSON | IMPLEMENTED / UNIT_TESTED / DOCKER_VALIDATED | `result.json` atomique | Pas de résultat COMPLETED réel en Docker |
| Annulation | IMPLEMENTED / UNIT_TESTED | test `cancel_task` | Pas de démonstration in-flight |
| Nettoyage | IMPLEMENTED / DOCKER_VALIDATED | `docker ps -a` vide après exécution contrôlée | Meilleur effort |
| Tests | 13 tests Quantar réussis | `pytest tests/core/test_quantar_*.py` | Pas d'analyse financière réelle |

## Commandes exécutées

```bash
cd examples/quantar
docker build -t quantar-runtime:real-task .
docker run --rm --read-only --user 1000:1000 --security-opt no-new-privileges --cap-drop ALL \
  --cpus 1.0 --memory 512m --pids-limit 128 --tmpfs /tmp:size=64m,mode=1777 \
  -v /tmp/quantar-docker-invalid/data:/data/quantar \
  quantar-runtime:real-task
docker ps -a --filter 'name=quantar'
.venv/bin/python -m pytest tests/core/test_quantar_*.py
```

## Résultats observés

- Image construite : `quantar-runtime:real-task`.
- Ancienne image préservée : `quantar-runtime:phase39`.
- Docker contrôlé : sortie `ticker is required`, code sortie `1`, `result.json` avec statut `FAILED`.
- Aucun conteneur résiduel.
- Python : 13 tests réussis, 0 échec.

## Blocages

- Aucun fournisseur LLM configuré et autorisé.
- Aucune analyse financière réelle lancée.
- Réseau externe non exercé.

## Risques résiduels

- Le statut `COMPLETED` dépend désormais de l'existence et de la validité de `result.json` dans le mode Docker.
- L'annulation pendant une exécution active de `propagate()` ne peut pas interrompre immédiatement une bibliothèque tierce.
- La configuration réseau docker `bridge` par défaut n'est pas celle du service; le service utilise `--network none`.
