"""Skills System — Système de compétences pour ETHAN.

Une Skill est une compétence de haut niveau composée d'outils.
Exemples : Programmer, Chercher sur Internet, Analyser un PDF, Lire un mail.

Architecture :
- SkillRegistry : Catalogue des skills
- SkillManager : Orchestrateur principal
- SkillExecutor : Exécution avec pipeline
- SkillSelector : Sélection intelligente
- SkillComposer : Composition de skills
"""

from .types import Skill, SkillStep, SkillContext, SkillResult, SkillStatus
from .registry import SkillRegistry
from .manager import SkillManager
from .executor import SkillExecutor
from .selector import SkillSelector
from .composer import SkillComposer

__all__ = [
    "Skill",
    "SkillStep",
    "SkillContext",
    "SkillResult",
    "SkillStatus",
    "SkillRegistry",
    "SkillManager",
    "SkillExecutor",
    "SkillSelector",
    "SkillComposer",
]