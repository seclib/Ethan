# ADR-4008 — Shadow mode pour migration Rust de l'Event Store

- **Statut** : Proposed
- **Date** : 2026-10-29
- **Contexte** : RUST-MIGRATION-AUDIT, bridge contract

## Contexte
Les backends Python NATS/Redis ont une lecture fragile et les checkpoints sont non implémentés. Rust est prototype TODO.

## Décision proposée
1. Corriger d'abord la parité Python (read durable, checkpoint, bounds).
2. Exécuter Rust en shadow mode (writes+reads parallèles).
3. Comparaison hash/count/timestamps/latence.
4. Activer uniquement par feature flag avec rollback.
5. Ne pas migrer logique métier vers Rust.

## Critères de sortie
- 0 perte sur charge test.
- latence ≥30-50% meilleure.
- mémoire stable.
- tests contrats.
