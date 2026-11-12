# MEM_013_REVISION_REPORT

Date : 2026-11-03
Statut : MEM_013_REVISED_PROPOSAL_PENDING_USER_APPROVAL

## Ancienne approbation enregistrée

L'ancienne proposition se trouvait dans le registre sur `PENDING_USER_DECISION`. Elle proposait :

- Python-only initially;
- Rust shadow si contrainte démontrée;
- Rust is external / DA.

Aucune approbation humaine n'avait été enregistrée. Elle n'est donc pas une décision approuvée masquée.

Son historique reste visible dans le registre et dans `ARCHITECTURE_OPTIONS.md`.

## Nouvelle préférence

Préférence de l'utilisateur :

- Rust constitue le socle principal d'Engineering Memory.
- Python intervient comme technologie complémentaire.
- Somme plus aucun préjugé que Python seul soit la stratégie cible.

## Impact préliminaire

- Le code Engineering Memory existant reste l'implémentation de référence actuelle.
- Rust a des bases partielles en production dans `core/rust/ethan_health` et `core/bus/backends/rust_event_store`.
- La migration ne sera envisagée qu'après une étude compare et preuves.
- Le présent changement garde une troisième option : séparation par surfaces.

## Risques clés

- duplication des logiques métier ;
- complexité de bindings ;
- perte de cohérence si schémas divergent ;
- maintenance de deux toolchains ;
- coût opérationnel pour un contrainte non prouvée ;
- difficultés de débogage ;
- dépendance Rust non présente sur chaque machine.

## Validation nécessaire

- Rapport de performance et de volumétrie.
- Tests de charge réels.
- Analyse sécurité interprocessus.
- Audit de portabilité.
- Decision gate humain.

## Conclusion

`MEM-013` reste une proposition à valider. Son statut dans le registre a été mis à jour sans déclarer de nouvelle décision approuvée.
