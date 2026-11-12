# QUANTAR — Compose security validation

Date : 2026-11-04

## Compose final vérifié

- `examples/quantar/compose.yaml` charge correctement (`docker compose config` succès).
- image canonique : `quantar-runtime:latest`
- utilisateur : `1000:1000`
- `cap_drop: ALL`
- `no-new-privileges:true`
- read-only filesystem
- tmpfs `/tmp`
- volumes dédiés uniquement ;
- réseau interne non attachable;
- limites CPU/mémoire/PID;
- aucun socket Docker;
- aucun démarrage d'analyse automatique.

## Tests réels

- `docker compose up -d` : conteneur démarré puis sorti (`Exited (1)`), car aucun `task.json` n'a été fourni.
- `docker compose down` : conteneur et réseau retirés, données non détruites par l'absence de `-v`.
- Aucune analyse financière réelle n'a été lancée.

## Preuves

- le runner échoue de façon contrôlée avec `task file not found`, prouvant l'absence de déclenchement involontaire.
- le conteneur utilise les restrictions de sécurité attendues.
- Aucune image ou volume n'a été supprimé.

## Limitations

- pas de démarrage réussissant d'une tâche réelle ;
- pas de WebUI action réellement testée dans cette phase pour démarrer un conteneur;
- le conteneur Compose one-shot nécessite un `task.json` valide ;
- critique : `QuantarService` Compose ne peut pas démarrer un conteneur sans une tâche préparée.

## Décision

Le Compose fournit le niveau de sécurité précédent. En revanche, le mode de démarrage Compose est réservé aux tests locaux/ops contrôlés; l'exécution d'analyse réelle reste supervisée par `run_task_in_container()` avec `use_docker=True`.

Le statut Quantar reste `PARTIALLY_VALIDATED`.
