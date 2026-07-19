# ETHAN Packaging & Build — CTO Notes

## Problème initial
- `pyproject.toml` packagé `src/openjarvis` inexistant → build cassé.
- Dockerfiles manquants ou obsolètes (Streamlit au lieu de Next.js).
- `legacy/` référencé via `ethan.*` / `openjarvis.*` mais non résolu.

## Solutions appliquées
1. **`src/sitecustomize.py`** : import hook redirigeant `ethan.*` / `openjarvis.*` vers `legacy/`.
2. **`pyproject.toml`** : `packages = ["core"]`, console_scripts corrigés.
3. **Dockerfiles** (`api`, `kernel`, `module`, `runtime`) : `COPY legacy/ src/` + `PYTHONPATH=/app/src:/app/legacy:/app/core:/app`.
4. **`Dockerfile.ui`** : multi-stage Next.js + `npm ci --legacy-peer-deps`.
5. **`docker-compose.yml`** : UI sur 3000, suppression `version:`.
6. **`Makefile`** : `PYTHONPATH=src:legacy:core:.`.
7. **`interfaces/webui/src/lib/animations.css`** : fichier manquant référencé par `globals.css`.

## Validation
- `PYTHONPATH=src .venv/bin/python -c "import ethan.core.types; import openjarvis.core.registry"` → OK.
- `docker compose build` → 11 images built (api, kernel, 7 modules, runtime, ui).

## Recommandations
- Migrer progressivement `legacy.*` → `core.*`.
- Supprimer `legacy/` après migration complète.
- Ajouter CI/CD (lint + test + build) sur PR.