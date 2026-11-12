"""Read-only generic application integration catalog for ETHAN (DTAI-02C)."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from typing import Any, Sequence
from pathlib import Path
from typing import Any, Mapping

from core.applications.application_registry import ApplicationIntegrationRegistry
from core.applications.local_repository_discovery import LocalRepositoryDiscovery, analyze_repository


@dataclass(slots=True)
class IntegrationCatalogState:
    discovered: bool
    validated: bool | None
    registered: bool | None
    installed: str
    available: str
    running: str
    authorized: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class IntegrationCatalogSource:
    source_id: str
    name: str
    source_type: str
    root_path: str
    configured_root: str
    enabled: bool = True
    discovery_status: str = "pending"
    repository_count: int = 0
    errors: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(slots=True)
class IntegrationCatalogItem:
    repository_path: str
    repository_name: str
    source_id: str
    source_name: str
    analysis: dict[str, Any]
    manifest_availability: str
    manifest_validation_status: str
    application_type: str
    declared_capabilities: tuple[str, ...]
    declared_dependencies: tuple[str, ...]
    declared_permissions: tuple[str, ...]
    required_permissions: tuple[str, ...]
    integration_preview: dict[str, Any] | None
    registration_status: str
    registered_identity: dict[str, Any] | None
    manifest_fingerprint: str | None
    sources: dict[str, str]
    states: IntegrationCatalogState
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["states"] = self.states.to_dict()
        return result


class IntegrationCatalogService:
    """Generic projection from discovery and registry, without side effects."""

    def __init__(
        self,
        registry: ApplicationIntegrationRegistry | None = None,
        manifest_repository: Any = None,
        manifest_store: Any = None,
        manifest_repo: Any = None,
    ) -> None:
        self._registry = registry or ApplicationIntegrationRegistry()
        self._manifest_repository = manifest_repository or manifest_store or manifest_repo

    @staticmethod
    def configured_roots(explicit_roots: Sequence[str | Path] | None = None) -> tuple[Path, ...]:
        roots: list[Path] = []
        seen: set[str] = set()

        def add(candidate: str | Path) -> None:
            expanded = Path(candidate).expanduser().resolve()
            key = str(expanded)
            if key not in seen:
                seen.add(key)
                roots.append(expanded)

        if explicit_roots:
            for candidate in explicit_roots:
                add(candidate)

        env_roots = os.environ.get("ETHAN_LOCAL_REPOSITORY_ROOTS")
        if env_roots:
            for candidate in env_roots.split(","):
                candidate = candidate.strip()
                if candidate:
                    add(candidate)

        env_root = os.environ.get("ETHAN_LOCAL_REPOSITORY_ROOT")
        if env_root:
            add(env_root)

        return tuple(roots)

    def build(self, root: Path | Sequence[str | Path] | None = None, roots: Sequence[str | Path] | None = None, max_depth: int = 4) -> dict[str, Any]:
        configured = self.configured_roots(explicit_roots=roots if roots is not None else ([root] if root is not None and not isinstance(root, (list, tuple)) else root))
        sources: list[IntegrationCatalogSource] = []
        discovered_by_canonical: dict[str, tuple[IntegrationCatalogSource, Any]] = {}
        repository_items: list[IntegrationCatalogItem] = []
        global_errors: list[str] = []

        if not configured:
            return {
                "root": "",
                "roots": [],
                "items": [],
                "sources": [],
                "source_errors": ["no discovery root configured"],
                "total_repositories": 0,
            }

        for index, source_root in enumerate(configured, start=1):
            source_type = "workspace" if index == 1 and "ETHAN_LOCAL_REPOSITORY_ROOTS" not in os.environ else "local_directory"
            source = IntegrationCatalogSource(
                source_id=f"local-root-{index}",
                name=f"Local Repository Root {index}",
                source_type=source_type,
                root_path=str(source_root),
                configured_root=str(source_root),
                enabled=True,
            )
            source_errors: list[str] = []
            source_warnings: list[str] = []
            analyses: list[Any] = []
            status = "success"

            if source_root == Path.home().resolve() or source_root == Path("/").resolve():
                source_errors.append(f"discovery root too broad: {source_root}")
                status = "failed"
            elif not source_root.exists() or not source_root.is_dir():
                source_errors.append(f"discovery root does not exist: {source_root}")
                status = "failed"
            else:
                try:
                    discovery = LocalRepositoryDiscovery(root=source_root, max_depth=max_depth)
                    analyses = discovery.discover()
                except Exception as exc:
                    source_errors.append(str(exc))
                    status = "failed"

                if status == "success" and source_errors:
                    status = "partial"
                for analysis in analyses:
                    if getattr(analysis, "errors", None):
                        source_errors.extend(str(item) for item in analysis.errors)
                        status = "partial"

            source = IntegrationCatalogSource(
                source_id=source.source_id,
                name=source.name,
                source_type=source.source_type,
                root_path=source.root_path,
                configured_root=source.configured_root,
                enabled=source.enabled,
                discovery_status=status,
                repository_count=len(analyses),
                errors=tuple(source_errors),
                warnings=tuple(source_warnings),
            )
            sources.append(source)

            for analysis in analyses:
                try:
                    canonical_path = str((source_root / getattr(analysis, "path", "")).resolve())
                except Exception:
                    canonical_path = str(source_root / getattr(analysis, "path", ""))
                if canonical_path in discovered_by_canonical:
                    continue
                discovered_by_canonical[canonical_path] = (source, analysis)

        errors_global = [error for source in sources for error in source.errors]

        for canonical_path, (source, analysis) in discovered_by_canonical.items():
            repository_path = str(getattr(analysis, "path", canonical_path))
            persisted_record = self._persisted_manifest_for(analysis)
            if persisted_record is not None:
                validated = persisted_record.validation_status == "valid"
                item_errors: list[str] = []
            else:
                validated = analysis.manifest_status == "valid"
                item_errors = []
                if analysis.manifest_status == "absent":
                    item_errors.append("ethan-application-manifest absent")
                elif analysis.manifest_status == "invalid":
                    item_errors.append("ethan-application-manifest invalid")

            if persisted_record is not None and persisted_record.manifest is not None:
                manifest_identity = persisted_record.manifest.identity
            else:
                manifest_identity = getattr(analysis, "identity", None)

            registered_record = self._find_registered(analysis)
            if registered_record is None and manifest_identity is not None:
                try:
                    registered_record = self._registry.get(manifest_identity.app_id, manifest_identity.instance_id)
                except Exception:
                    registered_record = None

            states = IntegrationCatalogState(
                discovered=True,
                validated=(True if validated else (False if getattr(analysis, "has_ethan_manifest", False) or persisted_record is not None else None)),
                registered=(registered_record is not None) if (validated and manifest_identity is not None) else False,
                installed="unknown",
                available="unknown",
                running="unknown",
                authorized="unknown",
            )
            persisted_metadata = {}
            if persisted_record is not None:
                persisted_metadata = persisted_record.manifest.metadata or {}
            application_type = persisted_metadata.get("application_category") or ("repository-application" if validated else "unknown")

            declared_capabilities = ()
            declared_dependencies = ()
            declared_permissions = ()
            if persisted_record is not None:
                declared_capabilities = tuple(cap.name for cap in persisted_record.manifest.capabilities)
                declared_dependencies = tuple(dep.name for dep in persisted_record.manifest.dependencies)
                declared_permissions = tuple(str(item) for item in persisted_record.manifest.permissions)

            preview = {
                "repository_identity": {
                    "path": analysis.path,
                    "name": analysis.name,
                    "branch": analysis.branch,
                    "head": analysis.head,
                    "remote": analysis.remote,
                },
                "estimated_project_types": list(analysis.estimated_project_types),
                "detected_files": list(analysis.detected_files),
                "working_tree_status": analysis.working_tree_status,
                "persisted_manifest": persisted_record.to_dict() if persisted_record is not None else None,
            }
            item = IntegrationCatalogItem(
                repository_path=repository_path,
                repository_name=analysis.name,
                source_id=source.source_id,
                source_name=source.name,
                analysis=analysis.to_dict(),
                manifest_availability="valid" if persisted_record is not None else analysis.manifest_status,
                manifest_validation_status=persisted_record.validation_status if persisted_record is not None else analysis.manifest_status,
                application_type=application_type,
                declared_capabilities=declared_capabilities,
                declared_dependencies=declared_dependencies,
                declared_permissions=declared_permissions,
                required_permissions=tuple(),
                integration_preview=preview,
                registration_status=("registered" if registered_record is not None else "not-registered"),
                registered_identity=(registered_record.to_dict() if registered_record is not None else None),
                manifest_fingerprint=( persisted_record.manifest_digest if persisted_record is not None else (registered_record.manifest_digest if registered_record is not None else None)),
                sources={"repository": "local_repository_discovery", "validated": "ContractValidator", "registered": "ApplicationIntegrationRegistry", "manifest": "ApplicationManifestRepository" if persisted_record is not None else "none"},
                states=states,
                errors=tuple(item_errors),
            )
            repository_items.append(item)

        repository_items.sort(key=lambda item: (item.repository_name, item.repository_path))
        return {
            "root": str(configured[0]) if configured else "",
            "roots": [str(root) for root in configured],
            "sources": [source.to_dict() for source in sources],
            "items": [item.to_dict() for item in repository_items],
            "source_errors": global_errors,
            "total_repositories": len(repository_items),
        }

    def _persisted_manifest_for(self, analysis: Any) -> Any | None:
        repository = self._manifest_repository
        if repository is None:
            return None
        repository_path = str(getattr(analysis, "path", "") or "")
        if not repository_path:
            return None
        try:
            for record in repository.list():
                if str(getattr(record, "repository_path", "") or "") == repository_path:
                    return record
        except Exception:
            return None
        return None

    def _find_registered(self, analysis: Any) -> Any | None:
        manifest = getattr(analysis, "identity", None)
        if manifest is None:
            return None
        try:
            return self._registry.get(manifest.app_id, manifest.instance_id)
        except Exception:
            return None

    def _find_registered(self, analysis: Any) -> Any | None:
        # Use manifest identity when discovered; otherwise only exact path is not reliable.
        manifest = getattr(analysis, "identity", None)
        if manifest is None:
            return None
        try:
            return self._registry.get(manifest.app_id, manifest.instance_id)
        except Exception:
            return None


def _local_discovery_root() -> Path:
    configured = os.environ.get("ETHAN_LOCAL_REPOSITORY_ROOT")
    return Path(configured).expanduser().resolve() if configured else Path("/home/fatsio/AI").resolve()
