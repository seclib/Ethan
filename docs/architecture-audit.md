# Audit d'Architecture ETHAN — Rapport Actualisé

> **Date** : 2026-07-19 (MAJ)  
> **Auteur** : Principal Software Architect  
> **Version** : 1.1 (corrigée)

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble-du-projet)
2. [Organisation des dossiers](#2-organisation-des-dossiers)
3. [Dépendances](#3-cartographie-des-dépendances)
4. [Points forts](#4-points-forts)
5. [Faiblesses](#5-faiblesses)
6. [Dette technique](#6-dette-technique)
7. [Recommandations](#7-recommandations)

---

## 1. Vue d'ensemble du projet

**Architecture réelle** :
- Core = Python pur (pas Go)
- API = FastAPI sur port 8000
- Communication = NATS JetStream
- Persistence = PostgreSQL + Redis

---

## 2. Organisation des dossiers

### Structure réelle

```
Ethan/
├── core/                   # ✅ Kernel Python
│   ├── agents/             # ✅ 12 fichiers (926 lignes) - NON VIDE
│   ├── orchestrator/       # ✅ Orchestrateur
│   ├── pkg/events/, types/ # ✅ NON VIDES (sous-dossiers)
│   └── bus/, state/, modules/ ...
│
├── interfaces/
│   └── api/main.py:13      # ⚠️ sys.path.insert() (violation)
│
├── plugins/                # ✅ Extensions
├── sdk/                    # ✅ SDK public
├── runtime/                # ⚠️ Runtime Go orphelin
└── rust/                   # ⚠️ Crates Rust orphelines
```

⚠️ NOTE : `core/orchestration/` n'existe PAS - c'était une erreur dans l'audit initial.

---

## 3. Cartographie des dépendances

### Core interne (bootstrap.py → kernel.py)

```
core/bootstrap.py
├── autonomy/controller.py
├── autonomy/curiosity.py
├── autonomy/environment.py
├── autonomy/healing.py
├── autonomy/idle.py
├── autonomy/scheduler.py
├── autonomy/weakness.py
├── bootstrap/bootstrapper.py
├── bus/nats_bus.py
├── goals/manager.py
├── kernel.py
├── learning/engine.py
├── learning/modeler.py
├── learning/store.py
├── learning/detector.py
├── learning/generator.py
├── metacognition/engine.py
├── metacognition/load.py
├── metacognition/prioritizer.py
├── metacognition/strategy.py
├── metacognition/trace.py
├── registry/module_registry.py
├── scheduler/scheduler.py
├── state/postgres_state.py
└── state/redis_state.py
```

---

## 4. Points forts

- ✅ Event-driven via NATS
- ✅ Registry pattern pour modules
- ✅ Multi-providers LLM
- ✅ FastAPI pour API Gateway
- ✅ Docker Compose orchestration
- ✅ import-linter configuré

---

## 5. Faiblesses

### Documentation vs Réalité

| Élément | Documentation | Réel |
|---------|---------------|------|
| Stack Core | Go + Python | Python |
| API | gRPC (50051) | FastAPI (8000) |
| agents/ | Vide | 12 fichiers |
| pkg/ | Vide | 2 sous-dossiers |

### Violations

- `interfaces/api/main.py:13` : sys.path hacking
- `plugins/memory/*.py` : import core.memory

### Doublons

- `core/registry/module.py` vs `module_registry.py`

---

## 6. Dette technique

| Priorité | Item | Action |
|----------|------|--------|
| P0 | README obsolète | Mettre à jour (Python, FastAPI, 8000) |
| P0 | sys.path hacking | Package éditable + suppression |
| P1 | Doublons registry | Unifier module.py et module_registry.py |
| P1 | runtime/ inutilisé | Décider (supprimer/documenter) |
| P2 | __pycache__/ | Nettoyer .gitignore |

---

## 7. Recommandations

### Actions immédiates

1. **Corriger README.md** : Python kernel + FastAPI + port 8000
2. **Supprimer sys.path hacking** après `pip install -e .[server,dev]`
3. **Vérifier core/registry/** pour doublon module.py

### Validation

```bash
# Package éditable installé
pip install -e ".[server,dev]"

# Test imports
python3 -c "from core.kernel import CognitiveKernel; print('OK')"

# Nettoyer cache
find . -name "__pycache__" -type d -exec rm -rf {} +
```

---

**Audit validé le 2026-07-19 : agents/ et pkg/ ne sont PAS vides, core/orchestration/ n'existe PAS.**