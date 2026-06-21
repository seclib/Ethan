# ADR-001: Architecture Initiale — Jarvis OS

> **Statut** : Accepted
> **Date** : 2026-06-21

---

## Context

Ethan est un projet open-source mature avec une architecture modulaire. Jarvis OS est construit comme une surcouche (overlay) qui étend Ethan sans le réécrire.

Le défi est de maintenir la compatibilité avec l'upstream tout en ajoutant les fonctionnalités nécessaires pour Jarvis OS.

## Decision

### Principe 1 : Ethan est l'upstream

- Ethan est le projet source (canonical upstream)
- Jarvis OS est une surcouche qui étend, jamais ne remplace
- Toute modification profonde d'Ethan doit être faite via RFC
- Les fonctionnalités génériques doivent être proposées à l'upstream

### Principe 2 : Modifications incrémentales

- Pas de réécriture globale
- Pas de refactoring sans RFC
- Les changements doivent être atomiques et réversibles
- Chaque modification doit préserver la compatibilité ascendante

### Principe 3 : Système RFC obligatoire

- Toute modification significative nécessite une RFC
- Les RFC sont reviewées avant implémentation
- Les décisions architecturales sont documentées via ADR
- Le système de gouvernance est lui-même défini par RFC-000

### Principe 4 : Séparation claire

- `engineering/` contient la gouvernance (RFC, ADR, templates, standards)
- `core/` contient les nouvelles abstractions Jarvis OS
- `src/ethan/` contient le code upstream Ethan
- Les plugins Jarvis OS vont dans `plugins/`

## Alternatives

| Alternative | Raison du rejet |
|-------------|-----------------|
| Fork complet d'Ethan | Perte de la compatibilité upstream, maintenance massive |
| Réécriture depuis zéro | Effort démesuré, perte de l'existant |
| Fusion totale dans un seul projet | Impossible (upstream ≠ notre vision) |

## Consequences

### Positives
- Compatibilité ascendante préservée
- Evolution contrôlée et documentée
- Nouvel engineer comprend l'architecture sans lire le code source
- Décisions traçables via ADR

### Négatives
- Overhead de processus (RFC, ADR)
- Nécessite discipline d'équipe
- Coordination avec upstream nécessaire

### Neutres
- Deux repositories à maintenir (upstream + overlay)
- Standards différents entre upstream et overlay

---

## Compliance

- Toute PR doit référencer une RFC ou un ADR
- Les PR sans RFC sont rejetées automatiquement
- Les modifications deep d'Ethan sont interdites sans RFC approuvée

## References

- [RFC-000: Engineering Bootstrap](/engineering/rfc/RFC-000-bootstrap.md)
- [Engineering Principles](/engineering/standards/engineering-principles.md)