"""Core lifecycle manager for long-running ETHAN missions."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any
from uuid import uuid4

from core.bus.interface import EventBus
from core.ethan_types.event import Event, EventType
from core.missions.types import Mission, MissionStatus, MissionStep, MissionVerdict, StepStatus
from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)


class MissionManager:
    """Own mission objectives, ordered steps, progress and state transitions."""

    _DOMAIN = "missions"

    def __init__(
        self,
        event_bus: EventBus | None = None,
        store: CoreRecordStore | None = None,
    ) -> None:
        self._bus = event_bus
        self._store = store or CoreRecordStore()

    async def create(
        self,
        title: str,
        description: str = "",
        steps: list[dict[str, Any]] | None = None,
        workspace_path: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> Mission:
        """Create a mission and its ordered work steps."""
        normalized_title = title.strip()
        if not normalized_title:
            raise ValueError("Mission title must not be empty")
        mission = Mission(
            id=str(uuid4()),
            title=normalized_title,
            description=description,
            workspace_path=workspace_path,
            metadata=dict(metadata or {}),
        )
        for index, step_data in enumerate(steps or []):
            mission.steps.append(self._new_step(mission.id, step_data, index))
        self._refresh_progress(mission)
        await self._persist(mission)
        await self._publish(EventType.MISSION_CREATED, "mission.created", {"mission": mission.to_dict()})
        return mission

    async def get(self, mission_id: str) -> Mission | None:
        """Retrieve a mission by id."""
        data = await self._store.get(self._DOMAIN, mission_id)
        return Mission.from_dict(data) if data else None

    async def list(self, status: MissionStatus | str | None = None) -> list[Mission]:
        """List missions, optionally by state."""
        state = MissionStatus(status) if status is not None else None
        missions = [Mission.from_dict(data) for data in await self._store.list(self._DOMAIN)]
        return [mission for mission in missions if state is None or mission.status == state]

    async def update(self, mission_id: str, data: dict[str, Any]) -> Mission | None:
        """Update mission metadata or top-level lifecycle state."""
        mission = await self.get(mission_id)
        if mission is None:
            return None
        if "title" in data:
            title = str(data["title"]).strip()
            if not title:
                raise ValueError("Mission title must not be empty")
            mission.title = title
        if "description" in data:
            mission.description = str(data["description"])
        if "status" in data:
            mission.status = MissionStatus(data["status"])
        if "workspace_path" in data:
            mission.workspace_path = str(data["workspace_path"])
        if "artifacts" in data:
            mission.artifacts.update(dict(data["artifacts"]))
        if "metadata" in data:
            mission.metadata.update(dict(data["metadata"]))
        mission.updated_at = datetime.utcnow()
        self._refresh_progress(mission)
        await self._persist(mission)
        await self._publish(EventType.MISSION_UPDATED, "mission.updated", {"mission": mission.to_dict()})
        return mission

    async def delete(self, mission_id: str) -> bool:
        """Delete a mission and all of its embedded tasks."""
        return await self._store.delete(self._DOMAIN, mission_id)

    async def add_step(self, mission_id: str, data: dict[str, Any]) -> MissionStep:
        """Append a task to a mission and return the generated step."""
        mission = await self._require(mission_id)
        step = self._new_step(mission.id, data, len(mission.steps))
        mission.steps.append(step)
        await self._touch_and_persist(mission)
        return step

    async def update_step(
        self,
        mission_id: str,
        step_id: str,
        data: dict[str, Any],
    ) -> MissionStep:
        """Update a task's result, error, dependency metadata or state."""
        mission = await self._require(mission_id)
        step = self._require_step(mission, step_id)
        if "title" in data:
            title = str(data["title"]).strip()
            if not title:
                raise ValueError("Mission step title must not be empty")
            step.title = title
        for field_name in ("description", "success_criterion", "verification_command", "result", "error"):
            if field_name in data:
                setattr(step, field_name, data[field_name])
        if "depends_on" in data:
            step.depends_on = list(data["depends_on"])
        if "access_level" in data:
            step.access_level = int(data["access_level"])
        if "status" in data:
            step.status = StepStatus(data["status"])
            if step.status == StepStatus.COMPLETED:
                step.completed_at = datetime.utcnow()
        step.updated_at = datetime.utcnow()
        await self._touch_and_persist(mission)
        return step

    async def verify_step(self, mission_id: str, step_id: str) -> dict[str, Any]:
        """Record successful verification and await an explicit approval."""
        mission = await self._require(mission_id)
        step = self._require_step(mission, step_id)
        if step.status in {StepStatus.CANCELLED, StepStatus.SKIPPED}:
            raise ValueError(f"Step {step_id} cannot be verified from {step.status.value}")
        step.verified = True
        step.status = StepStatus.WAITING_APPROVAL
        step.updated_at = datetime.utcnow()
        await self._touch_and_persist(mission)
        await self._publish(
            EventType.MISSION_STEP_VERIFIED,
            "mission.step.verified",
            {"mission_id": mission_id, "step_id": step_id, "verified": True},
        )
        return {"verified": True, "mission_id": mission_id, "step_id": step_id}

    async def approve_step(self, mission_id: str, step_id: str) -> dict[str, Any]:
        """Approve a verified step and advance the mission progress."""
        mission = await self._require(mission_id)
        step = self._require_step(mission, step_id)
        if not step.verified:
            raise ValueError(f"Step {step_id} must be verified before approval")
        step.status = StepStatus.COMPLETED
        step.completed_at = datetime.utcnow()
        step.updated_at = step.completed_at
        self._refresh_progress(mission)
        completed_now = mission.steps_total > 0 and mission.steps_completed == mission.steps_total
        if completed_now:
            mission.status = MissionStatus.COMPLETED
            mission.verdict = MissionVerdict.SUCCESS
            mission.completed_at = datetime.utcnow()
        mission.updated_at = datetime.utcnow()
        await self._persist(mission)
        await self._publish(
            EventType.MISSION_STEP_APPROVED,
            "mission.step.approved",
            {"mission_id": mission_id, "step_id": step_id},
        )
        if completed_now:
            await self._publish(
                EventType.MISSION_COMPLETED,
                "mission.completed",
                {"mission": mission.to_dict()},
            )
        return {"status": "approved", "mission_id": mission_id, "step_id": step_id}

    async def _touch_and_persist(self, mission: Mission) -> None:
        mission.updated_at = datetime.utcnow()
        self._refresh_progress(mission)
        await self._persist(mission)
        await self._publish(EventType.MISSION_UPDATED, "mission.updated", {"mission": mission.to_dict()})

    @staticmethod
    def _new_step(mission_id: str, data: dict[str, Any], default_order: int) -> MissionStep:
        title = str(data.get("title", "")).strip()
        if not title:
            raise ValueError("Mission step title must not be empty")
        return MissionStep(
            id=str(uuid4()),
            mission_id=mission_id,
            title=title,
            description=str(data.get("description", "")),
            success_criterion=str(data.get("success_criterion", "")),
            verification_command=data.get("verification_command"),
            access_level=int(data.get("access_level", 0)),
            depends_on=list(data.get("depends_on", [])),
            order=int(data.get("order", default_order)),
        )

    @staticmethod
    def _refresh_progress(mission: Mission) -> None:
        mission.steps_total = len(mission.steps)
        mission.steps_completed = sum(step.status == StepStatus.COMPLETED for step in mission.steps)

    async def _require(self, mission_id: str) -> Mission:
        mission = await self.get(mission_id)
        if mission is None:
            raise ValueError(f"Mission {mission_id} not found")
        return mission

    @staticmethod
    def _require_step(mission: Mission, step_id: str) -> MissionStep:
        for step in mission.steps:
            if step.id == step_id:
                return step
        raise ValueError(f"Step {step_id} not found in mission {mission.id}")

    async def _persist(self, mission: Mission) -> None:
        await self._store.save(self._DOMAIN, mission.id, mission.to_dict())

    async def _publish(self, event_type: EventType, subject: str, payload: dict[str, Any]) -> None:
        if self._bus is None:
            return
        await self._bus.publish(subject, Event(type=event_type, source="mission-manager", payload=payload))
