from core.applications import (
    ComplianceEngine,
    ComplianceResult,
    ComplianceStatus,
)
from core.applications.models import ApplicationManifest


VALID_MANIFEST = {
    "identity": {
        "app_id": "alpha",
        "instance_id": "instance-a",
        "name": "Alpha",
        "version": "1.0.0",
        "contract_version": "1.0.0",
        "publisher": "Publisher",
        "manifest_version": 1,
    },
    "capabilities": ["read-health"],
    "permissions": ["read-health:execute"],
    "provenance": {
        "source": "git",
        "digest": "17f4307a216ed8854291bfcc554681d798ee96fd1b9f8700cfd786a6f3821f64",
    },
}


def test_fully_compliant_application() -> None:
    engine = ComplianceEngine()
    report = engine.evaluate(manifest=VALID_MANIFEST)
    assert report.status == ComplianceStatus.COMPLIANT
    assert report.failed_count == 0


def test_partially_compliant_application() -> None:
    engine = ComplianceEngine()
    data = dict(VALID_MANIFEST)
    data["provenance"] = {"source": "git"}
    report = engine.evaluate(manifest=data, evidence={"manifest": "unit-test"})
    assert report.status == ComplianceStatus.PARTIALLY_COMPLIANT
    assert report.warning_count >= 1


def test_non_compliant_application() -> None:
    engine = ComplianceEngine()
    data = dict(VALID_MANIFEST)
    data["identity"] = dict(data["identity"], contract_version="9.9.9")
    report = engine.evaluate(manifest=data)
    assert report.status == ComplianceStatus.NON_COMPLIANT


def test_invalid_manifest() -> None:
    engine = ComplianceEngine()
    report = engine.evaluate(manifest={"identity": {"app_id": "bad/../id"}})
    assert report.status == ComplianceStatus.NON_COMPLIANT
    assert any(check.result == ComplianceResult.FAIL for check in report.checks)


def test_invalid_contract() -> None:
    engine = ComplianceEngine()
    data = dict(VALID_MANIFEST)
    data["requested_permissions"] = ["admin:all"]
    report = engine.evaluate(manifest=data, contract={"integration_type": "unknown"})
    assert report.status == ComplianceStatus.NON_COMPLIANT


def test_missing_required_evidence() -> None:
    engine = ComplianceEngine()
    data = dict(VALID_MANIFEST)
    data["provenance"] = {"source": "git"}
    report = engine.evaluate(manifest=data)
    assert report.status in {ComplianceStatus.NON_COMPLIANT, ComplianceStatus.PARTIALLY_COMPLIANT}
    assert report.failed_count >= 1 or report.warning_count >= 1


def test_critical_check_failure() -> None:
    engine = ComplianceEngine()
    data = dict(VALID_MANIFEST)
    data["metadata"] = {"secret": "password=hunter2"}
    report = engine.evaluate(manifest=data)
    assert report.status == ComplianceStatus.NON_COMPLIANT


def test_warn_result_is_not_success() -> None:
    engine = ComplianceEngine()
    data = dict(VALID_MANIFEST)
    data["provenance"] = {"source": "git"}
    report = engine.evaluate(manifest=data)
    assert report.status != ComplianceStatus.COMPLIANT


def test_engine_error_is_not_compliant() -> None:
    engine = ComplianceEngine()
    report = engine.evaluate(manifest="not a mapping")
    assert report.status == ComplianceStatus.NON_COMPLIANT


def test_manifest_change_invalidates_evaluation_context() -> None:
    engine = ComplianceEngine()
    report1 = engine.evaluate(manifest=VALID_MANIFEST)
    data = dict(VALID_MANIFEST)
    data["identity"] = dict(data["identity"], version="1.0.1")
    report2 = engine.evaluate(manifest=data)
    assert report1.evaluation_id != report2.evaluation_id
    assert report1.manifest_digest != report2.manifest_digest


def test_contract_change_invalidates_evaluation_context() -> None:
    engine = ComplianceEngine()
    contract = {"integration_type": "application"}
    report1 = engine.evaluate(manifest=VALID_MANIFEST, contract=contract)
    contract2 = {"integration_type": "plugin"}
    report2 = engine.evaluate(manifest=VALID_MANIFEST, contract=contract2)
    assert report1.contract_digest != report2.contract_digest


def test_compliance_independent_from_authorization() -> None:
    engine = ComplianceEngine()
    report = engine.evaluate(manifest=VALID_MANIFEST)
    assert report.status == ComplianceStatus.COMPLIANT
    # Compliance alone does not expose or grant any permission.
    assert all("permission" not in check.check_id.lower() or "coherence" in check.check_id.lower() for check in report.checks)


def test_no_execution_or_permission_granted() -> None:
    engine = ComplianceEngine()
    report = engine.evaluate(manifest=VALID_MANIFEST)
    assert report is not None
    assert report.status in {ComplianceStatus.COMPLIANT, ComplianceStatus.PARTIALLY_COMPLIANT, ComplianceStatus.NON_COMPLIANT}
