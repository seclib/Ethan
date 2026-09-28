"""Capability Manager — gestion du cycle de vie des composants optionnels.

Contrairement a core/capabilities (introspection des capacites du Core) et
core/security/policy/capabilities (droits d'action), ce module gere les
composants EXTERNES optionnels de l'ecosysteme : provider, model,
vector_database, runtime, service, integration, tool.

Cycle de vie : detect → install → configure → test → enable → disable → uninstall.
Le Core est la source de verite ; les interfaces (WebUI/CLI) ne font qu'afficher
et transmettre les intentions de l'utilisateur.

Principes :
- Jamais d'installation automatique : supported ≠ installed ≠ available.
- Etats explicites (CapabilityState), jamais un simple booleen.
- Plan avant mutation : l'utilisateur voit les operations avant de confirmer.
- Distinction stricte uninstall composant vs suppression de donnees.
- Aucune chaine utilisateur ne rejoint une argv (securite, section 10).
"""

from core.capability_manager.manager import CapabilityManager
from core.capability_manager.types import (
    CapabilitySpec,
    CapabilityState,
    CapabilityType,
    MutationPlan,
    PlanStep,
    Provenance,
    Requirements,
    TransitionError,
)

# Alias d'identite : « Component Manager » est le vocabulaire utilise par
# l'API (/v1/components, router ``component_lifecycle``). Il ne doit jamais
# exister une seconde implementation pour ce nom — l'alias permet aux
# appelants de desambiguiser d'avec le ``CapabilityManager`` du domaine
# securite (core/security/policy/capabilities.py, permissions d'agents)
# sans introduire de logique dupliquee (Premiere Loi, AGENTS.md).
ComponentManager = CapabilityManager

__all__ = [
    "CapabilityManager",
    "CapabilitySpec",
    "CapabilityState",
    "CapabilityType",
    "ComponentManager",
    "MutationPlan",
    "PlanStep",
    "Provenance",
    "Requirements",
    "TransitionError",
]
