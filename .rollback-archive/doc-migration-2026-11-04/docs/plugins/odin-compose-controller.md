# Gestion du cycle de vie Odin — architecture directe

## Principe

ETHAN pilote le cycle de vie du service Odin **directement** depuis `core/plugins/odin.py` via `docker compose` subprocess. Il n'existe plus de service intermédiaire `odin-controller`.

Le flux d'appel est :

```
WebUI → API → ETHAN Core → docker compose subprocess (projet `odin`)
```

Le socket Docker n'est monté que sur le service `api` de la stack ETHAN ; aucune interface n'y accède directement.

## Fichier Compose cible

- Projet Compose : `odin`
- Fichier : `examples/odin/compose.yaml`
- Dépôt : `/home/fatsio/AI/Ethan/examples/odin`

## Opérations autorisées

Seules les opérations figées suivantes sont exécutables, via la classe `OdinService` (Core) :

| Action | Commande docker compose |
|--------|-------------------------|
| Démarrer | `compose -p odin -f examples/odin/compose.yaml up -d` |
| Arrêter | `compose -p odin -f examples/odin/compose.yaml stop` |
| Redémarrer | `compose -p odin -f examples/odin/compose.yaml restart` |
| Désinstaller | `compose -p odin -f examples/odin/compose.yaml down` |
| État | `compose -p odin -f examples/odin/compose.yaml ps --all --format json` |
| Valider config | `compose -p odin -f examples/odin/compose.yaml config` |
| Logs | `compose -p odin -f examples/odin/compose.yaml logs --tail=N --no-color` |

Aucune commande Docker arbitraire n'est acceptée (allowlist stricte dans `OdinService._is_allowed_docker_args`).

## Confinement

Le service `OdinService` valide à chaque appel que le fichier Compose visé est exactement `examples/odin/compose.yaml` sous la racine ETHAN. Tout autre chemin est refusé (fail-closed).

La variable d'environnement `ETHAN_ODIN_REPO_DIR` peut surcharger le répertoire du dépôt, mais le fichier Compose doit rester `compose.yaml` à la racine de ce répertoire.

## Gestion manuelle depuis le dépôt Odin

Depuis le répertoire du dépôt Odin (`examples/odin`) :

```sh
# Vérifier la configuration
docker compose --project-name odin -f compose.yaml config

# Démarrer Odin
docker compose --project-name odin -f compose.yaml up -d

# Voir l'état des conteneurs
docker compose --project-name odin -f compose.yaml ps --all

# Arrêter Odin
docker compose --project-name odin -f compose.yaml stop

# Redémarrer Odin
docker compose --project-name odin -f compose.yaml restart

# Désinstaller (stop + suppression des conteneurs, volumes conservés)
docker compose --project-name odin -f compose.yaml down

# Voir les logs
docker compose --project-name odin -f compose.yaml logs --tail=100 --no-color
```

## Sécurité

- Le socket Docker est monté uniquement sur le service `api` de la stack ETHAN.
- Les secrets (tokens, clés API) sont automatiquement redactés dans les logs et sorties d'erreur (`OdinService._redact_secrets`).
- Aucun démarrage automatique non sollicité au boot d'ETHAN.
- L'authentification et le RBAC sont gérés par l'API ETHAN sur les routes WebUI.