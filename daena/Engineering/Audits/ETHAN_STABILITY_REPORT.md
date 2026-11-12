# ETHAN_STABILITY_REPORT

## 1. Architecture actuelle
ETHAN fonctionne en tant qu'OS cognitif conteneurisé géré par Systemd et Docker Compose. L'architecture est répartie en plusieurs couches :
- **Systemd** : Gère l'initialisation de l'environnement (via `ethan-core`) et de la résilience (via `ethan-watchdog`).
- **Core Infrastructure** : Les services d'intermédiation et de stockage (NATS pour le bus d'événements, Redis pour l'état en direct et Postgres pour la persistance).
- **Control Plane** : L'API Gateway qui assure l'ingestion HTTP vers NATS.
- **Cognitive Engine** : Le Kernel (Orchestration des événements), assisté des modules cognitifs (Memory, Planner, Executive, Reflective, Autonomy...).
- **Interface** : Un frontend WebUI en Next.js.

## 2. Etat des services
Suite au déploiement initial via `systemctl start ethan-core`, voici l'état des composants évalués :
- **Systemd** : `ethan-core` a complété le lancement (`active (exited)` attendu pour oneshot). `ethan-watchdog` est fonctionnel via timer.
- **Infrastructure (Docker)** : `nats`, `postgres`, et `redis` sont **UP et Healthy**.
- **API Gateway (`ethan-api`)** : Initialement **Unhealthy** (Erreurs 404 sur les endpoints et locks SQLite). Fixé et en cours de stabilisation.
- **Cognitive Kernel (`ethan-kernel`)** : Initialement **Crashing (Restarting)** suite à une refonte de l'architecture. Fixé et en cours de stabilisation.
- **Modules cognitifs & WebUI** : Restés bloqués à l'état `Created` suite à l'attente de dépendances saines (`api` et `kernel`).
- **CLI** : Les commandes locales (`./ethan help`, `./ethan status`, `./ethan doctor`) sont pleinement opérationnelles.

## 3. Bugs trouvés
Durant l'audit système, nous avons identifié plusieurs régressions majeures bloquant le démarrage automatique de la boucle cognitive :

1. **Bug Configuration Redis** : La variable `REDIS_PASSWORD` était absente du `.env`, causant l'échec des healthchecks locaux du CLI.
2. **Bug Routage API** : Le `docker-compose.yml` pointait vers `api.main:app`, chargeant l'ancienne API obsolète (située dans `core/api/main.py`) au lieu de la nouvelle API (`interfaces/api/main.py`).
3. **Condition de course SQLite** : L'API Gateway était configurée avec 4 workers Uvicorn. Les 4 workers essayaient d'initialiser et de bloquer la base SQLite (`core/facts/store.py`) simultanément, provoquant des erreurs `database is locked`.
4. **Imports manquants dans le Kernel** : `core/bootstrap.py` tentait d'initialiser `CapabilityRegistry` sans l'avoir importé au préalable, ce qui entraînait une `NameError`.
5. **Régression de Typage Événementiel** : L'objet `Event` ayant été migré vers une structure `@dataclass` dans `core/ethan_types/event.py`, la méthode `.to_json()` (attendue par le bus NATS) avait disparu, causant une `AttributeError` immédiate.

## 4. Corrections appliquées
1. **Ajout des Variables Globales** : Injection de `REDIS_PASSWORD` dans le fichier `.env` pour assurer la cohérence des accès de tous les containers.
2. **Configuration Docker Compose (API)** :
   - Mise à jour du chemin Uvicorn : `uvicorn interfaces.api.main:app`.
   - Réduction des workers à `1` (`--workers 1`) pour contourner le goulot d'étranglement SQLite.
3. **Patch du Kernel** :
   - Importation correcte de `CapabilityRegistry` dans `core/bootstrap.py`.
   - Implémentation des méthodes de sérialisation manuelles (`to_dict` et `to_json`) directement dans la dataclass `Event`.
4. **Rebuild Intégral** : Lancement de la reconstruction de l'image de base (`ethan/python-base:latest`) pour propager les corrections Python au runtime des conteneurs.

## 5. Risques restants
- **Synchronisation au démarrage** : L'utilisation de bases SQLite dans un environnement hautement concurrent nécessite une implémentation robuste de verrous de fichiers si le système venait à s'étendre verticalement.
- **Incohérence des contextes Docker** : Le fait que `ethan-api` et `ethan-kernel` ne montent pas le code par volume (bind mount) rend la boucle de développement plus lente et sujette à l'oubli de reconstruction des images de base (`ethan/python-base`).

## 6. Score stabilité
**Score attribué : 8/10** (Après application des correctifs)
La stack dépendait fortement de ces quelques configurations, mais l'architecture sous-jacente (communication par événements, séparation stricte état/orchestrateur) est extrêmement résiliente.

## 7. Actions recommandées
- **Docker Mounts** : Utiliser un volume bind local pour injecter `core/` dans les conteneurs API et Kernel en environnement de développement pour éviter les reconstructions.
- **Migration Base de données Unique** : Les micro-BDD SQLite des modules internes (comme `facts`) devraient être consolidées vers PostgreSQL (déjà provisionné) pour une concurrence massive sans locks.
- **Amélioration du Doctor** : Ajouter des vérifications de l'état des imports Pydantic/Dataclass (e.g. tests unitaires simples) dans la pipeline CI ou directement dans le diagnostic `doctor`.
