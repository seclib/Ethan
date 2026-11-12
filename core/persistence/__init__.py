"""Persistence — moteur de stockage des données cœur d'ETHAN.

Deux backends disponibles :
- Redis (stockage vivant) : états temporaires, caches, logs
- PostgreSQL (source de vérité) : données persistantes

Les backends sont agnostiques de driver (aucun import ``redis``/``asyncpg``
ici — ADR-1005) : les factories de driver sont injectées depuis
``interfaces/api/persistence/backend.py``.
"""
from __future__ import annotations

from core.persistence.backends import BackendNotConnected, PostgresBackend, RedisBackend
from core.persistence.types import PersistenceConfig
from core.persistence.storage import Persistence

__all__ = [
    "Persistence",
    "PersistenceConfig",
    "RedisBackend",
    "PostgresBackend",
    "BackendNotConnected",
]

