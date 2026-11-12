import tempfile
from pathlib import Path

from core.applications import (
    CapabilityDefinition,
    CapabilityDefinitionError,
    CapabilityLifecycleState,
    CapabilityRegistry,
    CapabilitySensitivity,
)


def valid_definition(capability_id: str = "application.lifecycle.read", status=CapabilityLifecycleState.ACTIVE) -> CapabilityDefinition:
    return CapabilityDefinition(
        capability_id=capability_id,
        name="Read lifecycle",
        description="Read lifecycle state",
        category="application",
        version="1.0.0",
        status=status,
        sensitivity=CapabilitySensitivity.MEDIUM,
        permissions=("application.lifecycle.read",),
    )


def test_valid_identifier_and_invalid_identifiers() -> None:
    definition = valid_definition()
    definition.validate(set())
    assert definition.capability_id == "application.lifecycle.read"

    for bad_id in ("read", "Read", "application..read", "application.read*", ""):
        try:
            bad = CapabilityDefinition(
                capability_id=bad_id,
                name="Bad",
                description="Bad",
                category="application",
                version="1.0.0",
            )
            bad.validate(set())
            raise AssertionError("invalid identifier accepted")
        except (CapabilityDefinitionError, ValueError):
            pass


def test_duplicate_definition_rejected() -> None:
    registry = CapabilityRegistry()
    registry.register(valid_definition())
    try:
        registry.register(valid_definition())
        raise AssertionError("duplicate accepted")
    except (CapabilityDefinitionError, ValueError):
        pass


def test_missing_required_field() -> None:
    try:
        definition = CapabilityDefinition(
            capability_id="application.lifecycle.read",
            name="",
            description="desc",
            category="application",
            version="1.0.0",
        )
        definition.validate(set())
        raise AssertionError("empty name accepted")
    except (CapabilityDefinitionError, ValueError):
        pass


def test_version_and_status_validation() -> None:
    try:
        bad = CapabilityDefinition(
            capability_id="application.lifecycle.read",
            name="Read",
            description="desc",
            category="application",
            version="latest",
        )
        bad.validate(set())
        raise AssertionError("bad version accepted")
    except (CapabilityDefinitionError, ValueError):
        pass

    definition = valid_definition(status=CapabilityLifecycleState.DRAFT)
    definition.validate(set())
    assert definition.status == CapabilityLifecycleState.DRAFT


def test_search_and_filter() -> None:
    registry = CapabilityRegistry()
    registry.register(valid_definition())
    assert registry.get("application.lifecycle.read") is not None
    assert registry.exists("application.lifecycle.read")
    assert "application.lifecycle" in " ".join(item.capability_id for item in registry.search("lifecycle"))
    assert len(registry.list(category="application")) == 1


def test_deprecate_and_retire_transitions() -> None:
    registry = CapabilityRegistry()
    registry.register(valid_definition())
    deprecated = registry.deprecate("application.lifecycle.read")
    assert deprecated.status == CapabilityLifecycleState.DEPRECATED
    retired = registry.retire("application.lifecycle.read")
    assert retired.status == CapabilityLifecycleState.RETIRED
    try:
        registry.activate("application.lifecycle.read")
        raise AssertionError("retired reactivation allowed")
    except (CapabilityDefinitionError, ValueError):
        pass


def test_unknown_capability_rejected() -> None:
    registry = CapabilityRegistry()
    try:
        registry.validate_capability_ids(["application.unknown.read"])
        raise AssertionError("unknown capability accepted")
    except (CapabilityDefinitionError, ValueError):
        pass


def test_permission_mapping_exact_and_wildcard_rejected() -> None:
    registry = CapabilityRegistry()
    registry.register(valid_definition())
    mapping = registry.permission_mapping("application.lifecycle.read")
    assert "application.lifecycle.read" in mapping
    assert registry.validate_permission_mapping("application.lifecycle.read", "application.lifecycle.read") is True
    assert registry.validate_permission_mapping("application.lifecycle.*", "application.lifecycle.read") is False


def test_unknown_permission_rejected() -> None:
    registry = CapabilityRegistry()
    registry.register(valid_definition())
    assert registry.validate_permission_mapping("unknown.permission", "application.lifecycle.read") is False


def test_persistence_survives_restart() -> None:
    with tempfile.TemporaryDirectory() as directory:
        db = Path(directory) / "state.sqlite"
        from core.applications import ApplicationStateStore
        store = ApplicationStateStore(db)
        registry = CapabilityRegistry(store=store)
        registry.register(valid_definition())
        history = registry.history("application.lifecycle.read")
        store.close()

        restarted_store = ApplicationStateStore(db)
        restarted_registry = CapabilityRegistry(store=restarted_store)
    assert restarted_registry.get("application.lifecycle.read") is not None
    assert restarted_registry.get("application.lifecycle.read").status == CapabilityLifecycleState.ACTIVE
    assert restarted_registry.history("application.lifecycle.read")


def test_no_automatic_permission() -> None:
    registry = CapabilityRegistry()
    registry.register(valid_definition())
    decision_like = registry.get("application.lifecycle.read")
    assert decision_like is not None
    # Registry defines permissions but cannot grant them.
    assert not hasattr(registry, "grant_permission")
