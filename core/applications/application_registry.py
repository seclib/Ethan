"""Application integration readiness registry (MEM-014 Phase 13)."""

from __future__ import annotations

import fcntl
import tempfile
from pathlib import Path

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Callable, Mapping, Sequence
from uuid import uuid4

from core.applications.contracts import ExtensionContract, ExtensionContractValidator
from core.applications.models import ApplicationManifest, ValidationError
from core.applications.permissions import manifest_fingerprint
from core.applications.permissions import PermissionService
from core.applications.compliance import ComplianceEngine
from core.applications.observability import EventCollector, IntegrationEvent, OBSERVABILITY_SCHEMA_VERSION
from core.applications.resilience import ApplicationLifecycleManager, LifecycleState
from core.applications.persistence import ApplicationStateStore


class ApplicationRegistrationState(StrEnum):
    REGISTERED = "registered"
    VALIDATED = "validated"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    WITHDRAWN = "withdrawn"


@dataclass(slots=True)
class ApplicationRecord:
    registration_id: str
    app_id: str
    instance_id: str
    manifest: ApplicationManifest
    manifest_digest: str
    contract: ExtensionContract | None = None
    contract_digest: str | None = None
    state: ApplicationRegistrationState = ApplicationRegistrationState.REGISTERED
    compliance_status: str = "NOT_EVALUATED"
    capabilities: tuple[str, ...] = field(default_factory=tuple)
    requested_permissions: tuple[str, ...] = field(default_factory=tuple)
    lifecycle_state: str = LifecycleState.REGISTERED.value
    available: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    withdrawn_reason: str | None = None
    events: tuple[str, ...] = field(default_factory=tuple)
    approval_reference: str | None = None
    correlation_id: str | None = None
    repository_identity: dict[str, Any] = field(default_factory=dict)
    manifest_validation_status: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "registration_id": self.registration_id,
            "app_id": self.app_id,
            "instance_id": self.instance_id,
            "manifest": self.manifest.to_dict(),
            "manifest_digest": self.manifest_digest,
            "contract": None if self.contract is None else self.contract.to_dict(),
            "contract_digest": self.contract_digest,
            "state": self.state.value,
            "compliance_status": self.compliance_status,
            "capabilities": list(self.capabilities),
            "requested_permissions": list(self.requested_permissions),
            "lifecycle_state": self.lifecycle_state,
            "available": self.available,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "withdrawn_reason": self.withdrawn_reason,
            "events": list(self.events),
            "approval_reference": self.approval_reference,
            "correlation_id": self.correlation_id,
            "repository_identity": dict(self.repository_identity),
            "manifest_validation_status": self.manifest_validation_status,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ApplicationRecord":
        manifest = ApplicationManifest.from_mapping(data["manifest"])
        contract = None if data.get("contract") is None else ExtensionContract.from_mapping(data["contract"])
        return cls(
            registration_id=str(data["registration_id"]),
            app_id=str(data["app_id"]),
            instance_id=str(data["instance_id"]),
            manifest=manifest,
            manifest_digest=str(data["manifest_digest"]),
            contract=contract,
            contract_digest=data.get("contract_digest"),
            state=ApplicationRegistrationState(str(data.get("state", "registered"))),
            compliance_status=str(data.get("compliance_status", "NOT_EVALUATED")),
            capabilities=tuple(str(item) for item in data.get("capabilities", [])),
            requested_permissions=tuple(str(item) for item in data.get("requested_permissions", [])),
            lifecycle_state=str(data.get("lifecycle_state", LifecycleState.REGISTERED.value)),
            available=bool(data.get("available", False)),
            created_at=datetime.fromisoformat(str(data["created_at"]).replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(str(data["updated_at"]).replace("Z", "+00:00")),
            withdrawn_reason=data.get("withdrawn_reason"),
            events=tuple(str(item) for item in data.get("events", [])),
            approval_reference=data.get("approval_reference"),
            correlation_id=data.get("correlation_id"),
            repository_identity=dict(data.get("repository_identity", {}) or {}),
            manifest_validation_status=data.get("manifest_validation_status"),
        )


class ApplicationIntegrationRegistry:
    """Registry and supervision facade for independent applications."""

    def __init__(
        self,
        *,
        store: ApplicationStateStore | None = None,
        permission_service: PermissionService | None = None,
        compliance_engine: ComplianceEngine | None = None,
        event_collector: EventCollector | None = None,
        capability_registry: Any = None,
    ) -> None:
        self.store = store
        self.permission_service = permission_service or PermissionService(production_mode=False)
        self.compliance_engine = compliance_engine or ComplianceEngine()
        self.event_collector = event_collector or EventCollector()
        self.capability_registry = capability_registry
        self.lifecycle_manager = ApplicationLifecycleManager(store=store)
        self._records: dict[tuple[str, str], ApplicationRecord] = {}
        if store is not None:
            try:
                for payload in store.load_records("application_registry_records"):
                    record = ApplicationRecord.from_dict(payload)
                    self._records[(record.app_id, record.instance_id)] = record
                    if record.lifecycle_state:
                        self.lifecycle_manager.set_initial(record.app_id, record.instance_id, LifecycleState(record.lifecycle_state))
            except Exception:
                pass

    def register(
        self,
        manifest: Any,
        *,
        contract: Any = None,
        actor: str = "system",
        emit_event: bool = True,
    ) -> ApplicationRecord:
        # Layered, store-aware duplicate detection. The file lock is only a
        # best-effort coordination aid shared by cooperating processes.
        lock_path = None
        store_path = None
        if self.store is not None and getattr(self.store, "path", None) is not None:
            store_path = Path(self.store.path)
            lock_path = store_path.with_suffix(".application-registry.lock")
            lock_path.parent.mkdir(parents=True, exist_ok=True)
        elif self.store is not None:
            lock_path = Path(tempfile.gettempdir()) / "ethan-application-registry.lock"

        acquired = None
        if lock_path is not None:
            try:
                acquired = open(lock_path, "a+", encoding="utf-8")
                fcntl.flock(acquired.fileno(), fcntl.LOCK_EX)
            except Exception:
                if acquired is not None:
                    try:
                        acquired.close()
                    except Exception:
                        pass
                acquired = None

        if self.store is not None:
            try:
                self._records.clear()
                for payload in self.store.load_records("application_registry_records"):
                    record = ApplicationRecord.from_dict(payload)
                    self._records[(record.app_id, record.instance_id)] = record
            except Exception:
                pass

        if isinstance(manifest, ApplicationManifest):
            manifest_obj = manifest
        elif isinstance(manifest, Mapping):
            manifest_obj = ApplicationManifest.from_mapping(manifest)
        else:
            raise ValidationError("manifest must be an ApplicationManifest or mapping")

        contract_obj = None if contract is None else (contract if isinstance(contract, ExtensionContract) else ExtensionContract.from_mapping(contract))

        # Detect duplicates before writing.
        if (manifest_obj.identity.app_id, manifest_obj.identity.instance_id) in self._records:
            raise ValueError("application instance is already registered")

        compliance_status = "NOT_EVALuated" if False else "NOT_EVALUATED"
        try:
            report = self.compliance_engine.evaluate(manifest=manifest_obj, contract=contract_obj)
            compliance_status = report.status.value
        except Exception:
            compliance_status = "NON_COMPLIANT"

        capabilities = tuple(capability.name for capability in manifest_obj.capabilities)
        requested_permissions = tuple(manifest_obj.permissions)

        # Validate contract if supplied.
        if contract_obj is not None:
            validator = ExtensionContractValidator(capability_registry=self.capability_registry)
            validation = validator.validate(contract_obj.to_dict())
            if not validation.is_valid:
                raise ValidationError("invalid extension contract: " + "; ".join(validation.errors))

        registration_id = str(uuid4())
        record = ApplicationRecord(
            registration_id=registration_id,
            app_id=manifest_obj.identity.app_id,
            instance_id=manifest_obj.identity.instance_id,
            manifest=manifest_obj,
            manifest_digest=manifest_fingerprint(manifest_obj),
            contract=contract_obj,
            contract_digest=None if contract_obj is None else _digest_mapping(contract_obj.to_dict()),
            state=ApplicationRegistrationState.REGISTERED,
            compliance_status=compliance_status,
            capabilities=capabilities,
            requested_permissions=requested_permissions,
        )
        self._records[(record.app_id, record.instance_id)] = record
        self.lifecycle_manager.set_initial(record.app_id, record.instance_id, LifecycleState.REGISTERED)
        if self.store is not None:
            try:
                self.store.save_record("application_registry_records", record.registration_id, record.to_dict())
            except Exception as exc:
                raise RuntimeError(f"application registration persistence failed: {exc}") from exc
        if emit_event:
            try:
                self.event_collector.record({
                    "event_id": str(uuid4()),
                    "schema_version": OBSERVABILITY_SCHEMA_VERSION,
                    "app_id": record.app_id,
                    "instance_id": record.instance_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event_type": "registration",
                    "operation": "register_application",
                    "status": "succeeded",
                    "provenance": "application_registry",
                    "evidence_refs": [record.manifest_digest],
                    "origin": "verified",
                })
            except Exception:
                pass

        # Release best-effort coordination lock.
        recovered_lock = locals().get("acquired")
        if recovered_lock is not None:
            try:
                fcntl.flock(recovered_lock.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
            try:
                recovered_lock.close()
            except Exception:
                pass

        return record

    def get(self, app_id: str, instance_id: str | None = None) -> ApplicationRecord | None:
        if instance_id is None:
            matches = [record for key, record in self._records.items() if key[0] == app_id]
            return matches[0] if matches else None
        return self._records.get((app_id, instance_id))

    def list(self) -> tuple[ApplicationRecord, ...]:
        return tuple(sorted(self._records.values(), key=lambda item: (item.app_id, item.instance_id)))

    def update_manifest(self, app_id: str, instance_id: str, manifest: Any, *, actor: str = "system") -> ApplicationRecord:
        record = self.get(app_id, instance_id)
        if record is None:
            raise ValueError("application is not registered")
        new_manifest = manifest if isinstance(manifest, ApplicationManifest) else ApplicationManifest.from_mapping(manifest)
        if (new_manifest.identity.app_id, new_manifest.identity.instance_id) != (app_id, instance_id):
            raise ValueError("manifest identity cannot change scope during update")
        old_digest = record.manifest_digest
        record.manifest = new_manifest
        record.manifest_digest = manifest_fingerprint(new_manifest)
        record.capabilities = tuple(capability.name for capability in new_manifest.capabilities)
        record.requested_permissions = tuple(new_manifest.permissions)
        # Re-run compliance; invalidate authorization-relevant state.
        try:
            report = self.compliance_engine.evaluate(manifest=new_manifest, contract=record.contract)
            record.compliance_status = report.status.value
        except Exception:
            record.compliance_status = "NON_COMPLIANT"
        record.updated_at = datetime.now(timezone.utc)
        record.state = ApplicationRegistrationState.VALIDATED
        if self.store is not None:
            try:
                self.store.save_record("application_registry_records", record.registration_id, record.to_dict())
            except Exception:
                pass
        return record

    def mark_available(self, app_id: str, instance_id: str, available: bool = True) -> ApplicationRecord:
        record = self.get(app_id, instance_id)
        if record is None:
            raise ValueError("application is not registered")
        record.available = available
        record.state = ApplicationRegistrationState.AVAILABLE if available else ApplicationRegistrationState.UNAVAILABLE
        record.updated_at = datetime.now(timezone.utc)
        if self.store is not None:
            try:
                self.store.save_record("application_registry_records", record.registration_id, record.to_dict())
            except Exception:
                pass
        return record

    def withdraw(self, app_id: str, instance_id: str, reason: str = "") -> ApplicationRecord:
        record = self.get(app_id, instance_id)
        if record is None:
            raise ValueError("application is not registered")
        record.state = ApplicationRegistrationState.WITHDRAWN
        record.available = False
        record.withdrawn_reason = reason
        record.updated_at = datetime.now(timezone.utc)
        if self.store is not None:
            try:
                self.store.save_record("application_registry_records", record.registration_id, record.to_dict())
            except Exception:
                pass

        return record


    def health_check(self, app_id: str, instance_id: str) -> dict[str, Any]:
        record = self.get(app_id, instance_id)
        if record is None:
            return {"status": "unknown", "available": False}
        return {
            "app_id": record.app_id,
            "instance_id": record.instance_id,
            "state": record.state.value,
            "available": record.available,
            "compliance_status": record.compliance_status,
            "manifest_digest": record.manifest_digest,
        }


def _digest_mapping(payload: Mapping[str, Any]) -> str:
    import hashlib
    import json
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# Aliases
ApplicationRegistry = ApplicationIntegrationRegistry
ApplicationIntegrationRegistryService = ApplicationIntegrationRegistry
IntegrationRegistry = ApplicationIntegrationRegistry


__all__ = [
    "ApplicationIntegrationRegistry",
    "ApplicationIntegrationRegistryService",
    "ApplicationRecord",
    "ApplicationRegistrationState",
    "ApplicationRegistry",
    "IntegrationRegistry",
]
