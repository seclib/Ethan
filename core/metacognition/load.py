"""Cognitive Load Manager — Monitors system load and adjusts reasoning depth."""

from __future__ import annotations

import logging
import os
from typing import Dict

from sdk.metacognition import CognitiveMode, COGNITIVE_MODES

logger = logging.getLogger(__name__)


class CognitiveLoadManager:
    """Adjusts reasoning depth based on system load."""

    def __init__(self):
        self.current_load = 0.0  # 0.0-1.0
        self.current_depth = 3  # 1-5

    async def assess(self) -> float:
        """Estimate current system load from environment."""
        # Simplified load = CPU + Memory + Queue pressure
        # In production: use psutil, metrics
        cpu_factor = 0.5  # placeholder CPU usage 0-1
        mem_factor = 0.5  # placeholder
        queue_depth = int(os.getenv("TASK_QUEUE_DEPTH", "0"))
        queue_factor = min(queue_depth / 100.0, 1.0)

        self.current_load = (cpu_factor + mem_factor + queue_factor) / 3.0
        logger.debug(f"Cognitive load assessed: {self.current_load:.2f}")
        return self.current_load

    async def adjust_depth(self, load: float) -> int:
        """Map load to reasoning depth 1-5."""
        # Low load → deep (5), high load → shallow (1)
        if load < 0.2:
            self.current_depth = 5
        elif load < 0.4:
            self.current_depth = 4
        elif load < 0.6:
            self.current_depth = 3
        elif load < 0.8:
            self.current_depth = 2
        else:
            self.current_depth = 1
        logger.debug(f"Reasoning depth adjusted: {self.current_depth} (load={load:.2f})")
        return self.current_depth

    async def recommend_mode(self, load: float) -> str:
        """Suggest a cognitive mode based on load."""
        depth = await self.adjust_depth(load)
        if load > 0.7:
            return "fast"
        elif load > 0.4:
            return "safe"
        else:
            return "deep"