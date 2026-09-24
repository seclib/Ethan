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

from .composer import SkillComposer
from .executor import SkillExecutor
from .manager import SkillManager
from .registry import SkillRegistry
from .selector import SkillSelector
from .types import Skill, SkillContext, SkillResult, SkillStatus, SkillStep

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
