# Contrat d'interface Event Bus — Migration Rust (Phase 3)

**Statut :** Conditionnel — déclenché uniquement si tests de charge confirment un goulot d'étranglement.

**Référence :** `docs/architecture/RUST-MIGRATION-AUDIT.md`

## Composant cible : Event Store Backend

| Implémentation actuelle | Cible | Justification |
|-------------------------|-------|---------------|
| `core/bus/backends/nats_jetstream.py` (read vide) | Rust + PyO3 | Performance, typage strict, fiabilité |
| `core/bus/backends/redis_streams.py` (read vide) | Rust + PyO3 | Idem |
| `core/bus/store.py:188` (rétention non implémentée) | Rust + PyO3 | Rétention des événements |

## Interface Rust (via PyO3)

```rust
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct Event {
    pub id: String,
    pub r#type: String,
    pub timestamp: DateTime<Utc>,
    pub payload: serde_json::Value,
    pub context: serde_json::Value,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct Position {
    pub stream: String,
    pub offset: u64,
}

#[pyfunction]
pub fn write(event: Event) -> PyResult<Position> { ... }

#[pyfunction]
pub fn read(pattern: String, start: DateTime<Utc>) -> PyResult<Vec<Event>> { ... }

#[pyfunction]
pub fn save_checkpoint(stream: String, position: Position) -> PyResult<()> { ... }

#[pyfunction]
pub fn replay(from: DateTime<Utc>) -> PyResult<Vec<Event>> { ... }
```

## Compatibilité

- Événements sérialisés en `serde_json` (compatibilité JSON existante)
- Même schéma d'événement : `{type, timestamp, payload, context}`
- Aucun changement côté modules Core (ils publient/consomment via le Event Bus)

## Plan d'expérimentation

1. Créer `core/bus/backends/rust_event_store/` avec le code Rust + PyO3
2. Créer des tests de charge comparant Python vs Rust
3. Si Rust gagne >30% sur latence/throughput, activer via configuration
4. Sinon, maintenir l'implémentation Python

## Fichiers à ne pas modifier pendant la phase d'expérimentation

- `core/bus/nats_bus.py`
- `core/bus/router.py`
- `core/bus/interface.py`
- `core/kernel.py`

Ces fichiers définissent le contrat d'interface et ne doivent pas changer.