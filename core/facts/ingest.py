"""MemoryIngest — Pipeline d'extraction LLM et réconciliation de faits."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from core.facts.store import FactStore
from core.facts.types import (
    DecayPolicy, Fact, FactCategory,
    FactRelationType, FactStatus, ObservationType,
)

logger = logging.getLogger(__name__)

CONFIDENCE_INFERENCE = 0.55
CONFIDENCE_EXPLICIT = 0.75
CONFIDENCE_CORRECTION = 0.90
CONFIRM_DELTA = 0.05
CONFIDENCE_CAP = 0.99

_DECAY_BY_CATEGORY: dict[FactCategory, DecayPolicy] = {
    FactCategory.IDENTITY: DecayPolicy.NONE,
    FactCategory.KNOWLEDGE: DecayPolicy.VERY_SLOW,
    FactCategory.RULE: DecayPolicy.SLOW,
    FactCategory.RELATIONSHIP: DecayPolicy.SLOW,
    FactCategory.PREFERENCE: DecayPolicy.MEDIUM,
    FactCategory.PROJECT: DecayPolicy.MEDIUM,
    FactCategory.GOAL: DecayPolicy.FAST,
    FactCategory.SKILL: DecayPolicy.MEDIUM,
    FactCategory.EVENT: DecayPolicy.FAST,
    FactCategory.OBSERVATION: DecayPolicy.MEDIUM,
    FactCategory.SYSTEM: DecayPolicy.NONE,
}

_STABLE_CATEGORIES: frozenset[FactCategory] = frozenset({
    FactCategory.IDENTITY,
    FactCategory.GOAL,
    FactCategory.RULE,
})


@dataclass
class IngestResult:
    """Résultat d'une ingestion complète."""
    facts_created: list[Fact] = field(default_factory=list)
    facts_confirmed: list[Fact] = field(default_factory=list)
    facts_superseded: list[Fact] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    arbiter_calls: int = 0

    @property
    def total_facts(self) -> int:
        return len(self.facts_created) + len(self.facts_confirmed)


class MemoryIngest:
    """Pipeline d'ingestion de faits depuis des sources textuelles.

    Utilise un LLM pour extraire les faits et les réconcilie avec
    le FactStore existant (confirm / supersede / new).
    """

    def __init__(
        self,
        store: FactStore,
        llm_extract_fn=None,
        llm_arbiter_fn=None,
    ):
        self._store = store
        self._llm_extract = llm_extract_fn or self._default_extract
        self._llm_arbiter = llm_arbiter_fn or self._default_arbiter

    async def ingest(
        self,
        content: str,
        source: str = "conversation",
        event_type: str = "exchange",
        metadata: dict | None = None,
    ) -> IngestResult:
        """Point d'entrée unique : extraire et réconcilier des faits."""
        result = IngestResult()

        try:
            candidates = await self._extract_facts(content, source)
        except Exception as e:
            logger.error("MemoryIngest: extraction failed: %s", e)
            result.errors.append(f"Extraction failed: {e}")
            return result

        if not candidates:
            return result

        for candidate in candidates:
            try:
                self._reconcile(candidate, result)
            except Exception as e:
                logger.warning("MemoryIngest: reconcile error: %s", e)
                result.errors.append(str(e))

        logger.info(
            "MemoryIngest done: %d created, %d confirmed, %d superseded",
            len(result.facts_created),
            len(result.facts_confirmed),
            len(result.facts_superseded),
        )
        return result

    async def _extract_facts(self, content: str, source: str) -> list[dict]:
        raw = await self._llm_extract(content, source)
        return self._parse_extract_response(raw)

    async def _default_extract(self, content: str, source: str) -> str:
        """Extracteur par défaut : retourne JSON vide.
        À remplacer par un vrai provider LLM."""
        logger.warning("MemoryIngest: no LLM configured, using default")
        return '{"facts": []}'

    async def _default_arbiter(self, prompt: str) -> str:
        return '{"verdict": "new", "target_fact_id": null, "notes": "no arbiter"}'

    def _reconcile(self, candidate: dict, result: IngestResult) -> None:
        subject = candidate.get("subject", "").strip()
        predicate = candidate.get("predicate", "").strip()
        obj = candidate.get("object", "").strip()
        cat_str = candidate.get("category", "knowledge")
        importance = float(candidate.get("importance", 0.5))

        if not all([subject, predicate, obj]):
            return

        try:
            category = FactCategory(cat_str)
        except ValueError:
            category = FactCategory.KNOWLEDGE

        decay = _DECAY_BY_CATEGORY.get(category, DecayPolicy.MEDIUM)
        initial_conf = (
            CONFIDENCE_EXPLICIT if candidate.get("confidence_source") == "explicit"
            else CONFIDENCE_CORRECTION if candidate.get("confidence_source") == "correction"
            else CONFIDENCE_INFERENCE
        )

        existing = self._store.find_active(subject, predicate, category.value)

        if existing is None:
            fact = Fact(
                subject=subject, predicate=predicate, object=obj,
                category=category, confidence=initial_conf,
                importance=importance, decay_policy=decay,
                source=candidate.get("confidence_source", "inference"),
                status=FactStatus.ACTIVE,
            )
            self._store.insert(fact)
            result.facts_created.append(fact)

        elif existing.object.strip().lower() == obj.strip().lower():
            new_conf = min(existing.confidence + CONFIRM_DELTA, CONFIDENCE_CAP)
            existing.confidence = new_conf
            existing.support_count += 1
            existing.last_seen_at = datetime.utcnow()
            self._store.update(existing)
            self._store.record_observation(
                fact_id=existing.id, event_id="",
                observation_type=ObservationType.CONFIRM,
                confidence_delta=CONFIRM_DELTA,
            )
            result.facts_confirmed.append(existing)

        elif category in _STABLE_CATEGORIES:
            existing.status = FactStatus.SUPERSEDED
            self._store.update(existing)
            new_fact = Fact(
                subject=subject, predicate=predicate, object=obj,
                category=category, confidence=initial_conf,
                importance=importance, decay_policy=decay,
                source=candidate.get("confidence_source", "inference"),
                status=FactStatus.ACTIVE,
            )
            self._store.insert(new_fact)
            self._store.link(new_fact.id, existing.id, FactRelationType.SUPERSEDES)
            result.facts_created.append(new_fact)
            result.facts_superseded.append(existing)
        else:
            fact = Fact(
                subject=subject, predicate=predicate, object=obj,
                category=category, confidence=initial_conf,
                importance=importance, decay_policy=decay,
                source=candidate.get("confidence_source", "inference"),
                status=FactStatus.ACTIVE,
            )
            self._store.insert(fact)
            result.facts_created.append(fact)

    @staticmethod
    def _parse_extract_response(raw: str) -> list[dict]:
        """Parse la réponse JSON du LLM avec tolérance ```json...```."""
        candidate = raw.strip()
        m = re.search(r"```(?:json)?\s*(.*?)\s*```", candidate, re.DOTALL)
        if m:
            candidate = m.group(1)
        match = re.search(r"\{.*\}", candidate, re.DOTALL)
        if not match:
            return []
        try:
            data = json.loads(match.group())
        except json.JSONDecodeError:
            return []
        raw_facts = data.get("facts", []) if isinstance(data, dict) else []
        return [
            item for item in raw_facts
            if isinstance(item, dict)
            and item.get("subject") and item.get("predicate") and item.get("object")
        ]
