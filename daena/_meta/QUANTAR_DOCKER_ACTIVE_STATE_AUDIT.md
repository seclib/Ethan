# QUANTAR — Audit du déploiement Docker et du cycle de vie

Date : 2026-11-04
Statut du déploiement : inactif (aucun conteneur actif)

## 1. Images présentes

- `quantar-runtime:latest` : `sha256:dc8f2c77c463`, créée 2026-11-04, 522MB.

Aucune autre image Quantar n'est référencée sur le daemon au moment de l'audit.

## 2. Conteneurs

Aucun conteneur actif ou arrêté détecté pour Quantar.

Les vérifications Docker `docker ps -a` et `docker ps -a --filter ancestor=...` ne retournent aucun conteneur Quantar.

## 3. Compose

Fichier réel : `examples/quantar/compose.yaml`

Nom de projet par défaut `quantar` si démarré avec `docker compose --project-name quantar`.

Le compose définit :
- `quantar-task` one-shot ;
- `read_only: true` ;
- utilisateur `1000:1000` ;
- `cap_drop: ALL` ;
- `no-new-privileges:true` ;
- `networks: ethan_quantar_isolated` (interne, non attachable) ;
- pas de healthcheck ;
- pas de mode autostart.

Il n'est pas référencé dans `docker-compose.yml` principal de ETHAN.

## 4. Service Quantar

- `QuantarTaskService` est instancié dans l'API avec `image: quantar-runtime:latest`.
- `run_task_in_container` construit une commande `docker run --rm ... one-shot`, pas Compose.
- `ComposeService` est aussi utilisé par ComposeService `quantar` avec `compose.yaml`, mais ce service n'est démarrré que via l'API lifecycle (`/lifecycle/start`).
- Aucun démarrage automatique n'est démontré.

## 5. API actuelle

- `/v1/quantar/status` : 200, available false, erreur module TradingAgents absent de l'API ETHAN.
- `/v1/quantar/lifecycle/status` : status `not_installed`.
- `/v1/quantar/tasks` : liste vide.

## 6. État des résultats

- aucun conteneur Quantar actif ;
- aucun conteneur Quantar arrêté ;
- aucun état persistant détecté ;
- aucune tâche en cours.

## Conclusions

- Quantar n'est actuellement pas déployé comme un conteneur persistant via Docker Compose.
- Aucun conteneur actif n'est attendu tant que `run_task_in_container` n'a pas été appelé avec `use_docker=True`, ou tant que le lifecycle Compose n'a pas été démarré.
- Le worker Quantar est conçu pour être one-shot, exécuté à la demande à travers la commande Docker construite côté service.
- Aucun conteneur n'apparaît actif car aucune analyse n'est en cours et Compose n'est pas started.
- Pour la WebUI Compose :
  - démarrer explicitement le lifecycle Compose (`/lifecycle/start` ou équivalent) ;
  - associer le task manager à l'action docker ;
  - prévoir le monitoring ;
  - s'assurer que les images existent ;
  - respecter les restrictions.
