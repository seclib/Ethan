import tempfile
from pathlib import Path

import yaml

from core.applications.manifest_repository import ApplicationManifestRepository
from core.applications.models import ApplicationManifest
from core.applications.validator import ContractValidator

MANIFEST = """identity:
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


def test_manifest_repository_persists_and_reloads():
    path = Path(tempfile.mkdtemp()) / "manifests.db"
    manifest = ApplicationManifest.from_mapping(yaml.safe_load(MANIFEST))
    repository = ApplicationManifestRepository(persistence_path=path)
    assert ContractValidator().validate_manifest_data(manifest.to_dict()).is_valid is True
    created = repository.create(manifest, source_type="local_repository", repository_path="/home/fatsio/AI/Ethan/examples/ComfyUI", git_revision="4ef23c3")
    assert created.validation_status == "valid"
    duplicate_raised = False
    try:
        repository.create(manifest)
    except Exception:
        duplicate_raised = True
    assert duplicate_raised
    reloaded = ApplicationManifestRepository(persistence_path=path)
    current = reloaded.get_current("comfyui", "comfyui-local-default")
    assert current is not None
    assert current.record_version == 1
    assert current.git_revision == "4ef23c3"
    assert current.manifest.metadata["application_category"] == "web_application"
