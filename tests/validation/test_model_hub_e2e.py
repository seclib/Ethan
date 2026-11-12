"""
Validation réelle de bout en bout du Model Hub d'ETHAN.

Parcours testé :
1. Hardware Detection : détection CPU, RAM, GPU, VRAM, backend
2. Hugging Face Search : recherche d'un modèle réel sur Hugging Face Hub
3. Hugging Face Metadata : récupération des métadonnées (formats, gating, taille)
4. Analyse de compatibilité : adéquation matérielle, mémoire, tokens/s
5. Sélection du chemin d'exécution : sélection déterministe (Ollama GGUF, vLLM, etc.)
6. Téléchargement / Installation : installation via ETHAN Core
7. Runtime Verification & Health-check : test de connectivité réel à Ollama
8. Modèle réellement disponible : vérification dans le catalogue ETHAN
9. Test d'un modèle Ollama déjà présent : inspection et validation directe
"""

import asyncio
import os
import sys
import time
from typing import Any

# Ensure ETHAN root is in python path
ETHAN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ETHAN_ROOT)


async def run_validation():
    results: dict[str, dict[str, Any]] = {}

    print("=" * 80)
    print("  VALIDATION DU MODEL HUB D'ETHAN — PARCOURS COMPLET RÉEL")
    print("=" * 80)

    # ──────────────────────────────────────────────────────────────────────────
    # 1. Hardware Detection
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[ETAPE 1] Hardware Detection")
    try:
        from core.hardware.detector import get_system_hardware
        hw = get_system_hardware()
        print(f"  CPU Cores : {hw.get('cpu_cores')}")
        print(f"  Total RAM : {hw.get('total_ram_gb')} Go (Dispo: {hw.get('available_ram_gb')} Go)")
        print(f"  GPU Count : {hw.get('gpu_count')}")
        print(f"  GPU Name  : {hw.get('gpu_name', 'N/A')}")
        print(f"  GPU VRAM  : {hw.get('gpu_vram_gb', 0)} Go (Libre: {hw.get('gpu_vram_free_gb', 0)} Go)")
        print(f"  Backend   : {hw.get('backend', 'N/A')}")

        if hw.get("cpu_cores") and hw.get("total_ram_gb"):
            results["1_hardware_detection"] = {
                "status": "PASS",
                "details": f"Détecté : {hw.get('cpu_cores')} coeurs, {hw.get('total_ram_gb')} Go RAM, {hw.get('gpu_name', 'CPU')} ({hw.get('backend')})",
            }
            print("  ==> STATUT : PASS")
        else:
            results["1_hardware_detection"] = {"status": "FAIL", "details": "Champs matériels manquants"}
            print("  ==> STATUT : FAIL")
    except Exception as e:
        results["1_hardware_detection"] = {"status": "FAIL", "details": str(e)}
        print(f"  ==> STATUT : FAIL ({e})")

    # ──────────────────────────────────────────────────────────────────────────
    # 2. Hugging Face Search
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[ETAPE 2] Hugging Face Search (Recherche d'un modèle réel)")
    hf_query = "qwen2.5-coder"
    hf_matches = []
    try:
        from core.models.hf import search_hf_models
        t0 = time.time()
        hf_matches = await search_hf_models(query=hf_query, limit=5)
        dt = time.time() - t0
        print(f"  Recherche '{hf_query}' sur Hugging Face Hub ({dt:.2f}s) :")
        for m in hf_matches:
            print(f"    - {m.get('id')} (formats: {m.get('formats_available', [])})")

        if len(hf_matches) > 0:
            results["2_hf_search"] = {
                "status": "PASS",
                "details": f"{len(hf_matches)} modèles trouvés en {dt:.2f}s (ex: {hf_matches[0].get('id')})",
            }
            print("  ==> STATUT : PASS")
        else:
            results["2_hf_search"] = {"status": "FAIL", "details": "Aucun résultat retourné par HF Hub"}
            print("  ==> STATUT : FAIL")
    except Exception as e:
        results["2_hf_search"] = {"status": "FAIL", "details": str(e)}
        print(f"  ==> STATUT : FAIL ({e})")

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Récupération des métadonnées Hugging Face
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[ETAPE 3] Récupération des métadonnées Hugging Face")
    target_hf_repo = "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
    hf_meta = {}
    try:
        from core.models.hf import inspect_hf_model
        t0 = time.time()
        hf_meta = await inspect_hf_model(target_hf_repo)
        dt = time.time() - t0
        print(f"  Repo cible : {target_hf_repo} ({dt:.2f}s)")
        print(f"    - Formats détectés : {hf_meta.get('formats_available')}")
        print(f"    - Est gated / privé : {hf_meta.get('is_gated')}")
        print(f"    - Fichiers examinés : {len(hf_meta.get('files', []))}")
        print(f"    - Paramètres estimés : {hf_meta.get('params_billions')}B")

        if "gguf" in hf_meta.get("formats_available", []):
            results["3_hf_metadata"] = {
                "status": "PASS",
                "details": f"Artefact GGUF confirmé sur {target_hf_repo}, {len(hf_meta.get('files', []))} fichiers",
            }
            print("  ==> STATUT : PASS")
        else:
            results["3_hf_metadata"] = {"status": "PARTIAL", "details": "Formats détectés mais non-GGUF"}
            print("  ==> STATUT : PARTIAL")
    except Exception as e:
        results["3_hf_metadata"] = {"status": "FAIL", "details": str(e)}
        print(f"  ==> STATUT : FAIL ({e})")

    # ──────────────────────────────────────────────────────────────────────────
    # 4. Analyse de compatibilité matérielle
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[ETAPE 4] Analyse de compatibilité matérielle")
    try:
        from core.hardware.fit import check_model_compatibility
        compat = check_model_compatibility(
            model_name=target_hf_repo,
            params_b=7.0,
            quantization="Q4_K_M",
            hardware=hw,
        )
        print(f"  Compatibilité pour 7B Q4_K_M sur le système :")
        print(f"    - Statut            : {compat.status} ({compat.status_label})")
        print(f"    - Méthode           : {compat.execution_method}")
        print(f"    - Runtime suggéré   : {compat.recommended_runtime}")
        print(f"    - RAM nécessaire    : ~{compat.ram_required_gb} Go")
        print(f"    - VRAM nécessaire   : ~{compat.vram_required_gb} Go")
        print(f"    - Vitesse estimée   : {compat.estimated_speed_tps} tok/s")
        print(f"    - Raison            : {compat.reason}")

        if compat.status in ("compatible", "compatible_with_constraints"):
            results["4_compatibility_analysis"] = {
                "status": "PASS",
                "details": f"Statut '{compat.status}', méthode '{compat.execution_method}', VRAM ~{compat.vram_required_gb}Go",
            }
            print("  ==> STATUT : PASS")
        else:
            results["4_compatibility_analysis"] = {
                "status": "FAIL",
                "details": f"Modèle marqué incompatible sans raison valable : {compat.reason}",
            }
            print("  ==> STATUT : FAIL")
    except Exception as e:
        results["4_compatibility_analysis"] = {"status": "FAIL", "details": str(e)}
        print(f"  ==> STATUT : FAIL ({e})")

    # ──────────────────────────────────────────────────────────────────────────
    # 5. Sélection d'une méthode compatible via Model Hub Façade
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[ETAPE 5] Sélection de la méthode compatible (ModelHub.inspect)")
    try:
        from core.models.hub import get_model_hub
        hub = get_model_hub()
        inspection = await hub.inspect(model_id=target_hf_repo, hardware=hw)
        print(f"  ModelHub.inspect('{target_hf_repo}') :")
        print(f"    - Can Run            : {inspection.get('can_run')}")
        print(f"    - Status             : {inspection.get('status')}")
        print(f"    - Method sélectionnée: {inspection.get('method')}")
        print(f"    - Formats            : {inspection.get('formats_available')}")

        if inspection.get("can_run") and "Ollama" in inspection.get("method", ""):
            results["5_method_selection"] = {
                "status": "PASS",
                "details": f"Méthode sélectionnée : {inspection.get('method')}",
            }
            print("  ==> STATUT : PASS")
        else:
            results["5_method_selection"] = {
                "status": "PARTIAL",
                "details": f"Méthode : {inspection.get('method')}",
            }
            print("  ==> STATUT : PARTIAL")
    except Exception as e:
        results["5_method_selection"] = {"status": "FAIL", "details": str(e)}
        print(f"  ==> STATUT : FAIL ({e})")

    # ──────────────────────────────────────────────────────────────────────────
    # 6. Vérification du runtime et Health-check
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[ETAPE 6] Vérification du runtime et Health-check réel")
    try:
        from core.llm.provider_manager import ProviderManager
        from core.llm.store import ProviderStore
        prov_store = ProviderStore()
        manager = ProviderManager(store=prov_store)
        await manager.initialize()

        hub = get_model_hub()
        health = await hub.check_runtime_health(manager=manager)
        print(f"  Health check global : {health.get('status')}")
        for r_name, r_info in health.get("runtimes", {}).items():
            print(f"    - Runtime {r_name} : actif={r_info.get('enabled')}, joignable={r_info.get('reachable')}, latence={r_info.get('latency_ms')}ms")

        ollama_status = health.get("runtimes", {}).get("ollama", {})
        if ollama_status.get("reachable"):
            results["6_runtime_healthcheck"] = {
                "status": "PASS",
                "details": f"Ollama joignable avec latence {ollama_status.get('latency_ms')}ms",
            }
            print("  ==> STATUT : PASS")
        else:
            results["6_runtime_healthcheck"] = {
                "status": "PARTIAL",
                "details": f"Runtimes testés mais Ollama non joignable (status={health.get('status')})",
            }
            print("  ==> STATUT : PARTIAL")
    except Exception as e:
        results["6_runtime_healthcheck"] = {"status": "FAIL", "details": str(e)}
        print(f"  ==> STATUT : FAIL ({e})")

    # ──────────────────────────────────────────────────────────────────────────
    # 7. Téléchargement / Installation du modèle dans ETHAN
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[ETAPE 7] Téléchargement / Installation du modèle dans ETHAN")
    # Pour ne pas bloquer sur un téléchargement multi-giga octets réseau,
    # on installe un tag léger ou un modèle disponible
    install_target = "qwen2.5:7b"
    try:
        from core.llm.model_store import ModelStore
        model_store = ModelStore()

        install_res = await hub.install(
            model_id=install_target,
            provider_hint="ollama",
            manager=manager,
            store=model_store,
            hardware=hw,
        )
        print(f"  Résultat de hub.install('{install_target}') :")
        print(f"    - Succès   : {install_res.get('success')}")
        print(f"    - Runtime  : {install_res.get('runtime')}")
        print(f"    - Provider : {install_res.get('provider')}")
        print(f"    - Message  : {install_res.get('message')}")

        if install_res.get("success"):
            results["7_model_installation"] = {
                "status": "PASS",
                "details": f"Modèle {install_target} installé avec succès via runtime {install_res.get('runtime')}",
            }
            print("  ==> STATUT : PASS")
        else:
            results["7_model_installation"] = {
                "status": "FAIL",
                "details": install_res.get("message", "Échec installation"),
            }
            print("  ==> STATUT : FAIL")
    except Exception as e:
        results["7_model_installation"] = {"status": "FAIL", "details": str(e)}
        print(f"  ==> STATUT : FAIL ({e})")

    # ──────────────────────────────────────────────────────────────────────────
    # 8. Modèle réellement disponible dans ETHAN
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[ETAPE 8] Modèle réellement disponible dans ETHAN (list_installed)")
    try:
        installed_list = await hub.list_installed(manager=manager, store=model_store)
        print(f"  Modèles retournés par hub.list_installed : {len(installed_list)}")
        installed_ids = [m.get("id") for m in installed_list]
        for item in installed_list[:5]:
            print(f"    - {item.get('id')} [{item.get('provider')}] (local={item.get('is_local')})")

        has_target = any(install_target in mid for mid in installed_ids)
        if len(installed_list) > 0 and has_target:
            results["8_model_available"] = {
                "status": "PASS",
                "details": f"{len(installed_list)} modèles disponibles, dont {install_target}",
            }
            print("  ==> STATUT : PASS")
        elif len(installed_list) > 0:
            results["8_model_available"] = {
                "status": "PARTIAL",
                "details": f"{len(installed_list)} modèles retournés mais {install_target} non listé",
            }
            print("  ==> STATUT : PARTIAL")
        else:
            results["8_model_available"] = {
                "status": "FAIL",
                "details": "Aucun modèle retourné dans list_installed",
            }
            print("  ==> STATUT : FAIL")
    except Exception as e:
        results["8_model_available"] = {"status": "FAIL", "details": str(e)}
        print(f"  ==> STATUT : FAIL ({e})")

    # ──────────────────────────────────────────────────────────────────────────
    # 9. Test d'un modèle Ollama déjà présent
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[ETAPE 9] Test d'un modèle Ollama déjà présent localement")
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://localhost:11434/api/tags")
            ollama_models = resp.json().get("models", [])

        if ollama_models:
            first_ollama = next((m["name"] for m in ollama_models if "3b" in m["name"] or "1b" in m["name"]), ollama_models[0]["name"])
            print(f"  Modèle Ollama existant sélectionné : {first_ollama}")
            # Inspecter ce modèle via le ModelHub
            ollama_inspection = await hub.inspect(model_id=first_ollama, hardware=hw)
            print(f"    - Can Run          : {ollama_inspection.get('can_run')}")
            print(f"    - Statut           : {ollama_inspection.get('status')}")
            print(f"    - Méthode          : {ollama_inspection.get('method')}")
            print(f"    - Runtime suggéré  : {ollama_inspection.get('compatibility', {}).get('recommended_runtime')}")

            # Tester la complétion minimale si le runtime est joignable (timeout 45s pour chargement initial VRAM)
            async with httpx.AsyncClient(timeout=45.0) as client:
                gen_resp = await client.post(
                    "http://localhost:11434/api/generate",
                    json={"model": first_ollama, "prompt": "Hi", "stream": False},
                )
                if gen_resp.status_code == 200:
                    ans = gen_resp.json().get("response", "")[:40].replace("\n", " ")
                    print(f"    - Inférence réelle : OK (réponse: '{ans}...')")
                    results["9_ollama_existing_model"] = {
                        "status": "PASS",
                        "details": f"Modèle {first_ollama} présent, inspecté et inférence confirmée",
                    }
                    print("  ==> STATUT : PASS")
                else:
                    results["9_ollama_existing_model"] = {
                        "status": "PARTIAL",
                        "details": f"Modèle {first_ollama} présent mais erreur generate ({gen_resp.status_code})",
                    }
                    print("  ==> STATUT : PARTIAL")
        else:
            results["9_ollama_existing_model"] = {
                "status": "NOT IMPLEMENTED",
                "details": "Aucun modèle présent dans Ollama sur l'hôte",
            }
            print("  ==> STATUT : NOT IMPLEMENTED (aucun modèle présent)")
    except Exception as e:
        results["9_ollama_existing_model"] = {"status": "FAIL", "details": str(e)}
        print(f"  ==> STATUT : FAIL ({e})")

    # ──────────────────────────────────────────────────────────────────────────
    # 10. Stockage racine (/models) et suivi des téléchargements
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[ETAPE 10] Emplacement de stockage racine (/models) et suivi des téléchargements")
    try:
        from core.models.downloader import get_model_downloader
        dl = get_model_downloader()
        downloads_list = hub.list_downloads()
        print(f"  Répertoire de stockage des modèles : {dl.cache_dir}")
        print(f"  Tâches de téléchargement enregistrées : {len(downloads_list)}")
        for d in downloads_list[:3]:
            print(f"    - {d.get('repo_id')} [{d.get('status')}] ({d.get('percent')}%) via {d.get('runtime')}")

        layout = hub.get_storage_layout()
        is_root_models = str(layout.models_dir).endswith("/models") and "/models" in dl.cache_dir
        if is_root_models and len(downloads_list) > 0:
            results["10_storage_and_downloads"] = {
                "status": "PASS",
                "details": f"Stockage configuré sur {layout.models_dir} (downloads: {dl.cache_dir}) avec {len(downloads_list)} tâche(s) tracée(s)",
            }
            print("  ==> STATUT : PASS")
        elif is_root_models:
            results["10_storage_and_downloads"] = {
                "status": "PASS",
                "details": f"Stockage configuré sur {layout.models_dir}",
            }
            print("  ==> STATUT : PASS")
        else:
            results["10_storage_and_downloads"] = {
                "status": "FAIL",
                "details": f"Emplacement de stockage inattendu : {dl.cache_dir}",
            }
            print("  ==> STATUT : FAIL")
    except Exception as e:
        results["10_storage_and_downloads"] = {"status": "FAIL", "details": str(e)}
        print(f"  ==> STATUT : FAIL ({e})")

    # ──────────────────────────────────────────────────────────────────────────
    # Résumé et Table Finale
    # ──────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("  TABLEAU RÉCAPITULATIF DE LA VALIDATION RÉELLE")
    print("=" * 80)
    print(f"  {'CAPACITE / PARCOURS':<35} | {'STATUT':<12} | DETAILS")
    print("  " + "-" * 76)
    for cap, info in results.items():
        st = info["status"]
        det = info["details"]
        print(f"  {cap:<35} | {st:<12} | {det}")
    print("=" * 80)

    pass_count = sum(1 for x in results.values() if x["status"] == "PASS")
    partial_count = sum(1 for x in results.values() if x["status"] == "PARTIAL")
    fail_count = sum(1 for x in results.values() if x["status"] == "FAIL")
    not_impl_count = sum(1 for x in results.values() if x["status"] == "NOT IMPLEMENTED")

    print(f"  Total : {len(results)} | PASS : {pass_count} | PARTIAL : {partial_count} | FAIL : {fail_count} | NOT IMPLEMENTED : {not_impl_count}")
    print("=" * 80 + "\n")

    return results


if __name__ == "__main__":
    asyncio.run(run_validation())
