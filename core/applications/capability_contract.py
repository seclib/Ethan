"""Canonical application capability contract (Campaign 02-F0)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from core.auth import Permission
from .models import ValidationError, _require_text, MAX_TEXT_LENGTH

CAPABILITY_CONTRACT_VERSION = "1.0.0"
SUPPORTED_CAPABILITY_CONTRACT_VERSIONS = frozenset({"1.0.0"})

_SUPPORTED_CATEGORIES = frozenset({"information", "analysis", "automation", "knowledge", "system"})
_SUPPORTED_INVOCATION_INTERFACES = frozenset({"application_api", "http", "mcp", "internal"})


def _require_mapping(data: Mapping[str, Any], field_name: str) -> dict[str, Any]:
    value = data.get(field_name, {})
    if value is None:
        value = {}
    if not isinstance(value, Mapping):
        raise ValidationError(f"{field_name} must be an object")
    return dict(value)


def _normalized_tuple(value: Any, *, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise ValidationError(f"{field_name} must be a list")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValidationError(f"{field_name} values must be non-empty strings")
        items.append(item)
    return tuple(items)


def _coerce_timeout(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError("timeout_seconds must be an integer")
    if value < 1 or value > 300:
        raise ValidationError("timeout_seconds must be between 1 and 300")
    return value


@dataclass(frozen=True, slots=True)
class ApplicationCapabilityContract:
    capability_id: str
    contract_version: str = CAPABILITY_CONTRACT_VERSION
    application_id: str = ""
    name: str = ""
    description: str = ""
    category: str = "analysis"
    invocation_interface: str = "application_api"
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    required_permissions: tuple[str, ...] = field(default_factory=tuple)
    runtime_requirements: dict[str, Any] = field(default_factory=dict)
    execution_constraints: dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 30
    activation_required: bool = False
    metadata: dict[str, str] = field(default_factory=dict)

    _ALLOWED_FIELDS = frozenset(
        {
            "capability_id",
            "contract_version",
            "application_id",
            "name",
            "description",
            "category",
            "invocation_interface",
            "input_schema",
            "output_schema",
            "required_permissions",
            "runtime_requirements",
            "execution_constraints",
            "timeout_seconds",
            "activation_required",
            "metadata",
        }
    )

    def validate(self) -> None:
        if not _IDENTIFIER_PATTERN.fullmatch(self.capability_id):
            raise ValidationError(f"invalid capability_id: {self.capability_id!r}")
        if self.contract_version not in SUPPORTED_CAPABILITY_CONTRACT_VERSIONS:
            raise ValidationError(f"unsupported capability contract_version: {self.contract_version!r}")
        if not _IDENTIFIER_PATTERN.fullmatch(self.application_id):
            raise ValidationError(f"invalid application_id: {self.application_id!r}")
        if not self.name.strip():
            raise ValidationError("capability name must not be empty")
        if len(self.name) > MAX_TEXT_LENGTH:
            raise ValidationError("capability name is too long")
        if not isinstance(self.description, str) or len(self.description) > MAX_TEXT_LENGTH:
            raise ValidationError("capability description is invalid")
        if self.category not in _SUPPORTED_CATEGORIES:
            raise ValidationError(f"unsupported capability category: {self.category!r}")
        if self.invocation_interface not in _SUPPORTED_INVOCATION_INTERFACES:
            raise ValidationError(f"unsupported invocation_interface: {self.invocation_interface!r}")
        if not isinstance(self.input_schema, dict):
            raise ValidationError("input_schema must be a JSON object")
        if not isinstance(self.output_schema, dict):
            raise ValidationError("output_schema must be a JSON object")
        permission_values = {permission.value for permission in Permission}
        for permission in self.required_permissions:
            if permission not in permission_values:
                raise ValidationError(f"unknown permission: {permission!r}")
        if not isinstance(self.runtime_requirements, dict):
            raise ValidationError("runtime_requirements must be an object")
        if not isinstance(self.execution_constraints, dict):
            raise ValidationError("execution_constraints must be an object")
        if self.timeout_seconds < 1 or self.timeout_seconds > 300:
            raise ValidationError("timeout_seconds must be between 1 and 300")
        if not isinstance(self.activation_required, bool):
            raise ValidationError("activation_required must be a boolean")
        for key, value in self.metadata.items():
            if not isinstance(key, str) or not key.strip() or not isinstance(value, str):
                raise ValidationError("metadata must contain only non-empty string keys and string values")

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ApplicationCapabilityContract":
        if not isinstance(data, Mapping):
            raise ValidationError("capability contract must be an object")
        unknown = set(data) - cls._ALLOWED_FIELDS
        if unknown:
            raise ValidationError(f"capability contract contains unknown fields: {sorted(unknown)}")
        try:
            contract = cls(
                capability_id=_require_text(data, "capability_id"),
                contract_version=str(data.get("contract_version", CAPABILITY_CONTRACT_VERSION)),
                application_id=_require_text(data, "application_id"),
                name=_require_text(data, "name"),
                description=str(data.get("description", "")),
                category=str(data.get("category", "analysis")),
                invocation_interface=str(data.get("invocation_interface", "application_api")),
                input_schema=_require_mapping(data, "input_schema"),
                output_schema=_require_mapping(data, "output_schema"),
                required_permissions=_normalized_tuple(data.get("required_permissions"), field_name="required_permissions"),
                runtime_requirements=_require_mapping(data, "runtime_requirements"),
                execution_constraints=_require_mapping(data, "execution_constraints"),
                timeout_seconds=_coerce_timeout(data.get("timeout_seconds", 30)),
                activation_required=bool(data.get("activation_required", False)),
                metadata=dict(data.get("metadata", {}) or {}),
            )
        except ValidationError:
            raise
        except Exception as exc:
            raise ValidationError("invalid capability contract") from exc
        contract.validate()
        return contract

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "contract_version": self.contract_version,
            "application_id": self.application_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "invocation_interface": self.invocation_interface,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "required_permissions": list(self.required_permissions),
            "runtime_requirements": self.runtime_requirements,
            "execution_constraints": self.execution_constraints,
            "timeout_seconds": self.timeout_seconds,
            "activation_required": self.activation_required,
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class ApplicationCapabilityRegistration:
    capability_id: str
    application_id: str
    contract: ApplicationCapabilityContract
    approved: bool
    registration_state: str = "registered"

    def validate(self) -> None:
        if self.capability_id != self.contract.capability_id:
            raise ValidationError("registered capability ID does not match contract")
        if self.application_id != self.contract.application_id:
            raise ValidationError("registered application ID does not match contract")
        if not isinstance(self.approved, bool):
            raise ValidationError("approved must be a boolean")
        if self.registration_state not in {"registered", "disabled"}:
            raise ValidationError("invalid registration_state")
        self.contract.validate()


from .application_registry import ApplicationIntegrationRegistry


class DuplicatedApplicationCapabilityError(ValueError):
    """Raised when a conflicting capability contract is registered."""


def register_application_capability(
    registry: ApplicationIntegrationRegistry,
    contract: ApplicationCapabilityContract,
    *,
    approved: bool = False,
) -> ApplicationCapabilityRegistration:
    contract.validate()
    application = registry.get(contract.application_id)
    if application is None:
        raise ValueError(f"application is not registered: {contract.application_id}")
    stores = getattr(registry, "_application_capability_contracts", None)
    if stores is None:
        stores = registry._application_capability_contracts = {}  # type: ignore[attr-defined]
    key = (contract.application_id, contract.capability_id)
    existing = stores.get(key)
    if existing is not None and existing.contract != contract:
        raise DuplicatedApplicationCapabilityError(
            f"capability contract already registered with a different definition: {contract.capability_id}"
        )
    if existing is not None:
        return existing
    registration = ApplicationCapabilityRegistration(
        capability_id=contract.capability_id,
        application_id=contract.application_id,
        contract=contract,
        approved=approved,
        registration_state="registered",
    )
    stores[key] = registration
    return registration


def get_application_capability_contracts(registry: ApplicationIntegrationRegistry) -> list[ApplicationCapabilityRegistration]:
    stores = getattr(registry, "_application_capability_contracts", None)
    if not stores:
        return []
    return list(stores.values())


def _require_mapping(data: Mapping[str, Any], field_name: str) -> dict[str, Any]:
    value = data.get(field_name, {})
    if value is None:
        value = {}
    if not isinstance(value, Mapping):
        raise ValidationError(f"{field_name} must be an object")
    return dict(value)


# Keep imports in existing models, but avoid unnamed identifier issue.
_IDENTIFIER_PATTERN = __import__("re").compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
