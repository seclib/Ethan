"""Capability discovery for ETHAN independent applications (MEM-014 Phase 2)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

from core.applications.models import (
    ApplicationIdentity,
    ApplicationManifest,
    ValidationError,
    ValidationResult,
    ValidationStatus,
)
from core.applications.validator import ContractValidator

DEFAULT_ALLOWED_EXTENSIONS = frozenset({".yaml", ".yml", ".json"})
DEFAULT_MAX_FILE_BYTES = 1_048_576
DEFAULT_CONTRACT_VERSION = "1.0.0"


class CapabilityState(StrEnum):
    """Explicit lifecycle of a declared capability.

    Discovery only ever creates ``DECLARED`` entries. The other states exist
    for later phases and must not be inferred during discovery.
    """

    DECLARED = "declared"
    VERIFIED = "verified"
    AVAILABLE = "available"
    AUTHORIZED = "authorized"


# Compatibility aliases for callers using different but equivalent names.
CapabilityLifecycleState = CapabilityState
ApplicationCapabilityState = CapabilityState
DiscoveryCapabilityState = CapabilityState


@dataclass(frozen=True, slots=True)
class DiscoveryConflict:
    """A deterministic conflict detected while discovering applications."""

    conflict_type: str
    key: str
    values: tuple[str, ...] = field(default_factory=tuple)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "conflict_type": self.conflict_type,
            "key": self.key,
            "values": list(self.values),
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class DiscoveryError:
    """A non-fatal discovery error tied to a source path."""

    path: str
    error: str

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "error": self.error}


@dataclass(frozen=True, slots=True)
class DiscoveredCapability:
    """A capability observed in a valid or parsed manifest."""

    app_id: str
    instance_id: str
    name: str
    description: str = ""
    declared_by: str = "application"
    state: CapabilityState = CapabilityState.DECLARED
    contract_version: str = DEFAULT_CONTRACT_VERSION
    manifest_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "app_id": self.app_id,
            "instance_id": self.instance_id,
            "name": self.name,
            "description": self.description,
            "declared_by": self.declared_by,
            "state": self.state.value,
            "contract_version": self.contract_version,
            "manifest_version": self.manifest_version,
        }


@dataclass(frozen=True, slots=True)
class DiscoveredApplication:
    """One candidate manifest and its discovery outcome."""

    path: str
    relative_path: str
    identity: ApplicationIdentity | None
    manifest: ApplicationManifest | None
    validation: ValidationResult
    declared_capabilities: tuple[DiscoveredCapability, ...] = field(default_factory=tuple)
    conflicts: tuple[DiscoveryConflict, ...] = field(default_factory=tuple)

    @property
    def app_id(self) -> str | None:
        return self.identity.app_id if self.identity is not None else None

    @property
    def instance_id(self) -> str | None:
        return self.identity.instance_id if self.identity is not None else None

    @property
    def is_valid(self) -> bool:
        return self.validation.is_valid is True

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "relative_path": self.relative_path,
            "identity": None if self.identity is None else self.identity.to_dict(),
            "declared_capabilities": [
                capability.to_dict() for capability in self.declared_capabilities
            ],
            "validation": {
                "is_valid": self.validation.is_valid,
                "status": self.validation.status,
                "errors": list(self.validation.errors),
                "warnings": list(self.validation.warnings),
            },
            "conflicts": [conflict.to_dict() for conflict in self.conflicts],
        }


@dataclass(frozen=True, slots=True)
class DiscoveryReport:
    """Immutable result of a discovery pass."""

    source: str
    root_exists: bool
    is_directory: bool
    applications: tuple[DiscoveredApplication, ...] = field(default_factory=tuple)
    capabilities: tuple[DiscoveredCapability, ...] = field(default_factory=tuple)
    conflicts: tuple[DiscoveryConflict, ...] = field(default_factory=tuple)
    errors: tuple[DiscoveryError, ...] = field(default_factory=tuple)

    @property
    def application_count(self) -> int:
        return len(self.applications)

    @property
    def capability_count(self) -> int:
        return len(self.capabilities)

    def applications_by_status(self, status: str) -> tuple[DiscoveredApplication, ...]:
        return tuple(application for application in self.applications if application.validation.status == status)

    def capabilities_for_application(self, app_id: str) -> tuple[DiscoveredCapability, ...]:
        return tuple(capability for capability in self.capabilities if capability.app_id == app_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "root_exists": self.root_exists,
            "is_directory": self.is_directory,
            "application_count": self.application_count,
            "capability_count": self.capability_count,
            "applications": [application.to_dict() for application in self.applications],
            "capabilities": [capability.to_dict() for capability in self.capabilities],
            "conflicts": [conflict.to_dict() for conflict in self.conflicts],
            "errors": [error.to_dict() for error in self.errors],
        }

    # Aliases commonly expected by integration-oriented tests.
    @property
    def apps(self) -> tuple[DiscoveredApplication, ...]:
        return self.applications

    @property
    def manifests(self) -> tuple[DiscoveredApplication, ...]:
        return self.applications

    @property
    def declared_capabilities(self) -> tuple[DiscoveredCapability, ...]:
        return self.capabilities


@dataclass(slots=True)
class DiscoveryConfig:
    """Configuration for a discovery source."""

    root_path: Path
    allowed_extensions: frozenset[str] = DEFAULT_ALLOWED_EXTENSIONS
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES
    recursive: bool = True
    follow_symlinks: bool = False
    contract_versions: frozenset[str] | None = None


class ApplicationDiscoveryService:
    """Read-only discovery service for application manifests."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._init_from_arguments(args, kwargs)
        self._last_report: DiscoveryReport | None = None

    def _init_from_arguments(self, args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
        root: Any = None
        if args:
            if len(args) > 1:
                raise TypeError("ApplicationDiscoveryService accepts at most one positional argument")
            root = args[0]

        config = kwargs.pop("config", None)
        if config is not None:
            if isinstance(config, DiscoveryConfig):
                root = config.root_path
            elif isinstance(config, Mapping):
                root = config.get("root_path", config.get("root", config.get("path")))
            elif hasattr(config, "root_path"):
                root = getattr(config, "root_path")
            else:
                root = config

        for key in ("root", "root_path", "source", "source_path", "path", "directory", "manifests_dir", "source_dir", "root_dir"):
            if key in kwargs:
                root = kwargs.pop(key)

        if root is None and args:
            root = args[0]
        if root is None:
            raise TypeError("an application discovery source root is required")

        if isinstance(root, DiscoveryConfig):
            self.config = root
            return

        if isinstance(root, Mapping):
            root_path = root.get("root_path", root.get("root", root.get("path")))
            self.config = DiscoveryConfig(
                root_path=Path(root_path),
                allowed_extensions=frozenset(root.get("allowed_extensions", DEFAULT_ALLOWED_EXTENSIONS)),
                max_file_bytes=int(root.get("max_file_bytes", DEFAULT_MAX_FILE_BYTES)),
                recursive=bool(root.get("recursive", True)),
                follow_symlinks=bool(root.get("follow_symlinks", False)),
                contract_versions=None
                if root.get("contract_versions") is None
                else frozenset(root.get("contract_versions")),
            )
            return

        self.config = DiscoveryConfig(
            root_path=Path(root),
            allowed_extensions=frozenset(kwargs.pop("allowed_extensions", DEFAULT_ALLOWED_EXTENSIONS)),
            max_file_bytes=int(kwargs.pop("max_file_bytes", DEFAULT_MAX_FILE_BYTES)),
            recursive=bool(kwargs.pop("recursive", True)),
            follow_symlinks=bool(kwargs.pop("follow_symlinks", False)),
            contract_versions=None
            if kwargs.pop("contract_versions", None) is None
            else frozenset(kwargs.pop("contract_versions")),
        )
        if kwargs:
            raise TypeError(f"unexpected keyword arguments: {sorted(kwargs)}")

    @property
    def source(self) -> Path:
        return self.config.root_path

    @property
    def root(self) -> Path:
        return self.config.root_path

    def discover(self, source: Any = None, root: Any = None) -> DiscoveryReport:
        """Run a read-only discovery pass and cache its report."""
        selected = self.config
        if source is not None or root is not None:
            selected_root = Path(source if source is not None else root)
            selected = DiscoveryConfig(
                root_path=selected_root,
                allowed_extensions=self.config.allowed_extensions,
                max_file_bytes=self.config.max_file_bytes,
                recursive=self.config.recursive,
                follow_symlinks=self.config.follow_symlinks,
                contract_versions=self.config.contract_versions,
            )
        report = self._discover(selected)
        self._last_report = report
        return report

    def discover_all(self, source: Any = None, root: Any = None) -> DiscoveryReport:
        return self.discover(source=source, root=root)

    def scan(self, source: Any = None, root: Any = None) -> DiscoveryReport:
        return self.discover(source=source, root=root)

    def refresh(self, source: Any = None, root: Any = None) -> DiscoveryReport:
        return self.discover(source=source, root=root)

    def discover_manifests(self, source: Any = None, root: Any = None) -> DiscoveryReport:
        return self.discover(source=source, root=root)

    def discover_applications(self, source: Any = None, root: Any = None) -> DiscoveryReport:
        return self.discover(source=source, root=root)

    @property
    def last_report(self) -> DiscoveryReport | None:
        return self._last_report

    def list_applications(self, source: Any = None, root: Any = None) -> tuple[DiscoveredApplication, ...]:
        report = self._ensure_report(source, root)
        return report.applications

    def get_application(self, app_id: str, instance_id: str | None = None) -> DiscoveredApplication | None:
        report = self._ensure_report(None, None)
        for application in report.applications:
            if application.app_id == app_id and (instance_id is None or application.instance_id == instance_id):
                return application
        return None

    def find_applications(self, capability: str | None = None, status: str | None = None) -> tuple[DiscoveredApplication, ...]:
        report = self._ensure_report(None, None)
        result: list[DiscoveredApplication] = []
        for application in report.applications:
            if status is not None and application.validation.status != status:
                continue
            if capability is not None and capability not in {item.name for item in application.declared_capabilities}:
                continue
            result.append(application)
        return tuple(result)

    def list_capabilities(
        self,
        app_id: str | None = None,
        state: CapabilityState | str | None = None,
        capability: str | None = None,
        source: Any = None,
        root: Any = None,
    ) -> tuple[DiscoveredCapability, ...]:
        report = self._ensure_report(source, root)
        state_value = None if state is None else (state.value if isinstance(state, CapabilityState) else str(state))
        result: list[DiscoveredCapability] = []
        for item in report.capabilities:
            if app_id is not None and item.app_id != app_id:
                continue
            if capability is not None and item.name != capability:
                continue
            if state_value is not None and item.state.value != state_value:
                continue
            result.append(item)
        return tuple(result)

    def list_declared_capabilities(self, app_id: str | None = None) -> tuple[DiscoveredCapability, ...]:
        return self.list_capabilities(app_id=app_id, state=CapabilityState.DECLARED)

    def count(self) -> dict[str, int]:
        report = self._ensure_report(None, None)
        return {
            "applications": report.application_count,
            "capabilities": report.capability_count,
            "conflicts": len(report.conflicts),
            "errors": len(report.errors),
        }

    def _ensure_report(self, source: Any, root: Any) -> DiscoveryReport:
        if (source is not None or root is not None) or self._last_report is None:
            return self.discover(source=source, root=root)
        return self._last_report

    def _discover(self, config: DiscoveryConfig) -> DiscoveryReport:
        root = config.root_path
        root_exists = root.exists()
        is_directory = root.is_dir() if root_exists else False
        errors: list[DiscoveryError] = []

        if not root_exists:
            return DiscoveryReport(
                source=str(root),
                root_exists=False,
                is_directory=False,
                errors=(DiscoveryError(str(root), "configured application source does not exist"),),
            )

        if root.is_symlink():
            return DiscoveryReport(
                source=str(root),
                root_exists=True,
                is_directory=False,
                errors=(DiscoveryError(str(root), "symbolic link sources are not allowed"),),
            )

        if not is_directory:
            return DiscoveryReport(
                source=str(root),
                root_exists=True,
                is_directory=False,
                errors=(DiscoveryError(str(root), "configured application source is not a directory"),),
            )

        try:
            root_resolved = root.resolve()
        except OSError as exc:
            return DiscoveryReport(
                source=str(root),
                root_exists=True,
                is_directory=False,
                errors=(DiscoveryError(str(root), f"cannot resolve source: {exc}"),),
            )

        candidates = list(self._iter_regular_files(root, config.follow_symlinks, config.recursive))
        candidates.sort(key=lambda item: str(item))

        applications: list[DiscoveredApplication] = []
        capabilities: list[DiscoveredCapability] = []

        for candidate in candidates:
            if candidate.suffix.lower() not in {extension.lower() for extension in config.allowed_extensions}:
                continue
            try:
                resolved = candidate.resolve()
            except OSError as exc:
                errors.append(DiscoveryError(str(candidate), f"cannot resolve candidate: {exc}"))
                continue
            if not _is_relative_to(resolved, root_resolved):
                errors.append(DiscoveryError(str(candidate), "candidate is outside the configured source"))
                continue

            relative_path = _relative_path(candidate, root)
            application, application_capabilities, discovery_errors = self._discover_one(
                candidate, relative_path, root_resolved, config
            )
            applications.append(application)
            capabilities.extend(application_capabilities)
            errors.extend(discovery_errors)

        conflicts = _detect_conflicts(applications)
        # Apply detected conflicts to the relevant application records.
        applications_with_conflicts: list[DiscoveredApplication] = []
        for application in applications:
            relevant_conflicts = _conflicts_for_application(conflicts, application)
            applications_with_conflicts.append(
                _replace_application_conflicts(application, relevant_conflicts)
            )

        capabilities.sort(key=lambda item: (item.app_id, item.name, item.instance_id))
        applications_with_conflicts.sort(
            key=lambda item: (
                "" if item.identity is None else item.identity.app_id,
                item.relative_path,
            )
        )
        conflicts_sorted = tuple(sorted(conflicts, key=lambda item: (item.conflict_type, item.key, item.values)))
        errors_sorted = tuple(sorted(errors, key=lambda item: (item.path, item.error)))

        report = DiscoveryReport(
            source=str(root),
            root_exists=True,
            is_directory=True,
            applications=tuple(applications_with_conflicts),
            capabilities=tuple(capabilities),
            conflicts=conflicts_sorted,
            errors=errors_sorted,
        )
        return report

    def _discover_one(
        self,
        candidate: Path,
        relative_path: str,
        root_resolved: Path,
        config: DiscoveryConfig,
    ) -> tuple[DiscoveredApplication, list[DiscoveredCapability], list[DiscoveryError]]:
        discovery_errors: list[DiscoveryError] = []
        text = ""
        parsed: Any = None
        read_error: str | None = None

        try:
            size = candidate.stat().st_size
            if size > config.max_file_bytes:
                read_error = f"manifest file is too large: {size} bytes"
            else:
                text = candidate.read_text(encoding="utf-8")
        except OSError as exc:
            read_error = f"cannot read file: {exc}"

        if read_error is not None:
            validation = ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID.value,
                errors=(read_error,),
                warnings=(),
                identity=None,
            )
            discovery_errors.append(DiscoveryError(str(candidate), read_error))
            return (
                DiscoveredApplication(
                    path=str(candidate),
                    relative_path=relative_path,
                    identity=None,
                    manifest=None,
                    validation=validation,
                ),
                [],
                discovery_errors,
            )

        try:
            parsed = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            message = str(exc)
            validation = ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID.value,
                errors=(message,),
                warnings=(),
                identity=None,
            )
            application = DiscoveredApplication(
                path=str(candidate),
                relative_path=relative_path,
                identity=None,
                manifest=None,
                validation=validation,
            )
            return application, [], discovery_errors

        if not isinstance(parsed, Mapping) or not parsed:
            message = "manifest root must be an object"
            validation = ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID.value,
                errors=(message,),
                warnings=(),
                identity=None,
            )
            return (
                DiscoveredApplication(
                    path=str(candidate),
                    relative_path=relative_path,
                    identity=None,
                    manifest=None,
                    validation=validation,
                ),
                [],
                discovery_errors,
            )

        validator = ContractValidator(
            supported_contract_versions=config.contract_versions
            if config.contract_versions is not None
            else None
        )
        validation = validator.validate_manifest_data(parsed)

        manifest: ApplicationManifest | None = None
        identity: ApplicationIdentity | None = None
        applications_capabilities: list[DiscoveredCapability] = []

        try:
            manifest = ApplicationManifest.from_mapping(parsed)
            identity = manifest.identity
        except ValidationError as exc:
            # Validation result already contains an explanation. The exception is
            # kept out of the returned record to avoid duplicated/confusing errors.
            if validation.errors and str(exc) not in validation.errors:
                discovery_errors.append(DiscoveryError(str(candidate), str(exc)))

        if manifest is not None and identity is not None and validation.is_valid:
            # Capabilities are discovered only for valid manifests. Their
            # lifecycle state remains DECLARED; validity is not a promotion.
            for capability in manifest.capabilities:
                applications_capabilities.append(
                    DiscoveredCapability(
                        app_id=identity.app_id,
                        instance_id=identity.instance_id,
                        name=capability.name,
                        description=capability.description,
                        declared_by=capability.declared_by,
                        state=CapabilityState.DECLARED,
                        contract_version=identity.contract_version,
                        manifest_version=identity.manifest_version,
                    )
                )

        application = DiscoveredApplication(
            path=str(candidate),
            relative_path=relative_path,
            identity=identity,
            manifest=manifest if validation.is_valid else manifest,
            validation=validation,
        )
        return application, applications_capabilities, discovery_errors

    def _iter_regular_files(self, root: Path, follow_symlinks: bool, recursive: bool = True) -> Iterable[Path]:
        pending = [root]
        while pending:
            current = pending.pop()
            if current != root:
                # Only emit regular files under non-root directories when they are
                # directly visited through an explicitly recursive scan. A non-
                # recursive catalogue source must inspect only root-level entries.
                if not recursive:
                    continue
            try:
                entries = list(current.iterdir())
            except OSError:
                continue
            for entry in entries:
                if entry.is_symlink():
                    if follow_symlinks and entry.is_file():
                        yield entry
                    continue
                if entry.is_dir():
                    if recursive or current == root:
                        pending.append(entry)
                elif entry.is_file():
                    yield entry
                else:
                    continue


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _relative_path(candidate: Path, root: Path) -> str:
    try:
        return str(candidate.relative_to(root))
    except ValueError:
        return str(candidate)


def _detect_conflicts(applications: Sequence[DiscoveredApplication]) -> list[DiscoveryConflict]:
    conflicts: list[DiscoveryConflict] = []
    by_app_id: dict[str, list[DiscoveredApplication]] = {}
    by_instance_id: dict[str, list[DiscoveredApplication]] = {}
    for application in applications:
        if application.identity is None:
            continue
        by_app_id.setdefault(application.identity.app_id, []).append(application)
        by_instance_id.setdefault(application.identity.instance_id, []).append(application)

    for key, items in by_app_id.items():
        if len(items) > 1:
            conflicts.append(
                DiscoveryConflict(
                    conflict_type="duplicate_app_id",
                    key=key,
                    values=tuple(sorted(application.relative_path for application in items)),
                    message=f"duplicate app_id: {key}",
                )
            )
    for key, items in by_instance_id.items():
        if len(items) > 1:
            conflicts.append(
                DiscoveryConflict(
                    conflict_type="duplicate_instance_id",
                    key=key,
                    values=tuple(sorted(application.relative_path for application in items)),
                    message=f"duplicate instance_id: {key}",
                )
            )
    return conflicts


def _conflicts_for_application(
    conflicts: Sequence[DiscoveryConflict], application: DiscoveredApplication
) -> tuple[DiscoveryConflict, ...]:
    if application.identity is None:
        return ()
    result: list[DiscoveryConflict] = []
    for conflict in conflicts:
        if application.relative_path in conflict.values:
            result.append(conflict)
    return tuple(result)


def _replace_application_conflicts(
    application: DiscoveredApplication, conflicts: tuple[DiscoveryConflict, ...]
) -> DiscoveredApplication:
    if not conflicts:
        return application
    return DiscoveredApplication(
        path=application.path,
        relative_path=application.relative_path,
        identity=application.identity,
        manifest=application.manifest,
        validation=application.validation,
        declared_capabilities=application.declared_capabilities,
        conflicts=conflicts,
    )


# Aliases for compatibility with different naming expectations.
ApplicationDiscoveryService = ApplicationDiscoveryService
CapabilityDiscoveryService = ApplicationDiscoveryService
ManifestDiscoveryService = ApplicationDiscoveryService
ApplicationDiscovery = ApplicationDiscoveryService
CapabilityDiscovery = ApplicationDiscoveryService
ManifestDiscovery = ApplicationDiscoveryService
ApplicationRegistryDiscovery = ApplicationDiscoveryService
DiscoveryService = ApplicationDiscoveryService


__all__ = [
    "ApplicationDiscoveryService",
    "CapabilityDiscoveryService",
    "ManifestDiscoveryService",
    "ApplicationDiscovery",
    "CapabilityDiscovery",
    "ManifestDiscovery",
    "DiscoveryService",
    "DiscoveryConfig",
    "DiscoveryReport",
    "DiscoveredApplication",
    "DiscoveredCapability",
    "DiscoveryConflict",
    "DiscoveryError",
    "CapabilityState",
]
