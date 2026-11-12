# Phase 02-bis — Deep Stabilization / Runtime Verification

Date : 2026-11-05

## Explorations
- Métier examinés : skills web contract, capability contract, application discovery/manifest, HROT gateway, frame runtime.
- Contrat test d'intégration `tests/interfaces/test_webui_api_contract.py` a révélé un vrai défaut : endpoints skill package import manquants côté FastAPI.

## Défaut confirmé et corrigé
- ANO-05 : WebUI appelle `/v1/skills/import/scan` et `/v1/skills/import-files`, mais l'application ne les exposait pas.
- Fichiers modifiés :
  - `interfaces/api/routers/v1.py` (import FastAPI, import SkillImportManager, alias endpoints)
  - `Obsidian/Architecture/ETHAN_GLOBAL_PROGRAM/PHASE01_ANOMALY_REGISTER.md`
- Aucun changement secret/permission au-delà de `Permission.PLUGINS` déjà prévu.

## Validations
- `tests/interfaces/test_webui_api_contract.py` : passé (4 tests).
- `tests/core/test_capability_manager.py + tests/core/test_capability_rust_contract.py + tests/interfaces/test_webui_api_contract.py` : 132 passed.
- `tests/test_skill_import_manager.py` : 7 passed.
- Core tests targeted application discovery/manifest/e2e/hrot/frame : 53 passed.
- Test `tests/skills/test_importer.py` non exploitable localement (dépendance `openjarvis` manquante).

## Changements préexistants
- Le statut Git reste sale : le diff inclut de nombreuses modifications déjà présentes (agent authz, etc.). Le changement de cette mission est isolé à la fin de `v1.py`.

## Restant à résoudre
- Durcissement des contrats `calendar`/`notes` via modèles Pydantic.
- Runtime Docker end-to-end pour Odin/Frame/Quantar.
- Transport Provider Gateway pour Quantar (still blocked).
- Dette contract non typée dans capabilities/v1.
