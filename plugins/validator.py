"""Plugin validator — shim de compatibilité (migration vers le Core).

La capacité de validation des plugins appartient à Core
(``core.plugins.validator``) — source de vérité unique.  Ce module
conserve l'import historique ``from plugins.validator import ...``
pour les clients legacy (``plugins.loader``, CLI) sans dupliquer la
logique métier.
"""

from __future__ import annotations

from core.plugins.validator import (
    FORBIDDEN_BUILTINS,
    FORBIDDEN_IMPORTS,
    PluginValidator,
    ValidationResult,
)

__all__ = [
    "FORBIDDEN_BUILTINS",
    "FORBIDDEN_IMPORTS",
    "PluginValidator",
    "ValidationResult",
]
