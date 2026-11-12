"""Isolation d'installation MCP — décision et backend (fail-closed).

Phase 3-B : fournit une abstraction indépendante du moteur (provider) et un
backend concret Docker pour exécuter acquisition/installation de code tiers dans
un conteneur durci. Sans backend effectif disponible et correctement configuré
pour le plan, l'installation est refusée (aucun repli hôte).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Protocol

from core.mcp_installer.isolation_backend import (
    BackendProbe,
    DockerInstallIsolationBackend,
    IsolationBackendError,
    default_install_backend,
)
from core.mcp_installer.plan import InstallationPlan, SourceType


class IsolationUnavailableError(RuntimeError):
    """Isolation effective requise mais indisponible (fail closed)."""

    def __init__(self, message: str, *, code: str = "MCP-ISOLATION-UNAVAILABLE") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class IsolationAssessment:
    required: bool
    available: bool
    effective: bool
    mechanism: str
    reason: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "required": self.required,
            "available": self.available,
            "effective": self.effective,
            "mechanism": self.mechanism,
            "reason": self.reason,
            "details": dict(self.details),
        }


class InstallIsolationProvider(Protocol):
    mechanism: str
    effective: bool

    def assess(self, plan: InstallationPlan) -> IsolationAssessment: ...
    def ensure_available(self, plan: InstallationPlan) -> IsolationAssessment: ...
    def backend(self) -> DockerInstallIsolationBackend | None: ...


def _requires_third_party_code_install(plan: InstallationPlan) -> bool:
    return plan.source_type in {
        SourceType.NPM_PACKAGE,
        SourceType.NPM_COMMAND,
        SourceType.GITHUB,
        SourceType.CUSTOM_COMMAND,
    }


def _image_for_plan(plan: InstallationPlan) -> tuple[str | None, str]:
    """(image, raison si absente). Sélection par besoin opérationnel."""
    st = plan.source_type
    if st in {SourceType.NPM_PACKAGE, SourceType.NPM_COMMAND}:
        img = (os.getenv("ETHAN_MCP_INSTALL_IMAGE_NODE") or "").strip() or "node:20-alpine"
        return img, "image Node/npm requise"
    if st == SourceType.GITHUB:
        manager = (plan.analysis.package_manager if plan.analysis else "") or ""
        if manager == "npm" or manager == "":
            img = (os.getenv("ETHAN_MCP_INSTALL_IMAGE_GIT_NODE") or "").strip()
            return (img or None), "image git+node/npm requise pour dépôt GitHub (non configurée)"
        if manager == "pip":
            img = (os.getenv("ETHAN_MCP_INSTALL_IMAGE_GIT_PYTHON") or "").strip()
            return (img or None), "image git+python/pip requise pour dépôt GitHub (non configurée)"
        return None, "gestionnaire de dépôt GitHub non supporté en isolation"
    if st == SourceType.CUSTOM_COMMAND:
        # Exécution/installation de commande custom tierce : nécessite image dédiée.
        img = (os.getenv("ETHAN_MCP_INSTALL_IMAGE_CUSTOM") or "").strip()
        return (img or None), "image d'exécution custom requise (non configurée)"
    return None, "aucune image requise"


class DefaultInstallIsolationProvider:
    """Provider par défaut : Docker effectif si disponible/configuré, sinon refus."""

    mechanism = "unconfigured"
    effective = False

    def __init__(
        self,
        *,
        allow_simulated: bool = False,
        simulated_effective: bool = False,
        backend: DockerInstallIsolationBackend | None = None,
    ) -> None:
        self._allow_simulated = allow_simulated
        self._simulated_effective = simulated_effective
        self._backend = backend

    def backend(self) -> DockerInstallIsolationBackend | None:
        return self._backend

    def _resolve_docker_backend(self) -> DockerInstallIsolationBackend | None:
        if self._backend is not None:
            return self._backend
        return default_install_backend()

    def assess(self, plan: InstallationPlan) -> IsolationAssessment:
        required = _requires_third_party_code_install(plan)
        if not required:
            return IsolationAssessment(
                required=False,
                available=True,
                effective=True,
                mechanism="none-required",
                reason="Aucune acquisition/exécution de code tiers sur l'hôte.",
            )

        mode = (os.getenv("ETHAN_MCP_INSTALL_ISOLATION") or "").strip().lower()
        if self._allow_simulated and mode == "simulated":
            return IsolationAssessment(
                required=True,
                available=True,
                effective=bool(self._simulated_effective),
                mechanism="simulated-test",
                reason=(
                    "Isolation simulée (double de test) : non validée comme isolation "
                    "effective réelle."
                    if not self._simulated_effective
                    else "Double d'isolation de test accepté explicitement (simulé)."
                ),
                details={"simulated": True},
            )

        if mode == "docker":
            backend = self._resolve_docker_backend()
            if backend is None:
                return IsolationAssessment(
                    required=True, available=False, effective=False,
                    mechanism="docker",
                    reason="Backend Docker d'installation indisponible (CLI introuvable).",
                )
            probe = backend.probe()
            if not (probe.available and probe.effective):
                return IsolationAssessment(
                    required=True, available=probe.available, effective=False,
                    mechanism="docker", reason=probe.reason, details=probe.details,
                )
            image, image_reason = _image_for_plan(plan)
            if not image:
                return IsolationAssessment(
                    required=True, available=True, effective=False,
                    mechanism="docker",
                    reason=f"Isolation Docker indisponible pour ce plan : {image_reason}.",
                    details={**probe.details, "image": None},
                )
            try:
                backend.ensure_image(image)
            except IsolationBackendError as exc:
                return IsolationAssessment(
                    required=True, available=True, effective=False,
                    mechanism="docker",
                    reason=f"Isolation Docker indisponible : {exc}",
                    details={**probe.details, "image": image},
                )
            self._backend = backend
            return IsolationAssessment(
                required=True, available=True, effective=True,
                mechanism="docker",
                reason="Backend Docker d'installation disponible pour ce plan.",
                details={**probe.details, "image": image},
            )

        # autres modes déclarés mais non prouvés
        if mode in {"container", "podman"}:
            backend = self._resolve_docker_backend() if mode == "container" else None
            probe = (
                backend.probe()
                if backend
                else BackendProbe(False, False, mode, "non implémenté", {})
            )
            return IsolationAssessment(
                required=True, available=probe.available, effective=False,
                mechanism=mode,
                reason="Backend déclaré mais non implémenté/prouvé pour ce mode (fail closed).",
                details=probe.details,
            )

        return IsolationAssessment(
            required=True,
            available=False,
            effective=False,
            mechanism=mode or "none",
            reason=(
                "Isolation effective requise pour l'installation de code tiers "
                "(npm/GitHub/commande custom) : aucun mécanisme prouvé disponible. "
                "Configurez ETHAN_MCP_INSTALL_ISOLATION=docker et les images requises ; "
                "refus en fermeture."
            ),
        )

    def ensure_available(self, plan: InstallationPlan) -> IsolationAssessment:
        assessment = self.assess(plan)
        if assessment.required and not (assessment.available and assessment.effective):
            raise IsolationUnavailableError(assessment.reason)
        return assessment


def default_isolation_provider() -> InstallIsolationProvider:
    return DefaultInstallIsolationProvider()
