# Rust / Python — etude architecturale de repartition

Date : 2026-11-04
Statut : proposition architecturale uniquement, sans modification.

## 1. Inventaire factuel

- Modules Python (hors .venv, exemples, tests) : 692
- Modules Rust (hors .git/target) : 13

### Repartition Python (top-level / sous-repertoire)

- `interfaces/cli` : 77
- `interfaces/api` : 62
- `core/llm` : 27
- `core/applications` : 26
- `core/bus` : 24
- `core/security` : 24
- `core/modules` : 23
- `core/skills` : 20
- `core/knowledge` : 19
- `core/memory` : 15
- `core/cognition` : 15
- `core/ethan_types` : 15
- `core/tools` : 14
- `core/plugins` : 13
- `core/state` : 12
- `core/integrations` : 11
- `core/auth` : 11
- `core/orchestrator` : 11
- `core/autonomy` : 10
- `core/rag` : 10
- `core/planner` : 8
- `core/config` : 8
- `core/models` : 8
- `core/engineering_memory` : 8
- `core/learning` : 8
- `core/metacognition` : 7
- `core/capability_manager` : 7
- `interfaces/bridge` : 7
- `core/agents` : 6
- `core/chat` : 6
- `core/persistence` : 6
- `core/deployment` : 6
- `interfaces/channels` : 6
- `core/facts` : 5
- `core/bootstrap` : 5
- `core/registry` : 5
- `core/metrics` : 5
- `scripts/locale-patches` : 5
- `core/capabilities` : 4
- `core/diagnostics` : 4
- `core/approval` : 4
- `core/dedup` : 4
- `core/hardware` : 4
- `core/cost` : 4
- `core/scheduler` : 4

### Repartition Rust

- `examples/craft-fonts` : 5
- `core/rust` : 3
- `interfaces/desktop` : 3
- `core/bus` : 1
- `.venv/lib` : 1

### Modules rust reels

- `core/bus/backends/rust_event_store/src/lib.rs`
- `core/rust/ethan_health/src/main.rs`
- `core/rust/ethan_capability_contract/src/main.rs`
- `core/rust/ethan_capability_contract/src/zz_marker.rs`
- `.venv/lib/python3.11/site-packages/pre_commit/resources/empty_template_main.rs`
- `interfaces/desktop/frontend/src-tauri/build.rs`
- `interfaces/desktop/frontend/src-tauri/src/main.rs`
- `interfaces/desktop/frontend/src-tauri/src/lib.rs`
- `examples/craft-fonts/crates/craft-fonts/build.rs`
- `examples/craft-fonts/crates/craft-fonts/src/parse.rs`
- `examples/craft-fonts/crates/craft-fonts/src/lib.rs`
- `examples/craft-fonts/crates/craft-fonts-tests/tests/fonts.rs`
- `examples/craft-fonts/crates/craft-fonts-tests/src/lib.rs`

## 2. Hypotheses et recommandations
- Rust absorbe detection/calc/validation et stockage.
- Les modules IA, agentique et machine learning restent en Python.
- Pas de nouvelle orchestration; reutiliser facade et HROT.

### Orientation generale

| Famille | Orientation | Rationale |
|---|---|---|
| `core/knowledge` | KEEP_PYTHON | embeddings, recherche, ML |
| `core/plugins` | HYBRID | lifecycle et wrappers |
| `core/applications` | REVIEW_REQUIRED | logique metier sensible |
| `core/hrot` | KEEP_PYTHON | autorite et contrats HROT |
| `core/rust/ethan_health` | MIGRATE_TO_RUST | detection pure |
| `core/bus/backends/rust_event_store` | MIGRATE_TO_RUST | persistence performante |

### Decisions restantes
- Transport HROT gateway;
- contrat d interface entre Python et Rust;
- strategie de validation et rollback.


## Decisions confirmees

- Python source de verite; Rust services specialises; HROT authority.
