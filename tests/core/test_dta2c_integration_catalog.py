from pathlib import Path

from core.applications.integration_catalog import IntegrationCatalogService


def test_generic_catalog_includes_comfyui_read_only():
    service = IntegrationCatalogService()
    result = service.build(Path("/home/fatsio/AI/Ethan"), max_depth=3)
    items = result["items"]
    comfy = [item for item in items if item["repository_name"] == "ComfyUI"]
    assert len(comfy) == 1
    assert comfy[0]["states"]["discovered"] is True
    assert comfy[0]["states"]["validated"] is None
    assert comfy[0]["states"]["registered"] is False
    assert comfy[0]["states"]["installed"] == "unknown"
    assert comfy[0]["states"]["running"] == "unknown"
    assert comfy[0]["states"]["authorized"] == "unknown"


def test_generic_catalog_remains_read_only():
    service = IntegrationCatalogService()
    result = service.build(Path("/home/fatsio/AI/Ethan"), max_depth=2)
    assert result["source_errors"] == []
    assert "items" in result


def test_catalog_consumes_persisted_manifest_without_repo_file():
    import yaml
    import tempfile
    from pathlib import Path
    from core.applications.models import ApplicationManifest
    from core.applications.manifest_repository import ApplicationManifestRepository
    from core.applications.integration_catalog import IntegrationCatalogService

    manifest_yaml = """identity:
  app_id: comfyui
  instance_id: comfyui-local-default
  name: ComfyUI
  version: 0.37.0
  contract_version: 1.0.0
  publisher: "ComfyUI project (upstream)"
  manifest_version: 1
capabilities:
  - name: runtime-observation
    description: Report observed ComfyUI state
metadata:
  application_category: web_application
"""
    database = Path(tempfile.mkdtemp()) / "manifests.sqlite"
    repository = ApplicationManifestRepository(persistence_path=database)
    manifest = ApplicationManifest.from_mapping(yaml.safe_load(manifest_yaml))
    record = repository.create(manifest, repository_path="examples/ComfyUI", git_revision="4ef23c3", validation_status="valid")
    assert record.manifest_digest

    service = IntegrationCatalogService(manifest_repository=repository)
    result = service.build(Path("/home/fatsio/AI/Ethan"), max_depth=3)
    items = [item for item in result["items"] if item["repository_name"] == "ComfyUI"]
    assert len(items) == 1
    assert items[0]["manifest_availability"] == "valid"
    assert items[0]["application_type"] == "web_application"
    assert items[0]["declared_capabilities"] == ("runtime-observation",)
