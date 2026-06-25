"""State Manager interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class StateManager(ABC):
    """Abstract state manager — Redis for live, PostgreSQL for persistent."""

    @abstractmethod
    async def connect(self) -> None:
        """Connect to state backend."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close connection."""
        ...


class LiveState(ABC):
    """Live state — Redis (fast, TTL-based)."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a value by key."""
        ...

    @abstractmethod
    async def set(self, key: str, value: Dict[str, Any], ttl: int = 3600) -> None:
        """Set a value with TTL (seconds)."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a key."""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        ...


class PersistentState(ABC):
    """Persistent state — PostgreSQL (ACID, no TTL)."""

    @abstractmethod
    async def execute(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute a raw SQL query."""
        ...

    @abstractmethod
    async def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a row and return it."""
        ...

    @abstractmethod
    async def update(self, table: str, where: Dict[str, Any], data: Dict[str, Any]) -> None:
        """Update rows matching where clause."""
        ...