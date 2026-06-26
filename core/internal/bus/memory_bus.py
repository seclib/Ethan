"""InMemoryBus — Bus d'événements en mémoire pour les tests.

Implémente EventBus sans dépendance externe.
Les événements sont stockés dans une deque mémoire.
Utile pour les tests unitaires et d'intégration.
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from typing import Any, Callable
from uuid import uuid4

from core.bus.interface import EventBus, EventHandler, Subscription
from core.types.event import Event

logger = logging.getLogger(__name__)


class InMemoryBus(EventBus):
    """Bus d'événements en mémoire.

    Implémente EventBus avec stockage en mémoire.
    Thread-safe via asyncio.Lock.
    """

    def __init__(self, max_events: int = 10000):
        self._subscriptions: dict[str, list[tuple[EventHandler, str | None]]] = {}
        self._history: deque[Event] = deque(maxlen=max_events)
        self._connected = False
        self._lock = asyncio.Lock()

    async def connect(self, servers: str = "") -> None:
        """Connexion au bus (immédiate pour in-memory).

        Args:
            servers: Ignoré pour le bus in-memory
        """
        self._connected = True
        logger.debug("InMemoryBus connected")

    async def publish(self, subject: str, event: Event) -> None:
        """Publie un événement et le distribue aux souscripteurs.

        Args:
            subject: Sujet de l'événement
            event: Événement à publier
        """
        if not self._connected:
            raise RuntimeError("InMemoryBus not connected")

        async with self._lock:
            self._history.append(event)

        # Distribuer aux souscripteurs
        tasks = []
        async with self._lock:
            for pattern, handlers in self._subscriptions.items():
                if self._matches(pattern, subject):
                    for handler, queue in handlers:
                        tasks.append(self._dispatch(handler, event))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def subscribe(
        self,
        pattern: str,
        handler: EventHandler,
        queue: str | None = None,
    ) -> Subscription:
        """Souscrit à un pattern de sujets.

        Args:
            pattern: Pattern avec wildcards (*, >)
            handler: Fonction appelée pour chaque événement
            queue: Queue group (ignoré pour in-memory)

        Returns:
            Subscription pour se désabonner
        """
        sub_id = str(uuid4())

        async with self._lock:
            if pattern not in self._subscriptions:
                self._subscriptions[pattern] = []
            self._subscriptions[pattern].append((handler, queue))

        logger.debug("Subscribed: %s (id=%s)", pattern, sub_id)

        return Subscription(
            id=sub_id,
            pattern=pattern,
            handler=handler,
        )

    async def request(
        self,
        subject: str,
        event: Event,
        timeout: float = 30.0,
    ) -> Event | None:
        """Publie une requête et attend une réponse.

        Args:
            subject: Sujet de la requête
            event: Événement de requête
            timeout: Timeout en secondes

        Returns:
            Événement de réponse, ou None si timeout
        """
        response_event = asyncio.Event()
        response_data: list[Event] = []

        async def response_handler(event: Event) -> None:
            response_data.append(event)
            response_event.set()

        # Générer un sujet de réponse unique
        response_subject = f"_response_{event.id}"

        sub = await self.subscribe(response_subject, response_handler)

        try:
            # Ajouter le sujet de réponse au metadata
            event.metadata["response_subject"] = response_subject
            await self.publish(subject, event)

            # Attendre la réponse
            await asyncio.wait_for(response_event.wait(), timeout=timeout)
            return response_data[0] if response_data else None

        except asyncio.TimeoutError:
            logger.warning("Request timeout: %s (timeout=%ss)", subject, timeout)
            return None
        finally:
            await sub.unsubscribe()

    async def close(self) -> None:
        """Ferme le bus."""
        async with self._lock:
            self._subscriptions.clear()
            self._history.clear()
            self._connected = False
        logger.debug("InMemoryBus closed")

    async def is_connected(self) -> bool:
        """Vérifie si le bus est connecté."""
        return self._connected

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    async def _dispatch(self, handler: EventHandler, event: Event) -> None:
        """Distribue un événement à un handler.

        Args:
            handler: Fonction de traitement
            event: Événement à distribuer
        """
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            logger.error("Handler error: %s", e)

    @staticmethod
    def _matches(pattern: str, subject: str) -> bool:
        """Vérifie si un subject correspond à un pattern NATS.

        Supporte :
        - "*" : un segment
        - ">" : un ou plusieurs segments (fin de pattern uniquement)

        Args:
            pattern: Pattern NATS (e.g., "ethan.module.*")
            subject: Sujet à tester (e.g., "ethan.module.executive")

        Returns:
            True si le subject correspond au pattern
        """
        pattern_parts = pattern.split(".")
        subject_parts = subject.split(".")

        # Pattern se termine par ">"
        if pattern.endswith(">"):
            return pattern_parts[:-1] == subject_parts[:len(pattern_parts) - 1]

        if len(pattern_parts) != len(subject_parts):
            return False

        for p, s in zip(pattern_parts, subject_parts):
            if p == "*":
                continue
            if p != s:
                return False

        return True

    # ──────────────────────────────────────────────
    # Test helpers
    # ──────────────────────────────────────────────

    @property
    def history(self) -> list[Event]:
        """Retourne l'historique des événements publiés."""
        return list(self._history)

    async def clear(self) -> None:
        """Vide l'historique et les souscriptions."""
        async with self._lock:
            self._history.clear()
            self._subscriptions.clear()

    @property
    def published_count(self) -> int:
        """Nombre d'événements publiés."""
        return len(self._history)

    def get_events_by_type(self, event_type: str) -> list[Event]:
        """Filtre l'historique par type d'événement.

        Args:
            event_type: Type d'événement à filtrer

        Returns:
            Liste des événements correspondants
        """
        return [e for e in self._history if e.type.value == event_type]