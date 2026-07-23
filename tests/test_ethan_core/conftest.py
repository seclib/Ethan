"""Fixtures ETHAN Core — Bus, Registry, Modules pour les tests."""

from __future__ import annotations

import pytest

from core.bus.interface import EventBus
from core.bus.memory_bus import InMemoryBus
from core.registry.capability import CapabilityRegistry
from core.registry.module import ModuleRegistry
from core.registry.events import EventSchemaRegistry
from core.modules.capability import Capability
from core.modules.dependency import Dependency
from core.modules.permissions import Permissions
from core.config.secrets import SecretManager


@pytest.fixture
def bus() -> InMemoryBus:
    """Bus d'événements in-memory pour les tests."""
    bus = InMemoryBus()
    return bus


@pytest.fixture
def capability_registry() -> CapabilityRegistry:
    """Registry de capacités vide pour les tests."""
    return CapabilityRegistry()


@pytest.fixture
def module_registry(bus, capability_registry) -> ModuleRegistry:
    """Registry de modules avec bus in-memory."""
    return ModuleRegistry(bus=bus, capability_registry=capability_registry)


@pytest.fixture
def schema_registry() -> EventSchemaRegistry:
    """Registry de schémas d'événements vide pour les tests."""
    return EventSchemaRegistry()


@pytest.fixture
def secret_manager() -> SecretManager:
    """Gestionnaire de secrets vide pour les tests."""
    return SecretManager()


@pytest.fixture
def sample_capability() -> Capability:
    """Capacité exemple pour les tests."""
    return Capability(
        name="test.capability",
        version="1.0.0",
        description="Test capability",
        inputs=["test.request"],
        outputs=["test.complete"],
        state_reads=["test:read:*"],
        state_writes=["test:write:*"],
    )


@pytest.fixture
def sample_capability_v2() -> Capability:
    """Version 2 d'une capacité exemple."""
    return Capability(
        name="test.capability",
        version="2.0.0",
        description="Test capability v2",
        inputs=["test.request", "test.admin"],
        outputs=["test.complete", "test.audit"],
        state_reads=["test:read:*"],
        state_writes=["test:write:*", "test:audit:*"],
    )


@pytest.fixture
def sample_dependency() -> Dependency:
    """Dépendance exemple pour les tests."""
    return Dependency(
        name="redis",
        version=">=7.0",
        required=True,
        description="Redis for state storage",
    )


@pytest.fixture
def sample_permissions() -> Permissions:
    """Permissions exemple pour les tests."""
    return Permissions(
        state_read=["test:*"],
        state_write=["test:write:*"],
        events_subscribe=["test.*"],
        events_publish=["test.*"],
        network=[],
        filesystem=["/tmp/*"],
    )