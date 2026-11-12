# ETHAN CLI Test Suite

Test suite complet pour l'ETHAN CLI — couvre l'ensemble des commandes, modules core, intégrations API, scénarios d'échec et gestion des timeouts.

## Structure

```
tests/cli/ethan/
├── TEST_PLAN.md              # Plan de test détaillé (266+ tests)
├── README.md                 # Ce fichier
├── conftest.py               # Fixtures partagées (mock API, isolation FS)
├── helpers.py                # Utilitaires de test (écriture fichiers, mocks)
├── unit/                     # Tests unitaires (modules core)
│   ├── test_registry.py      # 12 tests
│   ├── test_entrypoint.py    # 6 tests
│   ├── test_client.py        # 8 tests
│   ├── test_colors.py        # 18 tests
│   ├── test_config.py        # 14 tests
│   ├── test_daemon.py        # 10 tests
│   ├── test_errors.py        # 12 tests
│   ├── test_intent.py        # 16 tests
│   ├── test_loading.py       # 9 tests
│   ├── test_logging.py       # 8 tests
│   ├── test_memory.py        # 16 tests
│   ├── test_streaming.py     # 8 tests
│   ├── test_ux.py            # 10 tests
│   ├── test_first_run.py     # 5 tests
│   └── test_discovery.py     # 8 tests
├── commands/                 # Tests des commandes CLI
│   ├── test_chat.py          # 14 tests
│   ├── test_status.py        # 6 tests
│   ├── test_logs.py          # 8 tests
│   ├── test_memory_cmd.py    # 6 tests
│   ├── test_daemon_cmd.py    # 6 tests
│   └── test_suggest.py       # 5 tests
└── integration/              # Tests d'intégration
    ├── test_api_integration.py       # 8 tests
    ├── test_timeout_handling.py      # 8 tests
    ├── test_failure_scenarios.py     # 12 tests
    └── test_invalid_commands.py      # 8 tests
```

## Exécution

```bash
# Tous les tests ETHAN CLI
pytest tests/cli/ethan/ -v

# Tests unitaires uniquement
pytest tests/cli/ethan/unit/ -v

# Tests de commandes uniquement
pytest tests/cli/ethan/commands/ -v

# Tests d'intégration uniquement
pytest tests/cli/ethan/integration/ -v

# Un fichier spécifique
pytest tests/cli/ethan/unit/test_registry.py -v

# Avec couverture
pytest tests/cli/ethan/ --cov=cli --cov-report=term-missing -v

# Exécution parallèle
pytest tests/cli/ethan/ -n auto -v
```

## Stratégie de Mock

| Dépendance | Approche |
|---|---|
| API HTTP (`urlopen`) | `mock_api_server` fixture |
| Système de fichiers | `tmp_path` + `_isolate_ethan_dir` |
| `os.kill` | `patch_os_kill` context manager |
| `os.fork` | `patch_fork` context manager |
| `threading.Thread` | Threads réels autorisés (daemon) |
| Variables d'environnement | `monkeypatch.setenv` |
| `~/.ethan` | Redirigé vers `tmp_path` |
| `~/.config/ethan` | Redirigé vers `tmp_path` |

## Couverture Cible

- **`cli/` module**: ≥93% de couverture de ligne
- **Modules core**: 90-100% selon le module
- **Command files**: 90%+ chacun
- **Temps d'exécution**: <10 secondes (pas d'appels réseau réels)