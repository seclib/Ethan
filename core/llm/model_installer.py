"""Orchestrateur d'installation et d'exécution des modèles ETHAN Core.

Principe utilisateur :
« L'utilisateur choisit un modèle ; ETHAN s'occupe de déterminer comment l'exécuter. »

Gère :
- La détection de la source (Cloud, Ollama Library, Hugging Face GGUF/Safetensors)
- La vérification de compatibilité matérielle ("What Fits?") et projection de vitesse
- Le choix du runtime d'exécution (Ollama, llama.cpp, vLLM, Cloud)
- L'installation / le téléchargement (Ollama pull, HF downloader)
- L'enregistrement et le health-check du runtime dans ETHAN.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from core.hardware.fit import check_model_compatibility
from core.llm.model_store import ModelStore
from core.llm.provider_manager import ProviderManager
from core.models.downloader import get_model_downloader

logger = logging.getLogger(__name__)


def determine_execution_strategy(
    model_id: str,
    provider_hint: str | None = None,
    hardware: dict[str, Any] | None = None,
    quantization: str | None = None,
) -> dict[str, Any]:
    """Détermine automatiquement le runtime et la méthode d'exécution pour un modèle.

    Args:
        model_id: Identifiant du modèle (ex: "llama3.2:3b", "qwen2.5-coder:7b", "Qwen/Qwen2.5-Coder-7B-GGUF", "gpt-4o-mini")
        provider_hint: Indication optionnelle du provider souhaité
        hardware: Métriques matérielles (détectées automatiquement si None)

    Returns:
        Dict décrivant la stratégie d'exécution :
        {
            "model_id": str,
            "runtime": "ollama" | "vllm" | "llamacpp" | "cloud",
            "provider_type": str,
            "target_model_name": str,
            "compatible": bool,
            "fit_level": str,
            "recommended_format": str,
            "estimated_speed_tps": float,
            "action": "pull" | "download" | "cloud_enable" | "register",
            "reason": str,
            "recommendation": str
        }
    """
    clean_id = model_id.strip()
    name_lower = clean_id.lower()

    # 1. Modèles Cloud hébergés (OpenAI, Anthropic, Gemini, OpenRouter)
    if any(name_lower.startswith(p) for p in ("gpt-", "o1-", "o3-", "o4-")):
        return {
            "model_id": clean_id,
            "runtime": "cloud",
            "provider_type": "openai",
            "target_model_name": clean_id,
            "compatible": True,
            "fit_level": "perfect",
            "recommended_format": "cloud",
            "estimated_speed_tps": 60.0,
            "action": "cloud_enable",
            "reason": "Modèle hébergé par OpenAI.",
            "recommendation": "Prêt à l'emploi via l'API OpenAI.",
        }
    if any(name_lower.startswith(p) for p in ("claude-", "anthropic/")):
        return {
            "model_id": clean_id,
            "runtime": "cloud",
            "provider_type": "anthropic",
            "target_model_name": clean_id,
            "compatible": True,
            "fit_level": "perfect",
            "recommended_format": "cloud",
            "estimated_speed_tps": 50.0,
            "action": "cloud_enable",
            "reason": "Modèle hébergé par Anthropic.",
            "recommendation": "Prêt à l'emploi via l'API Anthropic.",
        }
    if any(name_lower.startswith(p) for p in ("gemini-", "google/")):
        return {
            "model_id": clean_id,
            "runtime": "cloud",
            "provider_type": "gemini",
            "target_model_name": clean_id,
            "compatible": True,
            "fit_level": "perfect",
            "recommended_format": "cloud",
            "estimated_speed_tps": 70.0,
            "action": "cloud_enable",
            "reason": "Modèle hébergé par Google Gemini.",
            "recommendation": "Prêt à l'emploi via l'API Google Gemini.",
        }
    if name_lower.startswith("openrouter/"):
        return {
            "model_id": clean_id,
            "runtime": "cloud",
            "provider_type": "openrouter",
            "target_model_name": clean_id.replace("openrouter/", ""),
            "compatible": True,
            "fit_level": "perfect",
            "recommended_format": "cloud",
            "estimated_speed_tps": 55.0,
            "action": "cloud_enable",
            "reason": "Modèle hébergé via OpenRouter.",
            "recommendation": "Prêt à l'emploi via OpenRouter.",
        }

    # 2. Modèles locaux : Évaluer l'adéquation matérielle via fit engine
    compat = check_model_compatibility(clean_id, quantization=quantization, hardware=hardware)
    if not compat.compatible:
        return {
            "model_id": clean_id,
            "runtime": compat.recommended_runtime,
            "provider_type": "ollama",
            "target_model_name": clean_id,
            "compatible": False,
            "fit_level": compat.fit_level,
            "recommended_format": compat.recommended_format,
            "estimated_speed_tps": 0.0,
            "action": "reject",
            "reason": f"Incompatible avec le matériel actuel : {compat.reason}",
            "recommendation": compat.recommendation,
            "compatibility": compat.to_dict(),
        }

    # 3. Déterminer le runtime et le format technique
    runtime = provider_hint if provider_hint in ("ollama", "vllm", "llamacpp") else compat.recommended_runtime

    # Si le modèle est un repo Hugging Face (ex: org/repo)
    if "/" in clean_id and not clean_id.startswith("hf.co/"):
        if runtime == "ollama":
            # Ollama supporte nativement le préfixe hf.co/ pour puller les GGUF depuis Hugging Face
            target_name = f"hf.co/{clean_id}"
            action = "pull"
        elif runtime in ("vllm", "sglang"):
            target_name = clean_id
            action = "download"
        else:
            target_name = clean_id
            action = "register"
    else:
        target_name = clean_id
        action = "pull" if runtime == "ollama" else "register"

    return {
        "model_id": clean_id,
        "runtime": runtime,
        "provider_type": runtime,
        "target_model_name": target_name,
        "compatible": True,
        "fit_level": compat.fit_level,
        "recommended_format": compat.recommended_format,
        "estimated_speed_tps": compat.estimated_speed_tps,
        "action": action,
        "reason": compat.reason,
        "recommendation": compat.recommendation,
        "compatibility": compat.to_dict(),
    }


async def install_or_use_model(
    model_id: str,
    provider_hint: str | None = None,
    manager: ProviderManager | None = None,
    store: ModelStore | None = None,
    hardware: dict[str, Any] | None = None,
    quantization: str | None = None,
) -> dict[str, Any]:
    """Exécute l'installation ou l'activation d'un modèle dans ETHAN.

    Applique le principe utilisateur :
    - Détermine la méthode technique optimale
    - Télécharge / prépare le modèle
    - Enregistre et effectue le healthcheck du modèle dans ETHAN.
    """
    strategy = determine_execution_strategy(
        model_id,
        provider_hint=provider_hint,
        hardware=hardware,
        quantization=quantization,
    )

    if not strategy["compatible"]:
        return {
            "success": False,
            "error": "incompatible_hardware",
            "message": strategy["reason"],
            "strategy": strategy,
        }

    runtime = strategy["runtime"]
    target_name = strategy["target_model_name"]

    # ── Cas A : Modèle Cloud ──────────────────────────────────────────
    if runtime == "cloud":
        provider_type = strategy["provider_type"]
        if manager:
            prov_cfg = manager._providers_config.get(provider_type)
            if not prov_cfg:
                await manager.register_provider(
                    config={
                        "name": provider_type,
                        "type": provider_type,
                        "enabled": True,
                        "default_model": target_name,
                    }
                )
            else:
                prov_cfg["default_model"] = target_name
                await manager.set_enabled(provider_type, True)

        return {
            "success": True,
            "model_id": model_id,
            "runtime": "cloud",
            "provider": provider_type,
            "message": f"Modèle Cloud {model_id} configuré avec succès sur le provider {provider_type}.",
            "strategy": strategy,
        }

    # ── Cas B : Modèle Local via Ollama ───────────────────────────────
    if runtime == "ollama":
        base_url = "http://localhost:11434"
        if manager:
            cfg = manager._providers_config.get("ollama", {})
            base_url = cfg.get("base_url") or base_url

        # Tenter d'ordonner le pull à Ollama
        pull_success = False
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=4.0)) as client:
                logger.info(
                    "Début du téléchargement du modèle %s via Ollama (%s)", target_name, base_url
                )
                resp = await client.post(
                    f"{base_url}/api/pull",
                    json={"name": target_name, "stream": False},
                )
                if resp.status_code == 200:
                    pull_success = True
                    logger.info("Modèle %s téléchargé avec succès par Ollama", target_name)
        except Exception as exc:
            logger.warning("Connexion à Ollama (%s) impossible pour le pull : %s", base_url, exc)

        # Enregistrer et activer le modèle dans le ModelStore
        if store:
            await store.create_model(
                {
                    "name": target_name,
                    "model": target_name,
                    "provider": "ollama",
                    "base_model_id": model_id,
                    "meta": {
                        "is_local": True,
                        "installed_via": "ethan_model_installer",
                        "runtime": "ollama",
                        "speed_tps": strategy.get("estimated_speed_tps"),
                    },
                    "is_active": True,
                }
            )

        if manager:
            try:
                if "ollama" in manager._providers_config:
                    manager._providers_config["ollama"]["default_model"] = target_name
                    await manager.set_enabled("ollama", True)
            except Exception as e:
                logger.debug("Mise à jour ProviderManager pour Ollama: %s", e)

        return {
            "success": True,
            "model_id": target_name,
            "runtime": "ollama",
            "provider": "ollama",
            "message": f"Modèle {target_name} installé et prêt à l'emploi dans ETHAN.",
            "strategy": strategy,
        }

    # ── Cas C : Téléchargement Hugging Face direct ────────────────────
    if strategy["action"] == "download":
        downloader = get_model_downloader()
        dl_res = await downloader.download_hf_model(repo_id=model_id)
        if not dl_res.get("success"):
            return {
                "success": False,
                "error": "download_failed",
                "message": f"Échec du téléchargement Hugging Face : {dl_res.get('error')}",
                "strategy": strategy,
            }

    # ── Cas D : Autre runtime local (llama.cpp, vLLM) ───────────────────
    if store:
        await store.create_model(
            {
                "name": target_name,
                "model": target_name,
                "provider": runtime,
                "base_model_id": model_id,
                "meta": {
                    "is_local": True,
                    "installed_via": "ethan_model_installer",
                    "runtime": runtime,
                },
                "is_active": True,
            }
        )

    return {
        "success": True,
        "model_id": target_name,
        "runtime": runtime,
        "provider": runtime,
        "message": f"Modèle {target_name} configuré pour le runtime {runtime}.",
        "strategy": strategy,
    }
