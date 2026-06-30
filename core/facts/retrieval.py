"""MemoryRetrieval — Récupération scorée de faits pertinents.

Score = importance × récence × pertinence × confiance.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime

from core.facts.types import DecayPolicy, Fact, FactStatus
from core.facts.store import FactStore

logger = logging.getLogger(__name__)

_HALFLIFE_DAYS: dict[DecayPolicy, float] = {
    DecayPolicy.NONE: float("inf"),
    DecayPolicy.VERY_SLOW: 730.0,
    DecayPolicy.SLOW: 365.0,
    DecayPolicy.MEDIUM: 90.0,
    DecayPolicy.FAST: 14.0,
}

_BM25_CAP = 20.0


@dataclass
class ScoredFact:
    fact: Fact
    score: float
    relevance: float = 0.0
    recency: float = 1.0
    contradictions: list[Fact] = field(default_factory=list)


class MemoryRetrieval:
    def __init__(self, store: FactStore):
        self._store = store

    def retrieve(self, query: str, k: int = 5, now: datetime | None = None) -> list[ScoredFact]:
        ref = now or datetime.utcnow()
        candidates = self._store.search(query, k=k * 4) if query else []
        if not candidates:
            cold = self._store.list_by_status(FactStatus.ACTIVE, limit=k)
            return [ScoredFact(fact=f, score=0.0, relevance=0.0) for f in cold]
        scored = []
        for fsr in candidates:
            if fsr.fact.status != FactStatus.ACTIVE:
                continue
            relevance = _bm25_to_relevance(fsr.score)
            recency = _recency_factor(fsr.fact, ref)
            total = fsr.fact.importance * recency * relevance * fsr.fact.confidence
            scored.append(ScoredFact(fact=fsr.fact, score=total, relevance=relevance, recency=recency))
        scored.sort(key=lambda s: -s.score)
        return scored[:k]


def _bm25_to_relevance(bm25: float) -> float:
    if bm25 == 0.0:
        return 0.0
    rel = math.exp(-min(abs(bm25), _BM25_CAP) / _BM25_CAP)
    return max(0.0, min(1.0, rel))


def _recency_factor(fact: Fact, now: datetime) -> float:
    halflife = _HALFLIFE_DAYS.get(fact.decay_policy, 90.0)
    if halflife == float("inf"):
        return 1.0
    delta = max(0.0, (now - fact.last_seen_at).total_seconds() / 86400.0)
    return 0.5 ** (delta / halflife)
