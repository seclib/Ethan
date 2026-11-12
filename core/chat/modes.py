"""ETHAN Core — Chat modes (Plan / Act / Debug).

Source de vérité unique des modes conversationnels.  Inspiré du principe
Plan/Act de Cline mais **adapté à l'architecture ETHAN** : les profils par
mode vivent ici (Core), pas dans l'interface — là où Cline duplique des clés
plates par provider × mode (``planModeOllamaModelId``…), ETHAN possède un
seul profil sérialisé par mode, résolu par priorité
``request > session > mode profile > global``.

Règle de capacité : un effort de raisonnement demandé n'est appliqué que si
le modèle cible déclare la capacité ``reasoning`` — sinon le résultat porte
``supported: False`` et aucune valeur fantôme n'est envoyée au provider.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChatMode(str, Enum):
    """Modes conversationnels du chat ETHAN."""

    PLAN = "plan"
    ACT = "act"
    DEBUG = "debug"


class ReasoningEffort(str, Enum):
    """Effort de raisonnement demandé au modèle.

    ``none`` désactive explicitement le raisonnement.  Le support réel est
    arbitré par :func:`resolve_reasoning` selon les capacités du modèle.
    """

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"


class SystemAccess(str, Enum):
    """Niveau d'accès système d'une session (§19).

    ``RESTRICTED`` : ressources explicitement attachées uniquement.
    ``WORKSPACE``  : workspace/projet autorisé.
    ``EXTENDED``   : ressources supplémentaires explicitement autorisées par
                     ETHAN — jamais un accès arbitraire à la machine ; soumis
                     au modèle de sécurité ETHAN.
    """

    RESTRICTED = "restricted"
    WORKSPACE = "workspace"
    EXTENDED = "extended"


class CompactionStrategy(str, Enum):
    """Stratégies de compaction du contexte (§15)."""

    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class DebugLevel(str, Enum):
    """Niveau d'autorisation du mode Debug (§9).

    ``DIAGNOSE``         : collecter, reproduire, expliquer la cause racine.
    ``DIAGNOSE_PROPOSE`` : + proposer un correctif (sans l'appliquer).
    ``DIAGNOSE_APPLY``   : + appliquer le correctif si les permissions
                           Runtime le permettent (jamais au-delà).
    """

    DIAGNOSE = "diagnose"
    DIAGNOSE_PROPOSE = "diagnose_propose"
    DIAGNOSE_APPLY = "diagnose_apply"


class TerminalPermission(str, Enum):
    """Politique terminale par défaut du mode."""

    ASK = "ask"
    ALLOW = "allow"
    DENY = "deny"


class AutoApproval(str, Enum):
    """Niveaux d'auto-approbation des actions (§21).

    Jamais au-delà des permissions Core/Runtime — le frontend ne peut pas
    contourner les restrictions.
    """

    OFF = "off"
    SAFE_ACTIONS = "safe_actions"
    ALL_ALLOWED_ACTIONS = "all_allowed_actions"


REASONING_CAPABILITY = "reasoning"


def resolve_reasoning(
    requested: ReasoningEffort | str | None,
    model_capabilities: list[str] | None,
) -> dict[str, Any]:
    """Résoudre l'effort de raisonnement selon les capacités du modèle.

    Returns:
        ``{"effort": str, "supported": bool}`` — ``supported`` est False si
        le modèle ne déclare pas la capacité ``reasoning`` : l'appelant ne
        doit alors pas transmettre d'effort au provider (pas de valeur
        fantôme), et l'UI doit afficher « non supporté ».
    """
    if requested is None:
        return {"effort": ReasoningEffort.NONE.value, "supported": True}
    effort = requested.value if isinstance(requested, ReasoningEffort) else str(requested)
    try:
        effort = ReasoningEffort(effort).value
    except ValueError:
        effort = ReasoningEffort.MEDIUM.value
    caps = [str(c).lower() for c in (model_capabilities or [])]
    supported = REASONING_CAPABILITY in caps
    return {"effort": effort, "supported": supported}


@dataclass
class TerminalCommandPolicy:
    """Politique de commandes terminales (modèle allow/deny à motifs glob).

    Motifs Cline-compatible (``git *``, ``rm -rf *``, ``sudo *``) mais
    **appliqués côté Core/Runtime** : le frontend n'est jamais une frontière
    de sécurité.  ``default`` tranche les commandes sans motif (ask/allow/deny).
    """

    allowed: list[str] = field(default_factory=list)
    denied: list[str] = field(default_factory=list)
    default: TerminalPermission = TerminalPermission.ASK

    def evaluate(self, command: str) -> TerminalPermission:
        """Résoudre une commande → permission (deny > allow > default)."""
        cmd = (command or "").strip()
        if not cmd:
            return TerminalPermission.DENY
        for pattern in self.denied:
            if fnmatch.fnmatch(cmd, pattern):
                return TerminalPermission.DENY
        for pattern in self.allowed:
            if fnmatch.fnmatch(cmd, pattern):
                return TerminalPermission.ALLOW
        return self.default

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": list(self.allowed),
            "denied": list(self.denied),
            "default": self.default.value,
        }


@dataclass
class ModeProfile:
    """Profil d'un mode (provider/model/reasoning/permissions…).

    ``provider_id`` et ``model`` sont optionnels : vides, ils retombent sur
    la sélection globale (fallback — pas de duplication de catalogue).
    """

    mode: ChatMode
    provider_id: str = ""
    model: str = ""
    reasoning_effort: ReasoningEffort = ReasoningEffort.MEDIUM
    auto_compact: bool = True
    system_access: SystemAccess = SystemAccess.WORKSPACE
    compaction_strategy: CompactionStrategy = CompactionStrategy.BALANCED
    debug_level: DebugLevel = DebugLevel.DIAGNOSE
    terminal: TerminalCommandPolicy = field(default_factory=TerminalCommandPolicy)
    auto_approval: AutoApproval = AutoApproval.OFF
    language: str = ""

    def permissions(self) -> ModePermissions:
        """Matrice de permissions effective du mode."""
        return effective_mode_permissions(self.mode, self.debug_level)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "provider_id": self.provider_id,
            "model": self.model,
            "reasoning_effort": self.reasoning_effort.value,
            "auto_compact": self.auto_compact,
            "system_access": self.system_access.value,
            "compaction_strategy": self.compaction_strategy.value,
            "debug_level": self.debug_level.value,
            "terminal": self.terminal.to_dict(),
            "auto_approval": self.auto_approval.value,
            "language": self.language,
            "permissions": self.permissions().to_dict(),
        }


def default_mode_profiles() -> dict[str, ModeProfile]:
    """Profils par défaut des trois modes."""
    return {
        ChatMode.PLAN.value: ModeProfile(
            mode=ChatMode.PLAN,
            reasoning_effort=ReasoningEffort.HIGH,
            system_access=SystemAccess.WORKSPACE,
            compaction_strategy=CompactionStrategy.CONSERVATIVE,
        ),
        ChatMode.ACT.value: ModeProfile(
            mode=ChatMode.ACT,
            reasoning_effort=ReasoningEffort.MEDIUM,
            system_access=SystemAccess.WORKSPACE,
            compaction_strategy=CompactionStrategy.BALANCED,
        ),
        ChatMode.DEBUG.value: ModeProfile(
            mode=ChatMode.DEBUG,
            reasoning_effort=ReasoningEffort.HIGH,
            system_access=SystemAccess.WORKSPACE,
            debug_level=DebugLevel.DIAGNOSE_PROPOSE,
            compaction_strategy=CompactionStrategy.BALANCED,
            terminal=TerminalCommandPolicy(
                allowed=["git *", "python *", "pytest *", "docker *", "npm *", "pnpm *"],
                denied=["rm -rf *", "sudo *"],
                default=TerminalPermission.ASK,
            ),
        ),
    }


MODE_SYSTEM_INSTRUCTIONS: dict[str, str] = {
    ChatMode.PLAN.value: (
        "Tu es en mode PLAN : comprendre, explorer, analyser, planifier et "
        "identifier les risques avant toute action.  Explore le contexte, "
        "produis une stratégie claire.  Ne modifie rien : ni fichiers, ni "
        "commandes d'écriture — lecture/diagnostic uniquement."
    ),
    ChatMode.ACT.value: (
        "Tu es en mode ACT : appliquer le plan — modifier, créer, exécuter, "
        "tester selon les permissions accordées.  Les actions sensibles "
        "respectent le modèle de sécurité ETHAN : jamais au-delà des "
        "ressources autorisées."
    ),
    ChatMode.DEBUG.value: (
        "Tu es en mode DEBUG : diagnostique et corrige les problèmes.\n"
        "Workflow : collecter le contexte → inspecter l'environnement → "
        "reproduire → diagnostiquer → expliquer la cause racine → proposer "
        "un correctif → appliquer si autorisé → lancer les tests → vérifier.\n"
        "Utilise logs, stack traces, fichiers, Git, terminal, configuration, "
        "services et tests disponibles.  Le diagnostic précède TOUJOURS la "
        "modification."
    ),
}


def mode_system_instructions(mode: ChatMode | str) -> str:
    """Section de prompt système décrivant le comportement du mode."""
    mode_value = mode.value if isinstance(mode, ChatMode) else str(mode)
    return MODE_SYSTEM_INSTRUCTIONS.get(mode_value, "")


@dataclass
class ModePermissions:
    """Permissions effectives d'un mode (matrice lue par le Runtime/pipeline).

    Le pipeline filtre le catalogue d'outils avec ces contraintes : un outil
    de risque HIGH n'est jamais proposé en Plan, et une action destructive
    reste soumise aux permissions Runtime (le mode n'élargit jamais).
    """

    allow_write: bool = False
    allow_execute: bool = False
    max_tool_risk: str = "medium"  # low | medium | high
    destructive_actions: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "allow_write": self.allow_write,
            "allow_execute": self.allow_execute,
            "max_tool_risk": self.max_tool_risk,
            "destructive_actions": self.destructive_actions,
        }


# Matrice de permissions par mode (§6/§7/§8).
MODE_PERMISSIONS: dict[str, dict[str, Any]] = {
    ChatMode.PLAN.value: {
        # Plan : comprendre/analyser/planifier — lecture seule par défaut.
        "allow_write": False,
        "allow_execute": False,
        "max_tool_risk": "low",
        "destructive_actions": False,
    },
    ChatMode.ACT.value: {
        # Act : modifier/créer/exécuter selon permissions Runtime.
        "allow_write": True,
        "allow_execute": True,
        "max_tool_risk": "high",
        "destructive_actions": False,
    },
    ChatMode.DEBUG.value: {
        # Debug : privilégie le diagnostic avant modification — écriture
        # conditionnelle au DebugLevel (voir DEBUG_LEVEL_CONSTRAINTS).
        "allow_write": False,
        "allow_execute": True,
        "max_tool_risk": "medium",
        "destructive_actions": False,
    },
}

DEBUG_LEVEL_CONSTRAINTS: dict[str, dict[str, Any]] = {
    DebugLevel.DIAGNOSE.value: {"allow_write": False, "max_tool_risk": "low"},
    DebugLevel.DIAGNOSE_PROPOSE.value: {"allow_write": False, "max_tool_risk": "medium"},
    DebugLevel.DIAGNOSE_APPLY.value: {"allow_write": True, "max_tool_risk": "medium"},
}


def effective_mode_permissions(
    mode: ChatMode | str,
    debug_level: DebugLevel | str | None = None,
) -> ModePermissions:
    """Permissions effectives d'un mode, contraintes par le niveau Debug."""
    mode_value = mode.value if isinstance(mode, ChatMode) else str(mode)
    perms = ModePermissions(
        **dict(MODE_PERMISSIONS.get(mode_value, MODE_PERMISSIONS[ChatMode.ACT.value]))
    )
    if mode_value == ChatMode.DEBUG.value and debug_level is not None:
        level_value = debug_level.value if isinstance(debug_level, DebugLevel) else str(debug_level)
        constraints = DEBUG_LEVEL_CONSTRAINTS.get(level_value)
        if constraints:
            perms.allow_write = constraints["allow_write"]
            perms.max_tool_risk = constraints["max_tool_risk"]
    return perms


__all__ = [
    "AutoApproval",
    "ChatMode",
    "CompactionStrategy",
    "DebugLevel",
    "ModePermissions",
    "ModeProfile",
    "REASONING_CAPABILITY",
    "ReasoningEffort",
    "SystemAccess",
    "TerminalCommandPolicy",
    "TerminalPermission",
    "default_mode_profiles",
    "effective_mode_permissions",
    "mode_system_instructions",
    "resolve_reasoning",
]
