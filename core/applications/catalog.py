"""Application catalog for ETHAN (MEM-014 Phase 41)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable, Mapping

from core.applications.discovery import ApplicationDiscoveryService, DiscoveryConfig, DiscoveredApplication
from core.applications.models import ApplicationManifest


class CatalogSource(StrEnum):
    BUILTIN = "builtin"
    LOCAL_EXAMPLE = "local_example"
    GITHUB = "github"


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    app_id: str
    instance_id: str
    source: CatalogSource
    manifest: ApplicationManifest
    manifest_digest: str
    location: str
    validated: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "app_id": self.app_id,
            "instance_id": self.instance_id,
            "source": self.source.value,
            "validated": self.validated,
            "manifest_digest": self.manifest_digest,
            "location": self.location,
            "manifest": self.manifest.to_dict(),
        }


@dataclass(slots=True)
class ApplicationCatalog:
    roots: dict[CatalogSource, Path]
    github_source_configured: bool = False
    recursive: bool = True
    _loaded: list[CatalogEntry] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        self._loaded.clear()
        for source, root in self.roots.items():
            if not root.exists():
                continue
            discovery = ApplicationDiscoveryService(DiscoveryConfig(root_path=root, recursive=self.recursive))
            report = discovery.discover()
            for application in report.applications:
                if application.identity is None or application.manifest is None:
                    continue
                if not application.is_valid:
                    continue
                self._loaded.append(
                    CatalogEntry(
                        app_id=application.identity.app_id,
                        instance_id=application.identity.instance_id,
                        source=source,
                        manifest=application.manifest,
                        manifest_digest=application.manifest_digest if hasattr(application, "manifest_digest") else None if application.manifest is None else None,
                        location=application.relative_path,
                        validated=True,
                    )
                )
        # fix digest via model fingerprint helper if not set
        from core.applications.permissions import manifest_fingerprint
        normalized: list[CatalogEntry] = []
        for entry in self._loaded:
            normalized.append(
                CatalogEntry(
                    app_id=entry.app_id,
                    instance_id=entry.instance_id,
                    source=entry.source,
                    manifest=entry.manifest,
                    manifest_digest=manifest_fingerprint(entry.manifest),
                    location=entry.location,
                    validated=entry.validated,
                )
            )
        self._loaded = normalized

    def entries(self) -> tuple[CatalogEntry, ...]:
        return tuple(sorted(self._loaded, key=lambda item: (item.source.value, item.app_id, item.instance_id)))

    def find(self, app_id: str) -> CatalogEntry | None:
        for entry in self._loaded:
            if entry.app_id == app_id:
                return entry
        return None

    def by_source(self, source: CatalogSource) -> tuple[CatalogEntry, ...]:
        return tuple(entry for entry in self.entries() if entry.source == source)


ApplicationCatalogService = ApplicationCatalog


__all__ = ["ApplicationCatalog", "ApplicationCatalogService", "CatalogEntry", "CatalogSource"]
