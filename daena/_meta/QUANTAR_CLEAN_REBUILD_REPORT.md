# QUANTAR_CLEAN_REBUILD_REPORT

Date : 2026-11-03
Statut : rebuild réalisé et validé

## Migration

- Source : `/home/fatsio/AI/TradingAgents`
- Destination : `/home/fatsio/AI/Ethan/examples/quantar`
- Méthode : `rsync` avec exclusions de `.git`, caches, venv, vendor.
- `vendor/` retiré de la destination.

## Build autonome

Commande :

```bash
cd /home/fatsio/AI/Ethan/examples/quantar
docker compose build
```

Image : `quantar-runtime:phase39`  
Digest : `sha256:4999dad937e947a75477a1ee283447562a8e30daf72e0745b08e4fee028f6697`

## Validation runtime

Commande :

```bash
cd /home/fatsio/AI/Ethan/examples/quantar
docker compose run --rm quantar sh -c 'id; (touch /etc/test && echo FAIL) || echo "root FS readonly OK"; python -c "import tradingagents; print(tradingagents.__version__)"'
```

Résultat :
- utilisateur : `uid=1000`;
- filesystem root : read-only ;
- `tradingagents 0.7.1` importable.

## Limites

- Aucune analyse réelle.
- Aucun secret utilisé.
- Aucun volume sensible monté.
- HROT fail-closed.
