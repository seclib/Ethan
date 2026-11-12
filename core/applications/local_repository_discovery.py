"""Local Git repository discovery and non-executable metadata analysis."""

from __future__ import annotations

import subprocess
import yaml
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse
import os

from core.applications.validator import ContractValidator
from core.applications.models import ApplicationManifest
from core.applications.validator import ContractValidator


DEFAULT_EXCLUDED_DIRECTORIES = {
    ".secrets",  # Kernel/identity secrets; never traverse for discovery
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "node_modules",
    "vendor",
    "target",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".next",
    "dist",
    "build",
}


@dataclass(frozen=True, slots=True)
class LocalRepositoryAnalysis:
    path: str
    name: str
    branch: str | None
    head: str | None
    remote: str | None
    remote_normalized: tuple[str, str, str] | None
    working_tree_status: str
    changed_files: int
    has_readme: bool
    has_ethan_manifest: bool
    manifest_status: str
    detected_files: tuple[str, ...]
    estimated_project_types: tuple[str, ...]
    classification: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _git(path: Path, args: list[str], timeout: float = 3.0) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(path), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def normalize_remote(remote: str | None) -> tuple[str, str, str] | None:
    if not remote:
        return None
    remote = remote.strip()

    parsed = None
    if "://" not in remote and ":" in remote:
        host, _, path_part = remote.partition(":")
        if host and path_part:
            host = host.split("@")[-1]
            path = path_part.strip("/")
            return (host, *path.removesuffix(".git").split("/", 1)) if len(path.split("/")) >= 2 else None

    if "://" in remote:
        parsed = remote
    if parsed is not None:
        try:
            parsed_url = urlparse(parsed)
        except ValueError:
            return None
        host = parsed_url.hostname or ""
        path = parsed_url.path.strip("/")
        if not host or not path:
            return None
        parts = path.split("/")
        repo = parts[-1].removesuffix(".git")
        owner = "/".join(parts[:-1]) if len(parts) > 1 else ""
        if not owner or not repo:
            return None
        return (host, owner, repo)

    return None


def analyze_repository(path: Path, root: Path, *, max_depth: int = 3) -> LocalRepositoryAnalysis:
    relative = path.relative_to(root).as_posix()
    name = path.name
    branch = _git(path, ["branch", "--show-current"])
    head = _git(path, ["rev-parse", "--short", "HEAD"])
    remote = _git(path, ["remote", "get-url", "origin"]) or _git(path, ["remote"])
    changed = _git(path, ["status", "--porcelain"])
    changed_count = len([line for line in (changed or "").splitlines() if line.strip()])
    status = "dirty" if changed_count else "clean" if head else "unknown"

    manifest_path = path / "ethan-application-manifest.yaml"
    manifest_status = "absent"
    manifest_payload: dict[str, Any] | None = None
    if manifest_path.is_file():
        try:
            loaded = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, ImportError, yaml.YAMLError):
            manifest_status = "invalid"
            loaded = None
        if loaded is not None:
            if not isinstance(loaded, Mapping) or not loaded:
                manifest_status = "invalid"
            else:
                manifest_payload = loaded
                # Campaign 01-A reads manifest metadata without enforcing the
                # full application contract. Preview-only fields such as
                # application_type/configuration are intentionally ignored by
                # the contract validator while identity and declared
                # capabilities are still checked when present.
                validation_payload = {
                    key: value for key, value in loaded.items()
                    if key not in {"application_type", "category", "type", "configuration", "config"}
                }
                validation = ContractValidator().validate_manifest_data(validation_payload)
                manifest_status = "valid" if validation.is_valid else "invalid"

    detected = ["README"] if (path / "README.md").is_file() or (path / "README").is_file() or (path / "README.rst").is_file() else []
    if (path / "Dockerfile").is_file():
        detected.append("Dockerfile")
    if any(str(item).startswith("docker-compose") or str(item) in ("compose.yaml", "compose.yml") for item in path.iterdir() if item.is_file()):
        detected.append("DockerCompose")
    if any((path / item).is_file() for item in ("package.json", "package-lock.json")):
        detected.append("Node")
    if any((path / item).is_file() for item in ("pyproject.toml", "requirements.txt", "setup.py")):
        detected.append("Python")
    if (path / "Cargo.toml").is_file():
        detected.append("Rust")

    estimated_types: list[str] = ["unknown"]
    if manifest_payload:
        manifest_type = manifest_payload.get("type")
        if isinstance(manifest_type, str) and manifest_type:
            estimated_types = [manifest_type]
        elif manifest_payload.get("application_type"):
            estimated_types = [str(manifest_payload.get("application_type"))]
        elif isinstance(manifest_payload.get("metadata"), Mapping) and manifest_payload.get("metadata", {}).get("application_category"):
            estimated_types = [str(manifest_payload["metadata"]["application_category"])]
    elif any(item in detected for item in ("Python", "Node", "Rust")):
        estimated_types = ["standalone"]

    classification = "DISCOVERED"
    if manifest_status == "invalid":
        classification = "INVALID"
    elif manifest_status == "valid":
        classification = "COMPATIBLE"

    return LocalRepositoryAnalysis(
        path=path.relative_to(root).as_posix(),
        name=name,
        branch=branch,
        head=head,
        remote=remote,
        remote_normalized=normalize_remote(remote),
        working_tree_status=status,
        changed_files=changed_count,
        has_readme=((path / "README.md").is_file() or (path / "README").is_file()),
        has_ethan_manifest=manifest_path.is_file(),
        manifest_status=manifest_status,
        detected_files=tuple(sorted(detected)),
        estimated_project_types=tuple(estimated_types),
        classification=classification,
    )


class LocalRepositoryDiscovery:
    """Read-only local Git repository discovery without executing project code."""

    def __init__(
        self,
        root: Path,
        *,
        max_depth: int = 4,
        excluded: Iterable[str] = (),
    ) -> None:
        self.root = Path(root).expanduser().resolve()
        if self.root == Path.home().resolve() or self.root == Path("/").resolve():
            raise ValueError("discovery root is too broad")
        if not self.root.is_dir():
            raise ValueError(f"discovery root does not exist: {self.root}")
        self.max_depth = max(0, int(max_depth))
        self.excluded = set(excluded) | DEFAULT_EXCLUDED_DIRECTORIES

    def discover(self) -> list[LocalRepositoryAnalysis]:
        results: list[LocalRepositoryAnalysis] = []
        seen: set[Path] = set()
        if not self.root.is_dir():
            return results

        # A caller may supply the repository itself, not a parent workspace.
        if (self.root / ".git").exists() or (self.root / ".git").is_file():
            try:
                resolved = self.root.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    results.append(analyze_repository(self.root, self.root.parent, max_depth=self.max_depth))
            except OSError:
                pass

        stack = [self.root]
        while stack:
            current = stack.pop()
            try:
                parent = current.parent
                if current == self.root:
                    depth = 0
                else:
                    depth = len(current.relative_to(self.root).parts)
            except ValueError:
                continue
            if depth > self.max_depth:
                continue
            try:
                entries = sorted(current.iterdir(), key=lambda item: item.name)
            except OSError:
                continue
            for entry in entries:
                if not entry.is_dir():
                    continue
                if entry.name in self.excluded:
                    continue
                if entry.is_symlink():
                    target = entry.resolve() if not entry.is_symlink() else entry.readlink()
                    # Python does not normalize via Path.resolve unless needed.
                    try:
                        target = entry.resolve()
                    except OSError:
                        target = entry
                    if target == entry or not str(target).startswith(str(self.root)):
                        # Do not follow discovery outside the authorized root.
                        continue
                try:
                    has_git = (entry / ".git").exists()
                except (OSError, PermissionError):
                    continue
                if has_git:
                    resolved = entry.resolve()
                    if resolved not in seen:
                        seen.add(resolved)
                        results.append(analyze_repository(entry, self.root, max_depth=self.max_depth))
                    # The outer repository is still traversed once, at bounded depth,
                    # so nested repositories are not lost.
                    if depth + 1 <= self.max_depth:
                        stack.append(entry)
                    continue
                stack.append(entry)

        return sorted(results, key=lambda item: item.path)


async def discover_local_repository_profiles(root: Path, *, max_depth: int = 4, include_github: bool = False) -> list[LocalRepositoryAnalysis]:
    reports = LocalRepositoryDiscovery(root=root, max_depth=max_depth).discover()
    if not include_github:
        return reports
    from core.applications.github_organization_discovery import discover_github_user_repositories

    # Correlate only explicit local remotes to published GitHub entries.
    remotes = {report.remote_normalized[1] + "/" + report.remote_normalized[2] for report in reports if report.remote_normalized and report.remote_normalized[0].endswith("github.com") and report.remote_normalized[1]}
    github_records = {record.full_name for record in discover_github_user_repositories("seclib")} if len(remotes) else set()
    for report in reports:
        if report.remote_normalized and report.remote_normalized[0].endswith("github.com") and (report.remote_normalized[1] + "/" + report.remote_normalized[2]) in github_records:
            # Keep analysis read-only; correlation is metadata only.
            pass
    return reports
