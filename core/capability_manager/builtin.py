"""Spécifications descriptives des capabilities intégrées (déploiement optionnel).

Ces définitions décrivent UNIQUEMENT le déploiement optionnel de services
externes. Elles n'implémentent PAS de logique métier : le RAG (client
vectoriel) vit dans core/rag/ — celles-ci sont des méta-données de
déploiement, pas de duplication de code.
"""

from __future__ import annotations

from core.capability_manager.types import (
    CapabilitySpec,
    CapabilityType,
    ConfigField,
    Dependency,
    HealthCheck,
    Provenance,
)


def qdrant() -> CapabilitySpec:
    """Qdrant en mode optionnel (Docker) — vectordb supporté mais absent par défaut."""
    return CapabilitySpec(
        id="qdrant",
        name="Qdrant Vector Database",
        description=(
            "Base de vecteurs optionnelle (Docker). ETHAN ne l'installe jamais "
            "automatiquement : supported != installed != available."
        ),
        type=CapabilityType.VECTOR_DATABASE,
        backend="docker",
        version="1.12",
        requires_confirmation=True,
        dependencies=(
            Dependency(
                id="docker",
                kind="system",
                command=("docker",),
                description="Docker est requis pour orchertrer Qdrant.",
            ),
        ),
        config_schema=(
            ConfigField(
                name="tag",
                type="string",
                required=False,
                default="v1.12.0",
                description="Tag d'image Docker.",
                choices=("latest", "v1.12.0", "v1.11.2"),
            ),
            ConfigField(
                name="http_port",
                type="port",
                required=False,
                default=6333,
                min_value=1,
                max_value=65535,
                description="Port HTTP exposé.",
            ),
            ConfigField(
                name="grpc_port",
                type="port",
                required=False,
                default=6334,
                min_value=1,
                max_value=65535,
                description="Port gRPC exposé.",
            ),
        ),
        install_actions=(
            {"action": "check_docker"},
            {"action": "pull", "image": "qdrant/qdrant:{config.tag}"},
            {"action": "create_volume", "volume": "qdrant_storage"},
            {
                "action": "run",
                "name": "ethan-qdrant",
                "image": "qdrant/qdrant:{config.tag}",
                "volume": "qdrant_storage:/qdrant/storage",
                "ports": ["{config.http_port}:6333", "{config.grpc_port}:6334"],
                "env": ["QDRANT__TELEMETRY__OPENCOLLECTOR__ENABLED=false"],
                "network": "ethan-net",
            },
        ),
        start_actions=({"action": "start", "name": "ethan-qdrant"},),
        stop_actions=({"action": "stop", "name": "ethan-qdrant"},),
        uninstall_actions=(
            {
                "action": "remove",
                "name": "ethan-qdrant",
                "keep_data": True,
                "data_to_delete": [{"kind": "volume", "name": "qdrant_storage"}],
            },
        ),
        data_resources=(
            {
                "kind": "volume",
                "name": "qdrant_storage",
                "description": "Données vectorielles Qdrant.",
            },
        ),
        health_checks=(
            HealthCheck(kind="tcp", level="basic", port="http_port"),
            HealthCheck(
                kind="endpoint",
                level="functional",
                url="http://127.0.0.1:{config.http_port}/readyz",
            ),
        ),
    )


def chromadb() -> CapabilitySpec:
    """ChromaDB via gestionnaire de paquets Python (dépendance locale)."""
    return CapabilitySpec(
        id="chromadb",
        name="ChromaDB (local package)",
        description=(
            "Vectordb embarquee installee comme paquet Python optionnel "
            "(dependance locale, jamais automatique)."
        ),
        type=CapabilityType.VECTOR_DATABASE,
        backend="python_package",
        version="0.6",
        requires_confirmation=True,
        dependencies=(
            Dependency(
                id="python",
                kind="system",
                command=("python3",),
                description="Python 3.10+ requis.",
            ),
        ),
        config_schema=(
            ConfigField(
                name="host",
                type="string",
                required=False,
                default="127.0.0.1",
                description="Hôte d'écoute.",
            ),
            ConfigField(
                name="port",
                type="int",
                required=False,
                default=8000,
                min_value=1,
                max_value=65535,
                description="Port d'écoute.",
            ),
        ),
        install_actions=(
            {"action": "pip_install", "packages": ["chromadb==0.6.3"]},
            {"action": "verify_import", "module": "chromadb"},
        ),
        start_actions=(),
        stop_actions=(),
        # Le volume des données locale est géré par le backend python_package ;
        # le manager délègue la suppression via data_resources.
        uninstall_actions=({"action": "pip_uninstall", "packages": ["chromadb"]},),
        data_resources=(
            {
                "kind": "directory",
                "path": "~/.local/share/ethan/chromadb",
                "description": "Données vectorielles ChromaDB.",
            },
        ),
        health_checks=(
            HealthCheck(
                kind="endpoint",
                level="functional",
                url="http://{config.host}:{config.port}/api/health",
            ),
        ),
    )


def memory() -> CapabilitySpec:
    """Backend vectoriel intégré (in-process) — toujours disponible.

    Exemple de la spec §8 : « Memory — Built-in in-process backend — Status:
    Ready — [Configure] ». Le health check est réel (import + smoke RAG),
    pas une simple déclaration.
    """
    return CapabilitySpec(
        id="memory",
        name="Memory (built-in vector backend)",
        description=(
            "Backend vectoriel in-process intégré au Core — aucune dépendance, "
            "données en mémoire process. Toujours présent, jamais installé."
        ),
        type=CapabilityType.VECTOR_DATABASE,
        backend="builtin",
        version="1.0",
        requires_confirmation=False,
        dependencies=(),
        config_schema=(
            ConfigField(
                name="collection",
                type="string",
                required=False,
                default="ethan",
                description="Nom de la collection par défaut.",
            ),
        ),
        install_actions=(),
        start_actions=(),
        stop_actions=(),
        uninstall_actions=(),
        data_resources=(
            {
                "kind": "memory",
                "name": "vectors (in-process)",
                "description": "Vecteurs en mémoire process — perdus au redémarrage.",
            },
        ),
        health_checks=(HealthCheck(kind="builtin", level="functional"),),
    )


def ollama() -> CapabilitySpec:
    """Ollama — serveur d'inférence local (provider LLM natif)."""
    return CapabilitySpec(
        id="ollama",
        name="Ollama",
        description=(
            "Serveur d'inférence LLM local. ETHAN détecte sa présence "
            "mais ne l'installe jamais automatiquement."
        ),
        type=CapabilityType.PROVIDER,
        backend="executable",
        version="0.5",
        requires_confirmation=False,
        provenance=Provenance(
            source="official",
            author="Ollama Inc.",
            url="https://ollama.com",
            license="MIT",
        ),
        dependencies=(),
        config_schema=(
            ConfigField(
                name="base_url",
                type="string",
                required=False,
                default="http://localhost:11434",
                description="URL de base de l'API Ollama.",
            ),
        ),
        install_actions=({"action": "verify_path", "executable": "ollama"},),
        start_actions=(),
        stop_actions=(),
        uninstall_actions=(),
        health_checks=(
            HealthCheck(
                kind="endpoint",
                level="functional",
                url="{config.base_url}/api/tags",
            ),
        ),
    )


def redis() -> CapabilitySpec:
    """Redis — backend d'état live optionnel (Docker)."""
    return CapabilitySpec(
        id="redis",
        name="Redis",
        description=(
            "Backend d'état en mémoire. Utilisé pour le state live, "
            "les sessions et le cache. Optionnel : ETHAN fonctionne "
            "sans (fallback en mémoire process)."
        ),
        type=CapabilityType.SERVICE,
        backend="docker",
        version="7.4",
        requires_confirmation=True,
        provenance=Provenance(
            source="official",
            author="Redis Ltd.",
            url="https://redis.io",
            license="RSALv2",
        ),
        dependencies=(
            Dependency(
                id="docker",
                kind="system",
                command=("docker",),
                description="Docker requis pour Redis.",
            ),
        ),
        config_schema=(
            ConfigField(
                name="port",
                type="port",
                required=False,
                default=6379,
                min_value=1,
                max_value=65535,
                description="Port TCP exposé.",
            ),
        ),
        install_actions=(
            {"action": "check_docker"},
            {"action": "pull", "image": "redis:7.4-alpine"},
            {"action": "create_volume", "volume": "ethan_redis_data"},
            {
                "action": "run",
                "name": "ethan-redis",
                "image": "redis:7.4-alpine",
                "ports": ["{config.port}:6379"],
                "volume": "ethan_redis_data:/data",
                "network": "ethan-net",
                "command": ["redis-server", "--appendonly", "yes"],
            },
        ),
        start_actions=({"action": "start", "name": "ethan-redis"},),
        stop_actions=({"action": "stop", "name": "ethan-redis"},),
        uninstall_actions=(
            {
                "action": "remove",
                "name": "ethan-redis",
                "keep_data": True,
                "data_to_delete": [{"kind": "volume", "name": "ethan_redis_data"}],
            },
        ),
        data_resources=(
            {
                "kind": "volume",
                "name": "ethan_redis_data",
                "description": "Données Redis persistantes (AOF).",
            },
        ),
        health_checks=(
            HealthCheck(kind="tcp", level="basic", port="port"),
            HealthCheck(
                kind="exec",
                level="functional",
                command=("docker", "exec", "ethan-redis", "redis-cli", "ping"),
            ),
        ),
    )


def searxng() -> CapabilitySpec:
    """SearXNG — moteur de recherche web privé (Docker)."""
    return CapabilitySpec(
        id="searxng",
        name="SearXNG",
        description=(
            "Moteur de méta-recherche web privé. Fournit la capacité "
            "de recherche web aux skills et au RAG sans dépendance API cloud."
        ),
        type=CapabilityType.SERVICE,
        backend="docker",
        version="latest",
        requires_confirmation=True,
        provenance=Provenance(
            source="community",
            author="SearXNG team",
            url="https://docs.searxng.org",
            license="AGPL-3.0",
        ),
        dependencies=(
            Dependency(
                id="docker",
                kind="system",
                command=("docker",),
                description="Docker requis.",
            ),
        ),
        config_schema=(
            ConfigField(
                name="http_port",
                type="port",
                required=False,
                default=8888,
                min_value=1,
                max_value=65535,
                description="Port HTTP exposé.",
            ),
        ),
        install_actions=(
            {"action": "check_docker"},
            {"action": "pull", "image": "searxng/searxng:latest"},
            {
                "action": "run",
                "name": "ethan-searxng",
                "image": "searxng/searxng:latest",
                "ports": ["{config.http_port}:8080"],
                "network": "ethan-net",
            },
        ),
        start_actions=({"action": "start", "name": "ethan-searxng"},),
        stop_actions=({"action": "stop", "name": "ethan-searxng"},),
        uninstall_actions=(
            {
                "action": "remove",
                "name": "ethan-searxng",
                "keep_data": True,
                "data_to_delete": [],
            },
        ),
        health_checks=(
            HealthCheck(kind="tcp", level="basic", port="http_port"),
            HealthCheck(
                kind="endpoint",
                level="functional",
                url="http://127.0.0.1:{config.http_port}/healthz",
            ),
        ),
    )


def whisper() -> CapabilitySpec:
    """Whisper — transcription audio locale (paquet Python)."""
    return CapabilitySpec(
        id="whisper",
        name="Whisper (OpenAI)",
        description=(
            "Modèle de transcription audio (speech-to-text) local. "
            "Installé comme paquet Python optionnel."
        ),
        type=CapabilityType.STT_TTS,
        backend="python_package",
        version="1.0",
        requires_confirmation=True,
        provenance=Provenance(
            source="official",
            author="OpenAI",
            url="https://github.com/openai/whisper",
            license="MIT",
        ),
        dependencies=(
            Dependency(
                id="python",
                kind="system",
                command=("python3",),
                description="Python 3.10+ requis.",
            ),
            Dependency(
                id="ffmpeg",
                kind="system",
                command=("ffmpeg",),
                optional=True,
                description="FFmpeg pour le décodage audio (recommandé).",
            ),
        ),
        config_schema=(
            ConfigField(
                name="model_size",
                type="string",
                required=False,
                default="base",
                choices=("tiny", "base", "small", "medium", "large"),
                description="Taille du modèle Whisper.",
            ),
        ),
        install_actions=(
            {"action": "pip_install", "packages": ["openai-whisper"]},
            {"action": "verify_import", "module": "whisper"},
        ),
        start_actions=(),
        stop_actions=(),
        uninstall_actions=({"action": "pip_uninstall", "packages": ["openai-whisper"]},),
        health_checks=(),
    )


def mcp_filesystem() -> CapabilitySpec:
    """Serveur MCP officiel « filesystem » (paquet Node) — accès fichiers.

    Transport stdio : le binaire installé est lancé à la demande par le
    client MCP d'ETHAN (`core/tools/mcp_client.py`), il n'y a donc aucun
    processus permanent — pas d'actions start/stop (comme `ollama`).
    """
    return CapabilitySpec(
        id="mcp-filesystem",
        name="MCP Filesystem Server",
        description=(
            "Serveur MCP officiel d'accès aux fichiers (transport stdio), "
            "installé comme paquet Node local. Lancé à la demande par le "
            "client MCP — aucun processus permanent."
        ),
        type=CapabilityType.MCP_SERVER,
        backend="node_package",
        version="2026.8.31",
        requires_confirmation=True,
        provenance=Provenance(
            source="official",
            author="Model Context Protocol (LF Projects, LLC.)",
            url="https://github.com/modelcontextprotocol/servers",
            # Licence upstream « SEE LICENSE IN LICENSE » : rien n'est
            # inventé, le champ reste vide si la source ne l'énonce pas.
            license="",
        ),
        dependencies=(
            Dependency(
                id="npm",
                kind="system",
                command=("npm",),
                description="Node.js/npm requis pour les paquets Node.",
            ),
        ),
        config_schema=(),
        install_actions=(
            {
                "action": "npm_install",
                "packages": ["@modelcontextprotocol/server-filesystem@2026.8.31"],
            },
            {"action": "verify_binary", "binary": "mcp-server-filesystem"},
        ),
        start_actions=(),
        stop_actions=(),
        uninstall_actions=(
            {
                "action": "npm_uninstall",
                "packages": ["@modelcontextprotocol/server-filesystem"],
            },
        ),
        # Pas d'endpoint permanent à sonder : aucun health check fonctionnel
        # n'est déclarable honnêtement — le composant reste INSTALLED, jamais
        # un faux READY (la présence est vérifiée par `verify_binary`).
        health_checks=(),
    )


def registry() -> list[CapabilitySpec]:
    """Catalogue des capabilities intégrées (déclaratif, extensible)."""
    return [
        memory(),
        ollama(),
        qdrant(),
        chromadb(),
        redis(),
        searxng(),
        whisper(),
        mcp_filesystem(),
    ]


def build_manager(**kwargs):
    """Construit un CapabilityManager pre-enregistre avec le catalogue builtin.

    Point d'entree unique pour l'API et les tests : evite la duplication de la
    boucle d'enregistrement dans les interfaces (le Core reste la source).
    """
    from core.capability_manager.manager import CapabilityManager

    manager = CapabilityManager(registry={}, **kwargs)
    for spec in registry():
        manager.register(spec)
    return manager
