"""Skills System — Système de compétences pour ETHAN.

Une Skill est une compétence de haut niveau composée d'outils.
Exemples : Programmer, Chercher sur Internet, Analyser un PDF, Lire un mail.

Layering (dette « unification skills/tools » close par décision) :
- `core.tools` = primitives d'exécution (ToolManager/ToolExecutor + enforcer
  de sécurité, MCP, egress) — couche sécurisée, consommée par chat/agents/API.
- `core.skills` = couche de composition au-dessus (une Skill = étapes
  d'outils) ; dépend de `core.tools` dans ce sens UNIQUE. Ne jamais fusionner
  les deux paquets : la frontière de l'enforcer (P0-2) vit dans `core.tools`.

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
