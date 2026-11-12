# ETHAN_PHASE_39_QUANTAR_DEDICATED_RUNTIME

Date : 2026-11-03
Statut : implémenté et vérifié

## Déploiement autonome

Le déploiement est désormais organisé exclusivement dans :

`/home/fatsio/AI/Ethan/examples/quantar/`

Fichiers :
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `ethan-application-manifest.yaml`
- `vendor/TradingAgents` (copie maîtrisée avec attribution)

Le dépôt upstream `/home/fatsio/AI/TradingAgents` n'est plus utilisé comme contexte de déploiement.

## Build

Commande :

```bash
cd /home/fatsio/AI/Ethan/examples/quantar
docker compose build
```

Résultat : succès.

Image : `quantar-runtime:phase39`  
Digest : `sha256:bf319df9c10678bdd96ac2b2a18715c55f102ce01e609ba32449234d9031b681`

## Runtime vérifié

Commande :

```bash
cd /home/fatsio/AI/Ethan/examples/quantar
docker compose run --rm quantar sh -c 'id; touch /etc/test || echo "root FS readonly OK"; python -c "import tradingagents; print(tradingagents.__version__)"'
```

Résultat observé :
- utilisateur non-root : `uid=1000`;
- filesystem racine en lecture seule ;
- `tradingagents 0.7.1` disponible.

## Limites

- Aucune analyse réelle de TradingAgentsGraph.
- Aucun secret réel.
- Aucun accès réseau granté sans passerelle.
- HROT fail-closed.
