# Migration legacy → core

## Objectif
Réduire la dette technique en supprimant `legacy/` (base OpenJarvis historique) au profit de `core/` (noyau ETHAN actuel).

## État actuel
- `legacy/` : 658 fichiers Python, 11 Mo
- `core/` : noyau actuel, packagé
- `src/sitecustomize.py` : redirige `ethan.*` / `openjarvis.*` → `legacy/`

## Stratégie progressive (par couches)

### Couche 1 — Tests
1. Identifier les tests qui importent `legacy.*` / `openjarvis.*` / `ethan.*`
2. Créer des shims dans `tests/conftest.py` qui mappent ces imports vers `core.*` quand l'équivalent existe
3. Marquer les tests legacy comme `@pytest.mark.legacy`

### Couche 2 — Modules
1. Pour chaque module `legacy/X` qui a un équivalent `core/X` :
   - Comparer les signatures publiques
   - Migrer les tests un par un
   - Supprimer `legacy/X` une fois 100% couvert par `core/X`

### Couche 3 — Nettoyage
1. Supprimer `src/sitecustomize.py` quand plus aucun import `legacy.*` n'existe
2. Supprimer `legacy/` du `PYTHONPATH` dans les Dockerfiles
3. Supprimer `legacy/` du repo

## Outil de détection
`scripts/audit_legacy_dupes.py` (à créer) : liste les fichiers présents dans
les deux `core/` et `legacy/` avec le même nom de module.

## Risques
- ⚠️ Supprimer `legacy/` avant migration complète = build cassé
- ⚠️ Les tests historiques dépendent de `legacy.*`
- ✅ Le redirecteur `sitecustomize.py` permet une transition sans rupture

## Recommandation CTO
Ne PAS supprimer `legacy/` maintenant. Migrer par incréments de modules
individuels, avec tests de non-régression à chaque étape.