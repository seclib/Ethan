"""Capability Registry — Ethan OS"""

from typing import Any, Callable, Dict, Optional


class CapabilityRegistry:
    """Registry global des Capabilities disponibles."""

    def __init__(self):
        self._capabilities: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}

    def register(self, capability: Any) -> None:
        name = getattr(capability, "name", capability.__class__.__name__)
        self._capabilities[name] = capability

    def register_factory(self, name: str, factory: Callable[[], Any]) -> None:
        self._factories[name] = factory

    def get(self, name: str) -> Optional[Any]:
        if name in self._capabilities:
            return self._capabilities[name]
        if name in self._factories:
            instance = self._factories[name]()
            self._capabilities[name] = instance
            return instance
        return None

    def list_all(self) -> Dict[str, Any]:
        return dict(self._capabilities)

    def list_names(self) -> list[str]:
        return list(self._capabilities.keys())

    def unregister(self, name: str) -> bool:
        if name in self._capabilities:
            del self._capabilities[name]
            return True
        return False