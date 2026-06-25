"""Self-Model Updater — Maintains system skills and confidence model."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from kernel.state.redis_state import RedisLiveState
from sdk.learning import SelfModel

logger = logging.getLogger(__name__)


class SelfModelUpdater:
    """Updates system self-model based on experience outcomes."""

    def __init__(self, redis: RedisLiveState):
        self.redis = redis
        self.model_key = "system:self_model"
        self.default_skills = {
            "linux": 0.5,
            "docker": 0.5,
            "reasoning": 0.5,
            "planning": 0.5,
            "execution": 0.5,
            "memory": 0.5,
        }

    async def load(self) -> SelfModel:
        """Load current self-model from Redis."""
        data = await self.redis.get(self.model_key)
        if not data:
            model = SelfModel(skills=dict(self.default_skills))
            await self.save(model)
            return model

        # Merge with defaults in case new skills were added
        skills = dict(self.default_skills)
        skills.update(data.get("skills", {}))
        return SelfModel(
            skills=skills,
            reliability=data.get("reliability", 0.0),
            error_rate=data.get("error_rate", 0.0),
            total_tasks=data.get("total_tasks", 0),
            successful_tasks=data.get("successful_tasks", 0),
            failed_tasks=data.get("failed_tasks", 0),
            updated_at=data.get("updated_at", ""),
        )

    async def save(self, model: SelfModel) -> None:
        """Persist self-model to Redis."""
        await self.redis.set(self.model_key, model.dict(), ttl=86400)
        logger.debug(f"Self-model saved: reliability={model.reliability:.2f} error_rate={model.error_rate:.2f}")

    async def update_skill(self, skill: str, outcome: str) -> None:
        """Update skill confidence based on outcome."""
        model = await self.load()

        # Initialize skill if new
        if skill not in model.skills:
            model.skills[skill] = 0.5

        # Adjust confidence: success +0.05, failure -0.05, clamp 0-1
        delta = 0.05 if outcome == "success" else (-0.05 if outcome == "failure" else 0.0)
        model.skills[skill] = max(0.0, min(1.0, model.skills[skill] + delta))

        # Update counters
        model.total_tasks += 1
        if outcome == "success":
            model.successful_tasks += 1
        elif outcome == "failure":
            model.failed_tasks += 1

        # Recompute reliability and error_rate
        if model.total_tasks > 0:
            model.reliability = model.successful_tasks / model.total_tasks
            model.error_rate = model.failed_tasks / model.total_tasks

        model.updated_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()

        await self.save(model)
        logger.info(f"Skill updated: {skill}={model.skills[skill]:.2f} outcome={outcome}")

    async def update_from_outcome(self, skill: str, outcome: str) -> None:
        """Alias for update_skill — kept for compatibility."""
        await self.update_skill(skill, outcome)

    async def get_model(self) -> Dict[str, Any]:
        """Get current self-model as dict."""
        model = await self.load()
        return model.dict()