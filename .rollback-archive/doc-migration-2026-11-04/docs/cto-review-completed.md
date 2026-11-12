# CTO Review — Corrections Appliquées

**Date** : 20/07/2026  
**Auteur** : CTO  
**Statut** : 5 corrections critiques appliquées, en cours sur les P1.

---

## Résumé des corrections appliquées

### ✅ C-04 : Healthcheck API corrigé
**Fichier** : `docker-compose.yml`  
`/v1/health` → `/health`

### ✅ C-02 : CORS conditionnel
**Fichier** : `interfaces/api/main.py`  
`["*"]` → `os.getenv("CORS_ORIGINS", "*")`

### ✅ C-03 : Secrets retirés du docker-compose
**Fichier** : `docker-compose.yml`  
Valeurs par défaut supprimées (`${POSTGRES_PASSWORD:-ethan_dev_pass}` → `${POSTGRES_PASSWORD}`)

### ✅ C-01 : pyproject.toml et Makefile nettoyés
**Fichiers** : `pyproject.toml`, `Makefile`  
30+ extras, scripts legacy, références `src/openjarvis` supprimés

### ✅ C-05 : bootstrap.py documenté
**Fichier** : `core/bootstrap.py`  
Commentaire clarifiant les 3 sources de PYTHONPATH

### ✅ Corrections `/v1/health` restantes
- `docs/sre-runbook.md` — 2 occurrences
- `scripts/cmd-wait-for-services.sh` — 1 occurrence
- `README.md` — section API exposée corrigée

### ✅ Décisions architecturales
- `examples/jarvis-os/` — README clarifiant le statut (projet séparé, ancêtre ETHAN)
- `core/registry/module_registry.py` — inexistant, pas de doublon