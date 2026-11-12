"""Central Capability Registry for ETHAN (MEM-014 Phase 9)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Callable, Iterable, Mapping
from uuid import uuid4

from core.applications.persistence import ApplicationStateStore

CAPABILITY_REGISTRY_VERSION = "1.0.0"
CAPABILITY_SCHEMA_VERSION = "1.0.0"

CAPABILITY_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$")
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z._-]+)*$")
MAX_TEXT_LENGTH = 4096


class CapabilityLifecycleState(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class CapabilitySensitivity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CapabilityDefinitionError(ValueError):
    """Raised for invalid capability definitions."""


@dataclass(frozen=True, slots=True)
class CapabilityConstraint:
    """A structured constraint attached to a capability definition."""

    name: str
    value: Any
    description: str = ""

    def validate(self) -> None:
        if not self.name.strip():
            raise CapabilityDefinitionError("constraint name must not be empty")
        if not isinstance(self.description, str):
            raise CapabilityDefinitionError("constraint description must be a string")

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "value": self.value, "description": self.description}

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "CapabilityConstraint":
        if not isinstance(data, Mapping) or "name" not in data:
            raise CapabilityDefinitionError("constraint must be an object with name")
        return cls(
            name=str(data["name"]),
            value=data.get("value"),
            description=str(data.get("description", "")),
        )


@dataclass(slots=True)
class CapabilityDefinition:
    """Versioned definition of an ETHAN capability."""

    capability_id: str
    name: str
    description: str
    category: str
    version: str = "1.0.0"
    status: CapabilityLifecycleState = CapabilityLifecycleState.DRAFT
    sensitivity: CapabilitySensitivity = CapabilitySensitivity.LOW
    permissions: tuple[str, ...] = field(default_factory=tuple)
    constraints: tuple[CapabilityConstraint, ...] = field(default_factory=tuple)
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    retired_at: datetime | None = None

    def validate(self, known_capabilities: set[str] | None = None) -> None:
        if not CAPABILITY_ID_PATTERN.fullmatch(self.capability_id):
            raise CapabilityDefinitionError(f"invalid capability_id: {self.capability_id!r}")
        if not self.name.strip():
            raise CapabilityDefinitionError("capability name must not be empty")
        if not self.description.strip():
            raise CapabilityDefinitionError("capability description must not be empty")
        if not self.category.strip():
            raise CapabilityDefinitionError("capability category must not be empty")
        if not SEMVER_PATTERN.fullmatch(self.version):
            raise CapabilityDefinitionError(f"invalid capability version: {self.version!r}")
        if not isinstance(self.permissions, (tuple, list)):
            raise CapabilityDefinitionError("permissions must be a list of strings")
        permissions = [str(item) for item in self.permissions]
        if len(permissions) != len(set(permissions)):
            raise CapabilityDefinitionError("permissions must be unique")
        if any(not item.strip() or "*" in item for item in permissions):
            raise CapabilityDefinitionError("permissions must be explicit and non-wildcard")
        if self.status not in CapabilityLifecycleState:
            raise CapabilityDefinitionError(f"invalid capability status: {self.status}")
        if self.sensitivity not in CapabilitySensitivity:
            raise CapabilityDefinitionError(f"invalid capability sensitivity: {self.sensitivity}")
        for permission in permissions:
            if not permission.strip():
                raise CapabilityDefinitionError("permission must not be empty")
        for constraint in self.constraints:
            constraint.validate()
        for dependency in self.dependencies:
            if not isinstance(dependency, str) or not dependency.strip():
                raise CapabilityDefinitionError("dependency must be a non-empty string")
        if self.capability_id in self.dependencies:
            raise CapabilityDefinitionError("a capability cannot depend on itself")
        if known_capabilities is not None:
            unknown = set(self.dependencies) - known_capabilities
            if unknown:
                raise CapabilityDefinitionError(
                    "unknown capability dependencies: " + ", ".join(sorted(unknown))
                )
        for key, value in self.metadata.items():
            if not isinstance(key, str) or not key.strip() or not isinstance(value, str):
                raise CapabilityDefinitionError("metadata keys and values must be strings")
            if len(key) > MAX_TEXT_LENGTH or len(value) > MAX_TEXT_LENGTH:
                raise CapabilityDefinitionError("metadata entry is too long")
        if self.retired_at is not None and self.status != CapabilityLifecycleState.RETIRED:
            raise CapabilityDefinitionError("retired_at requires retired status")
        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise CapabilityDefinitionError("timestamps must be timezone-aware")

    def is_declared_available(self) -> bool:
        return self.status == CapabilityLifecycleState.ACTIVE

    def permission_set(self) -> frozenset[str]:
        return frozenset(self.permissions)

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "version": self.version,
            "status": self.status.value,
            "sensitivity": self.sensitivity.value,
            "permissions": list(self.permissions),
            "constraints": [constraint.to_dict() for constraint in self.constraints],
            "dependencies": list(self.dependencies),
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "retired_at": None if self.retired_at is None else self.retired_at.isoformat(),
            "registry_version": CAPABILITY_REGISTRY_VERSION,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CapabilityDefinition":
        if not isinstance(data, Mapping):
            raise CapabilityDefinitionError("capability definition must be an object")
        try:
            created_raw = data.get("created_at")
            updated_raw = data.get("updated_at")
            retired_raw = data.get("retired_at")
            constraint_data = data.get("constraints", [])
            constraints = tuple(
                CapabilityConstraint.from_mapping(item) if isinstance(item, Mapping) else CapabilityConstraint(name=str(item), value=None)
                for item in constraint_data
            )
            definition = cls(
                capability_id=str(data["capability_id"]),
                name=str(data["name"]),
                description=str(data["description"]),
                category=str(data["category"]),
                version=str(data.get("version", "1.0.0")),
                status=CapabilityLifecycleState(str(data.get("status", "draft"))),
                sensitivity=CapabilitySensitivity(str(data.get("sensitivity", "low"))),
                permissions=tuple(str(item) for item in data.get("permissions", [])),
                constraints=constraints,
                dependencies=tuple(str(item) for item in data.get("dependencies", [])),
                metadata={str(k): str(v) for k, v in dict(data.get("metadata", {})).items()},
                created_at=datetime.fromisoformat(str(created_raw).replace("Z", "+00:00")) if created_raw else datetime.now(timezone.utc),
                updated_at=datetime.fromisoformat(str(updated_raw).replace("Z", "+00:00")) if updated_raw else datetime.now(timezone.utc),
                retired_at=datetime.fromisoformat(str(retired_raw).replace("Z", "+00:00")) if retired_raw else None,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise CapabilityDefinitionError(f"capability definition is missing or invalid: {exc}") from exc
        return definition


@dataclass(slots=True)
class CapabilityRegistry:
    """Central, versioned capability registry with optional durable storage."""

    registry_version: str = CAPABILITY_REGISTRY_VERSION
    schema_version: str = CAPABILITY_SCHEMA_VERSION
    store: Any | None = None
    _definitions: dict[str, CapabilityDefinition] = field(default_factory=dict)
    _history: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.store is not None:
            try:
                for payload in self.store.load_records("capability_definitions"):
                    definition = CapabilityDefinition.from_dict(payload)
                    definition.validate(set(self._definitions))
                    self._definitions[definition.capability_id] = definition
                for payload in self.store.load_records("capability_history"):
                    self._history.setdefault(str(payload.get("capability_id")), []).append(dict(payload))
            except Exception:
                pass

    def register(self, definition: CapabilityDefinition, *, actor: str = "system") -> CapabilityDefinition:
        definition.validate(set(self._definitions))
        if definition.capability_id in self._definitions:
            raise CapabilityDefinitionError(f"capability already registered: {definition.capability_id}")
        self._definitions[definition.capability_id] = definition
        self._history.setdefault(definition.capability_id, []).append(
            {
                "event": "registered",
                "actor": actor,
                "version": definition.version,
                "status": definition.status.value,
                "at": definition.created_at.isoformat(),
            }
        )
        if self.store is not None:
            self.store.save_record("capability_definitions", definition.capability_id, definition.to_dict())
            self.store.save_record("capability_history", str(uuid4()), {
                "history_id": str(uuid4()),
                "capability_id": definition.capability_id,
                "event": "registered",
                "actor": actor,
                "version": definition.version,
                "status": definition.status.value,
                "at": definition.created_at.isoformat(),
            })
        return definition

    def get(self, capability_id: str, version: str | None = None) -> CapabilityDefinition | None:
        definition = self._definitions.get(capability_id)
        if definition is None:
            return None
        if version is not None and definition.version != version:
            return None
        return definition

    def list(
        self,
        *,
        category: str | None = None,
        status: CapabilityLifecycleState | str | None = None,
        sensitivity: CapabilitySensitivity | str | None = None,
    ) -> tuple[CapabilityDefinition, ...]:
        result = list(self._definitions.values())
        if category is not None:
            result = [item for item in result if item.category == category]
        if status is not None:
            status_value = status.value if isinstance(status, CapabilityLifecycleState) else str(status)
            result = [item for item in result if item.status.value == status_value]
        if sensitivity is not None:
            sensitivity_value = sensitivity.value if isinstance(sensitivity, CapabilitySensitivity) else str(sensitivity)
            result = [item for item in result if item.sensitivity.value == sensitivity_value]
        result.sort(key=lambda item: (item.category, item.capability_id, item.version))
        return tuple(result)

    def search(self, query: str) -> tuple[CapabilityDefinition, ...]:
        needle = query.strip().lower()
        if not needle:
            return tuple()
        result = []
        for definition in self._definitions.values():
            haystack = " ".join(
                (definition.capability_id, definition.name, definition.description, definition.category)
            ).lower()
            if needle in haystack:
                result.append(definition)
        result.sort(key=lambda item: item.capability_id)
        return tuple(result)

    def exists(self, capability_id: str) -> bool:
        return capability_id in self._definitions

    def permission_mapping(self, capability_id: str) -> frozenset[str]:
        definition = self.get(capability_id)
        if definition is None:
            raise CapabilityDefinitionError(f"unknown capability: {capability_id}")
        return definition.permission_set()

    def validate_capability_ids(self, capability_ids: Iterable[str]) -> tuple[str, ...]:
        unknown = sorted({item for item in capability_ids if item not in self._definitions})
        if unknown:
            raise CapabilityDefinitionError("unknown capabilities: " + ", ".join(unknown))
        return tuple(unknown)

    def validate_permission_mapping(
        self, permission: str, capability_id: str, declared_permissions: set[str] | None = None
    ) -> bool:
        definition = self.get(capability_id)
        if definition is None:
            return False
        if permission not in definition.permission_set():
            return False
        if declared_permissions is not None and permission not in declared_permissions:
            return False
        return True

    def deprecate(self, capability_id: str, *, actor: str = "system") -> CapabilityDefinition:
        return self._transition(capability_id, CapabilityLifecycleState.DEPRECATED, actor=actor, require_active=True)

    def retire(self, capability_id: str, *, actor: str = "system") -> CapabilityDefinition:
        definition = self._transition(capability_id, CapabilityLifecycleState.RETIRED, actor=actor, require_active=False)
        definition.retired_at = datetime.now(timezone.utc)
        self._definitions[capability_id] = definition
        if self.store is not None:
            self.store.save_record("capability_definitions", definition.capability_id, definition.to_dict())
        return definition

    def activate(self, capability_id: str, *, actor: str = "system") -> CapabilityDefinition:
        definition = self._definitions.get(capability_id)
        if definition is None:
            raise CapabilityDefinitionError(f"unknown capability: {capability_id}")
        if definition.status == CapabilityLifecycleState.RETIRED:
            raise CapabilityDefinitionError("retired capability cannot be reactivated")
        if definition.status not in {CapabilityLifecycleState.DRAFT, CapabilityLifecycleState.DEPRECATED}:
            raise CapabilityDefinitionError(f"cannot activate capability from {definition.status.value}")
        updated = CapabilityDefinition(
            capability_id=definition.capability_id,
            name=definition.name,
            description=definition.description,
            category=definition.category,
            version=definition.version,
            status=CapabilityLifecycleState.ACTIVE,
            sensitivity=definition.sensitivity,
            permissions=definition.permissions,
            constraints=definition.constraints,
            dependencies=definition.dependencies,
            metadata=definition.metadata,
            created_at=definition.created_at,
            updated_at=datetime.now(timezone.utc),
            retired_at=None,
        )
        updated.validate(set(self._definitions) - {updated.capability_id})
        self._definitions[capability_id] = updated
        self._history.setdefault(capability_id, []).append(
            {"event": "activated", "actor": actor, "version": updated.version, "at": updated.updated_at.isoformat()}
        )
        if self.store is not None:
            self.store.save_record("capability_definitions", updated.capability_id, updated.to_dict())
            self.store.save_record("capability_history", str(uuid4()), {
                "history_id": str(uuid4()),
                "capability_id": capability_id,
                "event": "activated",
                "actor": actor,
                "version": updated.version,
                "at": updated.updated_at.isoformat(),
            })
        return updated

    def _transition(
        self,
        capability_id: str,
        state: CapabilityLifecycleState,
        *,
        actor: str,
        require_active: bool,
    ) -> CapabilityDefinition:
        definition = self._definitions.get(capability_id)
        if definition is None:
            raise CapabilityDefinitionError(f"unknown capability: {capability_id}")
        if state == CapabilityLifecycleState.DEPRECATED and definition.status != CapabilityLifecycleState.ACTIVE:
            raise CapabilityDefinitionError("only active capabilities can be deprecated")
        if state == CapabilityLifecycleState.RETIRED and definition.status not in {
            CapabilityLifecycleState.ACTIVE,
            CapabilityLifecycleState.DEPRECATED,
            CapabilityLifecycleState.DRAFT,
        }:
            raise CapabilityDefinitionError(f"cannot retire capability from {definition.status.value}")
        updated = CapabilityDefinition(
            capability_id=definition.capability_id,
            name=definition.name,
            description=definition.description,
            category=definition.category,
            version=definition.version,
            status=state,
            sensitivity=definition.sensitivity,
            permissions=definition.permissions,
            constraints=definition.constraints,
            dependencies=definition.dependencies,
            metadata=definition.metadata,
            created_at=definition.created_at,
            updated_at=datetime.now(timezone.utc),
            retired_at=definition.retired_at if state != CapabilityLifecycleState.RETIRED else datetime.now(timezone.utc),
        )
        updated.validate(set(self._definitions) - {updated.capability_id})
        self._definitions[capability_id] = updated
        self._history.setdefault(capability_id, []).append(
            {"event": state.value, "actor": actor, "version": updated.version, "at": updated.updated_at.isoformat()}
        )
        if self.store is not None:
            self.store.save_record("capability_definitions", updated.capability_id, updated.to_dict())
            self.store.save_record("capability_history", str(uuid4()), {
                "history_id": str(uuid4()),
                "capability_id": capability_id,
                "event": state.value,
                "actor": actor,
                "version": updated.version,
                "at": updated.updated_at.isoformat(),
            })
        return updated

    def history(self, capability_id: str) -> list[dict[str, Any]]:
        if capability_id not in self._definitions and capability_id not in self._history:
            raise CapabilityDefinitionError(f"unknown capability: {capability_id}")
        return [dict(item) for item in self._history.get(capability_id, [])]

    def compatibilities(self, capability_id: str, min_version: str | None = None) -> bool:
        definition = self.get(capability_id)
        if definition is None:
            return False
        if min_version is None:
            return definition.status == CapabilityLifecycleState.ACTIVE
        import re
        def _parts(value: str) -> tuple[int, ...]:
            return tuple(int(part) for part in value.split(".")[:3])
        return definition.version >= min_version and _parts(definition.version) >= _parts(min_version)

    def clear_cache(self) -> None:
        # Registry keeps definitions in memory intentionally; this method is for
        # tests only and does not affect durable storage.
        self._definitions.clear()
        self._history.clear()

    def __len__(self) -> int:
        return len(self._definitions)


# Aliases for consumers expecting different names.
CapabilityRegistryService = CapabilityRegistry
CapabilityCatalog = CapabilityRegistry
CapabilityRegistryManager = CapabilityRegistry


__all__ = [
    "CAPABILITY_REGISTRY_VERSION",
    "CapabilityCatalog",
    "CapabilityDefinition",
    "CapabilityDefinitionError",
    "CapabilityLifecycleState",
    "CapabilityRegistry",
    "CapabilityRegistryManager",
    "CapabilityRegistryService",
    "CapabilitySensitivity",
]
