"""Version installée du CLI ETHAN — source de vérité unique.

La version affichée par `ethan --version` DOIT identifier le paquet installé,
pas un littéral du checkout : on lit les métadonnées d'installation
(`Ethan`, paquet racine porteur du console script `ethan`), avec repli sur le
littéral local hors installation (checkout sans `pip install -e .`).
"""

from __future__ import annotations

_FALLBACK_VERSION = "1.0.0"


def _installed_version() -> str | None:
    try:
        from importlib.metadata import version
    except Exception:
        return None
    for dist in ("Ethan", "ethan-cli"):
        try:
            return version(dist)
        except Exception:
            continue
    return None


__version__ = _installed_version() or _FALLBACK_VERSION
