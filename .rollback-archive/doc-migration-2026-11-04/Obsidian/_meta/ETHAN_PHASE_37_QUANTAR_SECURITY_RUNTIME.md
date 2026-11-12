# ETHAN_PHASE_37_QUANTAR_SECURITY_RUNTIME

Date : 2026-11-03
Statut : configuration statique renforcée, isolation runtime non démontrée

## Frontière Docker

- `examples/quantar/docker-compose.security.yml` : utilisateur non-root, `cap_drop: ALL`, `no-new-privileges`, `read_only`, tmpfs dédié, volume dédié, réseau `internal`.
- Aucun Docker socket ni home utilisateur.
- Limites CPU, RAM et PIDs.

## Política de secrets

- Aucun secret réel monté.
- Seules des variables allowlistées peuvent être injectées au runtime.
- Les secrets ne peuvent pas provenir du filesystem.

## Capacités interdites

Quantar reste exclusivement analytique. Les capacités de trading, signature, transfert ou wallet n'ont pas été ajoutées.

## Limites

- Réseau bridge interne n'équivaut pas à une politique egress granulaire.
- Aucun test runtime n'a exécuté le conteneur hardened.
- HROT reste fail-closed.

