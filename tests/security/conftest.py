"""Quarantaine locale des tests legacy `openjarvis` de `tests/security` (test-infra).

Le paquet applicatif historique `openjarvis` a été supprimé au rebuild
« Docker Foundation Clean Architecture » (cf. commentaire de `tests/conftest.py`).
Les fichiers de ce dossier qui le référencent testent des capacités qui
n'existent plus dans l'architecture actuelle (BoundaryGuard, GuardrailsEngine,
InjectionScanner, scanners PII/secrets, taint tracking, setup_security, ...) et
leurs API modernes ont divergé (`core.security.validation.signature` n'expose
pas `generate_keypair/sign/verify`, `core.security.data.sensitive` n'expose pas
`CredentialStripper`, ...) : leur migration relève d'une RFC dédiée.

Ces fichiers sont donc CONSERVÉS mais ignorés à la collecte — sans liste de noms
à maintenir : un fichier est considéré legacy dès qu'il mentionne le paquet
`openjarvis`. Les tests du code de sécurité actuel (`core.security.*`,
`core.tools.*`, ...) ne sont pas concernés et restent collectés, y compris dans
la suite globale (`pytest tests/`), qui quarantainait auparavant tout le dossier
via `tests/conftest.py`.

Limite connue de pytest : les hooks d'ignore ne s'appliquent pas aux chemins
passés explicitement en ligne de commande. Cibler un fichier legacy en direct
(`pytest tests/security/test_audit.py`) échoue donc encore sur
`ModuleNotFoundError: openjarvis` ; cibler le dossier (`pytest tests/security`)
est propre.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_LEGACY_MARKER = "openjarvis"


def pytest_ignore_collect(collection_path: Path, config: pytest.Config) -> bool | None:
    """Ignore les modules de test legacy `openjarvis` de ce dossier."""
    if collection_path.suffix != ".py" or collection_path.name.startswith("conftest"):
        return None
    try:
        source = collection_path.read_text(encoding="utf-8")
    except OSError:
        return None
    return _LEGACY_MARKER in source
