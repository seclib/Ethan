import tempfile
from pathlib import Path

from core.applications import ApplicationCatalog, CatalogSource, CatalogEntry


def test_catalog_discovers_valid_manifest() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "a.yaml").write_text(
            "identity:\n  app_id: alpha\n  instance_id: i\n  name: A\n  version: 1.0.0\n"
            "  contract_version: 1.0.0\n  publisher: P\n  manifest_version: 1\n"
        )
        catalog = ApplicationCatalog({CatalogSource.LOCAL_EXAMPLE: root})
    entries = catalog.entries()
    assert len(entries) == 1
    assert entries[0].app_id == "alpha"
    assert entries[0].source == CatalogSource.LOCAL_EXAMPLE
    assert catalog.find("alpha") is not None
    assert catalog.github_source_configured is False
