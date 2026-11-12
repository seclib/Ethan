import asyncio
import tempfile
from pathlib import Path

from core.skills.anthropic_importer import AnthropicCyberSkillImporter
from core.skills.store import SkillStore
from core.state.record_store import CoreRecordStore


def _skill(dirpath, name, description="d", body="body"):
    folder = dirpath / "skills" / name
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "SKILL.md"
    path.write_text(
        "---\nname: %s\ndescription: %s\n"
        "domain: cybersecurity\nsubdomain: test\ntags:\n- a\n"
        "version: 1.0\nauthor: test\nlicense: Apache-2.0\n"
        "---\n\n# %s\n\n%s\n" % (name, description, name, body),
        encoding="utf-8",
    )
    return path


def test_discover_parse_import():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _skill(root, "skill-one", body="body-alpha")
        store = SkillStore(CoreRecordStore())
        importer = AnthropicCyberSkillImporter(source_root=root, store=store)
        result = asyncio.run(importer.import_all())
        assert result.discovered == 1
        assert result.imported == 1
        skills = asyncio.run(store.list_skills())
        assert len(skills) == 1
        assert skills[0]["name"] == "skill-one"
        assert "source" in skills[0]["meta"]


def test_idempotence_and_conflict():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _skill(root, "skill-one", body="body-alpha")
        store = SkillStore(CoreRecordStore())
        importer = AnthropicCyberSkillImporter(source_root=root, store=store)
        asyncio.run(importer.import_all())
        res2 = asyncio.run(importer.import_all())
        assert res2.imported == 0
        assert res2.skipped_existing == 1

        path = root / "skills" / "skill-one" / "SKILL.md"
        path.write_text(
            "---\nname: skill-one\ndescription: d\nversion: 1.0\nauthor: test\nlicense: Apache-2.0\n---\n\nnewly changed\n",
            encoding="utf-8",
        )
        res3 = asyncio.run(importer.import_all())
        assert res3.skipped_conflict == 1
        assert len(res3.conflicts) == 1


def test_invalid_skill():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        folder = root / "skills" / "bad"
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text("no frontmatter", encoding="utf-8")
        store = SkillStore(CoreRecordStore())
        importer = AnthropicCyberSkillImporter(source_root=root, store=store)
        result = asyncio.run(importer.import_all())
        assert result.invalid == 1
        assert not asyncio.run(store.list_skills())


def test_path_traversal():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        importer = AnthropicCyberSkillImporter(source_root=root, store=SkillStore())
        assert importer.source_root == root.resolve()
        from core.skills.anthropic_importer import _is_safe
        assert _is_safe(root / "skills", root)
