"""Modules — Processus métier avec responsabilité unique.

Un Module est un composant réactif qui répond aux événements.
Un Agent est un Module capable d'initiative autonome.

Tous les Agents sont des Modules.
Tous les Modules ne sont pas des Agents.
"""

from core.modules.base import Module, Agent
from core.modules.capability import Capability
from core.modules.dependency import Dependency
from core.modules.permissions import Permissions
from core.modules.interface import ModuleInterface

__all__ = [
    "Module",
    "Agent",
    "ModuleInterface",
    "Capability",
    "Dependency",
    "Permissions",
]