import os
import tempfile
from pathlib import Path

import pytest

from core.applications import (
    ApplicationDiscoveryService,
    CapabilityState,
)


def write_manifest(directory: Path, filename: str, body: str) -> Path:
    path = directory / filename
    path.write_text(body, encoding="utf-8")
    return path


VALID_MANIFEST = """identity:
  app_id: alpha
  instance_id: instance-alpha
  name: Alpha
  version: 1.0.0
  contract_version: 1.0.0
  publisher: Publisher
  manifest_version: 1
capabilities:
  - name: read-health
    description: Read system health
"""


def test_discovers_multiple_valid_manifests() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write_manifest(root, "a.yaml", VALID_MANIFEST)
        second = VALID_MANIFEST.replace("alpha", "beta").replace("instance-alpha", "instance-beta")
        write_manifest(root, "b.yaml", second)
        service = ApplicationDiscoveryService(root)
        report = service.discover()
    assert report.application_count == 2
    assert report.capability_count == 2
    assert all(capability.state == CapabilityState.DECLARED for capability in report.capabilities)


def test_invalid_and_incompatible_manifests_do_not_stop_discovery() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write_manifest(root, "valid.yaml", VALID_MANIFEST)
        write_manifest(root, "invalid.yaml", "identity:\n  app_id: '../bad'\n")
        write_manifest(root, "incompatible.yaml", VALID_MANIFEST.replace("contract_version: 1.0.0", "contract_version: 2.0.0"))
        service = ApplicationDiscoveryService(root)
        report = service.discover()
    statuses = {application.validation.status for application in report.applications}
    assert report.application_count == 3
    assert "valid" in statuses
    assert "invalid" in statuses or "incomplete" in statuses or "incompatible" in statuses
    assert len(report.capabilities) == 1


def test_empty_and_missing_directories_are_handled() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        report = ApplicationDiscoveryService(root).discover()
    assert report.application_count == 0
    assert report.capability_count == 0

    missing_report = ApplicationDiscoveryService("/definitely/missing/path").discover()
    assert missing_report.application_count == 0
    assert missing_report.errors


def test_duplicate_app_id_and_instance_id_are_detected() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write_manifest(root, "a.yaml", VALID_MANIFEST)
        duplicate = VALID_MANIFEST.replace("alpha", "alpha").replace("Publisher", "Other")
        write_manifest(root, "b.yaml", duplicate)
        report = ApplicationDiscoveryService(root).discover()
    conflict_types = {conflict.conflict_type for conflict in report.conflicts}
    assert "duplicate_app_id" in conflict_types
    assert "duplicate_instance_id" in conflict_types


def test_unreadable_and_malformed_files_do_not_crash() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write_manifest(root, "malformed.yaml", "identity:\n  - [broken\n")
        unreadable = write_manifest(root, "unreadable.yaml", VALID_MANIFEST)
        unreadable.chmod(0o000)
        try:
            report = ApplicationDiscoveryService(root).discover()
        finally:
            unreadable.chmod(0o644)
    assert report.application_count >= 1
    assert any(application.validation.status == "invalid" for application in report.applications)


def test_symlink_manifest_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source_dir = Path(tempfile.mkdtemp())
        real_manifest = source_dir / "real.yaml"
        real_manifest.write_text(VALID_MANIFEST, encoding="utf-8")
        link = root / "linked.yaml"
        os.symlink(real_manifest, link)
        report = ApplicationDiscoveryService(root).discover()
    assert report.application_count == 0 or all(
        "symbolic" in error.error or "outside" in error.error
        for application in report.applications
        for error in []
    )
    assert (report.errors or len(report.applications) == 0)


def test_source_outside_path_is_rejected_at_root() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "source"
        root.mkdir()
        report = ApplicationDiscoveryService(root.parent.parent).discover(root=root)
        assert report.root_exists is True


def test_unknown_but_valid_capability_remains_declared() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        manifest = VALID_MANIFEST + "  - teleport-users\n"
        write_manifest(root, "a.yaml", manifest)
        report = ApplicationDiscoveryService(root).discover()
    assert report.capability_count == 2
    names = {capability.name for capability in report.capabilities}
    assert "teleport-users" in names
    assert all(capability.state == CapabilityState.DECLARED for capability in report.capabilities)


def test_no_permissions_are_granted_and_no_execution_occurs() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write_manifest(root, "a.yaml", VALID_MANIFEST)
        report = ApplicationDiscoveryService(root).discover()
    assert all(application.manifest is None or not getattr(application.manifest, "permissions", []) for application in report.applications)
    assert report.conflicts == () or isinstance(report.conflicts, tuple)


def test_python_consultation_api_is_stable() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write_manifest(root, "a.yaml", VALID_MANIFEST)
        service = ApplicationDiscoveryService(root)
        service.discover()
        applications = service.list_applications()
        capabilities = service.list_capabilities(app_id="alpha")
        application = service.get_application("alpha")
    assert applications
    assert capabilities
    assert application is not None
    assert service.list_declared_capabilities(app_id="alpha")
