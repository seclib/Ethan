# Procédure de sauvegarde des volumes Docker ETHAN

**Objectif :** Préserver l'état avant toute refonte (Phase 0).

## Volumes à sauvegarder

| Volume | Service | Criticité | Contenu |
|--------|---------|-----------|---------|
| `postgres_data` | PostgreSQL | Critique | État persistant Core (collections, skills, plugins, agents) |
| `redis_data` | Redis | Critique | État live, cache, sessions |
| `nats_data` | NATS JetStream | Critique | Événements, streams (replay impossible si perdu) |
| `open_webui_data` | Open WebUI | Critique (utilisateurs OWUI) | SQLite propre à Open WebUI |

## Commandes de sauvegarde

```bash
# Arrêter les services proprement
./ethan down

# Sauvegarder chaque volume
docker run --rm -v ethan_postgres_data:/source -v $(pwd)/backups:/dest alpine tar czf /dest/postgres_data.tar.gz -C /source .
docker run --rm -v ethan_redis_data:/source -v $(pwd)/backups:/dest alpine tar czf /dest/redis_data.tar.gz -C /source .
docker run --rm -v ethan_nats_data:/source -v $(pwd)/backups:/dest alpine tar czf /dest/nats_data.tar.gz -C /source .
docker run --rm -v ethan_open_webui_data:/source -v $(pwd)/backups:/dest alpine tar czf /dest/open_webui_data.tar.gz -C /source .

# Vérifier
ls -la backups/
```

## Restauration

```bash
docker run --rm -v ethan_postgres_data:/target -v $(pwd)/backups:/source alpine tar xzf /source/postgres_data.tar.gz -C /target
# (idem pour les autres volumes)
./ethan up
```

## Fichier `.env`

**Ne jamais inclure dans les sauvegardes committées.** Le `.env` contient des secrets (POSTGRES_PASSWORD, REDIS_PASSWORD, NATS_TOKEN, JWT_SECRET, OPENAI_API_KEY, etc.). Conserver hors dépôt, copier manuellement sur l'environnement cible.