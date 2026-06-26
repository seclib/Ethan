"""Cognitive Kernel Engine — Fully isolated, no OS/CLI dependencies."""

from __future__ import annotations

import logging
from typing import Any

from core.bus.interface import EventBus
from core.registry.module import ModuleRegistry
from core.state.interface import StateBackend
from core.types.event import Event

logger = logging.getLogger(__name__)


class CognitiveKernel:
    """Event orchestrator — ZÉRO dépendance OS, CLI, ou modules spécifiques."""

    def __init__(
        self,
        bus: EventBus,
        state: StateBackend,
        registry: ModuleRegistry,
        config: dict[str, Any],
    ):
        self.bus = bus
        self.state = state
        self.registry = registry
        self.config = config
        self._running = False

    async def start(self) -> None:
        """Démarre le kernel."""
        if self._running:
            logger.warning("Kernel already running")
            return

        self._running = True
        logger.info("Cognitive Kernel starting")

        # Souscriptions abstraites (pas de modules spécifiques)
        await self.bus.subscribe("event.>", self._on_event, queue="kernel-events")
        await self.bus.subscribe("module.>", self._on_module_event, queue="kernel-modules")

        logger.info("Cognitive Kernel started")

    async def stop(self) -> None:
        """Arrête le kernel."""
        if not self._running:
            return

        self._running = False
        logger.info("Cognitive Kernel stopping")

        await self.bus.close()
        await self.state.close()
        logger.info("Cognitive Kernel stopped")

    async def dispatch_event(self, event: Event) -> None:
        """Route un événement vers les modules."""
        if not self._running:
            logger.warning("Kernel not running, cannot dispatch")
            return

        try:
            capability = self._resolve_capability(event.type)
            modules = self.registry.find_by_capability(capability)

            if not modules:
                logger.debug("No module for capability=%s event=%s", capability, event.id)
                return

            targets = [m.id for m in modules]
            logger.info("Dispatching %s to %s", event.type, targets)

            for module_id in targets:
                await self.bus.publish(f"module.{module_id}.event", event)

            await self.state.persist(event)

        except Exception as e:
            logger.error("Dispatch failed for %s: %s", event.id, e, exc_info=True)

    async def _on_event(self, event: Event) -> None:
        """Handler pour les événements."""
        await self.dispatch_event(event)

    async def _on_module_event(self, event: Event) -> None:
        """Handler pour les événements de module."""
        logger.debug("Module event: %s from %s", event.type, event.source)

    @staticmethod
    def _resolve_capability(event_type: str) -> str:
        """Résout la capability depuis le type d'événement."""
        # "interface.command" → "handle.command"
        return f"handle.{event_type.split('.')[-1]}"