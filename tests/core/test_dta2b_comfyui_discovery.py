from pathlib import Path

from core.applications.integration_preview import build_integration_preview
from core.applications.local_repository_discovery import LocalRepositoryDiscovery, analyze_repository


def test_comfyui_is_discovered_without_ethan_manifest():
    previews = build_integration_preview(Path("/home/fatsio/AI/Ethan"), max_depth=3)
    comfy = [preview for preview in previews if preview.repository_identity["name"] == "ComfyUI"]
    assert len(comfy) == 1
    assert comfy[0].manifest_availability == "absent"
    assert comfy[0].read_only is True


def test_comfyui_analysis_is_byte_style_python_web_backend():
    analysis = analyze_repository(Path("/home/fatsio/AI/Ethan/examples/ComfyUI"), Path("/home/fatsio/AI/Ethan"))
    assert analysis.path == "examples/ComfyUI"
    assert "Python" in analysis.detected_files
    assert analysis.has_readme is True
    assert analysis.manifest_status == "absent"
