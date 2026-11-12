import subprocess
import tempfile
from pathlib import Path

from core.applications.local_repository_discovery import LocalRepositoryDiscovery, normalize_remote


def _git(repo: Path, *args: str):
    subtotalprocess = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    assert subtotalprocess.returncode == 0, subtotalprocess.stderr


def test_discovery_finds_git_repository_and_reads_metadata(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    repo = root / "demo"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    (repo / "README.md").write_text("hello")
    _git(repo, "config", "user.email", "test@example.test")
    _git(repo, "config", "user.name", "Test")
    subprocess.run(["git","-C",str(repo),"add","README.md"], check=True, capture_output=True)
    subprocess.run(["git","-C",str(repo),"commit","-m","init"], check=True, capture_output=True)

    reports = LocalRepositoryDiscovery(root=root, max_depth=2).discover()
    assert len(reports) == 1
    assert reports[0].path == "demo"
    assert reports[0].has_readme
    assert reports[0].working_tree_status == "clean"
    assert reports[0].classification == "DISCOVERED"


def test_nested_repositories_are_both_discovered(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    outer = root / "outer"
    nested = outer / "nested"
    nested.mkdir(parents=True)
    for repository in (outer, nested):
        subprocess.run(["git", "init", str(repository)], check=True, capture_output=True)
        _git(repository, "config", "user.email", "test@example.test")
        _git(repository, "config", "user.name", "Test")
        subprocess.run(["git","-C",str(repository),"add","README.md"] , check=False, capture_output=True)
        subprocess.run(["git","-C",str(repository),"commit","--allow-empty","-m","init"], check=True, capture_output=True)
    reports = LocalRepositoryDiscovery(root=root, max_depth=3).discover()
    paths = {report.path for report in reports}
    assert "outer" in paths
    assert "outer/nested" in paths


def test_exclude_directories_and_depth_limits(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    direct = root / "repo"
    deeper = root / "deep" / "nested" / "much" / "deeper" / "git"
    for path in (direct, deeper):
        path.mkdir(parents=True)
        subprocess.run(["git", "init", str(path)], check=True, capture_output=True)
    reports = LocalRepositoryDiscovery(root=root, max_depth=1).discover()
    assert len(reports) == 1
    assert reports[0].path == "repo"


def test_remote_normalization():
    assert normalize_remote("git@github.com:seclib/Ethan.git") == ("github.com", "seclib", "Ethan")
    assert normalize_remote("https://github.com/seclib/Ethan.git") == ("github.com", "seclib", "Ethan")
    assert normalize_remote("ssh://git@github.com/seclib/Ethan.git") == ("github.com", "seclib", "Ethan")
