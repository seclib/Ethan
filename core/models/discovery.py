"""Service de découverte et d'exploration de modèles d'IA pour ETHAN Core.

Fournit une liste unifiée de modèles connus (Ollama Library, Hugging Face Hub,
providers cloud) enrichie automatiquement des métriques d'adéquation matérielle.
"""

from __future__ import annotations

import logging
from typing import Any

from core.hardware.detector import get_system_hardware
from core.hardware.fit import check_model_compatibility
from core.models.hf import search_hf_models

logger = logging.getLogger(__name__)

# Catalogue de modèles populaires pré-indexés (Hugging Face / Ollama / Cloud)
CURATED_MODEL_CATALOG: list[dict[str, Any]] = [
    {
        "id": "qwen2.5:7b",
        "name": "Qwen 2.5 7B",
        "provider": "ollama",
        "repo_id": "qwen2.5:7b",
        "params_b": 7.6,
        "description": "Modèle généraliste très performant en code et raisonnement.",
        "use_case": "coding",
        "quantization": "Q4_K_M",
        "source": "ollama",
    },
    {
        "id": "qwen2.5-coder:7b",
        "name": "Qwen 2.5 Coder 7B",
        "provider": "ollama",
        "repo_id": "qwen2.5-coder:7b",
        "params_b": 7.6,
        "description": "Spécialiste de la programmation et du débogage.",
        "use_case": "coding",
        "quantization": "Q4_K_M",
        "source": "ollama",
    },
    {
        "id": "llama3.1:8b",
        "name": "Llama 3.1 8B",
        "provider": "ollama",
        "repo_id": "llama3.1:8b",
        "params_b": 8.0,
        "description": "Modèle open-source phare de Meta pour les tâches générales.",
        "use_case": "general",
        "quantization": "Q4_K_M",
        "source": "ollama",
    },
    {
        "id": "llama3.2:3b",
        "name": "Llama 3.2 3B",
        "provider": "ollama",
        "repo_id": "llama3.2:3b",
        "params_b": 3.2,
        "description": "Ultra-léger, idéal pour les configurations sans GPU dédié.",
        "use_case": "chat",
        "quantization": "Q4_K_M",
        "source": "ollama",
    },
    {
        "id": "deepseek-r1:7b",
        "name": "DeepSeek R1 Distill 7B",
        "provider": "ollama",
        "repo_id": "deepseek-r1:7b",
        "params_b": 7.0,
        "description": "Modèle spécialisé dans le raisonnement logique pas-à-pas.",
        "use_case": "reasoning",
        "quantization": "Q4_K_M",
        "source": "ollama",
    },
    {
        "id": "mistral:7b",
        "name": "Mistral 7B Instruct",
        "provider": "ollama",
        "repo_id": "mistral:7b",
        "params_b": 7.2,
        "description": "Modèle compact et rapide de Mistral AI.",
        "use_case": "general",
        "quantization": "Q4_K_M",
        "source": "ollama",
    },
    {
        "id": "phi4:14b",
        "name": "Phi-4 14B",
        "provider": "ollama",
        "repo_id": "phi4:14b",
        "params_b": 14.0,
        "description": (
            "Modèle raisonneur de Microsoft avec d'excellentes performances "
            "synthétiques."
        ),
        "use_case": "reasoning",
        "quantization": "Q4_K_M",
        "source": "ollama",
    },
    {
        "id": "smollm2:1.7b",
        "name": "SmolLM2 1.7B",
        "provider": "ollama",
        "repo_id": "smollm2:1.7b",
        "params_b": 1.7,
        "description": "Ultra compact de HuggingFaceTB pour l'inférence ultra-rapide.",
        "use_case": "chat",
        "quantization": "Q4_K_M",
        "source": "ollama",
    },
    {
        "id": "gpt-4o-mini",
        "name": "OpenAI GPT-4o Mini",
        "provider": "openai",
        "repo_id": "gpt-4o-mini",
        "params_b": 0.0,
        "description": "Modèle Cloud rapide et économique d'OpenAI.",
        "use_case": "general",
        "quantization": "Cloud",
        "source": "cloud",
    },
    {
        "id": "claude-3-5-sonnet-20241022",
        "name": "Anthropic Claude 3.5 Sonnet",
        "provider": "anthropic",
        "repo_id": "claude-3-5-sonnet-20241022",
        "params_b": 0.0,
        "description": "Modèle Cloud de pointe d'Anthropic pour le code et l'analyse.",
        "use_case": "coding",
        "quantization": "Cloud",
        "source": "cloud",
    },
]


def discover_catalog_models(
    query: str = "",
    use_case: str | None = None,
    hardware: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Découvre et filtre le catalogue de modèles synchrones."""
    sys_hw = hardware or get_system_hardware()
    q = query.lower().strip()
    results = []

    for item in CURATED_MODEL_CATALOG:
        if q:
            searchable = f"{item['id']} {item['name']} {item.get('description', '')}".lower()
            if q not in searchable:
                continue

        if use_case and item.get("use_case") != use_case:
            continue

        compat = check_model_compatibility(
            model_name=item["id"],
            params_b=item.get("params_b"),
            quantization=item.get("quantization"),
            hardware=sys_hw,
        )

        entry = dict(item)
        entry["compatibility"] = compat.to_dict()
        results.append(entry)

    results.sort(key=lambda x: (not x["compatibility"]["compatible"], x["name"]))
    return results


async def discover_models_async(
    query: str = "",
    use_case: str | None = None,
    hardware: dict[str, Any] | None = None,
    include_hf: bool = True,
    source: str = "all",
) -> list[dict[str, Any]]:
    """Découvre des modèles en combinant le catalogue local et l'API Hugging Face Hub.

    Args:
        query: Terme de recherche
        use_case: Filtre par use_case
        hardware: Spécifications matérielles
        include_hf: Interroge Hugging Face si la recherche ne trouve pas assez de modèles
            (en source ``huggingface``, HF est interrogé même sans terme de recherche)
        source: Filtre par source — "all" (défaut), "curated", "huggingface" ou
            "local" (alias d'affichage du catalogue de référence servi localement).
    """
    normalized_source = (source or "all").lower()
    if normalized_source == "local":
        normalized_source = "curated"
    sys_hw = hardware or get_system_hardware()
    catalog_results: list[dict[str, Any]] = []
    if normalized_source in ("all", "curated"):
        catalog_results = discover_catalog_models(query=query, use_case=use_case, hardware=sys_hw)

    # Si une recherche spécifique est demandée et qu'elle contient un '/'
    # (format HF org/repo) ou peu de résultats.
    # Le filtre source "curated" exclut explicitement Hugging Face ;
    # "all"/"huggingface" l'autorisent.
    # source "huggingface" explicite : HF est interrogé même sans terme (top
    # downloads via search="") ; "all" sans terme reste exclu pour ne pas
    # noyer le catalogue curaté par le top Hugging Face.
    hf_query_allowed = bool(query.strip()) or normalized_source == "huggingface"
    if (
        include_hf
        and normalized_source in ("all", "huggingface")
        and hf_query_allowed
        and (len(catalog_results) < 3 or "/" in query)
    ):
        try:
            hf_items = await search_hf_models(query=query.strip(), limit=5)
            known_ids = {r["id"] for r in catalog_results}

            for item in hf_items:
                if item["id"] in known_ids:
                    continue

                compat = check_model_compatibility(
                    model_name=item["id"],
                    hardware=sys_hw,
                )
                entry = {
                    "id": item["id"],
                    "name": item["name"],
                    "provider": "huggingface",
                    "repo_id": item["repo_id"],
                    "description": (
                        "Modèle Hugging Face Hub "
                        f"({item.get('pipeline_tag', 'text-generation')})."
                    ),
                    "use_case": "general",
                    "quantization": (
                        "GGUF" if "gguf" in item.get("formats_available", []) else "Auto"
                    ),
                    "source": "huggingface",
                    "compatibility": compat.to_dict(),
                }
                # Le catalogue HF live n'expose pas de use_case fiable : les
                # entrées sont catégorisées « general ». Le filtre use_case
                # s'applique donc aussi ici — un filtre explicite (ex.
                # « coding ») n'invente pas de catégorie pour un modèle
                # dont le Core ignore l'usage réel.
                if use_case and entry.get("use_case") != use_case:
                    continue
                catalog_results.append(entry)
        except Exception as exc:
            logger.debug("Échec de l'enrichissement Hugging Face : %s", exc)

    catalog_results.sort(key=lambda x: (not x["compatibility"]["compatible"], x["name"]))
    return catalog_results
