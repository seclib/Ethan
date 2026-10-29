"""Background worker for Technical Memory synchronization.

This worker ensures that agent traces are periodically collected,
normalized, and synthesized into the knowledge base without
manual intervention.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from core.knowledge.agent_traces.sync_engine import SyncEngine

logger = logging.getLogger(__name__)

class TechnicalMemoryWorker:
    """
    Background worker that orchestrates the periodic synchronization
    of agent traces from various sources into the Obsidian vault.
    """

    def __init__(
        self,
        knowledge_root: Path | None = None,
        interval_seconds: int = 3600,
        enabled: bool = True
    ):
        self.sync_engine = SyncEngine(knowledge_root)
        self.interval = interval_seconds
        self.enabled = enabled
        self._stop_event = asyncio.Event()
        self._is_running = False
        self._task: asyncio.Task | None = None

    async def start(self):
        """Starts the background synchronization loop."""
        if not self.enabled:
            logger.info("TechnicalMemoryWorker is disabled; skipping start.")
            return

        if self._is_running:
            logger.warning("TechnicalMemoryWorker is already running.")
            return

        self._is_running = True
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("TechnicalMemoryWorker started (interval=%ds)", self.interval)

    async def stop(self):
        """Stops the background synchronization loop."""
        if not self._is_running:
            return

        logger.info("Stopping TechnicalMemoryWorker...")
        self._stop_event.set()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=10.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                self._task.cancel()

        self._is_running = False
        logger.info("TechnicalMemoryWorker stopped.")

    async def _run_loop(self):
        """Main loop for periodic synchronization."""
        try:
            while not self._stop_event.is_set():
                logger.debug("Starting scheduled Technical Memory sync...")
                try:
                    # Run the sync engine
                    results = self.sync_engine.sync()

                    # Since SyncEngine.sync is currently synchronous in the provided code,
                    # we run it in a thread to avoid blocking the event loop.
                    # However, looking at the code, SyncEngine.sync is a regular def.
                    # We use run_in_executor for CPU/IO bound sync.
                    loop = asyncio.get_running_loop()
                    results = await loop.run_in_executor(None, self.sync_engine.sync)

                    logger.info(
                        "Scheduled sync complete: %d collected, %d errors",
                        results.get("collected", 0),
                        results.get("errors", 0)
                    )
                except Exception as e:
                    logger.exception("Unexpected error during scheduled Technical Memory sync: %s", e)

                # Wait for the next interval or until stopped
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=self.interval)
                except asyncio.TimeoutError:
                    # Normal timeout, continue to next iteration
                    pass
        except asyncio.CancelledError:
            logger.debug("TechnicalMemoryWorker loop cancelled.")
        finally:
            self._is_running = False

    def get_status(self) -> dict[str, Any]:
        """Returns the current status of the worker."""
        return {
            "running": self._is_running,
            "enabled": self.enabled,
            "interval": self.interval,
            "knowledge_root": str(self.sync_engine.knowledge_root)
        }
