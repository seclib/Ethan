# QUANTAR — Audit technique préalable à la validation end-to-end (Phase 41)

Date : 2026-11-04
Statut : in_progress / PARTIALLY_VALIDATED
Périmètre : audit non destructif, aucune analyse financière réelle exécutée

## 1. Architecture constatée

Quantar est intégré à ETHAN comme application indépendante sous `examples/quantar/` et comme service Python unter `core/applications/` et `interfaces/api/routers/quantar.py`.

Composants principaux :

- `core/applications/quantar_service.py` : service de tâches en mémoire, statuts, exécution Docker locale;
- `core/applications/quantar_task_runner.py`, `quantar_docker_task.py`, `quantar_task_manager.py`, `quantar_runtime.py` : alias de compatibilité vers `quantar_service`;
- `examples/quantar/quantar_task_runner.py` : runner one-shot réel;
- `examples/quantar/tradingagents/` : dépôt TradingAgents vendored, version `0.7.1`;
- `examples/quantar/Dockerfile` : image isolée non-root;
- `examples/quantar/compose.yaml` : support Compose avec réseau interne;
- `core/plugins/quantar.py` : cycle de vie Docker Compose optionnel;
- `interfaces/api/routers/quantar.py` : endpoints tâches, statut, logs, résultats, annulation.

## 2. Cycle de vie observé

États canoniques :

`PREPARED -> QUEUED -> STARTING -> RUNNING -> COMPLETED / FAILED / CANCELLED`

Le runner conteneurisé exécute `TradingAgentsGraph(...).propagate(ticker, analysis_date)` une fois, sérialise `result.json`, puis termine. Aucun daemon résident n'est visible dans le design.

## 3. Composants examinés

### Service ETHAN

- création et préparation de tâches;
- démarrage/annulation;
- récupération du statut, journaux et résultats;
- exécution in-process si TradingAgents est disponible;
- exécution dans un conteneur via volume/workspace et subprocess;
- nettoyage `docker rm -f`.

### Runner Docker

- charge `task.json` atomiquement;
- propage via TradingAgents;
- écrit `result.json` atomiquement avec `.tmp` puis `replace`;
- codes de retour `0` en succès, `1` en échec;
- logs structurés JSON stdout/stderr.

### API

- endpoints publics sous `/v1/quantar` avec authentification read/write ;
- décision Read pour la majorité des lectures et démarrages ;
- permission PLUGINS pour cancel et lifecycle Compose.

## 4. Tests exécutés

Commande exécutée sans analyse réelle :

`.venv/bin/python -m pytest tests/core/test_quantar_service_phase36.py tests/core/test_quantar_real_task_runtime.py tests/core/test_quantar_security_phase37a.py tests/core/test_quantar_phase40.py`

Résultat : 11 passed, 1 warning.

Les tests exécutés sont des tests contrôlés : graphes factices, validation de service et sécurité du conteneur. Aucune exécution réelle de `TradingAgentsGraph.propagate()` n’a été observée.

## 5. Résultats et preuves recueillies

- TradingAgents importable dans ETHAN : False (module absent du venv).
- Version TradingAgents vendored : `0.7.1`.
- Docker daemon : accessible.
- Image locale : `quantar-runtime:real-task` présente.
- Image non-root : utilisateur `1000:1000`.
- Docker run command côté service impose read-only, réseau `none`, cap_drop ALL, no-new-privileges, limites CPU/mémoire/PID.
- Isolation : aucun socket Docker monté, aucun fichier sensible ETHAN monté, volume dédié.

## 6. Limites de validation

- Aucune exécution réelle démontrée.
- TradingAgents n'est pas installable avec les dépendances disponibles en environnement.
- Aucun fournisseur LLM n'a été validé.
- L'environnement n'a pas exécuté d'annulation sur un conteneur réel actuellement en cours.
- Le service Core est en mémoire uniquement : pas de restauration après redémarrage d'ETHAN.

## 7. Problèmes identifiés

1. TradingAgents absent de l'environnement ETHAN principal (`TRADINGAGENTS_AVAILABLE = False`).
2. Le service in-process ne peut pas exécuter de vraie analyse sans environnement TradingAgents opérationnel.
3. Provider selection se fait par nom uniquement (`TRADINGAGENTS_LLM_PROVIDER` / `_configure_provider`), sans démonstration de secret HROT ni de credential passing contrôlé.
4. Annulation en-process telle que codée n'arrête qu'un conteneur déjà nommé; elle ne tue pas nécessairement un processus actif dans le runner.
5. Les résultats sont persistés dans le workspace, mais le service ne recharge pas les tâches après redémarrage d'ETHAN.
6. Certaines alias de compatibilité sont volontairement massifs et peuvent masquer un problème d'API.
7. La plateforme WebUI existe pour Qurantar, mais n'est pas une preuve d'exécution réelle.
8. Les images construites sont exécutées en `--user 1000:100` côté service, alors que l'image est construite en `1000:1000`; ce point doit être documenté et réconcilié si l'UID/GID compte.

## 8. Risques de sécurité

- Pas de clé LLM détenue côté conteneur Quantar dans le code examiné.
- Réseau `none` par défaut dans `run_task_in_container`.
- Docker est durci côté commande.
- Le provider sélectionné dans la payload est une valeur de nom, pas un secret.
- Les logs contiennent stdout/stderr : risque d'exposition si TradingAgents ou dépendances impriment des secrets ; la politique de masquage doit être renforcée.
- `_configure_provider` écrit dans `os.environ`; environnement du conteneur doit être audité pour éviter fuites.

## 9. Blocages

- Pas de provider LLM démontré.
- Pas de test réel TradingAgents dans l'environnement ETHAN.
- Pas de preuve end-to-end.
- Pas de récupération après redémarrage.

## 10. Recommandations par priorité

P1:
- brancher un environnement TradingAgents (version vendored `0.7.1`) avec fournisseur LLM de test validé, sans stocker de secret;
- mettre en place HROT provider gateway;
- exécuter une vraie tâche en conteneur et archiver la preuve.

P2:
- persister et recharger les résultats/tâches après redémarrage;
- rendre l'annulation réelle (SIGTERM/Pkill conteneur + kill process);
- ajouter masquage secrets dans logs.

P3:
- clarify API permissions et alias;

## 11. Critères pour passer à la validation end-to-end

- une tâche réelle sans fake graph;
- provider autorisé et secret par mécanisme contrôlé;
- conteneur isolé validé;
- logs masqués;
- résultat réel persisté et récupérable;
- preuve de statut COMPLETED ou FAILED honnête.

## Statut final

`PARTIALLY_VALIDATED` — moteur et sécurité implémentés et testés de manière contrôlée, mais aucune exécution réelle validée.
