"""Règles par défaut du Policy Engine.

Règles minimales CORE (niveau 1) et SECURITY (niveau 2) illustrant la
hiérarchie de la Phase 03. Elles restent délibérément conservatrices :
ETHAN ne reçoit ici **aucun accès système plus large** — les actions
sensibles sont refusées par défaut ou soumises à confirmation humaine.

Ces règles sont chargées à l'instanciation du moteur ; aucune donnée
utilisateur, aucun prompt, aucune sortie de LLM ne peut les modifier.
"""

from __future__ import annotations

from core.security.policy.types import (
    ActionCategory,
    Policy,
    PolicyEffect,
    PolicyLevel,
)


def default_rules() -> list[Policy]:
    """Retourne les règles par défaut (CORE + SECURITY).

    Le résultat est une nouvelle liste à chaque appel : les règles sont
    immuables et ne doivent jamais être partagées par référence mutable.
    """
    return [
        # ── CORE (niveau 1) — inviolables ──────────────────────────────
        Policy(
            id="core.fs.write.system",
            level=PolicyLevel.CORE,
            category=ActionCategory.FILESYSTEM,
            action="write",
            resource="/etc/**",
            effect=PolicyEffect.DENY,
            reason="Ecriture interdite dans les zones systeme de l'hote (CR-3/CR-4).",
        ),
        Policy(
            id="core.shell.destructive",
            level=PolicyLevel.CORE,
            category=ActionCategory.SHELL,
            action="execute",
            resource="rm -rf*",
            effect=PolicyEffect.DENY,
            reason="Commande destructive interdite par la Constitution (CR-1/CR-5).",
        ),
        Policy(
            id="core.net.transmission",
            level=PolicyLevel.CORE,
            category=ActionCategory.EXTERNAL_TRANSMISSION,
            action="send",
            resource="*",
            effect=PolicyEffect.DENY,
            reason="Transmission externe de donnees locales interdite (CR-4).",
        ),
        Policy(
            id="core.config.constitution",
            level=PolicyLevel.CORE,
            category=ActionCategory.CONFIGURATION,
            action="write",
            resource="constitution:*",
            effect=PolicyEffect.DENY,
            reason="Les regles de la Constitution sont immuables a l'execution (PR-4).",
        ),
        # ── SECURITY (niveau 2) — deny par défaut / confirmation ───────
        Policy(
            id="security.fs.delete",
            level=PolicyLevel.SECURITY,
            category=ActionCategory.FILESYSTEM,
            action="delete",
            resource="*",
            effect=PolicyEffect.REQUIRE_CONFIRMATION,
            reason="Suppression de fichier : confirmation humaine requise (PR-7).",
        ),
        Policy(
            id="security.docker.execute",
            level=PolicyLevel.SECURITY,
            category=ActionCategory.DOCKER,
            action="execute",
            resource="*",
            effect=PolicyEffect.DENY,
            reason="Execution Docker refusee par defaut (aucun acces systeme elargi).",
        ),
        Policy(
            id="security.network.write",
            level=PolicyLevel.SECURITY,
            category=ActionCategory.NETWORK,
            action="write",
            resource="*",
            effect=PolicyEffect.REQUIRE_CONFIRMATION,
            reason="Transfert de donnees externe : confirmation requise (CR-4).",
        ),
        Policy(
            id="security.mcp.execute",
            level=PolicyLevel.SECURITY,
            category=ActionCategory.MCP,
            action="execute",
            resource="*",
            effect=PolicyEffect.REQUIRE_CONFIRMATION,
            reason="Execution d'un outil MCP : source externe non fiable (CR-5).",
        ),
        Policy(
            id="security.config.write",
            level=PolicyLevel.SECURITY,
            category=ActionCategory.CONFIGURATION,
            action="write",
            resource="*",
            effect=PolicyEffect.REQUIRE_CONFIRMATION,
            reason="Modification de configuration : confirmation requise (PR-7).",
        ),
        # ── Permissions de base (lecture sans effet de bord) ───────────
        Policy(
            id="base.fs.read.workspace",
            level=PolicyLevel.SECURITY,
            category=ActionCategory.FILESYSTEM,
            action="read",
            resource="/workspace/**",
            effect=PolicyEffect.ALLOW,
            reason="Lecture autorisee dans l'espace de travail de l'utilisateur.",
        ),
        Policy(
            id="base.memory.read",
            level=PolicyLevel.SECURITY,
            category=ActionCategory.MEMORY,
            action="read",
            resource="user:*",
            effect=PolicyEffect.ALLOW,
            reason="Lecture de la memoire utilisateur autorisee.",
        ),
    ]
