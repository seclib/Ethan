"""SkillLab — Sandbox Docker pour tester les plugins/skills candidats.

Crée un conteneur Docker temporaire, exécute le skill candidat,
valide le résultat, et nettoie. Permet de tester un skill en isolation
avant de l'installer sur le système.

Inspiré du SkillLab de Jarvis-OS, adapté pour l'architecture Ethan :
- Utilise le Docker SDK (déjà disponible dans le projet)
- Publie les résultats sur l'EventBus
- Supporte les conteneurs éphémères avec nettoyage automatique
"""

from __future__ import annotations

import json
import logging
import re
import tempfile
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

# Politique des dépendances du Skill Lab : seuls des noms de paquets
# PEP 508 simples (nom, extras, contrainte de version) sont acceptés —
# aucun espace ni métacaractère shell.  Les requirements sont ensuite passés
# en arguments positionnels du shell, jamais concaténés dans la commande
# exécutée.
_REQUIREMENT_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*"  # nom du paquet (PEP 508 simplifié)
    r"(\[[A-Za-z0-9_,.-]+\])?"  # extras optionnels (ex. django[argon2])
    r"([<>=!~]=?[A-Za-z0-9.*+!<>~_.,-]+)?"  # contrainte de version optionnelle
    r"$"
)

# Caractères autorisés dans un nom de conteneur Docker dérivé de l'entrée.
_CONTAINER_NAME_UNSAFE_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def _validate_requirements(requirements: list[str]) -> list[str]:
    """Normalise et valide les dépendances pip du sandbox (fail-closed).

    Raises:
        ValueError: si une entrée n'est pas un requirement PEP 508 simple
            (protection contre l'injection de commandes via ``sh -c``).
    """
    cleaned: list[str] = []
    for requirement in requirements:
        candidate = str(requirement).strip()
        if not candidate or not _REQUIREMENT_RE.match(candidate):
            raise ValueError(
                f"Requirement refusé par la politique Skill Lab : {requirement!r} "
                "(nom de paquet PEP 508 simple attendu)"
            )
        cleaned.append(candidate)
    return cleaned


def _safe_container_name(skill_name: str) -> str:
    """Nom de conteneur Docker sûr — jamais dérivé brut de l'entrée."""
    slug = _CONTAINER_NAME_UNSAFE_RE.sub("-", str(skill_name)).strip("-.") or "skill"
    return f"ethan-lab-{slug[:40]}-{uuid4().hex[:6]}"


class LabStatus(StrEnum):
    """Statut d'un test SkillLab."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    CANCELLED = "cancelled"


class LabResult:
    """Résultat d'un test SkillLab."""

    def __init__(
        self,
        skill_name: str,
        status: LabStatus = LabStatus.PENDING,
        passed: bool = False,
        output: str = "",
        error: str = "",
        duration_ms: float = 0.0,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.id = f"lab_{uuid4().hex[:10]}"
        self.skill_name = skill_name
        self.status = status
        self.passed = passed
        self.output = output
        self.error = error
        self.duration_ms = duration_ms
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "skill_name": self.skill_name,
            "status": self.status.value,
            "passed": self.passed,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "details": self.details,
            "timestamp": self.timestamp,
        }


class SkillLab:
    """Sandbox pour tester les skills/plugins candidats dans Docker.

    Utilise le SDK Docker pour créer un conteneur éphémère,
    y copier le skill, l'exécuter, et collecter les résultats.
    """

    def __init__(
        self,
        docker_client: Any = None,
        publish_fn: Any = None,
        image: str = "python:3.11-slim",
        timeout_seconds: int = 120,
    ) -> None:
        self._docker = docker_client
        self._publish_fn = publish_fn
        self._image = image
        self._timeout = timeout_seconds
        self._results: dict[str, LabResult] = {}

    @property
    def docker_available(self) -> bool:
        """True si un client Docker opérationnel est attaché (sandbox OK)."""
        return self._docker is not None

    # ── Test d'un skill ────────────────────────────────────────────

    async def test_skill(
        self,
        skill_code: str,
        skill_name: str = "test_skill",
        test_input: str = "",
        requirements: list[str] | None = None,
    ) -> LabResult:
        """Teste un skill candidat dans un conteneur Docker éphémère.

        Args:
            skill_code: Code Python du skill
            skill_name: Nom du skill
            test_input: Entrée de test (optionnelle)
            requirements: Dépendances pip additionnelles

        Returns:
            LabResult avec le statut et la sortie
        """
        if self._docker is None:
            # Sandbox obligatoire (CT-sécurité) : aucun fallback d'exécution
            # locale.  Le code candidat n'est JAMAIS évalué sur l'hôte.
            result = LabResult(
                skill_name=skill_name,
                status=LabStatus.ERROR,
                error=(
                    "Docker indisponible — le Skill Lab exige un sandbox "
                    "Docker fonctionnel. L'exécution locale du code candidat "
                    "est interdite."
                ),
            )
            self._results[result.id] = result
            return result

        result = LabResult(skill_name=skill_name, status=LabStatus.RUNNING)
        self._results[result.id] = result

        try:
            success, output, error = await self._run_in_docker(
                skill_code,
                skill_name,
                test_input,
                requirements or [],
            )
            result.status = LabStatus.PASSED if success else LabStatus.FAILED
            result.passed = success
            result.output = output
            result.error = error
        except Exception as e:
            result.status = LabStatus.ERROR
            result.error = str(e)
            logger.error("SkillLab: test failed for %s: %s", skill_name, e)

        self._results[result.id] = result
        if self._publish_fn:
            try:
                self._publish_fn({"type": "skill.lab.completed", **result.to_dict()})
            except Exception as e:
                logger.warning("SkillLab: publish failed: %s", e)

        logger.info(
            "SkillLab: %s → %s (passed=%s, duration=%.0fms)",
            skill_name,
            result.status.value,
            result.passed,
            result.duration_ms,
        )

        return result

    def _build_docker_command(
        self, container_name: str, temp_path: str, requirements: list[str]
    ) -> list[str]:
        """Commande ``docker run`` complète — dépendances validées en argv.

        Les requirements sont transmis en arguments positionnels du shell
        (``"$@"``) : même sans la validation amont, ils ne peuvent jamais
        devenir des commandes.  L'absence de dépendances exécute Python
        directement (aucun shell intermédiaire).
        """
        validated = _validate_requirements(requirements)
        cmd = [
            "docker",
            "run",
            "--rm",
            "--name",
            container_name,
            "--network",
            "none",  # Pas d'accès réseau
            "--memory",
            "256m",  # Limite mémoire
            "--cpus",
            "0.5",  # Limite CPU
            # Durcissement Red Team (F4 / Attaques 12-13) : aucune capacité
            # Linux supplémentaire et pas d'élévation de privilèges (setuid).
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            "--pids-limit",
            "64",  # Limitation du fork bomb
            "-v",
            f"{temp_path}:/tmp/skill.py:ro",
            self._image,
        ]
        if validated:
            cmd += [
                "sh",
                "-c",
                'pip install --no-input "$@" && python /tmp/skill.py',
                "ethan-lab",  # $0 du shell
                *validated,
            ]
        else:
            cmd += ["python", "/tmp/skill.py"]
        return cmd

    async def _run_in_docker(
        self,
        skill_code: str,
        skill_name: str,
        test_input: str,
        requirements: list[str],
    ) -> tuple[bool, str, str]:
        """Exécute le skill dans un conteneur Docker éphémère."""
        import asyncio

        # Créer un fichier temporaire avec le code du skill
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, prefix=f"skill_{skill_name}_"
        ) as f:
            f.write(skill_code)
            temp_path = f.name

        try:
            # Construire la commande Docker (requirements validés et passés en
            # argv — aucune interpolation dans la ligne de commande shell).
            container_name = _safe_container_name(skill_name)
            cmd = self._build_docker_command(container_name, temp_path, requirements)

            # Exécuter avec timeout
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self._timeout)
                output = stdout.decode("utf-8", errors="replace").strip()
                error = stderr.decode("utf-8", errors="replace").strip()
                success = proc.returncode == 0
                return success, output, error

            except asyncio.TimeoutError:
                # Nettoyer le conteneur en timeout
                try:
                    kill_proc = await asyncio.create_subprocess_exec(
                        "docker",
                        "kill",
                        container_name,
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL,
                    )
                    await kill_proc.wait()
                except Exception:
                    pass
                return False, "", f"Timeout after {self._timeout}s"

        finally:
            # Nettoyer le fichier temporaire
            try:
                Path(temp_path).unlink(missing_ok=True)
            except Exception:
                pass

    # ── Validation de plugin ───────────────────────────────────────

    async def validate_plugin(
        self,
        plugin_dir: str | Path,
    ) -> LabResult:
        """Valide un dossier de plugin complet.

        Vérifie :
        - La présence du manifeste
        - La validité du JSON
        - L'existence du point d'entrée
        - La cohérence des dépendances
        """
        plugin_path = Path(plugin_dir)
        skill_name = plugin_path.name
        result = LabResult(skill_name=skill_name, status=LabStatus.RUNNING)

        checks: list[dict[str, Any]] = []

        # Vérifier manifest.json
        manifest_path = plugin_path / "manifest.json"
        if manifest_path.exists():
            try:
                with manifest_path.open() as f:
                    manifest = json.load(f)
                checks.append({"check": "manifest", "passed": True, "detail": "Valid JSON"})

                # Vérifier les champs requis
                required = ["name", "version", "api_version"]
                missing = [r for r in required if r not in manifest]
                if missing:
                    checks.append(
                        {
                            "check": "required_fields",
                            "passed": False,
                            "detail": f"Missing: {', '.join(missing)}",
                        }
                    )
                else:
                    checks.append({"check": "required_fields", "passed": True})

                # Vérifier la compatibilité API
                if manifest.get("api_version") != "2":
                    checks.append(
                        {
                            "check": "api_version",
                            "passed": False,
                            "detail": f"Expected '2', got '{manifest.get('api_version')}'",
                        }
                    )

            except json.JSONDecodeError as e:
                checks.append({"check": "manifest", "passed": False, "detail": str(e)})
        else:
            checks.append(
                {"check": "manifest", "passed": False, "detail": "manifest.json not found"}
            )

        # Vérifier plugin.py
        plugin_py = plugin_path / "plugin.py"
        if plugin_py.exists():
            checks.append({"check": "entrypoint", "passed": True, "detail": "plugin.py found"})
        else:
            checks.append({"check": "entrypoint", "passed": False, "detail": "plugin.py not found"})

        # Vérifier requirements.txt
        req_txt = plugin_path / "requirements.txt"
        if req_txt.exists():
            checks.append(
                {"check": "requirements", "passed": True, "detail": "requirements.txt found"}
            )

        # Déterminer le résultat
        all_passed = all(c["passed"] for c in checks)
        result.status = LabStatus.PASSED if all_passed else LabStatus.FAILED
        result.passed = all_passed
        result.details["checks"] = checks
        result.output = json.dumps(checks, indent=2)

        self._results[result.id] = result
        if self._publish_fn:
            try:
                self._publish_fn({"type": "skill.lab.validated", **result.to_dict()})
            except Exception as e:
                logger.warning("SkillLab: publish failed: %s", e)

        logger.info(
            "SkillLab: validate %s → %s (%d/%d checks passed)",
            skill_name,
            result.status.value,
            sum(1 for c in checks if c["passed"]),
            len(checks),
        )

        return result

    # ── Requêtes ───────────────────────────────────────────────────

    def get_result(self, result_id: str) -> LabResult | None:
        """Récupère un résultat par son ID."""
        return self._results.get(result_id)

    def list_results(self, skill_name: str | None = None) -> list[LabResult]:
        """Liste tous les résultats de test."""
        if skill_name:
            return [r for r in self._results.values() if r.skill_name == skill_name]
        return list(self._results.values())

    def clear_results(self) -> None:
        """Vide l'historique des résultats."""
        self._results.clear()
