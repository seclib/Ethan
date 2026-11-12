"""Durable, generic application manifest storage (Campaign DTAI-03E)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping
from uuid import uuid4

from core.applications.models import ApplicationManifest, ValidationError
from core.applications.permissions import manifest_fingerprint
from core.applications.persistence import (
    ApplicationStateStore,
    open_application_state_store,
)
from core.applications.validator import ContractValidator

DEFAULT_VALIDATOR_VERSION = "ethan-contract-validator"


@dataclass(slots=True)
class ApplicationManifestRecord:
    """A durable manifest declaration, distinct from an registered application."""

    manifest_id: str
    app_id: str
    instance_id: str
    record_version: int
    manifest: ApplicationManifest
    manifest_digest: str
    source_type: str = "local_repository"
    repository_url: str | None = None
    repository_path: str | None = None
    git_revision: str | None = None
    analysis_timestamp: str | None = None
    validation_status: str = "valid"
    validation_errors: tuple[str, ...] = field(default_factory=tuple)
    validator_version: str = DEFAULT_VALIDATOR_VERSION
    validated_at: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_id": self.manifest_id,
            "app_id": self.app_id,
            "instance_id": self.instance_id,
            "record_version": self.record_version,
            "manifest": self.manifest.to_dict(),
            "manifest_digest": self.manifest_digest,
            "source_type": self.source_type,
            "repository_url": self.repository_url,
            "repository_path": self.repository_path,
            "git_revision": self.git_revision,
            "analysis_timestamp": self.analysis_timestamp,
            "validation_status": self.validation_status,
            "validation_errors": list(self.validation_errors),
            "validator_version": self.validator_version,
            "validated_at": self.validated_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ApplicationManifestRecord":
        manifest = ApplicationManifest.from_mapping(data["manifest"])
        return cls(
            manifest_id=str(data["manifest_id"]),
            app_id=str(data["app_id"]),
            instance_id=str(data["instance_id"]),
            record_version=int(data.get("record_version", 1)),
            manifest=manifest,
            manifest_digest=str(data["manifest_digest"]),
            source_type=str(data.get("source_type", "local_repository")),
            repository_url=data.get("repository_url"),
            repository_path=data.get("repository_path"),
            git_revision=data.get("git_revision"),
            analysis_timestamp=data.get("analysis_timestamp"),
            validation_status=str(data.get("validation_status", "valid")),
            validation_errors=tuple(str(item) for item in data.get("validation_errors", [])),
            validator_version=str(data.get("validator_version", DEFAULT_VALIDATOR_VERSION)),
            validated_at=str(data.get("validated_at", data.get("created_at", ""))),
            created_at=str(data.get("created_at", "")),
            updated_at=str(data.get("updated_at", "")),
        )


class ApplicationManifestConflictError(ValueError):
    """Raised when a durable manifest conflicts with existing identity or version."""


class ApplicationManifestRepository:
    """Durable generic manifest repository.

    Reuses the canonical ApplicationStateStore. This component does not
    register applications and does not grant execution authorization.
    """

    def __init__(self, store: Any = None, *, persistence_path: str | None = None) -> None:
        if store is not None:
            self._store = store
        elif persistence_path:
            self._store = open_application_state_store(persistence_path)
        else:
            default_path = Path.home() / ".ethan" / "application-manifests.sqlite"
            default_path.parent.mkdir(parents=True, exist_ok=True)
            self._store = open_application_state_store(default_path)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _manifest_digest(manifest: ApplicationManifest) -> str:
        return manifest_fingerprint(manifest)

    def _raw_records(self, app_id: str | None = None, instance_id: str | None = None, version: int | None = None) -> list[ApplicationManifestRecord]:
        rows = self._store.load_records("application_manifests")
        records: list[ApplicationManifestRecord] = []
        for payload in rows:
            record = ApplicationManifestRecord.from_dict(payload)
            if app_id is not None and record.app_id != app_id:
                continue
            if instance_id is not None and record.instance_id != instance_id:
                continue
            if version is not None and record.record_version != version:
                continue
            records.append(record)
        records.sort(key=lambda item: (item.app_id, item.instance_id, item.record_version))
        return records

    def list(self, app_id: str | None = None, instance_id: str | None = None) -> tuple[ApplicationManifestRecord, ...]:
        return tuple(self._raw_records(app_id=app_id, instance_id=instance_id))

    def versions(self, app_id: str, instance_id: str | None = None) -> tuple[ApplicationManifestRecord, ...]:
        return self.list(app_id=app_id, instance_id=instance_id)

    def get_current(self, app_id: str, instance_id: str | None = None) -> ApplicationManifestRecord | None:
        candidates = self._raw_records(app_id=app_id, instance_id=instance_id)
        if not candidates:
            return None
        if instance_id is not None:
            candidates = [record for record in candidates if record.instance_id == instance_id]
        if not candidates:
            return None
        return max(candidates, key=lambda item: item.record_version)

    def get(self, app_id: str, instance_id: str | None = None, version: int | None = None) -> ApplicationManifestRecord | None:
        if version is None:
            return self.get_current(app_id, instance_id)
        candidates = self._raw_records(app_id=app_id, instance_id=instance_id, version=version)
        if not candidates:
            return None
        return candidates[0]

    def by_id(self, manifest_id: str) -> ApplicationManifestRecord | None:
        for payload in self._store.load_records("application_manifests"):
            if payload.get("manifest_id") == manifest_id:
                return ApplicationManifestRecord.from_dict(payload)
        return None

    def create(
        self,
        manifest: Any,
        *,
        source_type: str = "local_repository",
        repository_url: str | None = None,
        repository_path: str | None = None,
        git_revision: str | None = None,
        analysis_timestamp: str | None = None,
        validation_status: str = "valid",
        validation_errors: Iterable[str] = (),
        validator_version: str = DEFAULT_VALIDATOR_VERSION,
        validated_at: str | None = None,
    ) -> ApplicationManifestRecord:
        manifest_obj = manifest if isinstance(manifest, ApplicationManifest) else ApplicationManifest.from_mapping(manifest)
        if validation_status.lower() == "valid":
            ContractValidator().validate_manifest_data(manifest_obj.to_dict())

        now = self._now()
        existing = self.list(app_id=manifest_obj.identity.app_id, instance_id=manifest_obj.identity.instance_id)
        if existing:
            raise ApplicationManifestConflictError(
                "application manifest already exists for "
                + f"{manifest_obj.identity.app_id}:{manifest_obj.identity.instance_id}"
            )

        record = ApplicationManifestRecord(
            manifest_id=str(uuid4()),
            app_id=manifest_obj.identity.app_id,
            instance_id=manifest_obj.identity.instance_id,
            record_version=1,
            manifest=manifest_obj,
            manifest_digest=self._manifest_digest(manifest_obj),
            source_type=source_type,
            repository_url=repository_url,
            repository_path=repository_path,
            git_revision=git_revision,
            analysis_timestamp=analysis_timestamp,
            validation_status=validation_status,
            validation_errors=tuple(str(item) for item in validation_errors),
            validator_version=validator_version,
            validated_at=validated_at or now,
            created_at=now,
            updated_at=now,
        )
        self._store.save_record("application_manifests", record.manifest_id, record.to_dict())
        return record

    # Compatibility aliases.
    add = create
    insert = create
    put = create
    save = create
    save_manifest = create

    def update(
        self,
        manifest: Any,
        *,
        app_id: str | None = None,
        instance_id: str | None = None,
        source_type: str | None = None,
        repository_url: str | None = None,
        repository_path: str | None = None,
        git_revision: str | None = None,
        analysis_timestamp: str | None = None,
        validation_status: str = "valid",
        validation_errors: Iterable[str] = (),
        validator_version: str = DEFAULT_VALIDATOR_VERSION,
        validated_at: str | None = None,
    ) -> ApplicationManifestRecord:
        manifest_obj = manifest if isinstance(manifest, ApplicationManifest) else ApplicationManifest.from_mapping(manifest)
        target_app = app_id or manifest_obj.identity.app_id
        target_instance = instance_id or manifest_obj.identity.instance_id
        current = self.get_current(target_app, target_instance)
        if current is not None and (manifest_obj.identity.app_id, manifest_obj.identity.instance_id) != (target_app, target_instance):
            raise ApplicationManifestConflictError("manifest identity cannot change scope during update")

        if validation_status.lower() == "valid":
            ContractValidator().validate_manifest_data(manifest_obj.to_dict())

        now = self._now()
        new_version = 1 if current is None else current.record_version + 1
        record = ApplicationManifestRecord(
            manifest_id=str(uuid4()),
            app_id=manifest_obj.identity.app_id,
            instance_id=manifest_obj.identity.instance_id,
            record_version=new_version,
            manifest=manifest_obj,
            manifest_digest=self._manifest_digest(manifest_obj),
            source_type=source_type or (current.source_type if current else "local_repository"),
            repository_url=repository_url if repository_url is not None else (current.repository_url if current else None),
            repository_path=repository_path if repository_path is not None else (current.repository_path if current else None),
            git_revision=git_revision if git_revision is not None else (current.git_revision if current else None),
            analysis_timestamp=analysis_timestamp if analysis_timestamp is not None else (current.analysis_timestamp if current else None),
            validation_status=validation_status,
            validation_errors=tuple(str(item) for item in validation_errors),
            validator_version=validator_version,
            validated_at=validated_at or now,
            created_at=current.created_at if current is not None else now,
            updated_at=now,
        )
        self._store.save_record("application_manifests", record.manifest_id, record.to_dict())
        return record

    update_manifest = update

    def delete(self, app_id: str, instance_id: str | None = None, version: int | None = None) -> bool:
        # The canonical persistence layer does not expose a targeted delete for
        # manifests; documents remain durable and must be withdrawn by policy,
        # not silently removed by a repository helper.
        raise NotImplementedError("manifest deletion is not supported by the durable store")

    def close(self) -> None:
        if hasattr(self._store, "close"):
            self._store.close()


# Compatibility aliases expected by tests and Discovery Magic.
ApplicationManifestRepo = ApplicationManifestRepository
ManifestRepository = ApplicationManifestRepository
ManifestStore = ApplicationManifestRepository
ApplicationManifestStore = ApplicationManifestRepository
ApplicationManifestRepo = ApplicationManifestRepository


__all__ = [
    "ApplicationManifestConflictError",
    "ApplicationManifestRecord",
    "ApplicationManifestRepository",
    "ApplicationManifestRepo",
    "ApplicationManifestStore",
    "ManifestRepository",
    "ManifestStore",
]
