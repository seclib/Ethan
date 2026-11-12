"""Read-only discovery and integration preview for ETHAN external applications (Campaign 01-A)."""

from __future__ import annotations

import yaml
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from core.applications.local_repository_discovery import LocalRepositoryDiscovery, analyze_repository


@dataclass(frozen=True, slots=True)
class IntegrationPreview:
    repository_identity: dict[str, Any]
    application_identity: dict[str, Any] | None
    application_category: str | None
    integration_type: str
    manifest_availability: str
    declared_capabilities: tuple[str, ...]
    configuration_requirements: tuple[str, ...]
    required_permissions: tuple[str, ...]
    lifecycle_adapter: str
    missing_requirements: tuple[str, ...]
    validation_warnings: tuple[str, ...]
    validation_errors: tuple[str, ...]
    security_implications: tuple[str, ...]
    read_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class IntegrationPreviewService:
    """Build deterministic, read-only integration previews without registration or authorization."""

    def discover(
        self,
        root: Any = None,
        *,
        source: Any = None,
        max_depth: int = 4,
    ) -> tuple[IntegrationPreview, ...]:
        selected_root = source if source is not None else root
        if selected_root is None:
            raise ValueError("a discovery root is required")
        selected_root = Path(selected_root)
        if not selected_root.is_dir():
            return ()
        try:
            analyses = LocalRepositoryDiscovery(root=selected_root, max_depth=max_depth).discover()
        except ValueError:
            return ()
        previews: list[IntegrationPreview] = []
        for analysis in analyses:
            repository_path = selected_root / analysis.path
            previews.append(self.build_preview(repository_path, selected_root, analysis))
        return tuple(sorted(previews, key=lambda item: item.repository_identity.get("path", "")))

    def build_preview(
        self,
        repository_path: Path,
        root: Any = None,
        analysis: Any = None,
    ) -> IntegrationPreview:
        repository_path = Path(repository_path)
        if root is None:
            root = repository_path.parent
        root = Path(root)
        if analysis is None:
            try:
                analysis = analyze_repository(repository_path, root)
            except (OSError, ValueError):
                analysis = None

        if analysis is None:
            missing = ("repository-analysis",)
            warnings = ("repository could not be analyzed",)
            errors = ("repository analysis failed",)
            repository_identity = {
                "path": str(repository_path),
                "name": repository_path.name,
            }
            return IntegrationPreview(
                repository_identity=repository_identity,
                application_identity=None,
                application_category=None,
                integration_type="unmanaged",
                manifest_availability="invalid",
                declared_capabilities=(),
                configuration_requirements=(),
                required_permissions=(),
                lifecycle_adapter="none",
                missing_requirements=missing,
                validation_warnings=warnings,
                validation_errors=errors,
                security_implications=("read-only metadata inspection performed", "no repository code executed"),
                read_only=True,
            )

        manifest_payload, manifest_parse_error = self._read_manifest_with_error(repository_path)
        if analysis.manifest_status != "valid":
            identity = None
        else:
            identity = manifest_payload.get("identity") if isinstance(manifest_payload.get("identity"), Mapping) else None
            if not isinstance(identity, dict):
                identity = None
        category = None
        if isinstance(manifest_payload, Mapping):
            category = (
                manifest_payload.get("application_type")
                or manifest_payload.get("category")
                or manifest_payload.get("type")
                or (manifest_payload.get("metadata", {}) or {}).get("application_category")
            )
        capabilities = self._as_strings(manifest_payload.get("capabilities")) if isinstance(manifest_payload, Mapping) else []
        configuration = self._as_strings(
            manifest_payload.get("configuration")
            if isinstance(manifest_payload, Mapping) and manifest_payload.get("configuration") is not None
            else (manifest_payload.get("config") if isinstance(manifest_payload, Mapping) else None)
        )
        permissions = self._as_strings(manifest_payload.get("permissions")) if isinstance(manifest_payload, Mapping) else []

        missing: list[str] = []
        if not analysis.has_readme:
            missing.append("readme")
        if analysis.manifest_status == "absent":
            missing.append("ethan-application-manifest")
        elif analysis.manifest_status == "invalid":
            missing.append("valid-manifest")

        warnings: list[str] = []
        if analysis.working_tree_status == "dirty":
            warnings.append("repository working tree is dirty")
        if analysis.manifest_status == "invalid":
            warnings.append("manifest validation failed")

        errors: list[str] = []
        if manifest_parse_error is not None:
            errors.append(manifest_parse_error)
        elif analysis.manifest_status == "invalid":
            sanitized = {}
            if isinstance(manifest_payload, Mapping):
                sanitized = {
                    key: value for key, value in manifest_payload.items()
                    if key not in {"application_type", "category", "type", "configuration", "config"}
                }
            from core.applications.validator import ContractValidator

            result = ContractValidator().validate_manifest_data(sanitized) if sanitized else None
            if result is not None and result.errors:
                errors.extend(str(item) for item in result.errors)
            if not errors:
                errors.append("manifest validation failed")
        elif analysis.manifest_status not in {"valid", "absent"}:
            errors.append(f"manifest status is {analysis.manifest_status}")

        security = ("read-only metadata inspection performed", "no repository code executed")
        if getattr(analysis, "has_ethan_manifest", False) and analysis.manifest_status == "valid":
            integration_type = "application"
        elif getattr(analysis, "has_ethan_manifest", False):
            integration_type = "application (manifest invalid)"
        else:
            integration_type = "unmanaged"
        lifecycle_adapter = "none" if not getattr(analysis, "has_ethan_manifest", False) else "application-discovery"

        return IntegrationPreview(
            repository_identity={
                "path": analysis.path,
                "name": analysis.name,
                "branch": analysis.branch,
                "head": analysis.head,
                "remote": analysis.remote,
                "remote_normalized": analysis.remote_normalized,
                "working_tree_status": analysis.working_tree_status,
                "changed_files": analysis.changed_files,
                "detected_files": list(analysis.detected_files),
                "estimated_project_types": list(analysis.estimated_project_types),
            },
            application_identity=identity if isinstance(identity, dict) else None,
            application_category=str(category) if category is not None else None,
            integration_type=integration_type,
            manifest_availability=analysis.manifest_status,
            declared_capabilities=tuple(capabilities),
            configuration_requirements=tuple(configuration),
            required_permissions=tuple(permissions),
            lifecycle_adapter=lifecycle_adapter,
            missing_requirements=tuple(missing),
            validation_warnings=tuple(warnings),
            validation_errors=tuple(errors),
            security_implications=tuple(security),
            read_only=True,
        )

    @staticmethod
    def _read_manifest_with_error(repository_path: Path) -> tuple[Mapping[str, Any], str | None]:
        path = repository_path / "ethan-application-manifest.yaml"
        if not path.is_file():
            return {}, None
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, ImportError, yaml.YAMLError) as exc:
            return {}, str(exc)
        if not isinstance(loaded, Mapping):
            return {}, "manifest root must be an object"
        return loaded, None

    @staticmethod
    def _read_manifest(repository_path: Path) -> Mapping[str, Any]:
        payload, _ = IntegrationPreviewService._read_manifest_with_error(repository_path)
        return payload

    @staticmethod
    def _as_strings(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, Mapping):
            if "name" in value:
                return [str(value["name"])]
            return [str(key) for key in value.keys()]
        if isinstance(value, (list, tuple, set)):
            result: list[str] = []
            for item in value:
                if isinstance(item, Mapping):
                    if "name" in item:
                        result.append(str(item["name"]))
                    else:
                        result.append(str(item))
                elif item is not None:
                    result.append(str(item))
            return result
        return [str(value)]


def build_integration_preview(root: Any, *, max_depth: int = 4, source: Any = None) -> tuple[IntegrationPreview, ...]:
    """Convenience entry point used by tests and future API adapters."""
    return IntegrationPreviewService().discover(root if source is None else source, max_depth=max_depth)
