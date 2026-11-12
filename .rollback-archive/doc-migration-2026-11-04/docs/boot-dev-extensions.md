 # Boot — Extensions développement

Ce document complète `docker-compose.yml` pour les développeurs.

## Services supplémentaires en développement

Le fichier `docker-compose.dev.yml` ajoute :

- `redis` / `postgres` en mode développement
- `qdrant` : vector store
- `chromadb` : vector store alternatif

## Activation

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## Profil LLM local

```bash
docker compose --profile llm up
```

Cela active `ollama` défini dans `docker-compose.yml`.

## Remarque

`interfaces/webui/package.json` doit être installé (`npm install`) avant `./ethan webui`.