"""Module de détection et d'interrogation du Hugging Face Hub pour ETHAN Core.

Fournit :
- La recherche de modèles sur le Hugging Face Hub
- L'inspection des fichiers et formats disponibles (.gguf, .safetensors)
- La détection des modèles restreints (gated / HF_TOKEN requis)
- Le repli hors-ligne résilient sans crash réseau
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

HF_API_BASE = "https://huggingface.co/api"


def _extract_params_from_tags(tags: list[str]) -> float | None:
    """Tente d'extraire la taille des paramètres depuis les tags du repo."""
    for tag in tags:
        m = re.search(r"\b(\d+(?:\.\d+)?)[bB]\b", tag)
        if m:
            return float(m.group(1))
    return None


async def inspect_hf_model(repo_id: str, hf_token: str | None = None) -> dict[str, Any]:
    """Inspecte un dépôt Hugging Face pour détecter ses formats, poids et restrictions.

    Args:
        repo_id: Identifiant du dépôt (ex: "Qwen/Qwen2.5-Coder-7B-Instruct")
        hf_token: Token Hugging Face optionnel (ou lu depuis env `HF_TOKEN`)

    Returns:
        Dict structuré :
        {
            "repo_id": str,
            "name": str,
            "pipeline_tag": str,
            "is_gated": bool,
            "formats_available": ["gguf", "safetensors", ...],
            "gguf_files": list[str],
            "params_b": float,
            "description": str
        }
    """
    token = hf_token or os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
    headers = {"User-Agent": "ETHAN-Cognitive-OS"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    result: dict[str, Any] = {
        "repo_id": repo_id,
        "name": repo_id.split("/")[-1] if "/" in repo_id else repo_id,
        "pipeline_tag": "text-generation",
        "is_gated": False,
        "formats_available": [],
        "gguf_files": [],
        "params_b": 7.0,
        "description": "",
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=3.0)) as client:
            resp = await client.get(f"{HF_API_BASE}/models/{repo_id}", headers=headers)
            if resp.status_code in (401, 403):
                result["is_gated"] = True
                return result
            if resp.status_code == 200:
                data = resp.json()
                result["pipeline_tag"] = data.get("pipeline_tag", "text-generation")
                result["is_gated"] = bool(data.get("gated", False) or data.get("private", False))

                # Extraire le nombre de paramètres
                tags = data.get("tags", [])
                extracted_p = _extract_params_from_tags(tags)
                if extracted_p is not None:
                    result["params_b"] = extracted_p

                # Inspecter les fichiers disponibles
                siblings = data.get("siblings", [])
                formats = set()
                gguf_files = []
                for s in siblings:
                    fname = s.get("rfilename", "")
                    if fname.endswith(".gguf"):
                        formats.add("gguf")
                        gguf_files.append(fname)
                    elif fname.endswith(".safetensors"):
                        formats.add("safetensors")
                    elif fname.endswith(".bin") or fname.endswith(".pt"):
                        formats.add("pytorch")

                result["formats_available"] = sorted(formats)
                result["gguf_files"] = gguf_files
    except Exception as exc:
        logger.debug("Échec de l'inspection en direct de Hugging Face (%s) : %s", repo_id, exc)
        # Repli heuristique local
        if "gguf" in repo_id.lower():
            result["formats_available"] = ["gguf"]
        else:
            result["formats_available"] = ["safetensors"]

    return result


async def search_hf_models(
    query: str, limit: int = 10, hf_token: str | None = None
) -> list[dict[str, Any]]:
    """Recherche des modèles sur le Hugging Face Hub (filtre text-generation).

    Args:
        query: Terme de recherche (ex: "qwen 2.5", "llama 3.2")
        limit: Nombre maximal de résultats
        hf_token: Token Hugging Face optionnel

    Returns:
        Liste de modèles découverts avec formats détectés.
    """
    token = hf_token or os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
    headers = {"User-Agent": "ETHAN-Cognitive-OS"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=3.0)) as client:
            resp = await client.get(
                f"{HF_API_BASE}/models",
                params={
                    "search": query,
                    "filter": "text-generation",
                    "sort": "downloads",
                    "direction": "-1",
                    "limit": limit,
                },
                headers=headers,
            )
            if resp.status_code == 200:
                items = resp.json()
                models = []
                for item in items:
                    repo_id = item.get("id", "")
                    tags = item.get("tags", [])
                    has_gguf = "gguf" in repo_id.lower() or "gguf" in tags
                    formats = ["gguf"] if has_gguf else ["safetensors"]

                    models.append(
                        {
                            "id": repo_id,
                            "name": repo_id.split("/")[-1] if "/" in repo_id else repo_id,
                            "repo_id": repo_id,
                            "provider": "huggingface",
                            "pipeline_tag": item.get("pipeline_tag", "text-generation"),
                            "formats_available": formats,
                            "source": "huggingface",
                            "downloads": item.get("downloads", 0),
                            "likes": item.get("likes", 0),
                        }
                    )
                return models
    except Exception as exc:
        logger.debug("Recherche Hugging Face API indisponible : %s", exc)

    return []
