# MEM_014_PHASE_15_ODIN_PILOT_READINESS

Date : 2026-11-03
Phase : MEM-014 Phase 15 — Odin Pilot Readiness
Statut : préparation technique, aucune application lancée

## Audit retenu

- Odin est contrôlé par `core/plugins/odin.py` avec allowlist stricte de commandes Docker Compose.
- Docker est local et le confinement est vérifié.
- Port par défaut : 4173.
- Les opérations `start`, `stop`, `restart`, `status`, `logs`, `health` sont les candidates documentées.
- Les opérations destructives (`down`) nécessitent une décision humaine et un HROT opérationnel.

## Capacités identifiées

- `application.health.read`
- `application.lifecycle.read`
- `application.logs.read`
- `application.control.start`
- `application.control.stop`
- `application.control.restart`

Aucune permission n'est automatiquement accordée par le manifeste.

## Mapping opérations / permissions

| Opération | Effet réel | Ressource | Permission nécessaire |
|---|---|---|---|
| status | lecture | container | application.lifecycle.read |
| health | lecture | endpoint HTTP | application.health.read |
| logs | lecture rédigée | logs | application.logs.read |
| start | démarrage | conteneur | application.control.start |
| stop | arrêt | conteneur | application.control.stop |
| restart | redémarrage | conteneur | application.control.restart |

## Contrat

Manifeste créé : `examples/odin/ethan-application-manifest.yaml`.

Validation : manifest valide, 6 capacités.

## Tests

- `tests/core/test_odin_pilot_phase15.py` : 3 passed.
- Régression phase 14 : 125 cumulés.

## Risques restants

- Docker en local, accès au socket.
- Contrôle HROT non opérationnel.
- Pas de flux humain réel.
- Port et health à superviser.

## Recommandation

Odin peut être le premier pilote si les opérations destructives restent bloquées jusqu'au déploiement complet du flux HROT.
