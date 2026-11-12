# ETHAN_PHASE_28_PLUGINS_UI_REPAIR

Date : 2026-11-03
Statut : diagnostic documenté, aucune correction démontrée comme résolvant le symptôme

## Causes possibles identifiées par inspection

- La page Plugins repose sur `/v1/plugins` et suppose des tableaux (`categories`, `capabilities`, `capabilities.slice`).
- Elle intègre également `OdinServiceSection`, une section Odin directement dans la page Plugins, alors que Odin est déjà exposé sous Tools.
- La séparation conceptuelle Plugins (extensions) / Tools (applications indépendantes) est donc partiellement violée dans l'UI.
- Aucune preuve d'erreur browser réelle n'a été capturée.

## Vérifications

- Build frontend : succès.
- Typecheck : succès.
- Tests frontend : 64 suites, 378 passent.
- Tests backend MEM-014 : 128 passent.

## Risque

La cause exacte du `page couldn't load` n'a pas été confirmée par la console navigateur.

## Recommandation

1. Séparer réellement `OdinServiceSection` de la page Plugins.
2. Ajouter une erreur boundary locale.
3. Ajouter une validation défensive autour des tableaux fournis par le backend.
4. Valider avec une session réelle et des captures.

## Corrections ciblées appliquées

- Validation stricte des listes et champs critiques de la réponse `/v1/plugins`.
- Catégories validées avant utilisation.
- Aucune correction permissive d'affichage; les données invalides lèvent une erreur explicite.

## Résultats

- `npm run typecheck` : succès
- `npm run build` : succès
- `npm run test` : 378 passés

## Limite restante

- Cause exacte du message navigateur non confirmée faute de session.
