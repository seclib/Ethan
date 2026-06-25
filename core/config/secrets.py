"""SecretManager — Gestion centralisée des secrets.

Supporte :
- Docker Secrets (V1, production)
- Variables d'environnement (développement)
- Vault (V2, future)
"""

from __future__ import annotations

import os
import logging
from typing import Any

logger = logging.getLogger(__name__)


class SecretNotFoundError(Exception):
    """Secret non trouvé dans aucune source."""
    pass


class SecretManager:
    """Gestionnaire de secrets.

    Hiérarchie de résolution :
    1. Docker Secrets (/run/secrets/<name>)
    2. Variable d'environnement (ETHAN_<NAME>)
    3. Variable d'environnement directe (<NAME>)
    4. Fichier local (./secrets/<name>)
    """

    def __init__(self):
        self._cache: dict[str, str] = {}

    def get(self, name: str, default: str | None = None) -> str:
        """Récupère un secret.

        Args:
            name: Nom du secret (e.g., \"openai-api-key\")
            default: Valeur par défaut si le secret n'est pas trouvé

        Returns:
            La valeur du secret

        Raises:
            SecretNotFoundError: Si le secret n'est trouvé nulle part
                et qu'aucun default n'est fourni
        """
        # Cache
        if name in self._cache:
            return self._cache[name]

        # 1. Docker Secrets
        value = self._from_docker_secret(name)
        if value is not None:
            self._cache[name] = value
            return value

        # 2. Variable d'environnement ETHAN_<NAME>
        env_name = f"ETHAN_{name.upper().replace('-', '_')}"
        value = os.environ.get(env_name)
        if value:
            self._cache[name] = value
            return value

        # 3. Variable d'environnement directe
        env_name = name.upper().replace("-", "_")
        value = os.environ.get(env_name)
        if value:
            self._cache[name] = value
            return value

        # 4. Fichier local
        value = self._from_local_file(name)
        if value is not None:
            self._cache[name] = value
            return value

        # Default
        if default is not None:
            return default

        raise SecretNotFoundError(
            f"Secret '{name}' not found in any source "
            f"(Docker Secrets, env vars, local file)"
        )

    def get_or_none(self, name: str) -> str | None:
        """Récupère un secret, retourne None si non trouvé.

        Args:
            name: Nom du secret

        Returns:
            La valeur du secret, ou None
        """
        try:
            return self.get(name)
        except SecretNotFoundError:
            return None

    def clear_cache(self) -> None:
        """Vide le cache des secrets."""
        self._cache.clear()
        logger.debug("Secret cache cleared")

    # ──────────────────────────────────────────────
    # Sources
    # ──────────────────────────────────────────────

    @staticmethod
    def _from_docker_secret(name: str) -> str | None:
        """Lit un secret depuis Docker Secrets.

        Args:
            name: Nom du secret

        Returns:
            La valeur du secret, ou None
        """
        path = f"/run/secrets/{name}"
        try:
            with open(path, "r") as f:
                return f.read().strip()
        except (FileNotFoundError, PermissionError, OSError):
            return None

    @staticmethod
    def _from_local_file(name: str) -> str | None:
        """Lit un secret depuis un fichier local.

        Args:
            name: Nom du secret

        Returns:
            La valeur du secret, ou None
        """
        # Chercher dans ./secrets/<name>
        for base in ["./secrets", "~/.ethan/secrets"]:
            path = os.path.expanduser(f"{base}/{name}")
            try:
                with open(path, "r") as f:
                    return f.read().strip()
            except (FileNotFoundError, PermissionError, OSError):
                continue
        return None

    # ──────────────────────────────────────────────
    # Factory
    # ──────────────────────────────────────────────

    @classmethod
    def create_default(cls) -> SecretManager:
        """Crée un SecretManager avec les sources par défaut.

        Returns:
            Instance de SecretManager
        """
        return cls()

    def __repr__(self) -> str:
        return f"SecretManager(cache_size={len(self._cache)})"