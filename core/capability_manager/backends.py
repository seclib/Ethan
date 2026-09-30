"""Backends d'installation — abstraction des mécanismes réels.

Règle de sécurité (section 10) : les backends ne construisent une argv
qu'à partir de la spec développeur (actions déclaratives figées) et de
paramètres typés. Aucune chaîne provenant de l'input utilisateur ne rejoint
une commande. `validate_install_actions` est la barrière structurelle.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from core.capability_manager.types import CapabilitySpec

logger = logging.getLogger(__name__)

# Actions déclaratives autorisées par backend (allowlist stricte).
_DOCKER_ACTIONS = {
    "check_docker",  # vérifie que Docker est fonctionnel (jamais l'installer)
    "pull",  # {"image": str}
    "create_volume",  # {"volume": str}
    "ensure_network",  # {"network": str}
    "run",  # {"name","image","ports","env","volume","network","command"}
    "start",  # {"name"}
    "stop",  # {"name"}
    "remove",  # {"name", "keep_data": bool, "data_to_delete": [...]}
}
_PY_ACTIONS = {"pip_install", "pip_uninstall", "verify_import"}
_NODE_ACTIONS = {"npm_install", "npm_uninstall", "verify_binary"}
_EXE_ACTIONS = {"verify_path", "note"}
_BUILTIN_ACTIONS: set[str] = set()  # composant intégré : aucune action système

# pip du meme interpreteur que le Core (jamais un pip arbitraire du PATH)
_PIP = [__import__("sys").executable, "-m", "pip"]


def validate_install_actions(spec: CapabilitySpec) -> None:
    """Barrière structurelle anti-injection : rejette toute action inconnue.

    Appelée à l'enregistrement d'une capability : une spec non conforme est
    refusée avant même de pouvoir être installée.
    """
    action_sets = {
        "docker": _DOCKER_ACTIONS,
        "python_package": _PY_ACTIONS,
        "node_package": _NODE_ACTIONS,
        "executable": _EXE_ACTIONS,
        "builtin": _BUILTIN_ACTIONS,
    }
    allowed = action_sets[spec.backend]
    for phase, actions in (
        ("install", spec.install_actions),
        ("uninstall", spec.uninstall_actions),
        ("start", spec.start_actions),
        ("stop", spec.stop_actions),
    ):
        for i, action in enumerate(actions):
            if not isinstance(action, dict) or "action" not in action:
                raise ValueError(f"{phase}[{i}]: action dict requise")
            if action["action"] not in allowed:
                raise ValueError(
                    f"{phase}[{i}]: action {action['action']!r} interdite "
                    f"pour le backend {spec.backend!r}"
                )


def npm_install_command(npm: str, prefix: str, packages: Any) -> list[str]:
    """Commande npm d'installation durcie (Red Team Attaque 18).

    ``--ignore-scripts`` interdit l'exécution automatique des hooks
    ``postinstall`` d'un paquet tiers (injection de code au moment de
    l'installation). Source unique : testée dans
    ``tests/security/test_runtime_isolation.py``.
    """
    return [
        npm,
        "install",
        "--global",
        "--prefix",
        str(prefix),
        "--no-audit",
        "--no-fund",
        "--ignore-scripts",
        *map(str, packages),
    ]


async def _run(argv: list[str], timeout: float = 300.0) -> tuple[bool, str]:
    """Exécute une argv figée (jamais shell=True) avec timeout."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except FileNotFoundError:
        return False, f"executable introuvable: {argv[0]}"
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return False, f"timeout apres {timeout:.0f}s: {' '.join(argv[:3])}…"
    ok = proc.returncode == 0
    text = (out or b"").decode(errors="replace")[-800:]
    return ok, text


def _subst(value: Any, config: dict[str, Any]) -> Any:
    """Substitue {config.<field>} dans les valeurs déclaratives de la spec.

    La substitution s'applique à des champs TYPÉS validés en amont par le
    manager (validate_config) : l'utilisateur ne fournit que des valeurs,
    jamais des fragments de commande.
    """
    if isinstance(value, str) and value.startswith("{config.") and value.endswith("}"):
        key = value[8:-1]
        return config.get(key, value)
    if isinstance(value, list):
        return [_subst(v, config) for v in value]
    if isinstance(value, dict):
        return {k: _subst(v, config) for k, v in value.items()}
    return value


# ── paquets Node (npm) ──────────────────────────────────────────────────────
# Préfixe GLOBAL npm géré par ETHAN : jamais /usr/lib/node_modules (préfixe
# système partagé), donc aucun sudo. npm est résolu côté Core (shutil.which),
# jamais fourni par l'utilisateur ; les paquets viennent de la spec.
def node_prefix() -> Path:
    """Racine des paquets Node installés par ETHAN."""
    return Path.home() / ".local" / "share" / "ethan" / "node"


def node_binary_path(binary: str) -> Path:
    """Chemin du binaire exposé par un paquet Node installé par ETHAN."""
    return node_prefix() / "bin" / binary


def node_binary_ok(binary: str) -> bool:
    """Vérification déterministe et réelle : présent ET exécutable."""
    path = node_binary_path(binary)
    return path.is_file() and os.access(path, os.X_OK)


def _unpinned(package: str) -> str:
    """Retire la version épinglée d'un nom de paquet npm (rollback).

    "@scope/pkg@1.2.3" -> "@scope/pkg" ; "pkg" -> "pkg".
    """
    name = package.rpartition("@")[0]
    return name or package


def _sha256_hex(value: str) -> str | None:
    """Normalise un digest/checksum en hex sha256, sinon ``None``.

    Accepte ``sha256:<hex>`` et ``repo/image@sha256:<hex>``. Un format non
    comparable (base64 npm, autre algorithme) renvoie ``None`` : l'appelant
    échoue explicitement plutôt que de comparer des valeurs non comparables.
    """
    text = (value or "").strip().lower()
    if "@" in text:
        text = text.rsplit("@", 1)[1]
    if text.startswith("sha256:"):
        text = text[7:]
    return text if re.fullmatch(r"[0-9a-f]{64}", text) else None


class InstallBackend(ABC):
    """Abstraction d'installation — masque le mécanisme au reste du Core."""

    name: str = "abstract"

    @abstractmethod
    async def check_prerequisites(self, spec: CapabilitySpec) -> tuple[bool, str]:
        """Vérifie les prérequis SANS rien installer (ex: Docker présent)."""

    @abstractmethod
    async def execute(
        self, spec: CapabilitySpec, phase: str, config: dict[str, Any]
    ) -> tuple[bool, str]:
        """Exécute une phase déclarative ("install"/"uninstall"/"start"/"stop")."""

    @abstractmethod
    async def plan(self, spec: CapabilitySpec, phase: str) -> list[tuple[str, str]]:
        """Décrive les opérations (description, kind) sans les exécuter."""

    @abstractmethod
    async def rollback(self, spec: CapabilitySpec, phase: str) -> tuple[bool, str]:
        """Retour à l'état précédent après un échec (quand possible)."""

    async def logs(
        self, spec: CapabilitySpec, config: dict[str, Any], tail: int
    ) -> tuple[bool, str]:
        """Logs d'exécution du composant — quand le backend en produit.

        Défaut honnête : les backends sans processus persistant géré par
        ETHAN (``builtin``, ``executable``, ``python_package``,
        ``node_package``) n'ont pas de logs à montrer — jamais de faux
        contenu ni de lecture arbitraire de fichiers système.
        """
        return False, (
            f"aucun log persistant pour le backend {self.name!r} "
            "(composant sans processus permanent géré par ETHAN)"
        )


class DockerBackend(InstallBackend):
    """Gère les composants Docker optionnels SANS dupliquer la logique.

    Ne jamais installer Docker lui-même : `check_prerequisites` échoue avec
    un message explicite si Docker est absent (à l'utilisateur de
    l'installer). Toutes les argv sont construites depuis la spec.
    """

    name = "docker"
    binary = "docker"  # point de patch pour les tests

    async def check_prerequisites(self, spec: CapabilitySpec) -> tuple[bool, str]:
        if shutil.which(self.binary) is None:
            return (
                False,
                "Docker est requis mais absent. Installez Docker manuellement "
                "(ETHAN n'installe jamais Docker lui-même).",
            )
        ok, out = await _run([self.binary, "info"], timeout=20.0)
        if not ok:
            return False, f"Docker injoignable: {out[:200]}"
        return True, "Docker operationnel"

    async def execute(
        self, spec: CapabilitySpec, phase: str, config: dict[str, Any]
    ) -> tuple[bool, str]:
        actions = {
            "install": spec.install_actions,
            "uninstall": spec.uninstall_actions,
            "start": spec.start_actions,
            "stop": spec.stop_actions,
        }[phase]
        for action in actions:
            kind = action["action"]
            if kind == "check_docker":
                ok, msg = await self.check_prerequisites(spec)
                if not ok:
                    return False, msg
                continue
            ok, out = await self._exec_action(kind, action, config)
            if not ok:
                return False, f"{kind} a echoue: {out}"
            if kind == "pull":
                # Intégrité : un checksum déclaré est vérifié sur l'image
                # réellement tirée (champ vide = non déclaré, jamais « conforme »).
                ok, msg = await self._verify_image_digest(action.get("image"), spec, config)
                if not ok:
                    return False, msg
        return True, "ok"

    async def _exec_action(
        self, kind: str, action: dict[str, Any], config: dict[str, Any]
    ) -> tuple[bool, str]:
        d = self.binary
        if kind == "pull":
            return await _run([d, "pull", str(action["image"])])
        if kind == "create_volume":
            ok, out = await _run([d, "volume", "create", str(action["volume"])])
            if not ok and "already exists" in out:
                return True, "volume deja present (idempotent)"
            return ok, out
        if kind == "ensure_network":
            ok, out = await _run([d, "network", "inspect", str(action["network"])])
            if not ok:
                return await _run([d, "network", "create", str(action["network"])])
            return True, "reseau deja present (idempotent)"
        if kind == "run":
            return await self._run_container(action, config)
        if kind == "start":
            return await _run([d, "start", str(action["name"])])
        if kind == "stop":
            return await _run([d, "stop", str(action["name"])])
        if kind == "remove":
            return await self._remove(action)
        return False, f"action inconnue: {kind}"  # pragma: no cover

    async def _run_container(
        self, action: dict[str, Any], config: dict[str, Any]
    ) -> tuple[bool, str]:
        d = self.binary
        name = str(action["name"])
        ok, _ = await _run([d, "container", "inspect", name])
        if ok:
            return True, "container deja present (idempotent)"
        argv = [d, "run", "-d", "--name", name, "--restart", "unless-stopped"]
        for port in action.get("ports", []):
            argv += ["-p", str(_subst(port, config))]
        for env in action.get("env", []):
            argv += ["-e", str(_subst(env, config))]
        if action.get("volume"):
            argv += ["-v", str(_subst(action["volume"], config))]
        if action.get("network"):
            argv += ["--network", str(action["network"])]
        for extra in action.get("flags", []):
            argv += [str(extra)]
        if action.get("command"):
            argv += [str(c) for c in action["command"]]
        argv.append(str(action["image"]))
        return await _run(argv)

    async def _remove(self, action: dict[str, Any]) -> tuple[bool, str]:
        """Distinction stricte : remove container vs suppression des données."""
        d = self.binary
        ok, out = await _run([d, "rm", "-f", str(action["name"])])
        if not ok:
            if "No such container" in out:
                return True, "container deja absent (idempotent)"
            return False, out
        if action.get("keep_data") is False:
            for resource in action.get("data_to_delete", []):
                if resource.get("kind") == "volume":
                    ok2, out2 = await _run([d, "volume", "rm", str(resource["name"])])
                    if not ok2 and "No such volume" not in out2:
                        return False, f"suppression donnees: {out2}"
            return True, "container et donnees supprimes"
        return True, "container supprime, donnees preservees"

    async def plan(self, spec: CapabilitySpec, phase: str) -> list[tuple[str, str]]:
        """Decrit les operations install/uninstall (description, kind)."""
        actions = {
            "install": spec.install_actions,
            "uninstall": spec.uninstall_actions,
        }[phase]
        steps: list[tuple[str, str]] = []
        for action in actions:
            kind = action["action"]
            if kind == "pull":
                steps.append((f"Telecharger l'image {action['image']}", "install"))
            elif kind == "create_volume":
                steps.append((f"Creer/verifier le volume {action['volume']}", "install"))
            elif kind == "ensure_network":
                steps.append((f"Creer/verifier le reseau {action['network']}", "install"))
            elif kind == "run":
                steps.append((f"Creer et demarrer le container {action['name']}", "install"))
            elif kind == "start":
                steps.append((f"Demarrer le container {action['name']}", "start"))
            elif kind == "stop":
                steps.append((f"Arreter le container {action['name']}", "stop"))
            elif kind == "remove":
                keep = action.get("keep_data", True)
                label = (
                    f"Supprimer le container {action['name']} (donnees preservees)"
                    if keep
                    else f"Supprimer le container {action['name']} ET ses donnees"
                )
                steps.append((label, "remove" if keep else "data"))
        return steps

    async def rollback(self, spec: CapabilitySpec, phase: str) -> tuple[bool, str]:
        if phase != "install":
            return True, "rien a faire"
        # Best-effort : retire les containers crees par l'install ratee.
        for action in spec.install_actions:
            if action.get("action") == "run":
                await _run([self.binary, "rm", "-f", str(action["name"])])
        return True, "rollback best-effort effectue"

    async def _verify_image_digest(
        self, image: Any, spec: CapabilitySpec, config: dict[str, Any]
    ) -> tuple[bool, str]:
        """Vérifie l'intégrité de l'image quand un digest est DÉCLARÉ.

        Sans `provenance.checksum`, aucune vérification n'est inventée (le
        champ vide signifie « non déclaré », pas « conforme »). Avec un
        digest déclaré, l'installation échoue si le digest réel de l'image
        tirée ne correspond pas : ETHAN n'installe jamais un artefact non
        conforme ni ne compare des formats non comparables.
        """
        declared = (spec.provenance.checksum or "").strip()
        if not declared:
            return True, "aucun digest declare"
        expected = _sha256_hex(declared)
        if expected is None:
            return False, (
                "checksum declare non verifiable par le backend docker "
                f"(format sha256 attendu): {declared!r}"
            )
        ref = str(_subst(image, config))
        ok, out = await _run(
            [
                self.binary,
                "image",
                "inspect",
                "--format",
                "{{index .RepoDigests 0}}",
                ref,
            ],
            timeout=30.0,
        )
        if not ok:
            return False, f"digest introuvable pour {ref!r}: verification impossible"
        actual = _sha256_hex(out.strip())
        if actual != expected:
            return False, (
                f"digest non conforme pour {ref!r}: attendu sha256:{expected}, "
                f"obtenu {out.strip()[:120]!r}"
            )
        return True, "digest d'image verifie"

    def _container_name(self, spec: CapabilitySpec) -> str | None:
        """Nom du container déclaré par la spec (jamais un input utilisateur)."""
        for action in (*spec.install_actions, *spec.start_actions, *spec.stop_actions):
            if action.get("action") in ("run", "start", "stop") and action.get("name"):
                return str(action["name"])
        return None

    async def logs(
        self, spec: CapabilitySpec, config: dict[str, Any], tail: int
    ) -> tuple[bool, str]:
        """Logs réels du container déclaré (`docker logs --tail N`)."""
        name = self._container_name(spec)
        if name is None:
            return False, "aucun container declare dans la spec"
        return await _run([self.binary, "logs", "--tail", str(tail), name], timeout=30.0)


class PythonPackageBackend(InstallBackend):
    """Installe des packages Python (pip) — mecanisme masque au Core."""

    name = "python_package"

    async def check_prerequisites(self, spec: CapabilitySpec) -> tuple[bool, str]:
        return True, "python disponible"

    async def execute(
        self, spec: CapabilitySpec, phase: str, config: dict[str, Any]
    ) -> tuple[bool, str]:
        actions = {
            "install": spec.install_actions,
            "uninstall": spec.uninstall_actions,
            "start": spec.start_actions,
            "stop": spec.stop_actions,
        }[phase]
        for action in actions:
            kind = action["action"]
            if kind == "pip_install":
                ok, out = await _run([_PIP, "install", "--no-input", *map(str, action["packages"])])
                if not ok:
                    return False, f"pip install a echoue: {out}"
            elif kind == "pip_uninstall":
                ok, out = await _run([_PIP, "uninstall", "-y", *map(str, action["packages"])])
                if not ok:
                    return False, f"pip uninstall a echoue: {out}"
            elif kind == "verify_import":
                code = "import importlib; importlib.import_module(" + repr(action["module"]) + ")"
                ok, out = await _run([__import__("sys").executable, "-c", code])
                if not ok:
                    return False, f"module {action['module']} indisponible: {out}"
        return True, "ok"

    async def plan(self, spec: CapabilitySpec, phase: str) -> list[tuple[str, str]]:
        if phase == "install":
            pkgs = [
                ",".join(a["packages"])
                for a in spec.install_actions
                if a.get("action") == "pip_install"
            ]
            if pkgs:
                return [(f"Installer les packages Python: {pkgs[0]}", "install")]
        if phase == "uninstall":
            pkgs = [
                ",".join(a["packages"])
                for a in spec.uninstall_actions
                if a.get("action") == "pip_uninstall"
            ]
            if pkgs:
                return [(f"Desinstaller les packages Python: {pkgs[0]}", "uninstall")]
        return []

    async def rollback(self, spec: CapabilitySpec, phase: str) -> tuple[bool, str]:
        if phase == "install":
            for action in spec.install_actions:
                if action.get("action") == "pip_install":
                    await _run([_PIP, "uninstall", "-y", *map(str, action["packages"])])
            return True, "rollback pip effectue"
        return True, "rien a faire"


class NodePackageBackend(InstallBackend):
    """Installe des packages Node (npm) dans un préfixe géré par le Core.

    Même discipline que `python_package` : npm est résolu côté Core
    (`shutil.which`), jamais un chemin fourni par l'utilisateur ; les paquets
    et versions viennent de la spec ; l'installation reste confinée dans
    `~/.local/share/ethan/node` (aucun sudo, aucun préfixe système).
    """

    name = "node_package"
    binary = "npm"  # point de patch pour les tests

    def _npm(self) -> str | None:
        """npm du système, résolu côté Core — jamais depuis un input."""
        return shutil.which(self.binary)

    async def check_prerequisites(self, spec: CapabilitySpec) -> tuple[bool, str]:
        npm = self._npm()
        if npm is None:
            return (
                False,
                "Node.js/npm est requis mais absent. Installez Node.js "
                "manuellement (ETHAN n'installe jamais Node lui-même).",
            )
        return True, f"npm opérationnel: {npm}"

    async def execute(
        self, spec: CapabilitySpec, phase: str, config: dict[str, Any]
    ) -> tuple[bool, str]:
        actions = {
            "install": spec.install_actions,
            "uninstall": spec.uninstall_actions,
            "start": spec.start_actions,
            "stop": spec.stop_actions,
        }[phase]
        for action in actions:
            kind = action["action"]
            if kind == "npm_install":
                npm = self._npm()
                if npm is None:
                    return False, "npm introuvable (requis pour installer un paquet Node)"
                ok, out = await _run(
                    npm_install_command(
                        npm,
                        str(node_prefix()),
                        action["packages"],
                    )
                )
                if not ok:
                    return False, f"npm install a echoue: {out}"
            elif kind == "npm_uninstall":
                npm = self._npm()
                if npm is None:
                    return False, "npm introuvable (requis pour desinstaller un paquet Node)"
                ok, out = await _run(
                    [
                        npm,
                        "uninstall",
                        "--global",
                        "--prefix",
                        str(node_prefix()),
                        *map(str, action["packages"]),
                    ]
                )
                if not ok:
                    return False, f"npm uninstall a echoue: {out}"
            elif kind == "verify_binary":
                binary = str(action["binary"])
                if not node_binary_ok(binary):
                    return False, (
                        f"binaire {binary!r} absent ou non executable: {node_binary_path(binary)}"
                    )
        return True, "ok"

    async def plan(self, spec: CapabilitySpec, phase: str) -> list[tuple[str, str]]:
        if phase == "install":
            pkgs = [
                ",".join(a["packages"])
                for a in spec.install_actions
                if a.get("action") == "npm_install"
            ]
            if pkgs:
                return [(f"Installer les packages Node: {pkgs[0]}", "install")]
        if phase == "uninstall":
            pkgs = [
                ",".join(a["packages"])
                for a in spec.uninstall_actions
                if a.get("action") == "npm_uninstall"
            ]
            if pkgs:
                return [(f"Desinstaller les packages Node: {pkgs[0]}", "uninstall")]
        return []

    async def rollback(self, spec: CapabilitySpec, phase: str) -> tuple[bool, str]:
        if phase != "install":
            return True, "rien a faire"
        npm = self._npm()
        names = [
            _unpinned(str(p))
            for a in spec.install_actions
            if a.get("action") == "npm_install"
            for p in a.get("packages", [])
        ]
        if npm is None or not names:
            return False, "rollback npm impossible (npm absent ou aucun package)"
        await _run(
            [
                npm,
                "uninstall",
                "--global",
                "--prefix",
                str(node_prefix()),
                *names,
            ]
        )
        return True, "rollback npm effectue"


class ExecutableBackend(InstallBackend):
    """Capability fournie par un executable local existant (pas d'install
    reelle : verification de presence uniquement)."""

    name = "executable"

    async def check_prerequisites(self, spec: CapabilitySpec) -> tuple[bool, str]:
        return True, "ok"

    async def execute(
        self, spec: CapabilitySpec, phase: str, config: dict[str, Any]
    ) -> tuple[bool, str]:
        for action in spec.install_actions:
            if action.get("action") == "verify_path":
                exe = action["executable"]
                if shutil.which(exe) is None:
                    return False, f"executable {exe!r} introuvable dans le PATH"
        return True, "ok"

    async def plan(self, spec: CapabilitySpec, phase: str) -> list[tuple[str, str]]:
        return [("Verifier la presence de l'executable local", "verify")]

    async def rollback(self, spec: CapabilitySpec, phase: str) -> tuple[bool, str]:
        return True, "rien a faire"


class BuiltinBackend(InstallBackend):
    """Composant intégré au process Core — rien à installer.

    Le backend `builtin` couvre les capacités toujours présentes (ex. le
    backend vectoriel "Memory" du moteur RAG) : installation/désinstallation
    sont des no-ops, le support est intrinsèque, la santé est vérifiée par le
    HealthChecker (paliers réels, pas un simple "✓ installé").
    """

    name = "builtin"

    async def check_prerequisites(self, spec: CapabilitySpec) -> tuple[bool, str]:
        return True, "intégré au Core — aucune dépendance"

    async def execute(
        self, spec: CapabilitySpec, phase: str, config: dict[str, Any]
    ) -> tuple[bool, str]:
        # install/uninstall/start/stop : rien à faire, toujours ok.
        return True, f"{phase} : intégré (no-op)"

    async def plan(self, spec: CapabilitySpec, phase: str) -> list[tuple[str, str]]:
        return [(f"Composant intégré au Core — {phase} sans opération", "verify")]

    async def rollback(self, spec: CapabilitySpec, phase: str) -> tuple[bool, str]:
        return True, "rien à faire"


_BACKENDS: dict[str, InstallBackend] = {}


def get_backend(name: str) -> InstallBackend:
    """Retourne le backend demande (instanciation paresseuse, testable)."""
    if name not in _BACKENDS:
        if name == "docker":
            _BACKENDS[name] = DockerBackend()
        elif name == "python_package":
            _BACKENDS[name] = PythonPackageBackend()
        elif name == "node_package":
            _BACKENDS[name] = NodePackageBackend()
        elif name == "executable":
            _BACKENDS[name] = ExecutableBackend()
        elif name == "builtin":
            _BACKENDS[name] = BuiltinBackend()
        else:
            raise ValueError(f"backend inconnu: {name!r}")
    return _BACKENDS[name]
