"""Event Router — Routage intelligent des événements."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from fnmatch import fnmatch
from typing import Any, Callable, Coroutine
from uuid import uuid4

from core.bus.priorities import Priority
from core.types.event import Event

logger = logging.getLogger(__name__)

# Type handler
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class RoutingStrategy(Enum):
    """Stratégies de routage."""
    BROADCAST = "broadcast"          # Tous les abonnés
    QUEUE_GROUP = "queue_group"      # Un seul par groupe (load balancing)
    PRIORITY = "priority"            # Par ordre de priorité
    FILTERED = "filtered"            # Avec filtres


@dataclass
class Route:
    """Route d'événement."""
    id: str
    pattern: str
    handler: EventHandler
    strategy: RoutingStrategy = RoutingStrategy.BROADCAST
    priority: Priority = Priority.NORMAL
    queue: str | None = None
    filters: list[Callable[[Event], bool]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class EventRouter:
    """Roue les événements vers les abonnés.
    
    Responsabilités :
    - Filtrage par sujet (pattern matching)
    - Routage par priorité
    - Load balancing (queue groups)
    - Fan-out (broadcast)
    """

    def __init__(self):
        self._routes: dict[str, list[Route]] = {}
        self._queue_groups: dict[str, list[Route]] = {}

    def add_route(
        self,
        pattern: str,
        handler: EventHandler,
        strategy: RoutingStrategy = RoutingStrategy.BROADCAST,
        priority: Priority = Priority.NORMAL,
        queue: str | None = None,
        filters: list[Callable[[Event], bool]] | None = None,
    ) -> Route:
        """Ajoute une route.

        Args:
            pattern: Pattern de sujet (e.g., "ethan.executor.*")
            handler: Fonction de traitement
            strategy: Stratégie de routage
            priority: Priorité
            queue: Queue group pour load balancing
            filters: Filtres optionnels

        Returns:
            Route créée
        """
        route = Route(
            id=str(uuid4()),
            pattern=pattern,
            handler=handler,
            strategy=strategy,
            priority=priority,
            queue=queue,
            filters=filters or [],
        )

        # Enregistrer par pattern
        if pattern not in self._routes:
            self._routes[pattern] = []
        self._routes[pattern].append(route)

        # Enregistrer par queue group
        if queue:
            if queue not in self._queue_groups:
                self._queue_groups[queue] = []
            self._queue_groups[queue].append(route)

        logger.debug(f"Route added: {pattern} -> {handler.__name__} (strategy: {strategy.value})")
        return route

    def remove_route(self, route_id: str) -> None:
        """Supprime une route.

        Args:
            route_id: ID de la route
        """
        # Chercher et supprimer
        for pattern, routes in list(self._routes.items()):
            self._routes[pattern] = [r for r in routes if r.id != route_id]
            if not self._routes[pattern]:
                del self._routes[pattern]

        # Supprimer des queue groups
        for queue, routes in list(self._queue_groups.items()):
            self._queue_groups[queue] = [r for r in routes if r.id != route_id]
            if not self._queue_groups[queue]:
                del self._queue_groups[queue]

        logger.debug(f"Route removed: {route_id}")

    async def route(self, event: Event) -> list[Route]:
        """Roue un événement.

        Args:
            event: Événement à router

        Returns:
            Liste des routes exécutées
        """
        # Trouver les routes correspondantes
        matching_routes = self._match_routes(event)

        if not matching_routes:
            logger.debug(f"No routes for event: {event.type}")
            return []

        # Trier par priorité (CRITICAL d'abord)
        matching_routes.sort(key=lambda r: r.priority.value, reverse=True)

        # Exécuter les handlers
        executed = []
        for route in matching_routes:
            # Vérifier les filtres
            if not self._apply_filters(route, event):
                continue

            try:
                await route.handler(event)
                executed.append(route)
            except Exception as e:
                logger.error(
                    f"Route {route.id} failed for {event.type}: {e}",
                    exc_info=True,
                )

        return executed

    def _match_routes(self, event: Event) -> list[Route]:
        """Trouve les routes correspondantes.

        Args:
            event: Événement

        Returns:
            Routes correspondantes
        """
        matching = []

        for pattern, routes in self._routes.items():
            if fnmatch(event.type.value, pattern):
                matching.extend(routes)

        return matching

    def _apply_filters(self, route: Route, event: Event) -> bool:
        """Applique les filtres d'une route.

        Args:
            route: Route
            event: Événement

        Returns:
            True si l'événement passe les filtres
        """
        for filter_fn in route.filters:
            if not filter_fn(event):
                return False
        return True

    def get_routes(self, pattern: str | None = None) -> list[Route]:
        """Récupère les routes.

        Args:
            pattern: Filtrer par pattern (optionnel)

        Returns:
            Liste de routes
        """
        if pattern is None:
            # Retourner toutes les routes
            all_routes = []
            for routes in self._routes.values():
                all_routes.extend(routes)
            return all_routes

        # Filtrer par pattern
        return self._routes.get(pattern, [])

    def get_queue_group(self, queue: str) -> list[Route]:
        """Récupère les routes d'une queue group.

        Args:
            queue: Nom de la queue

        Returns:
            Routes de la queue
        """
        return self._queue_groups.get(queue, [])

    def clear(self) -> None:
        """Supprime toutes les routes."""
        self._routes.clear()
        self._queue_groups.clear()
        logger.debug("All routes cleared")