# ESR-015 — Service Frame piloté par ETHAN

- Objectif : capacité "service externe Frame" dans WebUI Tools.
- Priorité : moyenne.
- Fichiers :
  - backend: `core/plugins/frame.py`, `interfaces/api/routers/frame.py`, `core/plugins/compose_service.py`
  - main: inclusion router `frame_router`
  - WebUI: `interfaces/webui/src/lib/api/frame.ts`, `interfaces/webui/src/app/frame/page.tsx`
  - Tools entry: bouton dans `interfaces/webui/src/components/features/tools/components/tools-workspace.tsx`
  - Compose: `examples/frame/compose.yaml`
  - tests: `tests/core/test_frame.py`, `tests/interfaces/test_frame_api.py`
- Critères : lifecycle, statut, santé, logs, port 5190, RBAC, open Studio.
- Port : `5190`, bind loopback.
- Statut : implanté; build complet des images non testé localement par absence de Bun.

- Production image final: `frame-frame:latest` = 6.6GB
- Dedicated image not yet optimized (source copy + dependencies + node_modules overlap).
