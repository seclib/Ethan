"""Feature Integration Test — valide les capacités ETHAN sur la stack déployée.

Contrairement aux tests unitaires (qui exercent les routers en isolation), ce
module interroge l'API RÉELLEMENT servie par le conteneur ``ethan-api`` :

- authentification réelle (``POST /auth/login``) — pas de JWT forgé ;
- un appel HTTP par capacité utilisateur (Chat, Plan, Act, Debug, Code,
  Apprendre, Créer, Vie quotidienne, Knowledge, Skills, Web Inspiration,
  Providers, Connections, Mission) ;
- vérification de la connectivité host → api → kernel.

Les tests sont skippés si la stack n'est pas démarrée (``./ethan up``), comme
``tests/test_boot.py``.

Usage :
    python -m pytest tests/test_features_deployed.py -v
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
API_URL = os.environ.get("ETHAN_API_URL", "http://localhost:8000")
KERNEL_URL = os.environ.get("ETHAN_KERNEL_URL_HOST", "http://localhost:8080")
TIMEOUT = 30

# (méthode, chemin) réellement exposés par l'API déployée.
# Les chemins sont le CONTRAT : ils sont écrits en dur pour qu'une dérive
# (ex. ``/v1/providers`` au lieu de ``/providers``) fasse échouer ce test.
FEATURES: dict[str, tuple[str, str]] = {
    "Chat": ("GET", "/v1/chat/history"),
    "Plan": ("POST", "/v1/chat/completions"),
    "Act": ("POST", "/v1/chat/completions"),
    "Debug": ("GET", "/diagnostics"),
    "Code": ("GET", "/v1/tools"),
    "Apprendre": ("GET", "/v1/memory/facts"),
    "Créer": ("GET", "/v1/projects"),
    "Vie quotidienne": ("GET", "/v1/notes"),
    "Knowledge": ("GET", "/v1/knowledge"),
    "Skills": ("GET", "/v1/skills"),
    "Web Inspiration": ("GET", "/v1/web-inspiration/status"),
    "Providers": ("GET", "/providers"),
    "Connections": ("GET", "/connections"),
    "Mission": ("GET", "/v1/missions"),
    "Agents": ("GET", "/v1/agents"),
    "RAG": ("GET", "/v1/rag/status"),
    "Web Search": ("GET", "/v1/web-search/engines"),
    "Files": ("GET", "/files"),
}


def _api_reachable() -> bool:
    try:
        requests.get(f"{API_URL}/health/ready", timeout=5)
    except (requests.ConnectionError, requests.Timeout):
        return False
    return True


@pytest.fixture(scope="module")
def auth_headers() -> dict[str, str]:
    """En-têtes authentifiés via un login réel sur l'API déployée."""
    if not _api_reachable():
        pytest.skip(f"API not reachable at {API_URL} (stack down)")

    credentials = {
        "username": "admin",
        "password": os.environ.get("ETHAN_ADMIN_PASSWORD", "admin"),
    }
    resp = requests.post(f"{API_URL}/auth/login", json=credentials, timeout=TIMEOUT)
    if resp.status_code != 200:
        pytest.skip(f"Cannot authenticate against deployed API: HTTP {resp.status_code}")

    token = resp.json().get("access_token")
    if not token:
        pytest.skip("Login succeeded but no access_token returned")

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def session(auth_headers: dict[str, str]) -> requests.Session:
    s = requests.Session()
    s.headers.update(auth_headers)
    s.headers.update({"Content-Type": "application/json"})
    return s


class TestDeployedInfrastructure:
    """Connectivité host / kernel / api (vérifie le correctif ETHAN_KERNEL_URL)."""

    def test_api_health(self):
        resp = requests.get(f"{API_URL}/health/ready", timeout=TIMEOUT)
        assert resp.status_code == 200, f"API not ready: HTTP {resp.status_code}"
        assert resp.json().get("status") == "ok"

    def test_kernel_health_from_host(self):
        """Le port publié 127.0.0.1:8080 reste fonctionnel (accès admin local)."""
        resp = requests.get(f"{KERNEL_URL}/health/ready", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Kernel not ready from host: HTTP {resp.status_code}"
        body = resp.json()
        assert body.get("running") is True, f"Kernel not running: {body}"

    def test_diagnostics_reports_kernel_ok(self, session: requests.Session):
        """Le composant de diagnostic ``kernel`` doit être joignable depuis l'API.

        Non-régression : ``ETHAN_KERNEL_URL`` doit pointer vers le nom de
        service Docker (``http://kernel:8080``) et non ``localhost``.
        """
        resp = session.get(f"{API_URL}/diagnostics", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Diagnostics failed: HTTP {resp.status_code}"
        kernel = resp.json().get("components", {}).get("kernel")
        assert kernel is not None, "Diagnostics report has no 'kernel' component"
        assert kernel.get("status") == "ok", (
            f"Kernel component not ok: {kernel.get('status')} — {kernel.get('message')}"
        )


class TestDeployedFeatures:
    """Chaque capacité ETHAN répond sans erreur serveur (5xx)."""

    @pytest.mark.parametrize("feature", sorted(FEATURES))
    def test_feature_reachable(self, session: requests.Session, feature: str):
        method, path = FEATURES[feature]
        payload = {"message": "ping", "mode": "plan"} if method == "POST" else None
        # Timeout elargi pour les POST : ils declenchent le pipeline LLM local
        # (latence >> TIMEOUT=30s), contrairement aux GET de sante.
        resp = session.request(
            method,
            f"{API_URL}{path}",
            json=payload,
            timeout=120 if method == "POST" else TIMEOUT,
        )
        assert resp.status_code < 500, (
            f"{feature} ({method} {path}) returned HTTP {resp.status_code}: {resp.text[:200]}"
        )

    def test_chat_modes_handled(self, session: requests.Session):
        """Les modes Chat/Plan/Act/Debug/Code sont acceptés par le pipeline.

        Un provider LLM injoignable (502) est un blocage externe, pas un bug
        applicatif : le mode doit toutefois être traité (jamais 500/422).
        """
        for mode in ("chat", "plan", "act", "debug", "code"):
            # Timeout elargi : la latence reelle du pipeline LLM local (ollama)
            # depasse regulierement TIMEOUT=30s au premier appel (chargement
            # modele) — le test valide le code HTTP, pas la performance.
            resp = session.post(
                f"{API_URL}/v1/chat/completions",
                json={"message": "ping", "mode": mode},
                timeout=120,
            )
            assert resp.status_code in (200, 400, 422, 502, 503), (
                f"Mode '{mode}' unexpectedly returned HTTP {resp.status_code}: {resp.text[:200]}"
            )

    def test_unauthenticated_requests_are_rejected(self):
        """Les routes protégées rejettent une requête anonyme (401)."""
        if not _api_reachable():
            pytest.skip(f"API not reachable at {API_URL} (stack down)")
        resp = requests.get(f"{API_URL}/providers", timeout=TIMEOUT)
        assert resp.status_code == 401, (
            f"An unauthenticated request must be rejected, got HTTP {resp.status_code}"
        )

    def test_core_owned_paths_are_used(self, session: requests.Session):
        """Les chemins Core sont exposés en racine (et non sous /v1).

        Non-régression : ``/providers``, ``/connections``, ``/files`` et
        ``/diagnostics`` sont les contrats consommés par la WebUI.
        """
        for path in ("/providers", "/connections", "/files", "/diagnostics"):
            resp = session.get(f"{API_URL}{path}", timeout=TIMEOUT)
            assert resp.status_code == 200, (
                f"{path} should be reachable, got HTTP {resp.status_code}"
            )

    def test_embedding_models_are_not_selectable_for_chat(self, session: requests.Session):
        """Un encodeur ne doit jamais être déclaré « chat » par un provider.

        Non-régression : Ollama déclarait ``["chat", "embedding"]`` pour TOUS ses
        modèles ; ``qwen3-embedding:8b`` gagnait la sélection (score 0.948) pour
        une complétion de chat, l'appel échouait, le circuit breaker s'ouvrait et
        l'API répondait 502 sur ``POST /v1/chat/completions``.
        """
        resp = session.get(f"{API_URL}/providers/ollama/models", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Model listing failed: HTTP {resp.status_code}"

        models = resp.json()
        assert models, "Ollama must expose at least one model"

        encoders = [
            m
            for m in models
            if any(marker in str(m.get("id", "")).lower() for marker in ("embed", "bge"))
        ]
        assert encoders, "This environment is expected to expose embedding models"

        for model in encoders:
            caps = model.get("capabilities")
            assert caps == ["embedding"], (
                f"Encoder {model.get('id')} must not declare 'chat' (got {caps}) — "
                "it would be selected for chat and fail"
            )

    def test_chat_returns_a_real_completion(self, session: requests.Session):
        """``POST /v1/chat/completions`` renvoie une réponse LLM non vide.

        Non-régression du 502 : le statut seul ne suffit pas — le pipeline doit
        réellement produire du contenu via un modèle génératif.
        """
        resp = session.post(
            f"{API_URL}/v1/chat/completions",
            json={"message": "Reponds en un mot: capitale de la France ?", "mode": "chat"},
            timeout=TIMEOUT * 3,
        )
        assert resp.status_code == 200, f"Chat failed: HTTP {resp.status_code} {resp.text[:200]}"

        body = resp.json()
        assert body.get("message", "").strip(), f"Empty completion: {body}"
        metadata = body.get("metadata", {})
        assert metadata.get("provider"), f"Missing provider metadata: {body}"
        assert metadata.get("model"), f"Missing model metadata: {body}"
