"""Registry — Gestion centralisée des modules, capacités et événements.

Le Registry est le point d'entrée unique pour :
- Enregistrer et découvrir des modules
- Déclarer et résoudre des capacités
- Valider et versionner des événements
"""

from core.registry.capability import CapabilityRegistry
from core.registry.module import ModuleRegistry
from core.registry.events import EventSchemaRegistry

__all__ = [
    "CapabilityRegistry",
    "ModuleRegistry",
    "EventSchemaRegistry",
]