# ETHAN_PHASE_29_PLUGINS_TOOLS_SEPARATION

Date : 2026-11-03
Statut : implémenté et vérifié par build/typecheck

## Modification

- Retrait de `OdinServiceSection` du corps principal de la page Plugins.
- Ajout d'un `ErrorBoundary` autour des grilles de plugins.

Odin reste accessible via Tools (`/odin`) et sa page reste intacte.

## Vérifications

- `npm run typecheck` : succès.
- `npm run build` : succès.
- Routes Plugins et Tools conservées.

## Limites

- Cause exacte du chargement initial non reproduite sans session navigateur.
- Aucune validation visuelle runtime réelle.
