# QUANTAR_REAL_ACTIVATION_FIX

Date : 2026-11-03
Statut : cheminement vérifié jusqu'à l'authentification; aucun démarrage réel

## Chaîne réelle observée

- Menu Tools contient `/quantar`.
- Page `/quantar` existe et consomme `/v1/quantar/status`, `/config`, `/lifecycle/status`.
- Route FastAPI quantifiee `/v1/quantar/*` répond `401` sans session.
- ComposeService backend existe via `QuantarService`.
- Démarrage réel déjà validé manuellement avec `docker compose`.

## Cause réelle de l'inutilisation

L'accès direct à `http://localhost:3001/quantar` redirige vers `/login` en l'absence de session authentifiée.

Aucune session utilisateur réelle n'a été créée par l'agent.

## Bouton/start handling

La page contient déjà `Start` et `Stop` et appelle `/v1/quantar/lifecycle/*`.

## Preuve disponible

- `GET /v1/quantar/status` (anonyme) : `401`.
- `GET /v1/quantar/lifecycle/status` (anonyme) : `401`.
- Build frontend : succès.
- 128 tests MEM-014 : réussis.

## Action requise

L'utilisateur doit établir une session authentifiée manuellement, ouvrir `/quantar`, puis tester Start/Stop.
