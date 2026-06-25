"""Event Priorities — Gestion des priorités d'événements."""

from __future__ import annotations

import asyncio
import logging
from enum import IntEnum
from typing import Any

from core.types.event import Event

logger = logging.getLogger(__name__)


class Priority(IntEnum):
    """Niveaux de priorité des événements."""
    CRITICAL = 4  # Erreurs système, sécurité
    HIGH = 3      # Goals, tasks, LLM calls
    NORMAL = 2    # Messages, interactions
    LOW = 1       # Logs, métriques, analytics


class PriorityQueue:
    """Queue avec priorités."""

    def __init__(self, maxsize: int = 10000):
        self._queues: dict[Priority, asyncio.Queue] = {
            Priority.CRITICAL: asyncio.Queue(maxsize=maxsize),
            Priority.HIGH: asyncio.Queue(maxsize=maxsize),
            Priority.NORMAL: asyncio.Queue(maxsize=maxsize),
            Priority.LOW: asyncio.Queue(maxsize=maxsize),
        }
        self._total_size = 0

    async def put(self, event: Event, priority: Priority = Priority.NORMAL) -> None:
        """Ajoute un événement avec priorité.

        Args:
            event: Événement
            priority: Niveau de priorité
        """
        await self._queues[priority].put(event)
        self._total_size += 1

    async def get(self) -> Event:
        """Récupère l'événement le plus prioritaire.

        Returns:
            Événement
        """
        # Vérifier CRITICAL d'abord
        for priority in [Priority.CRITICAL, Priority.HIGH, Priority.NORMAL, Priority.LOW]:
            if not self._queues[priority].empty():
                event = await self._queues[priority].get()
                self._total_size -= 1
                return event

        # Bloquer sur NORMAL par défaut
        event = await self._queues[Priority.NORMAL].get()
        self._total_size -= 1
        return event

    def qsize(self) -> int:
        """Taille totale de la queue.

        Returns:
            Nombre d'événements
        """
        return self._total_size

    def empty(self) -> bool:
        """Vérifie si toutes les queues sont vides.

        Returns:
            True si vide
        """
        return self._total_size == 0

    def clear(self) -> None:
        """Vide toutes les queues."""
        for queue in self._queues.values():
            while not queue.empty():
                queue.get_nowait()
        self._total_size = 0