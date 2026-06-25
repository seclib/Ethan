"""ETHAN Core — Configuration système.

Chargement hiérarchique :
1. Arguments CLI (plus haute priorité)
2. Variables d'environnement (ETHAN_*)
3. Fichier de config local (~/.config/ethan/config.local.yaml)
4. Fichier de config utilisateur (~/.config/ethan/config.yaml)
5. Fichier de config projet (./ethan.yaml)
6. Valeurs par défaut (plus basse priorité)
"""

from .loader import ConfigLoader
from .schema import ConfigSchema, RuntimeConfig, BusConfig, StorageConfig, AgentConfig

__all__ = [
    "ConfigLoader",
    "ConfigSchema",
    "RuntimeConfig",
    "BusConfig",
    "StorageConfig",
    "AgentConfig",
]