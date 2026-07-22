"""State Backend — Interface unifiée pour la persistance.

CLEAN ARCHITECTURE: Le Kernel dépend de cette interface, pas des implémentations concrètes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class StateBackend(ABC):
    """Interface abstraite pour les opérations d'état.
    
    - Live state (Redis) pour le cache actif
    - Persistent state (PostgreSQL) pour la persistance
    - Toutes les opérations sont asynchrones pour la robustesse
    
    Note: Certaines méthodes sont spécifiques à un backend ou l'autre.
    Les implémentations composites (Redis+PostgreSQL) implémentent toutes.
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Récupérer une valeur par clé."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Définir une valeur avec TTL optionnel."""
        pass
    
    @abstractmethod
    async def insert(self, table: str, payload: dict) -> Optional[Any]:
        """Insérer dans une table et retourner le record inséré."""
        pass
    
    @abstractmethod
    async def query(self, sql: str, params: Optional[tuple] = None) -> list[dict]:
        """Exécuter une requête SQL."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Fermer la connexion proprement."""
        pass

    # ── Convenience methods for composite backend ──────────────────────────────
    
    async def set_live(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Définir dans le backend live (Redis-like) - optionnel."""
        # Default implementation: use standard set
        await self.set(key, value, ttl=ttl)

    async def insert_persistent(self, table: str, payload: dict) -> Optional[Any]:
        """Insérer dans le backend persistant (PostgreSQL-like) - optionnel."""
        # Default implementation: use standard insert
        return await self.insert(table, payload)

    async def sync_event(self, event_id: str, payload: dict) -> None:
        """Synchroniser un événement dans les deux backends - optionnel.
        
        Cette méthode est utilisée par le Kernel pour persister les événements.
        Les implémentations composites l'override pour utiliser les deux backends.
        """
        # Default: just insert to persistent (most important)
        await self.insert("events", payload)