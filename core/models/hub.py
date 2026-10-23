"""Model Hub — Façade unifiée pour la gestion, découverte et exécution des modèles IA.

Applique la Première Loi d'ETHAN :
- Tout le calcul d'adéquation matérielle, d'inspection d'artefacts et de choix de runtime vit ici.
- L'interface ne contient aucune logique métier.
- Répond de manière déterministe à la question :
  « Ce modèle peut-il fonctionner sur cette machine, et par quelle méthode ? »
"""

from __future__ import annotations

import logging
from typing import Any

from core.hardware.detector import get_system_hardware
from core.hardware.fit import (
    CompatibilityResult,
    check_model_compatibility,
    parse_params_b,
)
from core.models.downloader import get_model_downloader
from core.models.hf import inspect_hf_model, search_hf_models
from core.models.registry import ModelEntry, get_model_registry
from core.models.storage import ModelStorageLayout, get_model_storage

logger = logging.getLogger(__name__)


class ModelHub:
    """Façade unifiée de découverte, évaluation et orchestration de modèles pour ETHAN Core.

    Point central de gestion des modèles (concept : Source → Model →
    Artifact / Format → Runtime → Endpoint → Hardware).

    ``ModelManager`` est un alias historique de cette même façade : il n'existe
    qu'une seule implémentation (pas de deuxième Manager/registry).
    """

    def __init__(self) -> None:
        self._registry = get_model_registry()
        self._downloader = get_model_downloader()
        self._storage = get_model_storage()

    def get_storage_layout(self) -> ModelStorageLayout:
        """Retourne la configuration de stockage du Model Hub."""
        return self._storage

    # ── 1. DÉCOUVERTE & RECHERCHE ──────────────────────────────────────────────

    async def discover(
        self,
        query: str = "",
        use_case: str | None = None,
        source: str = "all",
        limit: int = 25,
        hardware: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Recherche et découvre des modèles enrichis de leur compatibilité matérielle.

        Sources interrogées :
        - Catalogue de référence (curated)
        - Hugging Face Hub (si query non vide et connectivité active)
        """
        sys_hw = hardware or get_system_hardware()
        normalized_source = (source or "all").lower()
        if normalized_source == "local":
            normalized_source = "curated"
        q = query.lower().strip()
        results: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        # 1. Explorer le catalogue de référence
        if normalized_source in ("all", "curated"):
            catalog_results = self._registry.search(
                query=q,
                use_case=use_case,
                hardware=sys_hw,
            )
            for item in catalog_results:
                seen_ids.add(item["id"])
                results.append(item)

        # 2. Explorer Hugging Face si une recherche textuelle est demandée
        if q and normalized_source in ("all", "huggingface"):
            hf_matches = await search_hf_models(query=q, limit=limit)
            for hf_item in hf_matches:
                repo_id = hf_item.get("id") or hf_item.get("repo_id")
                if not repo_id or repo_id in seen_ids:
                    continue
                seen_ids.add(repo_id)

                # Évaluer la compatibilité matérielle
                p_b = parse_params_b(repo_id)
                compat = check_model_compatibility(
                    model_name=repo_id,
                    params_b=p_b,
                    hardware=sys_hw,
                )

                entry = {
                    "id": repo_id,
                    "name": repo_id.split("/")[-1],
                    "provider": "huggingface",
                    "repo_id": repo_id,
                    "params_b": p_b,
                    "description": hf_item.get("description", f"Modèle Hugging Face {repo_id}"),
                    "use_case": use_case or "general",
                    "quantization": (
                        "Q4_K_M (recommandé)"
                        if "gguf" in hf_item.get("formats_available", [])
                        else "Standard"
                    ),
                    "source": "huggingface",
                    "formats_available": hf_item.get("formats_available") or ["gguf"],
                    "is_installed": False,
                    "compatibility": compat.to_dict(),
                }
                results.append(entry)

        # Tri : compatibles d'abord, puis par compatibilité décroissante
        results.sort(
            key=lambda x: (
                0
                if x.get("compatibility", {}).get("status") == "compatible"
                else 1
                if x.get("compatibility", {}).get("status") == "compatible_with_constraints"
                else 2
                if x.get("compatibility", {}).get("status") == "insufficient_info"
                else 3
            )
        )
        return results[:limit]

    # ── 2. INSPECTION DÉTAILLÉE D'UN MODÈLE ──────────────────────────────────────

    async def inspect(
        self,
        model_id: str,
        hardware: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Inspecte un modèle et répond de manière fiable à la question :

        « Ce modèle peut-il fonctionner sur cette machine, et par quelle méthode ? »

        Distingue rigoureusement :
        - compatible
        - compatible_with_constraints (compatible avec contraintes)
        - incompatible
        - insufficient_info (information insuffisante)
        """
        sys_hw = hardware or get_system_hardware()
        p_billions = parse_params_b(model_id)

        # Vérifier si c'est un repo Hugging Face
        formats_detected: list[str] = ["gguf"]
        is_gated = False

        if "/" in model_id:
            hf_info = await inspect_hf_model(model_id)
            formats_detected = hf_info.get("formats_available", ["gguf"])
            hf_p = hf_info.get("params_b") or hf_info.get("params_billions")
            if hf_p:
                p_billions = hf_p

        # Analyse d'adéquation physique
        compat: CompatibilityResult = check_model_compatibility(
            model_name=model_id,
            params_b=p_billions,
            hardware=sys_hw,
        )

        # Déterminer la méthode d'exécution concrète
        can_run = compat.compatible
        status = compat.status
        status_label = compat.status_label
        method = compat.execution_method

        # Adapter la méthode selon les formats réellement disponibles
        if can_run:
            if "gguf" in formats_detected:
                if compat.recommended_runtime == "ollama":
                    method = f"Ollama local avec artefact GGUF natif ({compat.execution_method})"
                else:
                    method = f"Moteur GGUF local ({compat.execution_method})"
            elif "safetensors" in formats_detected:
                if "vllm" in compat.supported_runtimes:
                    method = f"vLLM serveur avec Safetensors ({compat.execution_method})"
                else:
                    method = "Safetensors détecté (Requiert vLLM ou moteur compatible)"
            elif compat.recommended_runtime == "cloud":
                method = "API Cloud distante (Aucune ressource locale)"
        else:
            if status == "insufficient_info":
                method = "Impossible à déterminer sans informations sur le modèle"
            else:
                method = f"Non exécutable : {compat.reason}"

        return {
            "model_id": model_id,
            "can_run": can_run,
            "status": status,
            "status_label": status_label,
            "method": method,
            "formats_available": formats_detected,
            "is_gated": is_gated,
            "params_b": p_billions,
            "conversion_supported": False,  # ETHAN ne force jamais de fausse conversion
            "reason": compat.reason,
            "recommendation": compat.recommendation,
            "estimated_speed_tps": compat.estimated_speed_tps,
            "compatibility": compat.to_dict(),
        }

    # ── 3. INSTALLATION & ORCHESTRATION ─────────────────────────────────────────

    async def install(
        self,
        model_id: str,
        provider_hint: str | None = None,
        quantization: str | None = None,
        manager: Any = None,
        store: Any = None,
        hardware: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Installe et active un modèle dans ETHAN via la stratégie validée.

        - Si GGUF + Ollama : tire le modèle via Ollama (support natif `hf.co/...`).
        - Si Cloud : active le provider dans ProviderManager.
        - Si Hugging Face direct : télécharge les artefacts de manière résiliente.
        - Enregistre la fiche dans ModelStore.
        """
        from core.llm.model_installer import install_or_use_model

        task_id = f"dl-{model_id.replace('/', '_')}"
        self._downloader.record_task(
            task_id=task_id,
            repo_id=model_id,
            runtime=provider_hint or "ollama",
            status="downloading",
            percent=10.0,
        )

        res = await install_or_use_model(
            model_id=model_id,
            provider_hint=provider_hint,
            quantization=quantization,
            manager=manager,
            store=store,
            hardware=hardware,
        )

        final_status = "completed" if res.get("success") else "failed"
        self._downloader.record_task(
            task_id=task_id,
            repo_id=model_id,
            runtime=res.get("runtime", provider_hint or "ollama"),
            status=final_status,
            percent=100.0 if final_status == "completed" else 0.0,
            error=res.get("message") if not res.get("success") else None,
        )
        return res

    def list_downloads(self) -> list[dict[str, Any]]:
        """Liste les téléchargements ordonnés par récence."""
        return self._downloader.list_downloads()

    # ── 4. MODÈLES INSTALLÉS / DISPONIBLES ───────────────────────────────────────

    async def list_installed(
        self,
        store: Any | None = None,
        manager: Any | None = None,
        hardware: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Liste les modèles réellement disponibles dans ETHAN.

        Union sans doublon :
        - fiches ``ModelStore`` (modèles installés via ``install()``),
        - modèles servis en direct par les providers locaux activés
          (Ollama et autres runtimes via ``manager.list_models()``).

        Un modèle Ollama présent (ex. ``llama3.2:latest``) mais sans fiche
        ``ModelStore`` apparaît avec ``source="live"`` et
        ``is_installed=True`` : il est réellement utilisable dans ETHAN.
        """
        results: list[dict[str, Any]] = []
        seen: set[str] = set()
        sys_hw = hardware or get_system_hardware()

        if store is not None:
            try:
                for card in await store.list_models():
                    card_uuid = str(card.get("id") or "")
                    mid = str(card.get("model") or card.get("name") or card_uuid)
                    if not mid or mid in seen or card_uuid in seen:
                        continue
                    seen.add(mid)
                    if card_uuid:
                        seen.add(card_uuid)
                    results.append(
                        {
                            "id": mid,
                            "name": card.get("name") or card.get("model") or mid,
                            "provider": card.get("provider", "custom"),
                            "is_local": True,
                            "is_installed": True,
                            "source": card.get("source", "custom"),
                            "context_length": card.get("context_length", 4096),
                            "capabilities": card.get("capabilities", ["chat"]),
                        }
                    )
            except Exception as e:
                logger.warning("Échec list_models depuis ModelStore: %s", e)

        if manager is not None:
            try:
                discovered = await manager.list_models()
            except Exception as e:
                logger.warning("Échec list_models depuis ProviderManager: %s", e)
                discovered = []
            for m in discovered:
                mid = str(getattr(m, "id", "") or "")
                if not mid or mid in seen:
                    continue
                seen.add(mid)
                compat = check_model_compatibility(model_name=mid, hardware=sys_hw)
                results.append(
                    {
                        "id": mid,
                        "name": getattr(m, "name", None) or mid,
                        "provider": getattr(m, "provider", "ollama"),
                        "is_local": True,
                        "is_installed": True,
                        "is_active": None,
                        "source": "live",
                        "context_length": getattr(m, "context_length", 4096),
                        "capabilities": list(getattr(m, "capabilities", []) or []),
                        "compatibility": compat.to_dict(),
                    }
                )

        return results

    # ── 5. HEALTH-CHECK DU RUNTIME ──────────────────────────────────────────────

    async def check_runtime_health(self, manager: Any = None) -> dict[str, Any]:
        """Vérifie la santé des runtimes d'inférence configurés.

        Deux couches complémentaires, sans doublon :
        - providers configurés dans le ProviderManager (Ollama et autres),
        - sondes HTTP directes des runtimes locaux connus (Ollama, llama.cpp,
          vLLM, SGLang, LM Studio) via leurs endpoints natifs.

        Un runtime local joignable mais non configuré dans le manager apparaît
        avec ``"enabled": False`` et ``"reachable": True`` : l'utilisateur voit
        ce qui tourne réellement sans fausse promesse d'utilisation.
        """
        runtimes_status: dict[str, Any] = {}

        if manager is not None:
            providers = await manager.list_providers()

            for prov in providers:
                prov_id = prov.get("id") or prov.get("name")
                if not prov_id:
                    continue
                is_enabled = prov.get("enabled", False)
                if not is_enabled:
                    runtimes_status[prov_id] = {"enabled": False, "reachable": False}
                    continue

                test_res = await manager.test_connection(prov_id)
                reachable = bool(test_res.get("connected") or test_res.get("success", False))
                runtimes_status[prov_id] = {
                    "enabled": True,
                    "reachable": reachable,
                    "latency_ms": test_res.get("latency_ms"),
                }

        # Sondes directes des runtimes locaux (complète le manager).
        for runtime_id, base_url, health_path in (
            ("ollama", "http://localhost:11434", "/api/tags"),
            ("llamacpp", "http://localhost:8080", "/health"),
            ("vllm", "http://localhost:8000", "/health"),
            ("sglang", "http://localhost:30000", "/health"),
            ("lmstudio", "http://localhost:1234", "/v1/models"),
        ):
            if runtime_id in runtimes_status and runtimes_status[runtime_id].get("reachable"):
                continue
            probe = await self._probe_runtime_endpoint(base_url, health_path)
            if probe.get("ethan_self"):
                # Self-probe ETHAN : l'endpoint répond mais n'est pas un
                # runtime LLM externe (ex: l'API ETHAN sur :8000 passerait
                # pour un vLLM, le kernel sur :8080 pour llama.cpp).
                logger.debug(
                    "Sonde %s sur %s : endpoint ETHAN détecté, ignoré.",
                    runtime_id,
                    base_url,
                )
                continue
            if probe["reachable"]:
                existing = runtimes_status.get(runtime_id, {})
                existing.update(
                    {
                        "enabled": bool(existing.get("enabled", False)),
                        "reachable": True,
                        "latency_ms": probe.get("latency_ms"),
                        "endpoint": f"{base_url}{health_path}",
                    }
                )
                runtimes_status[runtime_id] = existing

        if manager is None and not runtimes_status:
            return {"status": "uninitialized", "runtimes": {}}

        return {
            "status": (
                "healthy"
                if any(r.get("reachable") for r in runtimes_status.values())
                else "degraded"
            ),
            "runtimes": runtimes_status,
        }

    @staticmethod
    async def _probe_runtime_endpoint(base_url: str, health_path: str) -> dict[str, Any]:
        """Sonde HTTP courte d'un endpoint de runtime local (timeout 3 s).

        Détecte les self-probes ETHAN : si la réponse est le JSON de santé
        d'un service ETHAN (``service`` = ``api`` ou ``kernel``), l'endpoint
        est marqué ``ethan_self`` et non reachable — sinon l'API ETHAN sur
        :8000 passerait pour un vLLM local et fausserait le statut global.
        """
        import asyncio
        import json as _json
        import time
        import urllib.request

        ethan_self_services = frozenset({"api", "kernel"})

        def _sync_probe() -> dict[str, Any]:
            start = time.monotonic()
            req = urllib.request.Request(f"{base_url}{health_path}", method="GET")
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                latency_ms = round((time.monotonic() - start) * 1000, 1)
                status = resp.status
                body_raw = resp.read()

            ethan_self = False
            if status == 200:
                try:
                    body = _json.loads(body_raw.decode("utf-8"))
                except Exception:
                    body = None
                if isinstance(body, dict) and body.get("service") in ethan_self_services:
                    ethan_self = True

            return {
                "reachable": status == 200 and not ethan_self,
                "latency_ms": latency_ms,
                "ethan_self": ethan_self,
            }

        try:
            return await asyncio.to_thread(_sync_probe)
        except Exception:
            return {"reachable": False, "latency_ms": None, "ethan_self": False}

    def list_catalog(
        self,
        query: str = "",
        use_case: str | None = None,
        hardware: dict[str, Any] | None = None,
        installed_ids: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Retourne le catalogue de référence enrichi de compatibilité matérielle."""
        return self._registry.search(
            query=query,
            use_case=use_case,
            installed_ids=installed_ids,
            hardware=hardware,
        )

    def _resolve_entry(self, model_id: str) -> tuple[ModelEntry | None, str]:
        """Résout un model_id contre le registre en tolérant les variantes Ollama.

        Le catalogue de référence utilise des IDs canoniques (« llama3.2:3b »)
        tandis que l'API Ollama remonte souvent « llama3.2:latest ». Sans cette
        tolérance, ``detect_artifact_formats`` répondait systématiquement
        « Information insuffisante » pour tout modèle Ollama présent.

        Returns:
            Tuple (entrée registre ou None, formats source : "registry"|"heuristic").
        """
        entry = self._registry.get(model_id)
        if entry is not None and entry.formats_available:
            return entry, "registry"

        base = model_id.split(":", 1)[0].lower()
        for candidate in self._registry.list_all():
            cid_base = candidate.id.split(":", 1)[0].lower()
            if cid_base and cid_base == base and candidate.formats_available:
                return candidate, "registry"

        return None, "heuristic"

    async def detect_artifact_formats(
        self,
        model_id: str,
        hardware: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Inspecte les artefacts disponibles pour un modèle et répond à
        « Quels formats/poids sont réellement disponibles, et comment ça
        s'exécute sur cette machine ? »"""
        sys_hw = hardware or get_system_hardware()
        params_b = parse_params_b(model_id)

        entry, formats_origin = self._resolve_entry(model_id)
        if entry is not None:
            params_b = entry.params_b or params_b
            formats = list(entry.formats_available)
        else:
            formats = []

        result: dict[str, Any] = {
            "model_id": model_id,
            "params_b": params_b,
            "formats_available": [],
            "is_gated": False,
            "compatible": None,
            "status": "insufficient_info",
            "status_label": "Information insuffisante",
        }

        if "/" in model_id:
            try:
                hf_info = await inspect_hf_model(model_id)
            except Exception as exc:  # pas de blocage : garder la réponse heuristique
                logger.warning("inspect_hf_model(%s) a levé une exception : %s", model_id, exc)
                hf_info = {}

            result["formats_available"] = list(
                hf_info.get("formats_available") or formats or ["gguf"]
            )
            if not result["formats_available"]:
                result["formats_available"] = (
                    ["gguf"] if "gguf" in model_id.lower() else ["safetensors"]
                )
            result.update(
                {
                    "params_b": hf_info.get("params_b", params_b),
                    "description": hf_info.get("description", ""),
                    "pipeline_tag": hf_info.get("pipeline_tag", "text-generation"),
                    "is_gated": bool(hf_info.get("is_gated", False)),
                }
            )
        else:
            result["formats_available"] = formats

        compat = check_model_compatibility(
            model_name=model_id,
            params_b=result["params_b"],
            hardware=sys_hw,
        )
        result.update(
            {
                "compatible": compat.compatible,
                "status": compat.status,
                "status_label": compat.status_label,
                "recommended_runtime": compat.recommended_runtime,
                "recommended_format": compat.recommended_format,
                "supported_runtimes": compat.supported_runtimes,
                "gguf_files": (list(hf_info.get("gguf_files", [])) if "/" in model_id else []),
                "formats_origin": ("huggingface" if "/" in model_id else formats_origin),
                # Aucune conversion automatique : si un jour une conversion est
                # réellement supportée, elle sera exposée ici comme opération
                # contrôlée explicite.
                "conversion_supported": False,
                "conversion_operations": [],
                "details": {**compat.details, "model_id": model_id},
            }
        )
        result["method"] = compat.execution_method or (
            "Compatible avec contraintes"
            if compat.status == "compatible_with_constraints"
            else "Incompatible"
            if compat.status == "incompatible"
            else "Information insuffisante"
            if compat.status == "insufficient_info"
            else "Non déterminable"
        )
        return result


_global_model_hub: ModelHub | None = None


def get_model_hub() -> ModelHub:
    """Retourne l'instance unique du ModelHub pour ETHAN Core."""
    global _global_model_hub
    if _global_model_hub is None:
        _global_model_hub = ModelHub()
    return _global_model_hub


# Alias historique : ModelManager = ModelHub (façade unique, pas de doublon).
ModelManager = ModelHub
