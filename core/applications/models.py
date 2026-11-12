"""Application identity and manifest models for ETHAN (MEM-014 Phase 1)."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping, Sequence

# ETHAN contract version supported by this implementation. A manifest is
# compatible only when its ``contract_version`` belongs to this set. Keeping
# the value in one place avoids drift between identity, validator and schema.
ETHAN_CONTRACT_VERSION = "1.0.0"
CONTRACT_VERSION = ETHAN_CONTRACT_VERSION
SUPPORTED_CONTRACT_VERSIONS: frozenset[str] = frozenset({ETHAN_CONTRACT_VERSION})

VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z._-]+)*$")
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
SHA256_DIGEST_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
MAX_TEXT_LENGTH = 4096
MAX_LIST_LENGTH = 1000
MAX_MANIFEST_DEPTH = 32


class ValidationError(ValueError):
    """Raised for structurally invalid manifest or identity data."""


class ValidationStatus(StrEnum):
    """Explicit, structured validation outcome for agents and operators."""

    VALID = "valid"
    INVALID = "invalid"
    INCOMPLETE = "incomplete"
    INCOMPATIBLE = "incompatible"


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result returned by :class:`ContractValidator`."""

    is_valid: bool
    status: str
    errors: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    identity: "ApplicationIdentity | None" = None

    @property
    def errors_count(self) -> int:
        return len(self.errors)


@dataclass(frozen=True, slots=True)
class ApplicationIdentity:
    """Stable identity for an application and one of its instances.

    ``app_id`` identifies the application itself. ``instance_id`` identifies
    a deployed instance. They are deliberately distinct fields so callers
    cannot collapse application identity and deployment identity into one value.
    """

    app_id: str
    instance_id: str
    name: str
    version: str
    contract_version: str
    publisher: str
    manifest_version: int

    def validate(self) -> None:
        if not isinstance(self.app_id, str) or not IDENTIFIER_PATTERN.fullmatch(self.app_id):
            raise ValidationError(f"invalid app_id: {self.app_id!r}")
        if (
            not isinstance(self.instance_id, str)
            or not IDENTIFIER_PATTERN.fullmatch(self.instance_id)
        ):
            raise ValidationError(f"invalid instance_id: {self.instance_id!r}")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValidationError("name must not be empty")
        if not isinstance(self.version, str) or not VERSION_PATTERN.fullmatch(self.version):
            raise ValidationError(f"invalid version: {self.version!r}")
        if (
            not isinstance(self.contract_version, str)
            or not VERSION_PATTERN.fullmatch(self.contract_version)
        ):
            raise ValidationError(
                f"invalid contract_version: {self.contract_version!r}"
            )
        if not isinstance(self.publisher, str) or not self.publisher.strip():
            raise ValidationError("publisher must not be empty")
        if isinstance(self.manifest_version, bool) or not isinstance(self.manifest_version, int):
            raise ValidationError("manifest_version must be an integer")
        if self.manifest_version < 1:
            raise ValidationError("manifest_version must be positive")

    def is_contract_compatible(self, supported: Sequence[str] | None = None) -> bool:
        """Whether ``contract_version`` is supported by ETHAN or the given set."""
        candidates = set(supported) if supported is not None else set(SUPPORTED_CONTRACT_VERSIONS)
        return self.contract_version in candidates

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ApplicationIdentity":
        if not isinstance(data, Mapping):
            raise ValidationError("identity must be an object")
        try:
            if "manifest_version" not in data:
                raise KeyError("manifest_version")
            manifest_version_raw = data["manifest_version"]
            if isinstance(manifest_version_raw, bool):
                raise ValidationError("manifest_version must be an integer")
            if isinstance(manifest_version_raw, str):
                if not manifest_version_raw.isdigit():
                    raise ValidationError("manifest_version must be an integer")
                manifest_version = int(manifest_version_raw)
            elif isinstance(manifest_version_raw, int):
                manifest_version = manifest_version_raw
            else:
                raise ValidationError("manifest_version must be an integer")
            identity = cls(
                app_id=_require_text(data, "app_id"),
                instance_id=_require_text(data, "instance_id"),
                name=_require_text(data, "name"),
                version=_require_text(data, "version"),
                contract_version=_require_text(data, "contract_version"),
                publisher=_require_text(data, "publisher"),
                manifest_version=manifest_version,
            )
        except ValidationError:
            raise
        except KeyError as error:
            raise ValidationError(f"identity is missing required field: {error.args[0]!r}") from error
        except (TypeError, ValueError) as error:
            raise ValidationError("identity is missing required fields") from error
        identity.validate()
        return identity

    def to_dict(self) -> dict[str, Any]:
        return {
            "app_id": self.app_id,
            "instance_id": self.instance_id,
            "name": self.name,
            "version": self.version,
            "contract_version": self.contract_version,
            "publisher": self.publisher,
            "manifest_version": self.manifest_version,
        }


@dataclass(frozen=True, slots=True)
class ApplicationCapability:
    """A capability declared by an application, not an authorization."""

    name: str
    description: str = ""
    declared_by: str = "application"

    def validate(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValidationError("capability name must not be empty")
        if len(self.name) > MAX_TEXT_LENGTH:
            raise ValidationError("capability name is too long")
        if not isinstance(self.description, str) or len(self.description) > MAX_TEXT_LENGTH:
            raise ValidationError("capability description is invalid")
        if not isinstance(self.declared_by, str) or not self.declared_by.strip():
            raise ValidationError("capability declared_by must not be empty")

    @classmethod
    def from_value(cls, value: Any) -> "ApplicationCapability":
        if isinstance(value, str):
            return cls(name=value)
        if isinstance(value, Mapping):
            if "name" not in value:
                raise ValidationError("capability is missing required field: name")
            description_raw = value.get("description", "")
            declared_by_raw = value.get("declared_by", "application")
            if description_raw is None:
                description = ""
            elif not isinstance(description_raw, str):
                raise ValidationError("capability description must be a string")
            else:
                description = description_raw
            if declared_by_raw is None:
                declared_by = "application"
            elif not isinstance(declared_by_raw, str):
                raise ValidationError("capability declared_by must be a string")
            else:
                declared_by = declared_by_raw
            return cls(
                name=_require_text(value, "name"),
                description=description,
                declared_by=declared_by,
            )
        raise ValidationError("capability must be a string or an object")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "declared_by": self.declared_by,
        }


@dataclass(frozen=True, slots=True)
class ApplicationDependency:
    """A dependency declared by an application."""

    name: str
    version: str
    required: bool = True

    def validate(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValidationError("dependency name must not be empty")
        if not isinstance(self.version, str) or not self.version.strip():
            raise ValidationError("dependency version must not be empty")
        if len(self.name) > MAX_TEXT_LENGTH or len(self.version) > MAX_TEXT_LENGTH:
            raise ValidationError("dependency field is too long")
        if not isinstance(self.required, bool):
            raise ValidationError("dependency required must be a boolean")

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ApplicationDependency":
        if not isinstance(data, Mapping):
            raise ValidationError("dependency must be an object")
        return cls(
            name=_require_text(data, "name"),
            version=_require_text(data, "version"),
            required=_require_bool(data.get("required", True), "required"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "required": self.required,
        }


@dataclass(frozen=True, slots=True)
class InterfaceDescriptor:
    """An interface exposed by an application."""

    kind: str
    entrypoint: str
    description: str = ""

    _ALLOWED_KINDS = frozenset(
        {"cli", "http", "desktop", "api", "operator", "web", "grpc", "websocket"}
    )

    def validate(self) -> None:
        if self.kind not in self._ALLOWED_KINDS:
            raise ValidationError(f"unsupported interface kind: {self.kind}")
        if not isinstance(self.entrypoint, str) or not self.entrypoint.strip():
            raise ValidationError("interface entrypoint must not be empty")
        if len(self.entrypoint) > MAX_TEXT_LENGTH:
            raise ValidationError("interface entrypoint is too long")
        if not isinstance(self.description, str) or len(self.description) > MAX_TEXT_LENGTH:
            raise ValidationError("interface description is invalid")

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "InterfaceDescriptor":
        if not isinstance(data, Mapping):
            raise ValidationError("interface must be an object")
        kind = data.get("kind")
        if kind is None:
            # The mapping key itself may identify the interface kind.
            kind = data.get("type", "http")
        return cls(
            kind=str(kind),
            entrypoint=_require_text(data, "entrypoint"),
            description=str(data.get("description", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "entrypoint": self.entrypoint,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class ApplicationProvenance:
    """Provenance declared for a manifest."""

    source: str
    digest: str | None = None
    repository: str | None = None
    revision: str | None = None

    def validate(self) -> None:
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValidationError("provenance source must not be empty")
        if len(self.source) > MAX_TEXT_LENGTH:
            raise ValidationError("provenance source is too long")
        if self.digest is not None:
            if not isinstance(self.digest, str) or not SHA256_DIGEST_PATTERN.fullmatch(self.digest):
                raise ValidationError("provenance digest must be a 64-character SHA-256 hexadecimal")
        for value, label in ((self.repository, "repository"), (self.revision, "revision")):
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValidationError(f"provenance {label} must not be empty")
            if isinstance(value, str) and len(value) > MAX_TEXT_LENGTH:
                raise ValidationError(f"provenance {label} is too long")

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ApplicationProvenance":
        if not isinstance(data, Mapping):
            raise ValidationError("provenance must be an object")
        digest = data.get("digest")
        return cls(
            source=str(data.get("source", "unknown")),
            digest=None if digest is None else str(digest),
            repository=None if data.get("repository") is None else str(data.get("repository")),
            revision=None if data.get("revision") is None else str(data.get("revision")),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"source": self.source}
        if self.digest is not None:
            result["digest"] = self.digest
        if self.repository is not None:
            result["repository"] = self.repository
        if self.revision is not None:
            result["revision"] = self.revision
        return result


@dataclass
class ApplicationManifest:
    """Canonical manifest for an independent ETHAN ecosystem application."""

    identity: ApplicationIdentity
    capabilities: list[ApplicationCapability] = field(default_factory=list)
    dependencies: list[ApplicationDependency] = field(default_factory=list)
    compatibility: list[str] = field(default_factory=list)
    incompatibilities: list[str] = field(default_factory=list)
    interfaces: dict[str, InterfaceDescriptor] = field(default_factory=dict)
    permissions: list[str] = field(default_factory=list)
    provenance: ApplicationProvenance = field(
        default_factory=lambda: ApplicationProvenance(source="application")
    )
    metadata: dict[str, str] = field(default_factory=dict)

    _ALLOWED_ROOT_FIELDS = frozenset(
        {
            "identity",
            "capabilities",
            "dependencies",
            "compatibility",
            "incompatibilities",
            "interfaces",
            "permissions",
            "provenance",
            "metadata",
        }
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ApplicationManifest":
        if not isinstance(data, Mapping):
            raise ValidationError("manifest must be an object")

        unknown_fields = set(data) - cls._ALLOWED_ROOT_FIELDS
        if unknown_fields:
            raise ValidationError(
                "manifest contains unauthorized fields: "
                + ", ".join(sorted(str(field) for field in unknown_fields))
            )

        _check_depth_and_size(data)

        identity_raw = data.get("identity")
        if not isinstance(identity_raw, Mapping):
            raise ValidationError("manifest is missing required field: identity")
        identity = ApplicationIdentity.from_mapping(identity_raw)

        capabilities = _parse_capabilities(data.get("capabilities", []))
        dependencies = _parse_dependencies(data.get("dependencies", []))
        compatibility = _parse_string_list(data.get("compatibility", []), "compatibility")
        incompatibilities = _parse_string_list(
            data.get("incompatibilities", []), "incompatibilities"
        )
        interfaces = _parse_interfaces(data.get("interfaces", {}))
        permissions = _parse_string_list(data.get("permissions", []), "permissions")
        provenance = _parse_provenance(data.get("provenance", {"source": "application"}))
        metadata = _parse_metadata(data.get("metadata", {}))

        _check_unique(capabilities, "capability")
        _check_unique_dependencies(dependencies)
        _ensure_string_items(permissions, "permissions")
        _ensure_string_items(compatibility, "compatibility")
        _ensure_string_items(incompatibilities, "incompatibilities")

        manifest = cls(
            identity=identity,
            capabilities=capabilities,
            dependencies=dependencies,
            compatibility=compatibility,
            incompatibilities=incompatibilities,
            interfaces=interfaces,
            permissions=permissions,
            provenance=provenance,
            metadata=metadata,
        )
        manifest.validate()
        return manifest

    def validate(self) -> None:
        self.identity.validate()
        for capability in self.capabilities:
            capability.validate()
        for dependency in self.dependencies:
            dependency.validate()
        for interface in self.interfaces.values():
            interface.validate()
        self.provenance.validate()
        if not isinstance(self.compatibility, list):
            raise ValidationError("compatibility must be a list")
        if not isinstance(self.incompatibilities, list):
            raise ValidationError("incompatibilities must be a list")
        if not isinstance(self.permissions, list):
            raise ValidationError("permissions must be a list")
        if not isinstance(self.metadata, dict):
            raise ValidationError("metadata must be an object")
        for key, value in self.metadata.items():
            if not isinstance(key, str) or not key.strip():
                raise ValidationError("metadata keys must be non-empty strings")
            if not isinstance(value, str) or len(value) > MAX_TEXT_LENGTH:
                raise ValidationError("metadata values must be short strings")

    @staticmethod
    def json_schema() -> dict[str, Any]:
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://ethan.local/schemas/application-manifest.schema.json",
            "title": "ETHAN Application Manifest",
            "type": "object",
            "additionalProperties": False,
            "required": ["identity"],
            "properties": {
                "identity": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "app_id",
                        "instance_id",
                        "name",
                        "version",
                        "contract_version",
                        "publisher",
                        "manifest_version",
                    ],
                    "properties": {
                        "app_id": {"type": "string", "pattern": IDENTIFIER_PATTERN.pattern},
                        "instance_id": {"type": "string", "pattern": IDENTIFIER_PATTERN.pattern},
                        "name": {"type": "string", "minLength": 1, "maxLength": MAX_TEXT_LENGTH},
                        "version": {"type": "string", "pattern": VERSION_PATTERN.pattern},
                        "contract_version": {"type": "string", "pattern": VERSION_PATTERN.pattern},
                        "publisher": {"type": "string", "minLength": 1, "maxLength": MAX_TEXT_LENGTH},
                        "manifest_version": {"type": "integer", "minimum": 1},
                    },
                },
                "capabilities": {
                    "type": "array",
                    "maxItems": MAX_LIST_LENGTH,
                    "items": {
                        "oneOf": [
                            {"type": "string", "minLength": 1, "maxLength": MAX_TEXT_LENGTH},
                            {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["name"],
                                "properties": {
                                    "name": {"type": "string", "minLength": 1, "maxLength": MAX_TEXT_LENGTH},
                                    "description": {"type": "string", "maxLength": MAX_TEXT_LENGTH},
                                    "declared_by": {"type": "string", "minLength": 1, "maxLength": MAX_TEXT_LENGTH},
                                },
                            },
                        ]
                    },
                },
                "dependencies": {
                    "type": "array",
                    "maxItems": MAX_LIST_LENGTH,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["name", "version"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1, "maxLength": MAX_TEXT_LENGTH},
                            "version": {"type": "string", "minLength": 1, "maxLength": MAX_TEXT_LENGTH},
                            "required": {"type": "boolean"},
                        },
                    },
                },
                "compatibility": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1, "maxLength": MAX_TEXT_LENGTH},
                },
                "incompatibilities": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1, "maxLength": MAX_TEXT_LENGTH},
                },
                "interfaces": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "required": ["entrypoint"],
                        "properties": {
                            "kind": {"type": "string"},
                            "entrypoint": {"type": "string", "minLength": 1, "maxLength": MAX_TEXT_LENGTH},
                            "description": {"type": "string", "maxLength": MAX_TEXT_LENGTH},
                        },
                    },
                },
                "permissions": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1, "maxLength": MAX_TEXT_LENGTH},
                },
                "provenance": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["source"],
                    "properties": {
                        "source": {"type": "string", "minLength": 1, "maxLength": MAX_TEXT_LENGTH},
                        "digest": {
                            "type": "string",
                            "pattern": "^[0-9a-fA-F]{64}$",
                        },
                        "repository": {"type": "string", "minLength": 1, "maxLength": MAX_TEXT_LENGTH},
                        "revision": {"type": "string", "minLength": 1, "maxLength": MAX_TEXT_LENGTH},
                    },
                },
                "metadata": {
                    "type": "object",
                    "additionalProperties": {"type": "string", "maxLength": MAX_TEXT_LENGTH},
                },
            },
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ApplicationManifest":
        return cls.from_mapping(data)

    @classmethod
    def from_yaml(cls, payload: str) -> "ApplicationManifest":
        import yaml

        data = yaml.safe_load(payload)
        if not isinstance(data, Mapping):
            raise ValidationError("manifest root must be an object")
        return cls.from_mapping(data)

    @classmethod
    def from_json(cls, payload: str) -> "ApplicationManifest":
        data = json.loads(payload)
        if not isinstance(data, Mapping):
            raise ValidationError("manifest root must be an object")
        return cls.from_mapping(data)

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "capabilities": [capability.to_dict() for capability in self.capabilities],
            "dependencies": [dependency.to_dict() for dependency in self.dependencies],
            "compatibility": list(self.compatibility),
            "incompatibilities": list(self.incompatibilities),
            "interfaces": {
                name: descriptor.to_dict() for name, descriptor in self.interfaces.items()
            },
            "permissions": list(self.permissions),
            "provenance": self.provenance.to_dict(),
            "metadata": dict(self.metadata),
        }

    def to_yaml(self) -> str:
        import yaml

        return yaml.safe_dump(self.to_dict(), sort_keys=False, allow_unicode=True)


def _require_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{field_name} must be a boolean")
    return value


def _require_text(data: Mapping[str, Any], field_name: str) -> str:
    if field_name not in data:
        raise ValidationError(f"identity is missing required field: {field_name}")
    value = data[field_name]
    if not isinstance(value, str) or not value.strip():
        # Allow numeric app-like values only for manifest_version; strings are strict.
        raise ValidationError(f"{field_name} must be a non-empty string")
    if len(value) > MAX_TEXT_LENGTH:
        raise ValidationError(f"{field_name} is too long")
    return value


def _check_depth_and_size(value: Any, depth: int = 0) -> None:
    if depth > MAX_MANIFEST_DEPTH:
        raise ValidationError("manifest exceeds maximum nesting depth")
    if isinstance(value, Mapping):
        if len(value) > MAX_LIST_LENGTH:
            raise ValidationError("manifest object is too large")
        for item in value.values():
            _check_depth_and_size(item, depth + 1)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if len(value) > MAX_LIST_LENGTH:
            raise ValidationError("manifest list is too large")
        for item in value:
            _check_depth_and_size(item, depth + 1)
    elif isinstance(value, str) and len(value) > MAX_TEXT_LENGTH:
        raise ValidationError("manifest text value is too long")


def _parse_capabilities(value: Any) -> list[ApplicationCapability]:
    if not isinstance(value, list):
        raise ValidationError("capabilities must be a list")
    result: list[ApplicationCapability] = []
    for item in value:
        capability = ApplicationCapability.from_value(item)
        capability.validate()
        result.append(capability)
    return result


def _parse_dependencies(value: Any) -> list[ApplicationDependency]:
    if not isinstance(value, list):
        raise ValidationError("dependencies must be a list")
    result: list[ApplicationDependency] = []
    for item in value:
        dependency = ApplicationDependency.from_mapping(item if isinstance(item, Mapping) else {})
        if not isinstance(item, Mapping):
            raise ValidationError("dependencies must be objects with name and version")
        dependency.validate()
        result.append(dependency)
    return result


def _parse_interfaces(value: Any) -> dict[str, InterfaceDescriptor]:
    if not isinstance(value, Mapping):
        raise ValidationError("interfaces must be an object")
    result: dict[str, InterfaceDescriptor] = {}
    for key, raw in value.items():
        if not isinstance(key, str) or not key.strip():
            raise ValidationError("interface name must be a non-empty string")
        descriptor = InterfaceDescriptor.from_mapping(raw if isinstance(raw, Mapping) else {})
        if not isinstance(raw, Mapping):
            raise ValidationError(f"interface {key} must be an object")
        descriptor.validate()
        result[key] = descriptor
    return result


def _parse_string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise ValidationError(f"{field_name} must be a list")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValidationError(f"{field_name} must contain non-empty strings")
        if len(item) > MAX_TEXT_LENGTH:
            raise ValidationError(f"{field_name} item is too long")
        result.append(item)
    return result


def _parse_provenance(value: Any) -> ApplicationProvenance:
    if not isinstance(value, Mapping):
        raise ValidationError("provenance must be an object")
    provenance = ApplicationProvenance.from_mapping(value)
    provenance.validate()
    return provenance


def _parse_metadata(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ValidationError("metadata must be an object")
    result: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not key.strip():
            raise ValidationError("metadata keys must be non-empty strings")
        if not isinstance(item, str):
            raise ValidationError("metadata values must be strings")
        if len(key) > MAX_TEXT_LENGTH or len(item) > MAX_TEXT_LENGTH:
            raise ValidationError("metadata entry is too long")
        result[key] = item
    return result


def _check_unique(items: Sequence[ApplicationCapability], label: str) -> None:
    names = [item.name for item in items]
    if len(names) != len(set(names)):
        raise ValidationError(f"duplicate {label} name in manifest")


def _check_unique_dependencies(items: Sequence[ApplicationDependency]) -> None:
    names = [item.name for item in items]
    if len(names) != len(set(names)):
        raise ValidationError("duplicate dependency name in manifest")


def _ensure_string_items(items: Sequence[str], field_name: str) -> None:
    for item in items:
        if not isinstance(item, str) or not item.strip():
            raise ValidationError(f"{field_name} must contain non-empty strings")
