# ETHAN CLI Benchmark Suite

Suite de benchmarks pour mesurer la performance et la réactivité du CLI ETHAN.

## Architecture

```
tests/benchmarks/
├── __init__.py              # Export public API
├── benchmark_runner.py       # Runner, Result, Report, Metric
├── cold_start.py             # Groupe A: Startup & Discovery
├── commands.py               # Groupe B: Command performance
├── api_latency.py            # Groupe C: API latency
├── daemon.py                 # Groupe D: Daemon impact
├── streaming.py              # Groupe E: Streaming/rendering
├── results/                  # Rapports sauvegardés
│   └── .gitkeep
└── README.md                 # Ce fichier
```

## Métriques mesurées

### Groupe A — Cold Start & Discovery
| Métrique | Unité | Seuil warn | Seuil fail |
|----------|-------|-----------|------------|
| `avg_cold_start_ms` | ms | 500 | 2000 |
| `avg_warm_start_ms` | ms | 200 | 500 |
| `avg_discovery_ms` | ms | 200 | 500 |
| `commands_found` | count | — | — |

### Groupe B — Commandes
| Métrique | Unité | Seuil warn | Seuil fail |
|----------|-------|-----------|------------|
| `avg_response_ms` (help) | ms | 200 | 1000 |
| `avg_response_ms` (other) | ms | 500 | 2000 |

### Groupe C — API
| Métrique | Unité | Seuil warn | Seuil fail |
|----------|-------|-----------|------------|
| `avg_latency_ms` (health) | ms | 200 | 1000 |
| `avg_latency_ms` (state) | ms | 500 | 2000 |
| `p50_latency_ms` | ms | 300 | 1000 |
| `p95_latency_ms` | ms | 800 | 3000 |
| `p99_latency_ms` | ms | 1500 | 5000 |

### Groupe D — Daemon
| Métrique | Unité | Seuil warn | Seuil fail |
|----------|-------|-----------|------------|
| `avg_no_daemon_ms` | ms | 500 | 2000 |
| `avg_with_daemon_ms` | ms | 300 | 1000 |
| `daemon_rss_mb` | MB | 50 | 200 |
| `daemon_cpu_pct` | % | 10 | 50 |

### Groupe E — Streaming
| Métrique | Unité | Seuil warn | Seuil fail |
|----------|-------|-----------|------------|
| `streamer_init_ms` | ms | 5 | 20 |
| `streamer_write_100chunks_ms` | ms | 50 | 200 |
| `render_1000_lines_ms` | ms | 100 | 500 |

## Utilisation

### CLI ETHAN

```bash
# Tout exécuter
ethan bench

# Groupe spécifique
ethan bench --cold
ethan bench --commands
ethan bench --api
ethan bench --daemon
ethan bench --streaming

# Options
ethan bench --verbose      # Sortie détaillée
ethan bench --json         # Sortie JSON
ethan bench --md           # Sauvegarde rapport Markdown

# Combinaison
ethan bench --cold --commands --json
```

### API Python

```python
from tests.benchmarks import BenchmarkRunner

# Tout exécuter
runner = BenchmarkRunner()
report = runner.run_all()

# Score global
print(f"Score: {report.overall_score:.0f}/100")

# Sauvegarder
report.save_json("report.json")
report.save_markdown("report.md")

# Format dict
data = report.to_dict()
```

## Rapport

Les rapports sont sauvegardés dans `tests/benchmarks/results/` :

- `benchmark_YYYYMMDD_HHMMSS.json` — Format JSON
- `benchmark_YYYYMMDD_HHMMSS.md` — Format Markdown

## CI/CD

Pour intégrer dans GitHub Actions :

```yaml
- name: Run CLI benchmarks
  run: ethan bench --json
  env:
    ETHAN_BENCH: 1
```

## Instrumentation

Le benchmark s'appuie sur `cli/core/telemetry.py` qui fournit :

- `CLITelemetry` — Timers, compteurs et snapshots
- `benchmark` — Context manager `with benchmark("label"):`
- `telemetry` — Singleton global

Activation via variable d'environnement :
```bash
ETHAN_BENCH=1 ethan bench
```

## Ajouter un nouveau benchmark

1. Créer un fichier dans `tests/benchmarks/` avec une classe exposant `run() -> list[BenchmarkResult]`
2. Importer et enregistrer dans `__init__.py`
3. Ajouter la route dans `BenchmarkRunner._run_group()`
4. Ajouter le flag CLI correspondant dans `cli/commands/bench.py`