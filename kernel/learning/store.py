"""Experience Store — Redis + PostgreSQL for learning data."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from kernel.state.redis_state import RedisLiveState
from kernel.state.postgres_state import PostgresPersistentState
from sdk.learning import Experience

logger = logging.getLogger(__name__)


class ExperienceStore:
    """Stores experiences with TTL and persistent backup."""

    def __init__(self, redis: RedisLiveState, pg: PostgresPersistentState):
        self.redis = redis
        self.pg = pg

    async def save(self, experience: Experience) -> None:
        """Persist experience to Redis + PostgreSQL."""
        payload = experience.dict()

        # Redis hot storage (30 days)
        await self.redis.set(f"experience:{experience.experience_id}", payload, ttl=2592000)

        # PostgreSQL persistent storage
        await self.pg.insert("experiences", payload)
        logger.info(f"Experience saved: {experience.experience_id} outcome={experience.outcome}")

    async def get(self, experience_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve experience by ID."""
        return await self.redis.get(f"experience:{experience_id}")

    async def get_by_skill(self, skill: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent experiences for a skill."""
        # Simplified — in production use proper queries
        return await self.pg.execute(
            "SELECT * FROM experiences WHERE skill_invoked = $1 ORDER BY timestamp DESC LIMIT $2",
            skill, limit,
        )

    async def count_by_outcome(self, skill: str, outcome: str) -> int:
        """Count experiences by skill and outcome."""
        rows = await self.pg.execute(
            "SELECT COUNT(*) as cnt FROM experiences WHERE skill_invoked = $1 AND outcome = $2",
            skill, outcome,
        )
        return rows[0]["cnt"] if rows else 0

    async def get_recent(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get most recent experiences."""
        return await self.pg.execute(
            "SELECT * FROM experiences ORDER BY timestamp DESC LIMIT $1", limit,
        )