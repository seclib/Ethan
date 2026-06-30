"""ETHAN Core — Facts Module

Stockage de faits atomiques (subject, predicate, object, category)
avec observations, relations et recherche FTS5.
Mémoire structurée parallèle au stockage événementiel existant.
"""

from .store import FactStore
from .types import Fact, FactObservation, FactRelation, FactStatus, FactCategory, DecayPolicy
from .ingest import MemoryIngest, IngestResult
from .retrieval import MemoryRetrieval, ScoredFact

__version__ = "1.1.0"
__all__ = [
    "FactStore", "Fact", "FactObservation", "FactRelation",
    "FactStatus", "FactCategory", "DecayPolicy",
    "MemoryIngest", "IngestResult",
    "MemoryRetrieval", "ScoredFact",
]