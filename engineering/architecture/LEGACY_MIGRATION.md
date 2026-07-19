# Legacy/Core Migration

## Constat
Le projet contient deux arborescences Python :

- `core/` — noyau actuel ETHAN.
- `legacy/` — base historique OpenJarvis, toujours référencée par les tests et certains imports.

## Décision CTO
Ne pas casser la compatibilité existante. Mettre en place une couche de redirection d’imports plutôt que de toucher massivement le code legacy.

## Mécanisme
Fichier : `src/sitecustomize.py`

- Ajouté au `PYTHONPATH`.
- Installe un import hook (`MetaPathFinder`) qui redirige `ethan.*` et `openjarvis.*` vers `legacy/<rest>`.
- Garantit que `import ethan.core.types` et `import openjarvis.core.registry` fonctionnent sans modification du code legacy.

## PYTHONPATH recommandé
`src:legacy:core:.`

- `src` fournit `sitecustomize.py`
- `legacy` fournit les packages historiques
- `core` fournit le noyau actuel

## Docker
Tous les Dockerfiles Python incluent maintenant :
- `COPY legacy/ legacy/`
- `COPY src/ src/`
- `ENV PYTHONPATH=/app/src:/app/legacy:/app/core:/app`

## Étapes suivantes
- [ ] Migration progressive des imports `legacy.*` vers `core.*`
- [ ] Suppression de `legacy/` une fois la migration terminée
- [ ] Harmonisation des conventions de nommage (`ethan.*` vs `core.*`)