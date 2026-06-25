"""Permissions — Contrôle d'accès pour les modules.

Chaque module déclare explicitement ce qu'il peut :
- Lire/écrire dans l'état (Redis)
- Publier/souscrire à des événements
- Accéder au réseau
- Accéder au système de fichiers
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Permissions:
    """Permissions déclarées d'un module.

    Exemple :
        Permissions(
            state_read=["memory:*"],
            state_write=["memory:session:*"],
            events_subscribe=["interface.*", "planner.*"],
            events_publish=["memory.*"],
            network=["https://api.openai.com"],
            filesystem=["/var/lib/ethan/memory/*"],
        )
    """

    state_read: list[str] = field(default_factory=list)
    """Clés d'état autorisées en lecture (patterns glob, e.g., [\"memory:*\"])."""

    state_write: list[str] = field(default_factory=list)
    """Clés d'état autorisées en écriture (patterns glob, e.g., [\"memory:session:*\"])."""

    events_subscribe: list[str] = field(default_factory=list)
    """Patterns d'événements autorisés en souscription (e.g., [\"interface.*\"])."""

    events_publish: list[str] = field(default_factory=list)
    """Patterns d'événements autorisés en publication (e.g., [\"memory.*\"])."""

    network: list[str] = field(default_factory=list)
    """URLs autorisées pour les requêtes réseau (e.g., [\"https://api.openai.com\"])."""

    filesystem: list[str] = field(default_factory=list)
    """Chemins de fichiers autorisés (patterns glob, e.g., [\"/tmp/*\"])."""

    def can_read_state(self, key: str) -> bool:
        """Vérifie si une clé d'état peut être lue."""
        return self._matches_any(key, self.state_read)

    def can_write_state(self, key: str) -> bool:
        """Vérifie si une clé d'état peut être écrite."""
        return self._matches_any(key, self.state_write)

    def can_subscribe(self, pattern: str) -> bool:
        """Vérifie si un pattern d'événement peut être souscrit."""
        return self._matches_any(pattern, self.events_subscribe)

    def can_publish(self, pattern: str) -> bool:
        """Vérifie si un pattern d'événement peut être publié."""
        return self._matches_any(pattern, self.events_publish)

    def can_access_network(self, url: str) -> bool:
        """Vérifie si une URL peut être contactée."""
        return self._matches_any(url, self.network)

    def can_access_filesystem(self, path: str) -> bool:
        """Vérifie si un chemin de fichier peut être accédé."""
        return self._matches_any(path, self.filesystem)

    @staticmethod
    def _matches_any(value: str, patterns: list[str]) -> bool:
        """Vérifie si une valeur correspond à au moins un pattern glob."""
        import fnmatch
        for pattern in patterns:
            if fnmatch.fnmatch(value, pattern):
                return True
        return False


@dataclass(frozen=True)
class PermissionDenied(Exception):
    """Exception levée quand un module tente une action non autorisée."""
    module: str
    action: str
    target: str
    required_pattern: str | None = None

    def __str__(self) -> str:
        msg = f"Permission denied: module '{self.module}' cannot {self.action} '{self.target}'"
        if self.required_pattern:
            msg += f" (required pattern: '{self.required_pattern}')"
        return msg