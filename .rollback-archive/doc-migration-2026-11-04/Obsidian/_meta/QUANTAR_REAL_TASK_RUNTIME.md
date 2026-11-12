# QUANTAR_REAL_TASK_RUNTIME

Date : 2026-11-04
Statut : implémentation structurelle complétée ; validation runtime réelle partiellement bloquée par l'environnement

## Résumé

Quantar n'est plus présenté comme un conteneur permanent inerte. Le runtime applicatif appelle réellement `TradingAgentsGraph.propagate()` une fois par tâche, sérialise le résultat structuré, puis termine.

Sources principales :

- `core/applications/quantar_service.py`
- `examples/quantar/quantar_task_runner.py`
- `examples/quantar/Dockerfile`
- `examples/quantar/compose.yaml`
- `examples/quantar/docker-compose.security.yml`

## Service ETHAN

`QuantarTaskService` (alias `QuantarService`) implémente les états de tâche :

`PREPARED`, `QUEUED`, `STARTING`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`.

Capacités exposées :

- `create_task`
- `start_task`
- `run_task`
- `run_task_in_container`
- `cancel_task`
- `get_task`
- `list_tasks`
- `get_logs`
- `get_result`
- `cleanup_task`
- compatibilité ascendante avec `prepare_analysis`, `start_analysis`, `run_analysis`, `get_analysis`, `get_results`

Le cycle d'exécution appelle directement `TradingAgentsGraph(...).propagate(ticker, analysis_date)` et conserve le résultat structuré sans troncature artificielle.

## Runner Docker

Entrypoint :

```bash
python quantar_task_runner.py --task-file /data/quantar/task.json --result-file /data/quantar/result.json
```

Variables d'environnement équivalentes :

- `QUANTAR_TASK_FILE`
- `QUANTAR_RESULT_FILE`

Le runner :

1. lit un fichier JSON de tâche ;
2. valide `ticker` et `analysis_date` ;
3. charge la configuration TradingAgents ;
4. appelle réellement `TradingAgentsGraph.propagate()` ;
5. sérialise `task_id`, ticker, date, décision, rapports, métadonnées, logs ;
6. écrit `result.json` atomiquement ;
7. termine avec code `0` en succès, code `1` en échec.

Aucune boucle permanente, aucun `time.sleep(365*24*3600)`, aucun faux processus permanent ne remplace l'exécution réelle.

## Docker

Image dédiée : `quantar-runtime:real-task`.

Construction :

```bash
cd examples/quantar
docker build -t quantar-runtime:real-task .
```

Durcissement conservé :

- utilisateur non-root `1000:1000` ;
- `read_only: true` ;
- `cap_drop: ALL` ;
- `no-new-privileges:true` ;
- limites CPU `1.0`, mémoire `2g`, pids `256` ;
- volume dédié `quantar_task_data:/data/quantar` ;
- réseau isolé interne ;
- aucun socket Docker monté ;
- aucun fichier personnel ETHAN monté ;
- pas de healthcheck HTTP ;
- pas de démarrage automatique au lancement d'ETHAN.

## Test contrôlé sans requête financière réelle

Le test doit d'abord utiliser un moteur factice :

```python
class FakeGraph:
    def __init__(self, debug=False, config=None):
        self.debug = debug
        self.config = config

    def propagate(self, ticker, date):
        return "ok", {"decision": f"HOLD {ticker} {date}"}
```

Puis vérifier :

- statut final `COMPLETED` ;
- appel effectif à `propagate()` ;
- résultat `decision == "HOLD NVDA 2026-09-01"` ;
- métadonnées et logs persistés ;
- code de sortie du runner ;
- nettoyage du conteneur.

Un simple import TradingAgents n'est pas un test moteur.

## Commande Docker tâche ponctuelle

```bash
docker run --rm --read-only \
  --user 1000:1000 \
  --security-opt no-new-privileges \
  --cap-drop ALL \
  --cpus 1.0 --memory 2g --pids-limit 256 \
  --tmpfs /tmp:size=256m,mode=1777 \
  -v quantar_task_data:/data/quantar \
  -e QUANTAR_TASK_FILE=/data/quantar/task.json \
  -e QUANTAR_RESULT_FILE=/data/quantar/result.json \
  quantar-runtime:real-task
```

## Blocages réels documentés

- Docker daemon inaccessible dans cet environnement : `permission denied` sur `/var/run/docker.sock`.
- TradingAgents n'est pas installé dans le venv ETHAN de cet environnement ; le test moteur réel doit être exécuté avec un PYTHONPATH pointant vers `/home/fatsio/AI/TradingAgents` et un fournisseur LLM disponible.
- Aucune clé API LLM validée dans cet environnement ; aucune analyse réelle externe n'a donc été lancée.
- HROT/authentification opérateur restent hors scope et aucune secret n'a été stocké.

## Limites

- Le service in-process dépend de la disponibilité réelle de TradingAgents.
- Le nettoyage Docker est implémenté comme meilleur effort via `docker rm -f`.
- Les résultats dépendent du fournisseur LLM configuré et ne sont pas garantis déterministes.

## Statuts vérifiés le 2026-11-04

- Service Core : IMPLEMENTED / UNIT_TESTED
- Task Runner : IMPLEMENTED / UNIT_TESTED / DOCKER_VALIDATED
- Propagate : IMPLEMENTED / UNIT_TESTED
- Docker : IMPLEMENTED / DOCKER_VALIDATED
- Sécurité : IMPLEMENTED / DOCKER_VALIDATED
- Résultat JSON : IMPLEMENTED / UNIT_TESTED / DOCKER_VALIDATED
- Annulation : IMPLEMENTED / UNIT_TESTED
- Nettoyage : IMPLEMENTED / DOCKER_VALIDATED
- Tests : 13 réussis

Statut global : PARTIALLY_VALIDATED
Statut OPERATIONAL : non atteint (pas de fournisseur LLM réel configuré)
