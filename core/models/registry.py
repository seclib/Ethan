"""Registre central des modèles d'IA pour ETHAN Core.

Unifie le catalogue pré-indexé, les découvertes Hugging Face et les modèles
déjà installés ou servis localement.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any

from core.hardware.detector import get_system_hardware
from core.hardware.fit import check_model_compatibility
from core.models.discovery import CURATED_MODEL_CATALOG

logger = logging.getLogger(__name__)


@dataclass
class ModelEntry:
    """Entrée normalisée pour un modèle d'IA."""

    id: str
    name: str
    provider: str
    repo_id: str
    params_b: float = 7.0
    active_params_b: float = 7.0
    is_moe: bool = False
    context_length: int = 4096
    quantization: str = "Q4_K_M"
    formats_available: list[str] = field(default_factory=lambda: ["gguf"])
    capabilities: list[str] = field(default_factory=lambda: ["chat"])
    use_case: str = "general"
    description: str = ""
    source: str = "curated"  # "curated" | "huggingface" | "ollama" | "local" | "cloud"
    is_installed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ModelRegistry:
    """Gestionnaire du registre des modèles pour ETHAN Core."""

    def __init__(self) -> None:
        self._entries: dict[str, ModelEntry] = {}
        self._load_curated_catalog()

    def _load_curated_catalog(self) -> None:
        """Charge le catalogue initial de référence."""
        for item in CURATED_MODEL_CATALOG:
            entry = ModelEntry(
                id=item["id"],
                name=item["name"],
                provider=item.get("provider", "ollama"),
                repo_id=item.get("repo_id", item["id"]),
                params_b=item.get("params_b", 7.0),
                active_params_b=item.get("params_b", 7.0),
                use_case=item.get("use_case", "general"),
                quantization=item.get("quantization", "Q4_K_M"),
                description=item.get("description", ""),
                source=item.get("source", "curated"),
            )
            self._entries[entry.id] = entry

    def register(self, entry: ModelEntry) -> None:
        """Enregistre ou met à jour une entrée de modèle."""
        self._entries[entry.id] = entry

    def get(self, model_id: str) -> ModelEntry | None:
        """Récupère un modèle par son identifiant."""
        return self._entries.get(model_id)

    def list_all(self) -> list[ModelEntry]:
        """Retourne toutes les entrées enregistrées."""
        return list(self._entries.values())

    def search(
        self,
        query: str = "",
        use_case: str | None = None,
        installed_ids: set[str] | None = None,
        hardware: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Recherche dans le registre et enrichit chaque modèle de son adéquation matérielle.

        Args:
            query: Terme de recherche textuel
            use_case: Filtre par use_case ("coding", "reasoning", "general", "chat")
            installed_ids: Ensemble d'IDs de modèles déjà installés/servis
            hardware: Spécifications matérielles du système

        Returns:
            Liste de dictionnaires prêts pour l'API et le WebUI.
        """
        sys_hw = hardware or get_system_hardware()
        q = query.lower().strip()
        results = []

        for entry in self._entries.values():
            if q:
                searchable = f"{entry.id} {entry.name} {entry.description}".lower()
                if q not in searchable:
                    continue

            if use_case and entry.use_case != use_case:
                continue

            entry_dict = entry.to_dict()
            if installed_ids and entry.id in installed_ids:
                entry_dict["is_installed"] = True

            # Calculer la compatibilité avec le système hôte
            compat = check_model_compatibility(
                model_name=entry.id,
                params_b=entry.params_b,
                quantization=entry.quantization,
                context_length=entry.context_length,
                hardware=sys_hw,
            )
            entry_dict["compatibility"] = compat.to_dict()
            results.append(entry_dict)

        # Trier : modèles compatibles en premier, puis par nom
        results.sort(key=lambda x: (not x["compatibility"]["compatible"], x["name"]))
        return results


# Singleton global pour ETHAN Core
_global_registry = ModelRegistry()


def get_model_registry() -> ModelRegistry:
    """Retourne l'instance unique du ModelRegistry."""
    return _global_registry
