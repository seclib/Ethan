use chrono::{DateTime, Utc};
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

/// Événement ETHAN — schéma compatible avec l'implémentation Python.
#[derive(Serialize, Deserialize, Clone, Debug)]
#[pyclass]
pub struct Event {
    pub id: String,
    #[pyo3(get, set)]
    pub r#type: String,
    #[pyo3(get, set)]
    pub timestamp: DateTime<Utc>,
    #[pyo3(get, set)]
    pub payload: serde_json::Value,
    #[pyo3(get, set)]
    pub context: serde_json::Value,
}

/// Position dans l'Event Store (stream + offset).
#[derive(Serialize, Deserialize, Clone, Debug)]
#[pyclass]
pub struct Position {
    #[pyo3(get, set)]
    pub stream: String,
    #[pyo3(get, set)]
    pub offset: u64,
}

/// Écrit un événement dans l'Event Store.
///
/// Retourne la position de l'événement écrit.
#[pyfunction]
fn write(event: Event) -> PyResult<Position> {
    // TODO: implémenter l'écriture vers NATS JetStream ou Redis Streams
    // selon la configuration du backend actif.
    Ok(Position {
        stream: "default".to_string(),
        offset: 0,
    })
}

/// Lit des événements depuis l'Event Store.
///
/// `pattern` est un filtre de sujet (ex: "skills.>" pour tous les événements skills).
/// `start` est la date/heure de début de lecture.
#[pyfunction]
fn read(pattern: String, start: DateTime<Utc>) -> PyResult<Vec<Event>> {
    // TODO: implémenter la lecture depuis le backend actif.
    Ok(vec![])
}

/// Sauvegarde un point de contrôle (checkpoint) pour un stream donné.
#[pyfunction]
fn save_checkpoint(stream: String, position: Position) -> PyResult<()> {
    // TODO: implémenter la sauvegarde de checkpoint.
    Ok(())
}

/// Rejoue les événements depuis une date donnée.
#[pyfunction]
fn replay(from: DateTime<Utc>) -> PyResult<Vec<Event>> {
    // TODO: implémenter le replay depuis le backend actif.
    Ok(vec![])
}

/// Module Python exposé.
#[pymodule]
fn ethan_event_store(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Event>()?;
    m.add_class::<Position>()?;
    m.add_function(wrap_pyfunction!(write, m)?)?;
    m.add_function(wrap_pyfunction!(read, m)?)?;
    m.add_function(wrap_pyfunction!(save_checkpoint, m)?)?;
    m.add_function(wrap_pyfunction!(replay, m)?)?;
    Ok(())
}