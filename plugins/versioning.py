"""Plugin versioning — support semver et résolution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PluginVersion:
    """Version sémantique d'un plugin."""
    major: int
    minor: int
    patch: int
    raw: str

    @classmethod
    def parse(cls, version: str) -> PluginVersion:
        """Parse une chaîne de version '1.2.3'."""
        parts = version.split(".")
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        return cls(major=major, minor=minor, patch=patch, raw=version)

    def is_compatible_with(self, api_version: str) -> bool:
        """Vérifie compatibilité avec une version d'API (major match)."""
        api = PluginVersion.parse(api_version)
        return self.major == api.major

    def __lt__(self, other: PluginVersion) -> bool:
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        return self.patch < other.patch

    def __le__(self, other: PluginVersion) -> bool:
        return self < other or self == other

    def __gt__(self, other: PluginVersion) -> bool:
        return not (self <= other)

    def __ge__(self, other: PluginVersion) -> bool:
        return not (self < other)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PluginVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    def __str__(self) -> str:
        return self.raw


class VersionRegistry:
    """Registre des versions de plugins."""

    def __init__(self):
        self._versions: dict[str, dict[str, Any]] = {}  # name -> {version -> manifest}

    def register(self, name: str, version: str, manifest: Any) -> None:
        """Enregistre une version d'un plugin."""
        if name not in self._versions:
            self._versions[name] = {}
        self._versions[name][version] = manifest

    def resolve(self, name: str, constraint: str = ">=0.0.0") -> Any | None:
        """Résout la meilleure version selon une contrainte."""
        versions = self._versions.get(name, {})
        if not versions:
            return None

        min_version = PluginVersion.parse(constraint.replace(">=", ""))
        candidates = [
            (PluginVersion.parse(v), m)
            for v, m in versions.items()
            if PluginVersion.parse(v) >= min_version
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    def list_versions(self, name: str) -> list[str]:
        """Liste les versions disponibles d'un plugin."""
        return list(self._versions.get(name, {}).keys())

    def latest(self, name: str) -> str | None:
        """Retourne la version la plus récente."""
        versions = self._versions.get(name, {})
        if not versions:
            return None
        return max(versions.keys(), key=lambda v: PluginVersion.parse(v))