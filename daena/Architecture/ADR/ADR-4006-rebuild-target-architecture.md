# ADR-4006 — Architecture cible rebuild ETHAN (hybride Rust + Python, socle parallèle)

- **Statut** : Proposed (audit P0 requis)
- **Date** : 2026-10-29
- **Contexte** : `Obsidian/Engineering/Audits/ETHAN_REBUILD_P0_AUDIT.md`

## Contexte
ETHAN est un système Core/Runtime/Services/Interfaces. La WebUI doit rester remplaçable. L'audit P0 a vérifié que Core Python et API sont substantiels, que doublons existent, et que les prototypes Rust sont non opérationnels.

## Décision
1. Le Core Python reste source de vérité métier.
2. Rust est limité à des sous-systèmes natifs via contrat stable, d'abord event store.
3. Le nouveau socle se construit en parallèle, migration progressive.
4. Les interfaces ne contiennent pas de logique métier.
5. Open WebUI est candidate UI, sous décision licence préalable.
6. Odin reste externe.
7. Human Root of Trust conserve l'autorisation racine.

## Alternatives
- Réécrire ETHAN entièrement en Rust (rejeté : logique métier évolutive).
- Adopter Open WebUI backend comme source vérité (rejeté : viole AGENTS.md).
- Conserver Next.js et importer UX (gardé comme fallback).

## Conséquences
- Plus de frontières à tester via contract tests.
- Besoin de governances fork et shadow mode.
- Migration plus longue mais moins risquée.

## Conditions bloquantes
- Licence/marque.
- Contrats API v1 signés/tests.
- Sécurité approval/root of trust documentée.
- Persistance/backup plan approuvé.
