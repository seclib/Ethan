# ADR-MEM-014 Phase 8 — Persistance durable SQLite

- Date : 2026-11-03
- Statut : proposé et implémenté
- Décision associée : MEM-014 Phase 8

## Contexte

MEM-014 comportait des registres en mémoire pour les permissions, événements, évaluations de conformité et états de cycle de vie.

## Décision

Utiliser SQLite standard, en mode WAL, avec migrations versionnées, via `core/applications/persistence.py`.

## Alternatives considérées

- PostgreSQL/Redis : déjà utilisés par `CoreRecordStore`, mais dépendance à une infrastructure externe et inadapté aux tests déterministes de fondation.
- Fichiers JSON : simples mais moins robustes pour la concurrence et les transactions.
- Rust storage : reporté à MEM-013 si les performances l'exigent.

## Garanties réelles

- Transactions atomiques SQLite.
- Reprise après redémarrage.
- Intégrité référentielle partielle et contraintes d'unicité.
- Migrations versionnées.
- Aucun secret stocké par la couche MEM-014.
- Aucune promotion HROT fondée sur la seule présence d'un enregistrement.

## Limites

- Tests et composants orientés mono-processus.
- Pas de réplication.
- Les autorisations restent conditionnées à la vérification HROT au redémarrage.
