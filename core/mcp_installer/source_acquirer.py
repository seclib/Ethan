"""Acquisition de source MCP — clone git, info npm, commande custom.

Acquisitions strictement **en lecture seule** : aucune installation, aucun
script, aucun exécutable tiers lancé. Les sorties sont bornées et les sources
réseau sont validées en amont (SSRF, schéma, hôte) par ``source_validation``.
"""

from __future__ import annotations

import json
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

from core.mcp_installer.plan import SourceType
from core.mcp_installer.source_validation import (
    McpSourceValidationError,
    bounded_stdout,
    validate_github_url,
    validate_npm_package_name,
)


def parse_npx_command(source: str) -> tuple[str, list[str]]:
    """Extrait ``(package, args supplémentaires)`` d'une commande npx.

    Les drapeaux du lanceur (``-y``, ``--yes``…) précédant le package sont
    ignorés : ils sont réappliqués par le plan. Les arguments situés APRÈS le
    package sont conservés (ils configurent souvent le serveur MCP).
    """
    try:
        parts = shlex.split(source)
    except ValueError:
        parts = source.split()
    if not parts:
        return "", []
    index = 1 if Path(parts[0]).name in {"npx", "npx.cmd"} else 0
    while index < len(parts) and parts[index].startswith("-"):
        index += 1
    if index >= len(parts):
        return "", []
    return parts[index], parts[index + 1 :]


def detect_source_type(source: str) -> SourceType:
    """Détecte le type de source à partir d'une chaîne."""
    source = source.strip()
    if source.startswith("http://") or source.startswith("https://"):
        if "github.com" in source:
            return SourceType.GITHUB
        return SourceType.REMOTE_HTTP
    if source.startswith("npx ") or source.startswith("npx\t"):
        return SourceType.NPM_COMMAND
    # npm package: @org/pkg or simple name (no spaces, no slash at start)
    if " " not in source and not source.startswith("/"):
        if source.startswith("@") or re.match(r"^[a-z0-9][a-z0-9._-]*$", source):
            return SourceType.NPM_PACKAGE
    if " " in source:
        return SourceType.CUSTOM_COMMAND
    return SourceType.CUSTOM_COMMAND


def acquire_npm_info(package: str) -> dict[str, Any]:
    """Récupère les métadonnées npm d'un package via `npm view` (lecture seule)."""
    result: dict[str, Any] = {"package": package, "errors": []}
    try:
        safe_package = validate_npm_package_name(package)
    except McpSourceValidationError as exc:
        result["errors"].append(str(exc))
        return result
    try:
        proc = subprocess.run(
            ["npm", "view", safe_package, "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            stderr = bounded_stdout(proc.stderr, limit=4000)
            result["errors"].append(f"npm view failed: {stderr.strip()[:200]}")
            return result
        stdout = bounded_stdout(proc.stdout)
        data = json.loads(stdout)
        result["name"] = data.get("name", safe_package)
        result["version"] = data.get("version", "")
        result["description"] = data.get("description", "")
        result["keywords"] = data.get("keywords", [])
        result["bin"] = data.get("bin", {})
        result["dependencies"] = list((data.get("dependencies") or {}).keys())
        result["engines"] = data.get("engines", {})
        result["repository"] = data.get("repository", {})
        result["homepage"] = data.get("homepage", "")
        result["license"] = data.get("license", "")
    except McpSourceValidationError as exc:
        result["errors"].append(str(exc))
    except FileNotFoundError:
        result["errors"].append("npm not found on PATH")
    except subprocess.TimeoutExpired:
        result["errors"].append("npm view timed out")
    except json.JSONDecodeError:
        result["errors"].append("invalid npm view output")
    except Exception as e:  # noqa: BLE001
        result["errors"].append(str(e))
    return result


def acquire_github_repo(url: str, target_dir: str) -> dict[str, Any]:
    """Clone un dépôt GitHub dans target_dir (lecture seule, pas d'exécution).

    Le contenu cloné n'est jamais exécuté par l'analyse. Le clone est borné
    (profondeur 1, timeout) et durci (pas de hooks, pas de suivi de
    redirections HTTP git) pour réduire la surface d'acquisition.
    """
    result: dict[str, Any] = {"url": url, "errors": []}
    try:
        safe_url = validate_github_url(url)
        result["url"] = safe_url
    except McpSourceValidationError as exc:
        result["errors"].append(str(exc))
        return result
    try:
        if not shutil.which("git"):
            result["errors"].append("git not found on PATH")
            return result
        target = Path(target_dir)
        if target.exists():
            result["errors"].append(f"target directory already exists: {target_dir}")
            return result
        target.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            [
                "git",
                "-c",
                "core.hooksPath=/dev/null",
                "-c",
                "http.followRedirects=false",
                "-c",
                "advice.detachedHead=false",
                "clone",
                "--depth",
                "1",
                "--single-branch",
                "--no-tags",
                safe_url,
                str(target),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            stderr = bounded_stdout(proc.stderr, limit=4000)
            result["errors"].append(f"git clone failed: {stderr.strip()[:300]}")
            return result
        result["cloned"] = True
        result["path"] = str(target)
    except McpSourceValidationError as exc:
        result["errors"].append(str(exc))
    except subprocess.TimeoutExpired:
        result["errors"].append("git clone timed out")
    except Exception as e:  # noqa: BLE001
        result["errors"].append(str(e))
    return result


def detect_runtime() -> dict[str, Any]:
    """Détecte les runtimes disponibles (node, npm, npx, python, pip)."""
    result: dict[str, Any] = {}
    for cmd in ("node", "npm", "npx", "python3", "python", "pip", "pip3", "git"):
        path = shutil.which(cmd)
        if path:
            try:
                proc = subprocess.run(
                    [cmd, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                version = (proc.stdout or proc.stderr).strip()
            except Exception:  # noqa: BLE001
                version = "unknown"
            result[cmd] = {"path": path, "version": version}
        else:
            result[cmd] = None
    return result
