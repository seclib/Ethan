"""CognitiveModule interface — ABC for all Ethan cognitive modules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from sdk.event import Event


class ModuleContext:
    """Context provided to a module during initialization."""

    def __init__(
        self,
        module_id: str,
        nats_url: str = "nats://localhost:4222",
        config: Optional[Dict[str, Any]] = None,
    ):
        self.module_id = module_id
        self.nats_url = nats_url
        self.config = config or {}


class ModuleManifest:
    """Identity and capabilities declaration."""

    def __init__(
        self,
        module_id: str,
        name: str,
        version: str = "1.0.0",
        capabilities: Optional[list[str]] = None,
        topics_subscribed: Optional[list[str]] = None,
        topics_published: Optional[list[str]] = None,
    ):
        self.id = module_id
        self.name = name
        self.version = version
        self.capabilities = capabilities or []
        self.topics_subscribed = topics_subscribed or []
        self.topics_published = topics_published or []


class CognitiveModule(ABC):
    """Interface for all cognitive modules in Ethan.
    
    Each module:
    - Runs as an independent service
    - Communicates only via NATS
    - Has a clear cognitive responsibility
    - Is replaceable without system impact
    """

    @abstractmethod
    def get_manifest(self) -> ModuleManifest:
        """Declare module identity and capabilities."""
        ...

    @abstractmethod
    async def initialize(self, context: ModuleContext) -> None:
        """Initialize module resources (LLM connection, models, caches)."""
        ...

    @abstractmethod
    async def handle_event(self, event: Event) -> Optional[Event]:
        """Process an incoming event and optionally return a response.
        
        Module must be stateless — state lives in Kernel's StateManager.
        """
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Release resources before shutdown."""
        ...