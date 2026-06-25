"""Event Bus — Interface abstraite.

Toute communication entre composants ETHAN passe par cette interface.
L'implémentation concrète est interchangeable (NATS, InMemory, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Coroutine

from core.types.event import Event

# Type pour un handler d'événement asynchrone
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


@dataclass
class Subscription:
    """Représente un abonnement actif à un sujet."""
    id: str
    pattern: str
    handler: EventHandler

    async def unsubscribe(self) -> None:
        """Se désabonne du sujet."""
        ...


class EventBus(ABC):
    """Bus d'événements abstrait.

    Principes :
    - Toute communication passe par ce bus
    - Les événements sont immutables
    - Les handlers sont asynchrones
    - Le bus garantit au-moins-une livraison (selon implémentation)
    """

    @abstractmethod
    async def connect(self, servers: str) -> None:
        """Connexion au bus.
        
        Args:
            servers: URL ou liste d'URLs de serveurs (e.g., "nats://localhost:4222")
        """
        ...

    @abstractmethod
    async def publish(self, subject: str, event: Event) -> None:
        """Publie un événement sur un sujet.
        
        Args:
            subject: Sujet NATS (e.g., "ethan.interface.message")
            event: L'événement à publier
        """
        ...

    @abstractmethod
    async def subscribe(
        self,
        pattern: str,
        handler: EventHandler,
        queue: str | None = None,
    ) -> Subscription:
        """Souscrit à un pattern de sujets.
        
        Args:
            pattern: Pattern NATS (e.g., "ethan.module.*")
            handler: Fonction appelée à chaque événement
            queue: Queue group pour le load balancing
            
        Returns:
            Subscription pour se désabonner
        """
        ...

    @abstractmethod
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
            Événement de réponse ou None si timeout
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Ferme la connexion au bus."""
        ...

    @abstractmethod
    async def is_connected(self) -> bool:
        """Vérifie si le bus est connecté."""
        ...