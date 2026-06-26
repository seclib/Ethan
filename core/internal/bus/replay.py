"""Event Replayer — Replay des événements."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncIterator, Callable

from core.types.event import Event

logger = logging.getLogger(__name__)


@dataclass
class ReplayResult:
    """Résultat d'un replay."""
    replayed: int
    errors: list[tuple[str, str]]
    duration_ms: float


class ReplayFilter:
    """Filtres pour le replay."""

    def __init__(self):
        self._filters: list[Callable[[Event], bool]] = []

    def by_source(self, source: str) -> ReplayFilter:
        """Filtre par source."""
        self._filters.append(lambda e: e.source == source)
        return self

    def by_type(self, event_type: str) -> ReplayFilter:
        """Filtre par type."""
        self._filters.append(lambda e: e.type.value == event_type)
        return self

    def by_correlation(self, correlation_id: str) -> ReplayFilter:
        """Filtre par correlation_id."""
        self._filters.append(lambda e: e.correlation_id == correlation_id)
        return self

    def apply(self, event: Event) -> bool:
        """Applique tous les filtres."""
        return all(f(event) for f in self._filters)


class EventReplayer:
    """Rejoue des événements.
    
    Responsabilités :
    - Replay depuis un point dans le temps
    - Filtres
    - Recovery après crash
    """

    def __init__(self, event_store: Any, bus: Any):
        self._store = event_store
        self._bus = bus

    async def replay(
        self,
        subject_pattern: str,
        start_time: datetime,
        end_time: datetime | None = None,
        filters: ReplayFilter | None = None,
    ) -> ReplayResult:
        """Replay des événements.

        Args:
            subject_pattern: Pattern de sujets
            start_time: Date de début
            end_time: Date de fin (optionnel)
            filters: Filtres optionnels

        Returns:
            Résultat du replay
        """
        import time

        replayed = 0
        errors = []
        start = time.time()

        logger.info(f"Starting replay from {start_time} to {end_time or 'now'}")

        async for event in self._store.replay(subject_pattern, start_time, end_time):
            # Appliquer les filtres
            if filters and not filters.apply(event):
                continue

            try:
                await self._bus.publish(event.type.value, event)
                replayed += 1
            except Exception as e:
                errors.append((event.id, str(e)))
                logger.error(f"Replay error for {event.id}: {e}")

        duration_ms = (time.time() - start) * 1000

        logger.info(f"Replay complete: {replayed} events, {len(errors)} errors, {duration_ms:.1f}ms")

        return ReplayResult(
            replayed=replayed,
            errors=errors,
            duration_ms=duration_ms,
        )

    async def replay_correlation(self, correlation_id: str) -> ReplayResult:
        """Replay tous les événements d'une corrélation.

        Args:
            correlation_id: ID de corrélation

        Returns:
            Résultat du replay
        """
        # TODO: Implémenter la recherche par correlation_id
        logger.warning("replay_correlation not fully implemented")
        return ReplayResult(replayed=0, errors=[], duration_ms=0.0)

    async def recover_from_checkpoint(self, checkpoint_id: str) -> ReplayResult:
        """Recovery depuis un checkpoint.

        Args:
            checkpoint_id: ID du checkpoint

        Returns:
            Résultat du replay
        """
        logger.info(f"Recovering from checkpoint: {checkpoint_id}")

        try:
            async for event in self._store.replay_from_checkpoint(checkpoint_id):
                await self._bus.publish(event.type.value, event)
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
            return ReplayResult(replayed=0, errors=[(checkpoint_id, str(e))], duration_ms=0.0)

        return ReplayResult(replayed=0, errors=[], duration_ms=0.0)