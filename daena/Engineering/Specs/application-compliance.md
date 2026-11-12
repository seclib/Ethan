# Spécification — Moteur de conformité (MEM-014 Phase 5)

## Résultat d'évaluation

Chaque contrôle retourne `PASS`, `FAIL`, `WARN` ou `NOT_APPLICABLE`.

## États

- `COMPLIANT`
- `PARTIALLY_COMPLIANT`
- `NON_COMPLIANT`
- `NOT_EVALUATED`

## Règles

- Un contrôle obligatoire échoué interdit `COMPLIANT`.
- Un `WARN` n'est jamais converti en succès.
- Une erreur interne ne produit jamais `COMPLIANT`.
- La conformité ne confère aucune autorisation.

## Traçabilité

- Identifiant stable par contrôle.
- Catégorie, gravité, description, référence de preuve, version de règle.
- Horodatage et identifiant d'évaluation.
- Invalidité implicite en cas de changement de manifeste ou de contrat.
