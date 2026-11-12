"""Adapteurs d'intégration non invasifs pour l'Engineering Memory."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from core.engineering_memory.models import (
    ConfidenceLevel,
    MemoryRecord,
    RecordOrigin,
    RecordType,
    SourceOfFactLevel,
)
from core.engineering_memory.service import EngineeringMemoryService

logger = logging.getLogger(__name__)


@dataclass
class IntegrationStats:
    """State simple permettant de détecter les pertes d'événements."""

    records_accepted: int = 0
    records_failed: int = 0
    last_failure: str = ""


class EngineeringMemoryIntegration:
    """Adaptateur central pour réduirre le couplage entre composants et Obsidian."""

    def __init__(self, service: EngineeringMemoryService, source: str = "ethan.core"):
        self.service = service
        self.source = source
        self.stats = IntegrationStats()

    def _record(self, record: MemoryRecord) -> MemoryRecord | None:
        try:
            stored = self.service.record(record)
            self.stats.records_accepted += 1
            return stored
        except Exception as exc:  # la collecte ne doit jamais masquer l'échec
            self.stats.records_failed += 1
            self.stats.last_failure = str(exc)
            logger.error("Engineering Memory collection failed: %s", exc, exc_info=True)
            return None

    def record_service_event(
        self,
        *,
        component: str,
        event_type: str,
        title: str,
        status: str,
        origin: RecordOrigin = RecordOrigin.OBSERVED,
        source_of_fact: str,
        confidence: ConfidenceLevel = ConfidenceLevel.HIGH,
        details: str = "",
    ) -> MemoryRecord | None:
        now = datetime.now(timezone.utc).isoformat()
        return self._record(
            MemoryRecord(
                id=f"EVT-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}-OBSERVED",
                record_type=RecordType.ENGINEERING_EVENT,
                title=title,
                status=status,
                source_of_fact=source_of_fact,
                provenance_level=SourceOfFactLevel.OBSERVED,
                components=[component],
                created_at=now,
                updated_at=now,
                evidence_refs=[],
                authors=[self.source],
                origin=origin,
                confidence=confidence,
                notes=details,
                tags=[event_type],
                task_id=None,
            )
        )

    def record_agent_lifecycle(
        self,
        *,
        action: str,
        agent_id: str,
        status: str,
        observed: bool,
        details: str = "",
    ) -> MemoryRecord | None:
        event_origin = RecordOrigin.OBSERVED if observed else RecordOrigin.DECLARED
        event_type = f"agent.{action}"
        now = datetime.now(timezone.utc).isoformat()
        return self._record(
            MemoryRecord(
                id=f"EVT-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}-AGENT",
                record_type=RecordType.ENGINEERING_EVENT,
                title=f"Agent {action}: {agent_id}",
                status=status,
                source_of_fact="core/agents/manager.py",
                provenance_level=SourceOfFactLevel.OBSERVED if observed else SourceOfFactLevel.DERIVED,
                components=["CMP-agents"],
                created_at=now,
                updated_at=now,
                evidence_refs=[],
                authors=[self.source],
                origin=event_origin,
                confidence=ConfidenceLevel.HIGH if observed else ConfidenceLevel.MEDIUM,
                notes=details,
                tags=[event_type],
                task_id=agent_id,
            )
        )

    def record_component_state(
        self,
        *,
        component: str,
        previous_state: str,
        new_state: str,
        observed: bool,
    ) -> MemoryRecord | None:
        origin = RecordOrigin.OBSERVED if observed else RecordOrigin.DECLARED
        source_level = SourceOfFactLevel.OBSERVED if observed else SourceOfFactLevel.DERIVED
        confidence = ConfidenceLevel.HIGH if observed else ConfidenceLevel.MEDIUM
        now = datetime.now(timezone.utc).isoformat()
        return self._record(
            MemoryRecord(
                id=f"EVT-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}-STATE",
                record_type=RecordType.ENGINEERING_EVENT,
                title=f"State change: {component}",
                status="RECORDED",
                source_of_fact="core/capability_manager or runtime",
                provenance_level=source_level,
                components=[component],
                created_at=now,
                updated_at=now,
                evidence_refs=[],
                authors=[self.source],
                origin=origin,
                confidence=confidence,
                notes=f"{previous_state} -> {new_state}",
                tags=["component.state_change"],
                task_id=component,
            )
        )

    def record_configuration_change(
        self,
        *,
        domain: str,
        key: str,
        old_value: str,
        new_value: str,
        observed: bool,
    ) -> MemoryRecord | None:
        return self.record_component_state(
            component=f"config/{domain}",
            previous_state=old_value,
            new_state=new_value,
            observed=observed,
        )

    def record_knowledge_operation(
        self,
        *,
        operation: str,
        collection: str,
        item_count: int | None,
        observed: bool,
    ) -> MemoryRecord | None:
        now = datetime.now(timezone.utc).isoformat()
        origin = RecordOrigin.OBSERVED if observed else RecordOrigin.DECLARED
        confidence = ConfidenceLevel.HIGH if observed else ConfidenceLevel.MEDIUM
        source_level = SourceOfFactLevel.OBSERVED if observed else SourceOfFactLevel.DERIVED
        return self._record(
            MemoryRecord(
                id=f"EVT-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}-KNOW",
                record_type=RecordType.ENGINEERING_EVENT,
                title=f"Knowledge operation: {operation}",
                status="RECORDED",
                source_of_fact="core/knowledge",
                provenance_level=source_level,
                components=[f"knowledge/{collection}"],
                created_at=now,
                updated_at=now,
                evidence_refs=[],
                authors=[self.source],
                origin=origin,
                confidence=confidence,
                notes=f"collection={collection}; item_count={item_count}",
                tags=["knowledge.operation", operation],
                task_id=None,
            )
        )


    def record_skill_lifecycle(
        self,
        *,
        action: str,
        skill_id: str,
        status: str,
        observed: bool = True,
    ) -> MemoryRecord | None:
        now = datetime.now(timezone.utc).isoformat()
        origin = RecordOrigin.OBSERVED if observed else RecordOrigin.DECLARED
        source_level = SourceOfFactLevel.OBSERVED if observed else SourceOfFactLevel.DERIVED
        confidence = ConfidenceLevel.HIGH if observed else ConfidenceLevel.MEDIUM
        return self._record(
            MemoryRecord(
                id=f"EVT-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}-SKL",
                record_type=RecordType.ENGINEERING_EVENT,
                title=f"Skill {action}: {skill_id}",
                status="RECORDED",
                source_of_fact="core/skills/store.py",
                provenance_level=source_level,
                components=[f"skill/{skill_id}"],
                created_at=now,
                updated_at=now,
                evidence_refs=[],
                authors=[self.source],
                origin=origin,
                confidence=confidence,
                notes=f"action={action}; status={status}",
                tags=["skill.operation", action],
                task_id=skill_id,
            )
        )
