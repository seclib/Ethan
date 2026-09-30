"""Exécution isolée des serveurs MCP stdio (Tier 3 — Docker).

CTO Security Architecture Review — Phase 1.3, composant Top 10 #6
(``core/tools/sandbox_runner.py``) ; Red Team Attaques 12/13 + règle non
négociable #4 (« aucun code externe sur l'hôte »).

Un serveur MCP stdio exécute du code tiers. Toute commande stdio est donc
**wrappée dans un conteneur Docker éphémère durci** avant d'être lancée par
le SDK ``mcp`` — sauf opt-out explicite de l'opérateur.

Modes (env ``ETHAN_MCP_STDIO_SANDBOX``) :

- ``docker`` (défaut) : **fail-closed** — sans CLI Docker ou sans image
  configurée, la connexion stdio est REFUSÉE (jamais de repli silencieux).
- ``off`` : exécution hôte directe — opt-out explicite et tracé par un
  warning (tests d'intégration, environnements sans Docker).

Configuration :

- ``ETHAN_MCP_STDIO_SANDBOX_IMAGE``    : image du serveur (OBLIGATOIRE en
  mode docker — l'image doit fournir la commande stdio).
- ``ETHAN_MCP_STDIO_SANDBOX_NETWORK``  : réseau du conteneur (défaut
  ``none`` — pas de réseau sans décision explicite).

Drapeaux du conteneur (IMMUABLES — opérateur ne peut pas les alléger) :
``--cap-drop=ALL``, ``--security-opt=no-new-privileges:true``,
``--pids-limit=64``, ``--read-only`` + ``--tmpfs /tmp``. Les chemins
absolus existants (commande + arguments fichier) sont montés en lecture
seule à leur chemin (``-v path:path:ro``).
"""

from __future__ import annotations

import logging
import os
import re
import shutil

logger = logging.getLogger(__name__)

ENV_SANDBOX = "ETHAN_MCP_STDIO_SANDBOX"
ENV_IMAGE = "ETHAN_MCP_STDIO_SANDBOX_IMAGE"
ENV_NETWORK = "ETHAN_MCP_STDIO_SANDBOX_NETWORK"

MODE_DOCKER = "docker"
MODE_OFF = "off"

DEFAULT_NETWORK = "none"

_DOCKER_ALIASES = frozenset({"docker", "on", "1", "true", "yes", "container"})
_OFF_ALIASES = frozenset({"off", "host", "0", "false", "no"})
_NETWORK_RE = re.compile(r"^[A-Za-z0-9_.-]+$")

# Drapeaux immuables du conteneur (Red Team Attaques 12/13 — F4).
CONTAINER_FLAGS: tuple[str, ...] = (
    "--cap-drop=ALL",
    "--security-opt=no-new-privileges:true",
    "--pids-limit=64",
    "--read-only",
    "--tmpfs",
    "/tmp:rw,size=64m",
)


class SandboxError(RuntimeError):
    """Sandboxing stdio indisponible → connexion REFUSÉE (fail-closed)."""


def sandbox_mode() -> str:
    """Mode effectif (``docker`` par défaut) — invalide ⇒ ``SandboxError``."""
    raw = os.getenv(ENV_SANDBOX, MODE_DOCKER).strip().lower()
    if raw == "" or raw in _DOCKER_ALIASES:
        return MODE_DOCKER
    if raw in _OFF_ALIASES:
        return MODE_OFF
    raise SandboxError(f"{ENV_SANDBOX} invalide : {raw!r} (attendu : docker | off)")


def _mountable_paths(command: str, args: list[str]) -> list[str]:
    """Chemins absolus existants (commande + args fichier) à monter en ro."""
    seen: list[str] = []
    for path in (command, *(str(a) for a in args)):
        if os.path.isabs(path) and os.path.exists(path) and path not in seen:
            seen.append(path)
    return seen


def wrap_stdio_command(
    command: str,
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    cwd: str | None = None,
) -> tuple[str, list[str]]:
    """Wrappe une commande stdio dans le sandbox Docker durci (Tier 3).

    Args:
        command: commande absolue (déjà validée par ``server_policy``).
        args: arguments (liste de chaînes, jamais de shell).
        env: variables d'environnement demandées — REFUSÉES en mode docker
            (un secret ne part jamais dans un conteneur par accident).
        cwd: répertoire de travail — REFUSÉ en mode docker (l'image pilote).

    Returns:
        ``(command, args)`` à passer à ``StdioServerParameters``.

    Raises:
        SandboxError: si le sandbox est requis mais indisponible
            (fail-closed — jamais de repli silencieux sur l'hôte).
    """
    if sandbox_mode() == MODE_OFF:
        logger.warning(
            "MCP stdio sandbox désactivé (%s=off) : %s s'exécute sur l'hôte",
            ENV_SANDBOX,
            command,
        )
        return command, list(args)

    if env:
        raise SandboxError(
            "env stdio non supporté en mode sandbox docker "
            "(refusé plutôt que silencieusement ignoré)"
        )
    if cwd:
        raise SandboxError(
            "cwd stdio non supporté en mode sandbox docker "
            "(refusé plutôt que silencieusement ignoré)"
        )

    docker = shutil.which("docker")
    if not docker:
        raise SandboxError(
            f"CLI Docker introuvable : sandbox stdio requis (opt-out explicite : {ENV_SANDBOX}=off)"
        )

    image = os.getenv(ENV_IMAGE, "").strip()
    if not image:
        raise SandboxError(
            f"{ENV_IMAGE} manquante : image du sandbox stdio obligatoire "
            f"(opt-out explicite : {ENV_SANDBOX}=off)"
        )

    network = os.getenv(ENV_NETWORK, DEFAULT_NETWORK).strip() or DEFAULT_NETWORK
    if not _NETWORK_RE.match(network):
        raise SandboxError(f"{ENV_NETWORK} invalide : {network!r}")

    argv: list[str] = [
        docker,
        "run",
        "--rm",
        "-i",
        *CONTAINER_FLAGS,
        f"--network={network}",
    ]
    for path in _mountable_paths(command, args):
        argv += ["-v", f"{path}:{path}:ro"]
    argv += [image, command, *(str(a) for a in args)]

    logger.info(
        "MCP stdio sandboxed (docker) : image=%s réseau=%s mounts=%d",
        image,
        network,
        len(_mountable_paths(command, args)),
    )
    return argv[0], argv[1:]


__all__ = [
    "CONTAINER_FLAGS",
    "DEFAULT_NETWORK",
    "ENV_IMAGE",
    "ENV_NETWORK",
    "ENV_SANDBOX",
    "MODE_DOCKER",
    "MODE_OFF",
    "SandboxError",
    "sandbox_mode",
    "wrap_stdio_command",
]
