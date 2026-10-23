# Contrôleur Compose Odin

Le cycle de vie Odin est exécuté par `odin-controller`, un service interne du
Compose ETHAN. Seul ce service reçoit `/var/run/docker.sock`; l'API ETHAN lui
transmet des opérations prédéfinies et conserve l'authentification et le RBAC
des routes WebUI. Le navigateur n'accède jamais au socket ni au contrôleur.

Le contrôleur est limité au projet `odin`, au fichier
`examples/odin/compose.yaml` et aux actions `config`, `ps`, `up -d`, `stop`,
`restart`, `down`, `logs` et à la sonde HTTP interne. Il n'accepte aucun chemin,
nom de projet ou argument Compose arbitraire. La désinstallation utilise
`down` sans `-v`; elle conserve les volumes et les fichiers du dépôt.

Le dépôt Odin doit être présent sur l'hôte dans `examples/odin`. Le chemin du
projet ETHAN est transmis par `${PWD}` au démarrage de Compose; lancez donc
`docker compose` depuis la racine ETHAN. Le contrôleur monte le dépôt Odin en
lecture seule au même chemin absolu que l'hôte. Le daemon Docker résout ainsi
correctement le contexte `build: .` et le bind mount du Compose Odin.
Il s'exécute avec l'UID/GID hôte (pour lire le `.env` protégé) et reçoit le GID
du socket en groupe supplémentaire. Si le groupe du socket n'est pas `118`,
définissez `DOCKER_GID` dans l'environnement avant d'exécuter Compose, par
exemple `DOCKER_GID=$(stat -c %g /var/run/docker.sock) docker compose up -d`.

Après une modification de l'API ou du contrôleur, reconstruisez l'image partagée
puis recréez ces services sans toucher aux volumes :

```sh
docker compose build api
docker compose up -d --no-deps odin-controller api
```

Le contrôleur possède le socket Docker, ce qui constitue une autorité élevée
sur le daemon. Il est isolé de l'API, sans port publié, avec système de fichiers
en lecture seule, capacités Linux supprimées et `no-new-privileges`. Garder le
code du contrôleur et le Compose Odin dans le périmètre de confiance de
l'opérateur; le jeton interne dérive du `JWT_SECRET` ETHAN et ne doit pas être
copié dans une interface ou un client externe.

Ce mécanisme ne clone ni ne met à jour le dépôt Odin. Le dépôt upstream reste
indépendant et sa préparation demeure une opération d'administration.
