# Migration legacy → core — Statut

## Audit (2026-07-10)
- `core/` : 310 modules
- `legacy/` : 656 modules
- Chevauchements (mêmes noms) : 11
  - `agents`, `learning`, `scheduler`, `security.types`, `skills`,
    `skills.executor`, `skills.manager`, `skills.types`, `telemetry`, `tools`

## Décision CTO
**Ne pas supprimer `legacy/` maintenant.**

Raison :
1. `legacy/` contient 656 modules, dont 645 sans équivalent dans `core/`
2. Les tests importent `ethan.*` / `openjarvis.*` → résolus via `src/sitecustomize.py`
3. Supprimer `legacy/` = build cassé immédiatement

## Plan d'action (par priorité)
1. **Court terme** : CI/CD en place (`.github/workflows/ci.yml`)
2. **Moyen terme** : pour les 11 modules en chevauchement, comparer les
   signatures et migrer les tests un par un vers `core/`
3. **Long terme** : une fois `legacy/` vide de références, supprimer
   `src/sitecustomize.py` et `legacy/`

## Outil
`scripts/audit_legacy_dupes.py` — liste les chevauchements à chaque exécution.