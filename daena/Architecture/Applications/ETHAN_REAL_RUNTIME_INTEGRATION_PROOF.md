# ETHAN — Preuve d'intégration runtime réelle (Mission 11)

Date : 2026-11-04

## Executions reelles

### ODIN — VALIDATED (API + contrôleur)

Preuves :
- ODIN installé via API (`POST /v1/plugins/odin/install`) : statut `running`.
- Health : `{"status":"healthy","reachable":true}`.
- Aucun conteneur arrête dans cette mission après validation.

Statut : `VALIDATED` pour le cycle API/contrôleur observé.

### Frames — BLOCKED

Preuves :
- Statut API : `not_installed`.
- Tentative `POST /v1/plugins/frame/start` : erreur réelle (`repo_dir /app/examples/frame` introuvable dans l'image API).
- `ComposeService` existe mais le runtime Frames n'est pas matériellement present dans l'image API déployée.

Statut : `BLOCKED` par absence du dépôt `examples/frame` dans le conteneur API.

### Quantar — PARTIALLY_VALIDATED

Preuves :
- Statut API : image disponible, in-process indisponible.
- Correction précédente rend le status `runtime=ready` si l'image trouve.
- Aucune tâche réelle exécutée dans cette mission (pas de dependance tradingagents dans Core/API).

Statut : `PARTIALLY_VALIDATED`.

### Rust Health — PARTIALLY_VALIDATED

- Façade Python retourne `status=ok`.
- Route réelle dans l'image déployée non expose (OpenAPI ne la listait pas).

Statut : `PARTIALLY_VALIDATED`.

## Tests exécutés et résultats associes aux composants

- ODIN / health checks unitaires : déjà verts.
- Capacities manager : 111 verts.
- Rust contract : 2 verts.
- HROT provider gateway : 14 verts.

## Blocages restants

1. Frames ne peut pas démarrer sans volume/montage du dépôt examples/frame.
2. API réelle n'expose pas le route Rust Health.
3. Quantar dépend de l'image quantar-runtime mais sa présence n'équivaut pas à une exécution réussie.
4. E2E WebUI authentifié n'a pas été ré-exécuté avec le build modifié sauf palette.

## Statut final

- ODIN : `VALIDATED`
- Frames : `BLOCKED` (déploiement runtime manquant)
- Quantar : `PARTIALLY_VALIDATED`
- WebUI : `PARTIALLY_VALIDATED`
- HROT/provider gateway : `VALIDATED`
- Capability Manager/Rust contract : `VALIDATED`
