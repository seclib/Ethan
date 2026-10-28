# ETHAN Knowledge Base — Guide d'utilisation

## Vue d'ensemble

Le module `core/knowledge/agent_traces` collecte, normalise et archive les conversations
des agents IA (Cline, Codex, Copilot) en fichiers Markdown portables.

## Installation

Aucune dépendance supplémentaire requise. Le module utilise uniquement la bibliothèque
standard Python (json, pathlib, hashlib, re, sqlite3).

Pour la lecture des fichiers YAML (Copilot workspace.yaml), PyYAML est optionnel :
```bash
pip install pyyaml  # optionnel
```

## Utilisation

### Synchronisation manuelle

```bash
# Synchroniser tous les agents
python scripts/ethan-knowledge-sync.py

# Synchroniser des agents spécifiques
python scripts/ethan-knowledge-sync.py --agents cline,codex

# Spécifier un répertoire personnalisé
python scripts/ethan-knowledge-sync.py --root /path/to/knowledge
```

### Utilisation programmatique

```python
from core.knowledge.agent_traces import SyncEngine

engine = SyncEngine()  # utilise ~/ethan-knowledge par défaut
results = engine.sync()

print(f"Collectées: {results['collected']}")
print(f"Doublons: {results['duplicates']}")
print(f"Ignorées: {results['ignored']}")
print(f"Erreurs: {results['errors']}")
```

## Structure de la base de connaissance

```
~/ethan-knowledge/
├── INDEX.md                    # Index principal
├── raw/                        # Archives brutes (non modifiées)
│   ├── cline/tasks/<id>/
│   ├── codex/sessions/<date>/
│   └── copilot/session-state/<uuid>/
├── sessions/                   # Archives Markdown normalisées
│   ├── cline/<date>/<id>.md
│   ├── codex/<date>/<id>.md
│   └── copilot/<date>/<id>.md
├── index/                      # Index de recherche
├── summaries/                  # Synthèses par agent
│   └── by-agent/
│       ├── cline-summary.md
│       ├── codex-summary.md
│       └── copilot-summary.md
└── metadata/
    └── sync-state.json         # État de synchronisation
```

## Sécurité

- Les secrets sont automatiquement filtrés (clés API, tokens, mots de passe, JWT)
- Les fichiers d'authentification (auth.json) ne sont jamais copiés
- Les historiques sources ne sont jamais modifiés
- Chaque détection de secret est signalée dans l'archive Markdown

## Limites

- Les conversations de l'extension ChatGPT (VS Code) ne sont pas accessibles localement
- Les checkpoints Cline (hashes Git) ne sont pas extraits
- Les données SQLite Codex/Copilot nécessitent une extraction manuelle
- Les sessions Copilot compressées perdent les messages originaux (seul le résumé est conservé)

## Tests

```bash
python -m pytest tests/test_agent_traces.py -v
```
