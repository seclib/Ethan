# ESR-003 — Docker Provisioning

**Statut** : Implémenté (sous réserve d'accès au binaire Docker — voir §8)
**Date** : 2026-09-23
**Décision parente** : [ADR-4001](/docs/architecture/adr/ADR-4001-capability-manager.md),
[ADR-4002](/docs/architecture/adr/ADR-4002-install-on-demand.md)
**Code** : [`core/capability_manager/backends.py`](/core/capability_manager/backends.py)
(`DockerBackend`), [`core/capability_manager/builtin.py`](/core/capability_manager/builtin.py)
(`qdrant()`)

---

## 1. Principe

Le backend `docker` orchestre des composants optionnels en conteneurs via
la CLI Docker, avec des **actions déclaratives figées** dans la spec
développeur. Aucune chaîne utilisateur n'atteint une argv (substitution
`{config.*}` uniquement sur des valeurs typées — voir
[ESR-006](/docs/engineering/esr/ESR-006-security-model.md)).

**Docker lui-même n'est jamais installé par ETHAN** : il est une
dépendance `system` de la spec (`Dependency(id="docker",
command=("docker",))`) ; son absence bloque l'installation avec un
message clair.

## 2. Actions allowlistées

```python
_DOCKER_ACTIONS = {
    "check_docker",     # docker fonctionnel ? (jamais l'installer)
    "pull",             # {"image": "qdrant/qdrant:{config.tag}"}
    "create_volume",    # {"volume": "qdrant_storage"}
    "ensure_network",   # {"network": "ethan-net"}
    "run",              # {"name","image","ports","env","volume","network","command"}
    "start", "stop",    # {"name"}
    "remove",           # {"name", "keep_data": bool, "data_to_delete": [...]}
}
```

Toute autre action **refuse l'enregistrement** de la spec
(`validate_install_actions`).

Le `pull` est suivi d'une **vérification d'intégrité** quand
`provenance.checksum` (sha256) est déclaré : le `RepoDigest` réel de l'image
tirée doit correspondre, sinon l'installation échoue sans conteneur créé.
Champ vide = non déclaré — jamais « conforme » par défaut (aucune
vérification inventée).

## 3. Ressources (exemple `qdrant`)

| Ressource | Valeur déclarée |
|---|---|
| Image | `qdrant/qdrant:{config.tag}` (choices: `latest`, `v1.12.0`, `v1.11.2`) |
| Container | `ethan-qdrant` (nom fixe, déterministe) |
| Volume | `qdrant_storage` → `/qdrant/storage` |
| Network | `ethan-net` |
| Ports | `{config.http_port}:6333` (HTTP), `{config.grpc_port}:6334` (gRPC) |
| Environment | `QDRANT__TELEMETRY__OPENCOLLECTOR__ENABLED=false` |

Les `env` sont des chaînes déclaratives de la spec (pas d'environnement
utilisateur injecté) ; les secrets éventuels passeraient par la couche
SecretManager, jamais dans la spec ni les événements.

## 4. Health checks

Deux paliers réels sur `qdrant` :

1. `tcp` niveau `basic` — port `http_port` ouvert (timeout 2 s) ;
2. `endpoint` niveau `functional` — `GET
   http://127.0.0.1:{config.http_port}/readyz` (timeout 3 s).

`READY` n'est acquis que si le check `functional` passe.

## 5. Start / Stop

`start_actions` / `stop_actions` = `docker start|stop ethan-qdrant`
(via le backend). `stop` conserve toujours les données ;
`start` re-vérifie la santé avant `READY`.

## 6. Uninstall & conservation des données

Action `remove` avec :

- `keep_data=True` (défaut) → conteneur supprimé, **volume `qdrant_storage`
  conservé** ;
- `keep_data=False` (double confirmation requise —
  [ADR-4003](/docs/architecture/adr/ADR-4003-data-lifecycle.md)) →
  `data_to_delete=[{"kind": "volume", "name": "qdrant_storage"}]`.

Les `data_resources` de la spec documentent à l'utilisateur ce qui existe
et ce que la suppression détruit.

## 7. Détection

`_detect_installed` (backend docker) : `docker` présent dans le PATH,
puis `docker container inspect <nom>` — la présence du conteneur nommé
est la preuve d'installation ; l'état réel (running/exit) est ensuite
réconcilié par la santé.

## 8. Contraintes et limites (constatées en live)

- **L'API doit avoir accès au binaire Docker.** Dans le déploiement
  actuel (container `ethan-api`), `docker` est absent : l'installation de
  `qdrant` échoue honnêtement avec
  *« Docker est requis mais absent. Installez Docker manuellement
  (ETHAN n'installe jamais Docker lui-même) »* → état `ERROR`, puis
  réconciliation `SUPPORTED` après détection. C'est le comportement
  voulu ; la résolution (socket Docker monté, API hôte ou daemon distant,
  ex. docker-over-SSH) est une **décision de déploiement** hors périmètre
  de ce module.
- Timeouts : pull/run passent par `_run` (300 s par défaut, kill au
  dépassement) ; un pull très lent peut nécessiter un ajustement.
- Pas de re-pull automatique : si l'image est absente au `start`, l'échec
  est explicite.