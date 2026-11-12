"""Campaign 01-A: read-only local discovery and integration preview."""

from __future__ import annotations

import subprocess
from pathlib import Path

from core.applications.integration_preview import IntegrationPreviewService, build_integration_preview

def _git_repo(root: Path, name: str, manifest: str | None = None) -> Path:
    repo = root / name
    repo.mkdir(parents=True)
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.test"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True, capture_output=True)
    (repo / "README.md").write_text("demo", encoding="utf-8")
    if manifest is not None:
        (repo / "ethan-application-manifest.yaml").write_text(manifest, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"], check=True, capture_output=True)
    return repo

MANIFEST = """identity:
  app_id: demo-app
  instance_id: instance-1
  name: Demo
  version: 1.0.0
  contract_version: 1.0.0
  publisher: Test
  manifest_version: 1
application_type: backend
capabilities:
  - analyze
configuration:
  - port
permissions:
  - read
"""

def test_controlled_fixture_discovery_and_preview(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    _git_repo(root, "demo", MANIFEST)
    service = IntegrationPreviewService()
    previews = service.discover(root)
    assert len(previews) == 1
    preview = previews[0]
    assert preview.read_only is True
    assert preview.application_category == "backend"
    assert "analyze" in preview.declared_capabilities
    assert preview.manifest_availability == "valid"
    assert preview.validation_errors == ()

def test_unknown_repository_missing_manifest(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    _git_repo(root, "no-manifest", None)
    previews = build_integration_preview(root)
    assert len(previews) == 1
    preview = previews[0]
    assert preview.manifest_availability == "absent"
    assert "ethan-application-manifest" in preview.missing_requirements

def test_invalid_manifest_generates_preview_errors(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    _git_repo(root, "bad", "this: [\n")
    previews = build_integration_preview(root)
    assert previews[0].validation_errors != ()
    assert previews[0].manifest_availability == "invalid"

def test_discovery_and_preview_do_not_mutate_catalog_or_registry(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    _git_repo(root, "demo", MANIFEST)
    previews = build_integration_preview(root)
    assert isinstance(previews, tuple)
    assert len(previews) == 1
    assert previews[0].read_only is True