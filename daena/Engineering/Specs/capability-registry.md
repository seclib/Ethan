# Spécification — Capability Registry (MEM-014 Phase 9)

## Modèle

Chaque capacité possède un identifiant unique, un nom, une description, une catégorie, une version, un statut, une sensibilité, des permissions, des contraintes, des dépendances, des métadonnées et des horodatages.

## États

- `draft`
- `active`
- `deprecated`
- `retired`

Une capacité retirée ne peut pas être réactivée.

## Permissions

Les relations sont explicites et validées. Aucun wildcard ni correspondance par préfixe.

## HROT

Le registre décrit et valide. Il n'accorde aucune permission. L'autorisation finale exige toujours HROT.
