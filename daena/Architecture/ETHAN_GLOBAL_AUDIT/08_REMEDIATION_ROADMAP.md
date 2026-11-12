# 08 — Remediation Roadmap

## Mission 20 — Aligner états application (Priorité haute)
- Objectif : séparer declared/registered/docker/service.
- Fichiers : `core/applications/*`, `core/components/*`, routers applications.
- Tests : status, docker false, store.
- Critère : UI n’affiche "running" que si conteneur/service réel.

## Mission 21 — Vérifier contrats plugin/capability
- Objectif : comparaison types TS/Pydantic, routestests.
- Fichiers : `interfaces/api/routers/plugins.py`, `capabilities.py`, `src/lib/api/*`.
- Tests : contract tests, permission tests.
- Critère : install plugin/cap test.

## Mission 22 — Cartographie et rationalisation managers
- Objectif : garder divers managers mais document/fix overlap.
- Fichiers : core/applications, core/plugins, capability_manager.
- Tests ciblés existants.
- Critère : statut dashboard indépendant.
