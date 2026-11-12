"""Importeur simple pour skills Anthropic Cybersecurity."""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from core.skills.store import SkillStore


_DEFAULT_SOURCE = Path("/home/fatsio/AI/Anthropic-Cybersecurity-Skills")


def _is_safe(child: Path, root: Path) -> bool:
    try:
        return root.resolve() in child.resolve().parents or child.resolve() == root.resolve()
    except OSError:
        return False


@dataclass
class ImportResult:
    discovered: int = 0
    imported: int = 0
    skipped_existing: int = 0
    skipped_conflict: int = 0
    invalid: int = 0
    errors: list[str] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    imported_ids: list[str] = field(default_factory=list)


class AnthropicCyberSkillImporter:
    def __init__(self, source_root: Path | str = _DEFAULT_SOURCE, store: SkillStore | None = None):
        self.source_root = Path(source_root).expanduser()
        self.store = store or SkillStore()

    async def discover(self) -> list[Path]:
        skills_dir = (self.source_root / "skills").resolve()
        if not _is_safe(skills_dir, self.source_root):
            raise ValueError("Path traversal detected in source root.")
        if not skills_dir.exists():
            return []
        return sorted(
            path for path in skills_dir.glob("*/SKILL.md")
            if _is_safe(path, self.source_root)
        )

    def _parse(self, path: Path) -> tuple[dict[str, Any] | None, list[str]]:
        raw = path.read_text(encoding="utf-8")
        if not raw.startswith("---"):
            return None, [f"No YAML frontmatter found in {path}"]
        parts = raw.split("---", 2)
        if len(parts) < 3:
            return None, [f"Missing closing frontmatter marker in {path}"]
        try:
            fm = yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError as exc:
            return None, [f"YAML parse error in {path}: {exc}"]
        if not isinstance(fm, dict):
            return None, [f"Frontmatter must be a mapping in {path}"]
        body = parts[2].strip()
        name = str(fm.get("name", "")).strip()
        description = str(fm.get("description", "")).strip()
        if not name or not description or not body:
            return None, [f"Missing required field in {path}"]
        payload = {
            "name": name,
            "description": description[:500],
            "content": body,
            "kind": "prompt",
            "tags": ["cybersecurity", str(fm.get("domain", "")).strip(), str(fm.get("subdomain", "")).strip()],
            "author": str(fm.get("author", "Anthropic Cybersecurity Skills")).strip(),
            "version": str(fm.get("version", "1.0")).strip(),
            "meta": {
                "source": "anthropic-cybersecurity-skills",
                "source_path": str(path.relative_to(self.source_root)),
                "license": fm.get("license"),
                "domain": fm.get("domain"),
                "subdomain": fm.get("subdomain"),
                "nist_csf": fm.get("nist_csf", []),
                "mitre_attack": fm.get("mitre_attack", []),
                "references": fm.get("references", []),
            },
        }
        checksum = hashlib.sha256((name + "\n" + body).encode()).hexdigest()
        return {"payload": payload, "checksum": checksum}, []

    async def import_all(self, dry_run: bool = False) -> ImportResult:
        result = ImportResult()
        discovered = await self.discover()
        result.discovered = len(discovered)
        existing = {str(s.get("name", "")).casefold(): s for s in await self.store.list_skills()}

        for path in discovered:
            parsed, errors = self._parse(path)
            if errors:
                result.invalid += 1
                result.errors.extend(errors)
                continue

            payload = parsed["payload"]
            name = payload["name"]
            checksum = parsed["checksum"]

            existing_skill = existing.get(name.casefold())
            if existing_skill is not None:
                old_checksum = hashlib.sha256(
                    (str(existing_skill.get("name", "")) + "\n" + str(existing_skill.get("content", ""))).encode()
                ).hexdigest()
                if old_checksum == checksum:
                    result.skipped_existing += 1
                else:
                    result.skipped_conflict += 1
                    result.conflicts.append(
                        {
                            "name": name,
                            "path": str(path),
                            "existing_id": existing_skill.get("id"),
                            "reason": "Existing skill has different content.",
                        }
                    )
                continue

            if dry_run:
                result.imported += 1
                result.imported_ids.append("dry-run")
                continue

            created = await self.store.create_skill(payload)
            result.imported += 1
            result.imported_ids.append(str(created.get("id", "")))
            existing[name.casefold()] = created

        return result


async def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=_DEFAULT_SOURCE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    importer = AnthropicCyberSkillImporter(source_root=args.source, store=SkillStore())
    result = await importer.import_all(dry_run=args.dry_run)
    print(
        {
            "discovered": result.discovered,
            "imported": result.imported,
            "skipped_existing": result.skipped_existing,
            "skipped_conflict": result.skipped_conflict,
            "invalid": result.invalid,
            "errors": result.errors[:10],
            "conflicts": result.conflicts[:10],
        }
    )
    if result.errors:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
