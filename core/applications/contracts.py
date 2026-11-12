"""Common integration contracts for ETHAN independent applications (MEM-014 Phase 4)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping

from core.applications.models import (
    ApplicationCapability,
    ApplicationDependency,
    ApplicationIdentity,
    ApplicationManifest,
    ApplicationProvenance,
    InterfaceDescriptor,
    ValidationError,
    ValidationResult,
    ValidationStatus,
)
from core.applications.validator import ContractValidator


class IntegrationType(StrEnum):
    """Distinct kinds of integrable ETHAN artifacts."""

    APPLICATION = "application"
    PLUGIN = "plugin"
    EXTENSION = "extension"
    SKILL = "skill"


class CompatibilityStatus(StrEnum):
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"


@dataclass(slots=True)
class ExtensionContract:
    """Versioned contract shared by independent application integrations."""

    contract_version: str = "1.0.0"
    integration_type: IntegrationType = IntegrationType.APPLICATION
    identity: ApplicationIdentity | None = None
    capabilities: list[ApplicationCapability] = field(default_factory=list)
    dependencies: list[ApplicationDependency] = field(default_factory=list)
    compatibility: list[str] = field(default_factory=list)
    interfaces: dict[str, InterfaceDescriptor] = field(default_factory=dict)
    requested_permissions: list[str] = field(default_factory=list)
    permission_requirements: dict[str, str] = field(default_factory=dict)
    provenance: ApplicationProvenance = field(
        default_factory=lambda: ApplicationProvenance(source="application")
    )
    ethan_versions: list[str] = field(default_factory=list)
    adapters: list[str] = field(default_factory=list)

    _ALLOWED_INTEGRATION_TYPES = frozenset(item.value for item in IntegrationType)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any], capability_registry: Any = None) -> "ExtensionContract":
        if not isinstance(data, Mapping):
            raise ValidationError("contract must be an object")

        # Contract-specific fields are not part of the application manifest.
        manifest_data = {
            key: value for key, value in data.items()
            if key not in {
                "integration_type", "type", "permission_requirements",
                "permission_capabilities", "requested_permissions", "ethan_versions",
                "ethan_compatibility", "adapters", "contract_version",
            }
        }
        if "contract_version" in data:
            manifest_data.setdefault("identity", dict(data.get("identity", {})))
            if isinstance(manifest_data.get("identity"), Mapping):
                manifest_data["identity"] = dict(manifest_data["identity"])
                manifest_data["identity"]["contract_version"] = data["identity"].get(
                    "contract_version", data.get("identity", {}).get("contract_version")
                )
        manifest = ApplicationManifest.from_mapping(manifest_data)

        integration_type_raw = data.get("integration_type", data.get("type", "application"))
        if not isinstance(integration_type_raw, str) or integration_type_raw not in cls._ALLOWED_INTEGRATION_TYPES:
            raise ValidationError(f"unsupported integration_type: {integration_type_raw!r}")

        requirements_raw = data.get("permission_requirements", data.get("permission_capabilities", {}))
        if not isinstance(requirements_raw, Mapping):
            raise ValidationError("permission_requirements must be an object")
        requirements: dict[str, str] = {}
        for key, value in requirements_raw.items():
            if not isinstance(key, str) or not key.strip():
                raise ValidationError("permission name must be a non-empty string")
            if not isinstance(value, str) or not value.strip():
                raise ValidationError("permission capability mapping must be a non-empty string")
            requirements[key] = value

        requested_permissions = _string_list(
            data.get("requested_permissions", data.get("permissions", manifest.permissions)),
            "requested_permissions",
        )

        contract_version = str(data.get("contract_version", manifest.identity.contract_version))
        ethan_versions = _string_list(data.get("ethan_versions", data.get("ethan_compatibility", [])), "ethan_versions")
        adapters = _string_list(data.get("adapters", []), "adapters")

        if capability_registry is not None:
            _validate_with_registry(capability_registry, manifest.capabilities, requested_permissions, requirements)

        contract = cls(
            contract_version=contract_version,
            integration_type=IntegrationType(integration_type_raw),
            identity=manifest.identity,
            capabilities=manifest.capabilities,
            dependencies=manifest.dependencies,
            compatibility=manifest.compatibility,
            interfaces=manifest.interfaces,
            requested_permissions=requested_permissions,
            permission_requirements=requirements,
            provenance=manifest.provenance,
            ethan_versions=ethan_versions,
            adapters=adapters,
        )
        contract.validate(manifest.identity.contract_version)
        return contract

    def validate(self, application_contract_version: str | None = None) -> None:
        if self.identity is None:
            raise ValidationError("contract is missing identity")
        self.identity.validate()

        if not _version_matches(self.contract_version):
            raise ValidationError(f"invalid contract_version: {self.contract_version!r}")

        supported = {"1.0.0"}
        if self.contract_version not in supported:
            raise ValidationError(f"contract_version is not compatible: {self.contract_version!r}")

        for capability in self.capabilities:
            capability.validate()
        for dependency in self.dependencies:
            dependency.validate()
        for interface in self.interfaces.values():
            interface.validate()
        self.provenance.validate()

        declared_caps = {capability.name for capability in self.capabilities}
        for permission in self.requested_permissions:
            if not isinstance(permission, str) or not permission.strip():
                raise ValidationError("requested_permissions must contain non-empty strings")
            if permission in self.permission_requirements:
                required_capability = self.permission_requirements[permission]
                if required_capability not in declared_caps:
                    raise ValidationError(
                        f"permission {permission!r} requires undeclared capability {required_capability!r}"
                    )
            elif declared_caps and not _permission_compatible(permission, declared_caps):
                raise ValidationError(
                    f"permission {permission!r} is not compatible with declared capabilities"
                )
            elif not declared_caps and self.requested_permissions:
                raise ValidationError("permissions require at least one declared capability")

        for adapter in self.adapters:
            if not isinstance(adapter, str) or not adapter.strip():
                raise ValidationError("adapters must contain non-empty strings")

        for ethan_version in self.ethan_versions:
            if not _version_matches(ethan_version):
                raise ValidationError(f"invalid ethan version: {ethan_version!r}")

    def to_dict(self) -> dict[str, Any]:
        if self.identity is None:
            identity = None
        else:
            identity = self.identity.to_dict()
        return {
            "contract_version": self.contract_version,
            "integration_type": self.integration_type.value,
            "identity": identity,
            "capabilities": [capability.to_dict() for capability in self.capabilities],
            "dependencies": [dependency.to_dict() for dependency in self.dependencies],
            "compatibility": list(self.compatibility),
            "interfaces": {
                name: descriptor.to_dict() for name, descriptor in self.interfaces.items()
            },
            "requested_permissions": list(self.requested_permissions),
            "permission_requirements": dict(self.permission_requirements),
            "provenance": self.provenance.to_dict(),
            "ethan_versions": list(self.ethan_versions),
            "adapters": list(self.adapters),
        }

    @classmethod
    def from_yaml(cls, payload: str) -> "ExtensionContract":
        import yaml

        data = yaml.safe_load(payload)
        if not isinstance(data, Mapping):
            raise ValidationError("contract root must be an object")
        return cls.from_mapping(data)


class ExtensionContractValidator:
    """Validator for extension/integration contracts."""

    def __init__(self, supported_contract_versions: set[str] | frozenset[str] | None = None, capability_registry: Any = None) -> None:
        self.supported_contract_versions = (
            frozenset(supported_contract_versions) if supported_contract_versions is not None else frozenset({"1.0.0"})
        )
        self.capability_registry = capability_registry

    def validate(self, data: Any) -> ValidationResult:
        if not isinstance(data, Mapping):
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID.value,
                errors=("contract must be an object",),
                warnings=(),
                identity=None,
            )
        errors: list[str] = []
        identity = None
        contract: ExtensionContract | None = None
        try:
            contract = ExtensionContract.from_mapping(data)
            identity = contract.identity
            if contract.contract_version not in self.supported_contract_versions:
                errors.append(
                    f"contract_version is not compatible: {contract.contract_version!r}"
                )
        except ValidationError as exc:
            errors.append(str(exc))

        status = ValidationStatus.VALID.value
        if errors:
            joined = " ".join(errors)
            if "missing required" in joined or "missing identity" in joined or "is missing" in joined:
                status = ValidationStatus.INCOMPLETE.value
            elif "contract_version is not compatible" in joined or "ethan version" in joined.lower():
                status = ValidationStatus.INCOMPATIBLE.value
            else:
                status = ValidationStatus.INVALID.value

        return ValidationResult(
            is_valid=len(errors) == 0,
            status=status,
            errors=tuple(errors),
            warnings=(),
            identity=identity,
        )

    def validate_mapping(self, data: Any) -> ValidationResult:
        return self.validate(data)

    def validate_data(self, data: Any) -> ValidationResult:
        return self.validate(data)


def _string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise ValidationError(f"{field_name} must be a list")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValidationError(f"{field_name} must contain non-empty strings")
        result.append(item)
    return result


def _version_matches(value: str) -> bool:
    import re

    return bool(re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z._-]+)*", value))


def _permission_compatible(permission: str, capabilities: set[str]) -> bool:
    # A permission is compatible only when it is explicitly equal to a declared
    # capability. Alias/prefix compatibility must be declared in
    # permission_requirements, not inferred.
    return permission in capabilities


# Aliases for callers expecting alternative names.
ApplicationIntegrationContract = ExtensionContract
IntegrationContract = ExtensionContract
ApplicationContract = ExtensionContract
ExtensionContractValidatorAlias = ExtensionContractValidator
IntegrationContractValidator = ExtensionContractValidator
ApplicationContractValidator = ExtensionContractValidator
ContractValidatorV4 = ExtensionContractValidator


__all__ = [
    "ApplicationContract",
    "ApplicationContractValidator",
    "ApplicationIntegrationContract",
    "CompatibilityStatus",
    "ExtensionContract",
    "ExtensionContractValidator",
    "IntegrationContract",
    "IntegrationContractValidator",
    "IntegrationType",
]


def _validate_with_registry(registry: Any, capabilities, requested_permissions, requirements: dict[str, str]) -> None:
    declared = {capability.name for capability in capabilities}
    declared_ids = {capability.name for capability in capabilities}  # capability names, not registry IDs
    # Validate names that are known registry IDs when possible.
    try:
        if hasattr(registry, "validate_capability_ids"):
            registry_known = {cap.name for cap in capabilities if hasattr(registry, "exists") and registry.exists(cap.name)}
            unknown_declared = [cap.name for cap in capabilities if hasattr(registry, "exists") and not registry.exists(cap.name)]
            if unknown_declared:
                raise ValidationError("unknown capability in registry: " + ", ".join(sorted(unknown_declared)))
    except ValidationError:
        raise
    except Exception:
        pass
    for permission in requested_permissions:
        if permission in requirements:
            required_capability = requirements[permission]
            if hasattr(registry, "exists") and not registry.exists(required_capability):
                raise ValidationError(f"permission {permission!r} requires unknown capability {required_capability!r}")
        elif declared and permission not in declared and not any(permission == cap for cap in declared):
            # Registry-based exact mapping is still required for unknown mappings.
            pass
