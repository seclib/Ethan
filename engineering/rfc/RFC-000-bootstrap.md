# RFC-000: Engineering System Bootstrap

> **Statut** : Accepted
> **Auteur** : Principal Platform Engineer
> **Date** : 2026-06-21

---

## Context

Jarvis OS est construit sur Ethan. Pour garantir la qualité, la stabilité et la maintenabilité, un système de gouvernance technique est nécessaire.

Sans ce système, les risques sont :
- Modifications non coordonnées
- Décisions architecturales non documentées
- Régressions non détectées
- Difficulté d'onboarding des nouveaux engineers

## Objective

Créer un système de gouvernance technique qui :
1. Documente toutes les décisions architecturales (ADR)
2. Structure les propositions de changement (RFC)
3. Définit les standards d'engineering
4. Permet à un nouvel engineer de comprendre le projet rapidement

## Scope

- Création du dossier `engineering/` avec sa structure
- Templates RFC et ADR
- Premier ADR (architecture initiale)
- Standards d'engineering
- Processus de gouvernance

## Non-scope

- Modification du code source
- Modification du déploiement Docker
- Réorganisation des dossiers existants
- Implémentation de fonctionnalités

## Design

### Structure engineering/

```
engineering/
├── rfc/           # RFCs (Requests for Comments)
│   └── RFC-000-bootstrap.md
├── adr/           # ADRs (Architecture Decision Records)
│   └── ADR-001-initial-architecture.md
├── reports/       # Rapports d'audit et d'analyse
│   ├── repository-audit.md
│   ├── architecture-overview.md
│   ├── dependency-map.md
│   ├── deployment-analysis.md
│   └── technical-risks.md
├── templates/     # Templates réutilisables
│   ├── RFC_TEMPLATE.md
│   └── ADR_TEMPLATE.md
└── standards/     # Standards d'engineering
    └── engineering-principles.md
```

### Processus RFC

```
1. Draft ──► 2. Review ──► 3. Accepted/Rejected
    ↑              │
    └── Feedback ──┘
```

1. **Draft** : Créer une RFC en utilisant le template
2. **Review** : Soumettre à review (PR)
3. **Accepted/Rejected** : Décision finale
4. **Implementation** : Si acceptée, implémenter selon le plan
5. **Validation** : Vérifier les critères de validation

### Processus ADR

1. **Proposed** : Proposition de décision
2. **Accepted** : Décision validée
3. **Deprecated** : Décision obsolète
4. **Superseded** : Remplacée par une nouvelle décision

### Règles

1. Toute modification significative nécessite une RFC
2. Toute décision architecturale nécessite un ADR
3. Les PR sans RFC/ADR sont rejetées
4. Les RFC doivent inclure un plan de rollback
5. Les ADR ne sont jamais supprimés (historique)

## Alternatives Considered

| Alternative | Pros | Cons |
|-------------|------|------|
| Pas de gouvernance | Aucun overhead | Chaos technique |
| Gouvernance légère (issues only) | Simple | Pas de traçabilité |
| ADR uniquement | Simple | Pas de processus de proposition |
| RFC + ADR (choisi) | Complet, traçable | Overhead modéré |

## Implementation Plan

1. ✅ Créer la structure `engineering/`
2. ✅ Créer les templates RFC et ADR
3. ✅ Créer ADR-001 (architecture initiale)
4. ✅ Créer RFC-000 (ce document)
5. ✅ Créer les standards d'engineering
6. ⏳ Former l'équipe au processus

## Risks

| Risque | Impact | Probabilité | Mitigation |
|--------|--------|-------------|------------|
| Overhead de processus | Moyen | Haute | Templates clairs, review rapide |
| Non-respect du processus | Élevé | Moyenne | CI checks, code review |
| ADR obsolètes non mis à jour | Moyen | Haute | Revue trimestrielle des ADR |

## Rollback Plan

Si le système de gouvernance s'avère trop lourd :
1. Réduire les sections obligatoires des templates
2. Passer en revue asynchrone uniquement
3. Supprimer les checks CI si nécessaire

## Validation Criteria

- [x] Dossier `engineering/` créé avec sous-dossiers
- [x] Template RFC disponible et réutilisable
- [x] Template ADR disponible et réutilisable
- [x] ADR-001 documente l'architecture initiale
- [x] RFC-000 documente le processus
- [x] Standards d'engineering définis
- [x] Aucun code source modifié
- [x] Aucune fonctionnalité cassée

---

## References

- [ADR-001: Architecture Initiale](/engineering/adr/ADR-001-initial-architecture.md)
- [Engineering Principles](/engineering/standards/engineering-principles.md)