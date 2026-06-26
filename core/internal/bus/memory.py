"""InMemory Bus — Implémentation en mémoire pour développement et tests.

Utilisé en mode standalone (sans Kernel Go ni NATS).
Tous les events restent dans le processus Python.
Pas de sérialisation, pas de persistance.
"""

from __future__ import annotations

import logging
from fnmatch import fnmatch
from typing import Any
from uuid import uuid4

from core.bus.interface import EventBus, EventHandler, Subscription
from core.types.event import Event

logger = logging.getLogger(__name__)


class InMemoryBus(EventBus):
    """Bus d'événements en mémoire.

    Avantages :
    - Zéro dépendance (pas de NATS, pas de Redis)
    - Tests ultra-rapides (pas d'I/O)
    - Mode standalone pour le développement

    Limitations :
    - Pas de persistance (events perdus au redémarrage)
    - Pas de distribution (mono-processus)
    - Pas de garantie de livraison (pas de JetStream)
    """

    def __init__(self, record_history: bool = True):
        self._subscribers: list[_Subscriber] = []
        self._history: list[Event] = []
        self._record_history = record_history
        self._connected = False
        self._server_url: str = ""

    async def connect(self, servers: str) -> None:
        """Connexion (immédiate en mémoire)."""
        self._server_url = servers
        self._connected = True
        logger.debug(f"InMemoryBus connected (simulated: {servers})")

    async def publish(self, subject: str, event: Event) -> None:
        """Publie un événement à tous les souscripteurs dont le pattern match."""
        if not self._connected:
            logger.warning(f"Bus not connected, dropping event on {subject}")
            return

        # Historique
        if self._record_history:
            self._history.append(event)

        # Dispatch
        matching = 0
        for sub in self._subscribers:
            if sub.matches(subject):
                try:
                    await sub.handler(event)
                    matching += 1
                except Exception as e:
                    logger.error(
                        f"Handler error for {subject} ({sub.pattern}): {e}",
                        exc_info=True,
                    )

        if matching == 0:
            logger.debug(f"No subscribers for {subject}")

    async def subscribe(
        self,
        pattern: str,
        handler: EventHandler,
        queue: str | None = None,
    ) -> Subscription:
        """Souscrit à un pattern de sujets.

        Les patterns supportent les wildcards UNIX (fnmatch) :
        - '*' : correspond à un segment
        - '?' : correspond à un caractère
        """
        sub = _Subscriber(
            id=str(uuid4()),
            pattern=pattern,
            handler=handler,
            queue=queue,
        )
        self._subscribers.append(sub)

        logger.debug(f"Subscribed to {pattern} (queue: {queue})")
        return Subscription(
            id=sub.id,
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

        La réponse est attendue sur le sujet 'ethan.response.<correlation_id>'.
        """
        import asyncio

        if not event.correlation_id:
            event.correlation_id = str(uuid4())

        response_subject = f"ethan.response.{event.correlation_id}"
        response_future: asyncio.Future[Event] = asyncio.Future()

        async def response_handler(ev: Event) -> None:
            if not response_future.done():
                response_future.set_result(ev)

        sub = await self.subscribe(response_subject, response_handler)
        try:
            await self.publish(subject, event)
            done, _ = await asyncio.wait(
                [response_future],
                timeout=timeout,
            )
            if done:
                return response_future.result()
            return None
        finally:
            self._subscribers = [s for s in self._subscribers if s.id != sub.id]

    async def close(self) -> None:
        """Ferme le bus et vide les souscripteurs."""
        self._subscribers.clear()
        self._connected = False
        logger.debug("InMemoryBus closed")

    async def is_connected(self) -> bool:
        """Vérifie si le bus est connecté."""
        return self._connected

    # ─── Méthodes utilitaires ────────────────────────────────────────

    def get_history(self, subject_pattern: str | None = None) -> list[Event]:
        """Récupère l'historique des événements.

        Args:
            subject_pattern: Filtre optionnel sur le sujet (pattern NATS)

        Returns:
            Liste des événements filtrés
        """
        if subject_pattern is None:
            return list(self._history)
        return [e for e in self._history if fnmatch(str(e.type.value), subject_pattern)]

    def clear_history(self) -> None:
        """Vide l'historique des événements."""
        self._history.clear()

    @property
    def subscriber_count(self) -> int:
        """Nombre de souscripteurs actifs."""
        return len(self._subscribers)


class _Subscriber:
    """Souscripteur interne avec matching de pattern."""

    def __init__(
        self,
        id: str,
        pattern: str,
        handler: EventHandler,
        queue: str | None = None,
    ):
        self.id = id
        self.pattern = pattern
        self.handler = handler
        self.queue = queue

    def matches(self, subject: str) -> bool:
        """Vérifie si le sujet match le pattern (support wildcards)."""
        return fnmatch(subject, self.pattern)