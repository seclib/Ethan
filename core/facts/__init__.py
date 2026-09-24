"""ETHAN Core — Facts Module

Stockage de faits atomiques (subject, predicate, object, category)
avec observations, relations et recherche FTS5.
Mémoire structurée parallèle au stockage événementiel existant.
"""

from .ingest import IngestResult, MemoryIngest
from .retrieval import MemoryRetrieval, ScoredFact
from .store import FactStore
from .types import DecayPolicy, Fact, FactCategory, FactObservation, FactRelation, FactStatus

__version__ = "1.1.0"
__all__ = [
    "FactStore",
    "Fact",
    "FactObservation",
    "FactRelation",
    "FactStatus",
    "FactCategory",
    "DecayPolicy",
    "MemoryIngest",
    "IngestResult",
    "MemoryRetrieval",
    "ScoredFact",
]
