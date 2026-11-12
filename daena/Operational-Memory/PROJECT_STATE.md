
---
### C4.1 + C3.16 + C3.17 (2026-11-09)
- C4.1: mesures géospatiales interactives via `odin/geo` — 33/33 tests passes, 5 nouvelles fonctions exports.
- C3.16: B-05 résolu (alias `carto-dark` + enum `set_map_stack`) ; suite GEV 95/95.
- C3.17: DEC-2026-003 retenue DEFERRED ; `transitFeeds.js` non migré (coût boundary disproportionné).

### Observatory workspace (2026-11-10)
- Nouveau workspace WebUI `Observatory` (Workspaces) : Overview, Vault (read+edit, Archives/ immutables), Graph, Timeline, Search, Engineering, AI Insights, Canvas.
- Nouveau service Core `core/engineering_memory/vault.py` (lecture seule, allowlist, protection chemins) + routes vault RBAC dans le router Engineering Memory.
- 22 tests Core/router nouveaux ; 421 tests WebUI ; typecheck/eslint propres ; build Next OK (8 routes prérendues). API sur :8000 non redémarrée — routes vault actives après restart opérateur.
- Session : `docs/memory/sessions/2026-11-10-observatory.md` ; rapport d'audit Phase 1 : `OBSERVATORY_AUDIT_REPORT.md`.
