import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.applications import (
    ApplicationDiscoveryService,
    ComplianceEngine,
    EngineeringMemoryPromotionFilter,
    EventCollector,
    EventOrigin,
    EventStatus,
    ExtensionContract,
    ExtensionContractValidator,
    HumanAuthority,
    IntegrationEvent,
    LifecycleState,
    OBSERVABILITY_SCHEMA_VERSION,
    PermissionService,
    manifest_fingerprint,
    ApplicationLifecycleManager,
)
from core.applications.models import ApplicationManifest


VALID_MANIFEST = """identity:
  app_id: alpha
  instance_id: instance-alpha
  name: Alpha
  version: 1.0.0
  contract_version: 1.0.0
  publisher: Publisher
  manifest_version: 1
capabilities:
  - read-health
permissions:
  - read-health:execute
provenance:
  source: git
  digest: 17f4307a216ed8854291bfcc554681d798ee96fd1b9f8700cfd786a6f3821f64
"""


def test_chain_a_manifest_to_compliance() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "alpha.yaml").write_text(VALID_MANIFEST, encoding="utf-8")
        discovery = ApplicationDiscoveryService(root).discover()
        assert discovery.application_count == 1
        application = discovery.applications[0]
        assert application.validation.is_valid is True

        contract_data = application.manifest.to_dict()
        contract_data["integration_type"] = "application"
        contract_data["requested_permissions"] = ["read-health:execute"]
        contract_data["permission_requirements"] = {"read-health:execute": "read-health"}
        contract = ExtensionContract.from_mapping(contract_data)
        assert contract.integration_type.value == "application"

        validator = ExtensionContractValidator()
        contract_result = validator.validate(contract_data)
        assert contract_result.is_valid is True

        compliance = ComplianceEngine().evaluate(manifest=application.manifest, contract=contract)
        assert compliance.status.value == "COMPLIANT"
        states = [check.check_id + ":" + check.result.value for check in compliance.checks]
        assert "COMPLIANCE_MANIFEST_VALID:PASS" in states
        assert compliance.manifest_digest == manifest_fingerprint(application.manifest)


def test_chain_b_hrot_authorization() -> None:
    service = PermissionService()
    authority = HumanAuthority(principal_id="human-1", principal_type="human", trusted=True, human=True)
    request = service.request_permission("alpha", "instance-alpha", "read-health", "system-health", "read")
    grant = service.approve_request(request.request_id, approved=True, authority=authority)
    assert grant.permission_id

    decision = service.authorize("alpha", "instance-alpha", "read-health", "system-health", "read")
    assert decision.decision.value == "allow"
    assert decision.permission_id == grant.permission_id

    # Textual approved_by alone must not grant.
    service2 = PermissionService()
    request2 = service2.request_permission("alpha", "instance-alpha", "read-health", "system-health", "read")
    try:
        service2.approve_request(request2.request_id, approved=True, approved_by="fake-human")
        raise AssertionError("textual approval granted a permission")
    except ValueError:
        pass
    assert service2.authorize("alpha", "instance-alpha", "read-health", "system-health", "read").decision.value == "deny"


def test_chain_c_invalidation_after_manifest_change() -> None:
    service = PermissionService()
    authority = HumanAuthority(principal_id="human-1", principal_type="human", trusted=True, human=True)
    service.grant_permission(
        "alpha",
        "instance-alpha",
        "read-health",
        "system-health",
        "read",
        approved_by="human-1",
        authority=authority,
        manifest_digest="original-digest",
    )
    first = service.authorize("alpha", "instance-alpha", "read-health", "system-health", "read", manifest_digest="changed-digest")
    assert first.decision.value == "deny"
    assert first.reason_code == "MANIFEST_CHANGED"

    engine = ComplianceEngine()
    original = ApplicationManifest.from_yaml(VALID_MANIFEST)
    changed = ApplicationManifest.from_yaml(VALID_MANIFEST.replace("version: 1.0.0", "version: 1.0.1"))
    report1 = engine.evaluate(manifest=original)
    report2 = engine.evaluate(manifest=changed)
    assert report1.manifest_digest != report2.manifest_digest
    assert report1.evaluation_id != report2.evaluation_id


def test_chain_d_lifecycle_controlled_without_execution() -> None:
    engine = ComplianceEngine()
    manifest = ApplicationManifest.from_yaml(VALID_MANIFEST)
    report = engine.evaluate(manifest=manifest)
    assert report.status.value == "COMPLIANT"

    service = PermissionService()
    authority = HumanAuthority(principal_id="human-1", principal_type="human", trusted=True, human=True)
    service.grant_permission(
        "alpha",
        "instance-alpha",
        "read-health",
        "system-health",
        "read",
        approved_by="human-1",
        authority=authority,
    )
    assert service.authorize("alpha", "instance-alpha", "read-health", "system-health", "read").decision.value == "allow"

    manager = ApplicationLifecycleManager()
    manager.set_initial("alpha", "instance-alpha", LifecycleState.REGISTERED)
    manager.transition("alpha", "instance-alpha", LifecycleState.VALIDATED)
    manager.transition("alpha", "instance-alpha", LifecycleState.READY)
    assert manager.get_state("alpha", "instance-alpha") == LifecycleState.READY

    # No real application process is started by these APIs.


def test_chain_e_observability_provenance_and_filtering() -> None:
    service = PermissionService()
    authority = HumanAuthority(principal_id="human-1", principal_type="human", trusted=True, human=True)
    decision = service.authorize("alpha", "instance-alpha", "read-health", "system-health", "read")
    # No grant exists; decision must be denied and still observable.
    assert decision.decision.value == "deny"

    collector = EventCollector()
    event = collector.record(
        {
            "event_id": "auth-1",
            "schema_version": OBSERVABILITY_SCHEMA_VERSION,
            "app_id": "alpha",
            "instance_id": "instance-alpha",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "authorization",
            "operation": "authorize",
            "status": EventStatus.SUCCEEDED.value if decision.decision.value == "allow" else EventStatus.FAILED.value,
            "provenance": "permission_service",
            "evidence_refs": ["permission:decision"],
            "origin": EventOrigin.VERIFIED.value,
        }
    )
    assert collector.count(app_id="alpha", instance_id="instance-alpha") == 1
    assert event.provenance == "permission_service"

    promotion_filter = EngineeringMemoryPromotionFilter()
    promoted = promotion_filter.promote(event)
    # Ordinary operational events are not promoted to Engineering Memory.
    assert promoted is None
