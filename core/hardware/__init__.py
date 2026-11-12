"""Détection hardware et compatibilité matérielle ETHAN.

Fournit la sonde hardware centralisée (CPU, RAM, GPU/VRAM) et l'analyseur
d'adéquation matérielle ("What Fits?") pour les modèles d'IA.
"""

from .detector import get_system_hardware
from .fit import CompatibilityResult, check_model_compatibility

__all__ = [
    "get_system_hardware",
    "check_model_compatibility",
    "CompatibilityResult",
]
