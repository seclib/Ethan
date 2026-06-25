"""ETHAN Core — Plugin System.

Plugins Python chargés dynamiquement par les modules.
Plugins Go compilés dans le Kernel (module séparé).

Deux niveaux :
- Kernel plugins (Go) : transport, stockage, haute performance
- Python plugins : tools, providers, extensions cognitives
"""

from .interface import EthanPlugin, PluginManifest
from .loader import PluginLoader

__all__ = ["EthanPlugin", "PluginManifest", "PluginLoader"]