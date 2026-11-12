# Session — 2026-11-11 — Démarrage ETHAN : python-base / modules

## Contexte

Branche : `refactor/ethan-rebuild-p0`. Incident de démarrage : `sudo ethan up`
échouait sur `python-base` (« container ethan-python-base has no healthcheck
configured ») et bloquait `modules`.

## Cause racine

`modules.depends_on.python-base: condition: service_healthy`, alors que
`python-base` est un conteneur utilitaire (`CMD sleep infinity`) sans
healthcheck. Compose refusait de démarrer `modules`. `ethan up` poursuivait
ensuite le boot et attendait 120 s la santé de `modules` (qui devenait
pourtant `healthy` via son propre healthcheck).

## Changements effectués

- `docker-compose.yml` :
  - `modules.depends_on.python-base` : `service_healthy` → `service_started`.
  - Commentaire explicatif sur le réseau `ethan_ethan-core` (artefact
    manuellement créé, subnet erroné, non déclaré `external`, non supprimé).
- `interfaces/cli/commands/up.py` :
  - `_wait_for_services` : fail-fast sur tout service sorti (`exited`/`dead`/
    `restarting`) au lieu d'attendre le timeout ; délai par défaut 60 s → 30 s.
  - Appel `_wait_for_services(compose_cmd, timeout=30, ...)`.

## Tests exécutés

- `docker compose config --quiet` : OK (exit 0).
- `sudo ethan up` : boot complet en ~4.6 s ; 10/10 démarrés, 9/10 healthy.
- `ethan-modules` : `running` / `healthy`.
- `ethan-python-base` : `running` (sans healthcheck, attendu).
- `ruff check interfaces/cli/commands/up.py` : All checks passed.
- `pytest tests/cli/ethan` : 630 passed (1 échec intermittent de benchmark
  `status` dû à la latence Docker, passe isolément).

## Réseau `ethan_ethan-core`

Artefact manuellement créé lors de tests antérieurs (subnet 172.28.0.0/16,
aucun label Compose). Non supprimé, non déclaré `external`. Warning Compose
attendu tant que l'artefact existe.

## Dettes restantes

- Suppression éventuelle du réseau artefact (nécessite confirmation
  explicite de l'opérateur).
- Le benchmark `status` reste sensible à la latence Docker (mocké dans les
  tests, mais non dans l'exécution réelle).
