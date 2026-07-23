"""Tests pour CapabilityRegistry."""

from __future__ import annotations

import pytest

from core.modules.capability import Capability
from core.registry.capability import (
    CapabilityRegistry,
    CapabilityConflictError,
)


class TestCapabilityRegistry:
    """Tests du CapabilityRegistry."""

    def test_register(self, capability_registry: CapabilityRegistry, sample_capability: Capability):
        """Enregistrement d'une capacité."""
        capability_registry.register("test-module", sample_capability)

        assert capability_registry.count() == 1
        assert sample_capability.name in capability_registry

    def test_register_duplicate_not_shared(self, capability_registry: CapabilityRegistry):
        """Deux modules ne peuvent pas enregistrer la même capacité non-shared."""
        cap = Capability(
            name="conflict.capability",
            version="1.0.0",
            shared=False,
        )

        capability_registry.register("module-a", cap)

        with pytest.raises(CapabilityConflictError):
            capability_registry.register("module-b", cap)

    def test_register_duplicate_shared(self, capability_registry: CapabilityRegistry):
        """Une capacité shared peut être écrasée."""
        cap1 = Capability(name="shared.capability", version="1.0.0", shared=True)
        cap2 = Capability(name="shared.capability", version="2.0.0", shared=True)

        capability_registry.register("module-a", cap1)
        capability_registry.register("module-b", cap2)

        assert capability_registry.count() == 1
        cap = capability_registry.get("shared.capability")
        assert cap is not None
        assert cap.version == "2.0.0"

    def test_get(self, capability_registry: CapabilityRegistry, sample_capability: Capability):
        """Récupération d'une capacité par nom."""
        capability_registry.register("test-module", sample_capability)

        result = capability_registry.get("test.capability")
        assert result is not None
        assert result.name == "test.capability"
        assert result.version == "1.0.0"

    def test_get_not_found(self, capability_registry: CapabilityRegistry):
        """Récupération d'une capacité inexistante."""
        result = capability_registry.get("nonexistent")
        assert result is None

    def test_unregister(self, capability_registry: CapabilityRegistry, sample_capability: Capability):
        """Suppression d'une capacité."""
        capability_registry.register("test-module", sample_capability)
        assert capability_registry.count() == 1

        result = capability_registry.unregister("test.capability")
        assert result is True
        assert capability_registry.count() == 0

    def test_unregister_not_found(self, capability_registry: CapabilityRegistry):
        """Suppression d'une capacité inexistante."""
        result = capability_registry.unregister("nonexistent")
        assert result is False

    def test_unregister_module(self, capability_registry: CapabilityRegistry):
        """Suppression de toutes les capacités d'un module."""
        cap1 = Capability(name="capability.one", version="1.0.0")
        cap2 = Capability(name="capability.two", version="1.0.0")

        capability_registry.register("module-a", cap1)
        capability_registry.register("module-a", cap2)
        assert capability_registry.count() == 2

        capability_registry.unregister_module("module-a")
        assert capability_registry.count() == 0

    def test_get_by_module(self, capability_registry: CapabilityRegistry):
        """Récupération des capacités d'un module."""
        cap1 = Capability(name="cap.one", version="1.0.0")
        cap2 = Capability(name="cap.two", version="1.0.0")

        capability_registry.register("module-a", cap1)
        capability_registry.register("module-b", cap2)

        module_a_caps = capability_registry.get_by_module("module-a")
        assert len(module_a_caps) == 1
        assert module_a_caps[0].name == "cap.one"

    def test_resolve(self, capability_registry: CapabilityRegistry, sample_capability: Capability):
        """Résolution par nom et version."""
        capability_registry.register("test-module", sample_capability)

        # Sans version
        results = capability_registry.resolve("test.capability")
        assert len(results) == 1

        # Avec bonne version
        results = capability_registry.resolve("test.capability", "1.0.0")
        assert len(results) == 1

        # Avec mauvaise version
        results = capability_registry.resolve("test.capability", "2.0.0")
        assert len(results) == 0

    def test_validate_dependencies(self, capability_registry: CapabilityRegistry):
        """Validation des dépendances."""
        cap = Capability(
            name="dependent.capability",
            version="1.0.0",
            dependencies=["required.capability"],
        )

        # Dépendance manquante
        missing = capability_registry.validate_dependencies(cap)
        assert len(missing) == 1
        assert "required.capability" in missing

        # Ajouter la dépendance
        capability_registry.register(
            "required-module",
            Capability(name="required.capability", version="1.0.0"),
        )

        # Dépendance satisfaite
        missing = capability_registry.validate_dependencies(cap)
        assert len(missing) == 0

    def test_check_write_conflicts(self, capability_registry: CapabilityRegistry):
        """Détection des conflits d'écriture."""
        cap1 = Capability(
            name="cap.one",
            version="1.0.0",
            state_writes=["shared:key:*"],
            shared=False,
        )
        cap2 = Capability(
            name="cap.two",
            version="1.0.0",
            state_writes=["shared:key:*"],
            shared=False,
        )

        capability_registry.register("module-a", cap1)
        capability_registry.register("module-b", cap2)

        conflicts = capability_registry.check_write_conflicts()
        assert len(conflicts) == 1
        assert conflicts[0][0] == "shared:key:*"
        assert conflicts[0][1] == "module-a"

    def test_list_all(self, capability_registry: CapabilityRegistry):
        """Liste de toutes les capacités."""
        capability_registry.register("module-a", Capability(name="cap.one", version="1.0.0"))
        capability_registry.register("module-b", Capability(name="cap.two", version="1.0.0"))

        all_caps = capability_registry.list_all()
        assert len(all_caps) == 2

    def test_list_modules(self, capability_registry: CapabilityRegistry):
        """Liste de tous les modules enregistrés."""
        capability_registry.register("module-a", Capability(name="cap.one", version="1.0.0"))
        capability_registry.register("module-b", Capability(name="cap.two", version="1.0.0"))

        modules = capability_registry.list_modules()
        assert len(modules) == 2
        assert "module-a" in modules
        assert "module-b" in modules

    def test_contains(self, capability_registry: CapabilityRegistry, sample_capability: Capability):
        """Opérateur 'in'."""
        capability_registry.register("test-module", sample_capability)

        assert "test.capability" in capability_registry
        assert "nonexistent" not in capability_registry

    def test_len(self, capability_registry: CapabilityRegistry):
        """Opérateur len()."""
        assert len(capability_registry) == 0
        capability_registry.register("m", Capability(name="test", version="1.0.0"))
        assert len(capability_registry) == 1