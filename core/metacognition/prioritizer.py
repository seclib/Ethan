"""Module Prioritizer — Ranks modules by skill confidence."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sdk.metacognition import ModulePriority
from sdk.learning import SelfModel

logger = logging.getLogger(__name__)


class ModulePrioritizer:
    """Ranks modules for a task based on skill confidence."""

    async def rank(
        self,
        modules: List[Dict[str, Any]],
        task_type: str,
        self_model: Optional[SelfModel] = None,
        mode: str = "fast",
    ) -> ModulePriority:
        """Sort modules by relevance to task."""
        scored = []
        skill_key = task_type

        mode_multiplier = {
            "deep": 1.2,
            "exploration": 1.1,
            "safe": 0.9,
            "debug": 1.0,
            "fast": 1.0,
        }.get(mode, 1.0)

        for m in modules:
            caps = m.get("capabilities", [])
            match = any(skill_key in c for c in caps)
            base_score = 0.7 if match else 0.3
            skill_conf = self_model.skills.get(skill_key, 0.5) if self_model else 0.5
            score = base_score * skill_conf * mode_multiplier

            scored.append({
                "module_id": m.get("id"),
                "score": round(score, 3),
                "match": match,
                "skill": skill_key,
            })

        scored.sort(key=lambda x: x["score"], reverse=True)

        priority = ModulePriority(task_type=task_type, rankings=scored)
        logger.info("Module priorities updated for %s", task_type)
        return priority