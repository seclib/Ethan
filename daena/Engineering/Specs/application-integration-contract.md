# Spécification — Contrat d'intégration applicative (MEM-014 Phase 4)

## Format

Contrat versionné, fondé sur le manifeste de Phase 1 et réutilisant ses règles strictes.

## Typage des artéfacts

- `application` : application indépendante.
- `plugin` : composant intégré déclaratif.
- `extension` : contrat d'extension.
- `skill` : capacité d'intelligence réutilisable.

Les types sont distincts et ne sont pas interchangeables.

## Compatibilité des permissions

Une permission demandée doit :

- soit être directement accompagnée d'un mapping vers une capacité déclarée ;
- soit correspondre à une capacité déclarée par préfixe ou égalité.

Aucune permission implicite ou automatique n'est accordée.

## Sécurité

- Contrat non fiable et strictement validé.
- Aucune exécution de contenu.
- Aucun contournement du validateur, de l'autorisation Phase 3 ou de HROT.
- Distinction explicite des états déclaré, vérifié, disponible et autorisé.
