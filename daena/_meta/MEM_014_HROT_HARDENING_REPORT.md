# MEM_014_HROT_HARDENING_REPORT

Date : 2026-11-03
Statut : implémenté et testé

## Corrections HROT

- `approved_by` seul ne peut plus accorder de permission.
- Toute permission positive exige une `HumanAuthority` vérifiée.
- `production_mode=True` sans vérificateur de confiance fait échouer toute autorisation.
- Les preuves sont liées à l'identité, à la capacité, à la permission et au contexte.
- Expiration, révocation et invalidation après changement de manifeste conservées.
- Décisions fail-closed.

## Mapping strict

- `_permission_compatible` exige l'égalité exacte avec une capacité déclarée.
- La compatibilité implicite par préfixe est supprimée.
- Les mappings explicites restent pris en charge via `permission_requirements`.

## Tests transversaux

Fichier : `tests/core/test_application_mem014_end_to_end.py`

Chaînes couvertes :
- Manifeste → validation → découverte → contrat → conformité → résultat traçable.
- Capacité déclarée → permission demandée → approbation HROT → décision.
- Approbation → modification → invalidation → refus → nouvelle évaluation.
- Conformité → permissions → cycle de vie contrôlé.
- Décision → événement → provenance → filtrage Engineering Memory.

Résultats :
- 5 tests transversaux passent.
- 84 tests cumulés MEM-014 passent.

## Limites cryptographiques restantes

- `HumanAuthority` reste une structure Python vérifiée structurellement.
- Aucun mécanisme cryptographique de production n'est disponible.
- En mode production, l'absence de vérificateur entraîne le refus.

## Risques résiduels

- Les registres restent en mémoire.
- Les alias d'API publics restent nombreux.
- Les capacités applicatives restent un vocabulaire ouvert.
