from pathlib import Path
import tempfile

from core.applications.integration_catalog import IntegrationCatalogService
from core.applications.manifest_repository import ApplicationManifestRepository


def test_manifest_persists_and_is_found_after_reload():
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "manifests.sqlite"
        repository = ApplicationManifestRepository(persistence_path=db)
        import yaml
        from core.applications.models import ApplicationManifest
        yaml_text = """identity:
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
        manifest = ApplicationManifest.from_mapping(yaml.safe_load(yaml_text))
        record = repository.create(manifest, repository_path="examples/ComfyUI", validation_status="valid")
        repository.close()

        reloaded = ApplicationManifestRepository(persistence_path=db)
        found = reloaded.get_current("comfyui", "comfyui-local-default")
        assert found is not None
        assert found.validation_status == "valid"
        assert found.manifest_digest == record.manifest_digest

        service = IntegrationCatalogService(manifest_repository=reloaded)
        result = service.build(Path("/home/fatsio/AI/Ethan"), max_depth=3)
        items = [item for item in result["items"] if item["repository_name"] == "ComfyUI"]
        assert len(items) == 1
        assert items[0]["manifest_validation_status"] == "valid"
        assert items[0]["application_type"] == "web_application"
        assert items[0]["declared_capabilities"] == ("runtime-observation",)
        reloaded.close()


def test_catalog_lists_comfyui_once_and_counts_repositories():
    from core.applications.integration_catalog import IntegrationCatalogService
    from pathlib import Path

    service = IntegrationCatalogService()
    result = service.build(Path("/home/fatsio/AI/Ethan"), max_depth=3)
    comfy = [item for item in result["items"] if item["repository_name"] == "ComfyUI"]
    assert len(comfy) == 1
    assert result["total_repositories"] == len(result["items"])
