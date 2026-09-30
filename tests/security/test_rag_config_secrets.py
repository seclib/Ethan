"""Secrets de configuration RAG — jamais exposés, jamais persistés.

``RAGPipeline`` accepte une ``vector_backend_config`` fournie par un rôle
privilégié (ex. ``PUT /v1/rag/config`` avec la clé API d'un backend Qdrant).
Faille confirmée par audit :

- ``get_config()`` renvoyait la config backend **verbatim** → la clé était
  lisible par tout rôle authentifié via ``GET /v1/rag/config`` (le GET n'est
  pas restreint alors que le PUT exige ADMIN) ;
- ``persist_config()`` sauvegardait ``get_config()`` → la clé était écrite en
  clair dans le record store ;
- un round-trip GET→PUT (éditeur JSON de la WebUI) pouvait écraser le secret.

Garantis ici : redaction en sortie (présence booléenne uniquement),
persistance sans secret, préservation du secret lors d'un round-trip UI, et
effacement explicite possible (chaîne vide).

Aucun appel réseau : le backend vectoriel n'est pas chargé (``_loaded=False``).
"""

from __future__ import annotations

import asyncio

from core.rag.pipeline import RAGPipeline
from core.state.record_store import CoreRecordStore

_SECRET = "sk-qdrant-secret"


def _pipeline() -> RAGPipeline:
    return RAGPipeline(store=CoreRecordStore())


def test_get_config_redacts_backend_secret():
    """``get_config()`` remplace la valeur du secret par un booléen."""
    pipeline = _pipeline()
    pipeline._vector_backend_config = {
        "host": "qdrant",
        "port": 6333,
        "api_key": _SECRET,
    }

    config = pipeline.get_config()

    backend = config["vector_backend_config"]
    assert backend["host"] == "qdrant"
    assert backend["api_key"] is True  # présence, jamais la valeur
    assert _SECRET not in str(config)


def test_persist_config_never_writes_secret():
    """La config persistée (survit au redémarrage) ne contient aucun secret."""

    async def run():
        pipeline = _pipeline()
        await pipeline.configure(
            vector_backend="qdrant",
            vector_backend_config={"host": "qdrant", "port": 6333, "api_key": _SECRET},
        )
        await pipeline.persist_config()

        stored = await pipeline._store.get("rag-config", "global")
        assert stored is not None
        assert "api_key" not in stored["vector_backend_config"]
        assert stored["vector_backend_config"]["host"] == "qdrant"

    asyncio.run(run())


def test_round_trip_get_put_keeps_secret():
    """L'UI renvoie ``api_key: true`` (redacté) : le secret doit survivre."""

    async def run():
        pipeline = _pipeline()
        await pipeline.configure(
            vector_backend="qdrant",
            vector_backend_config={"api_key": _SECRET, "host": "old"},
        )
        # Simule le PUT issu de l'éditeur JSON (booléen de présence + host modifié).
        await pipeline.configure(
            vector_backend="qdrant",
            vector_backend_config={"api_key": True, "host": "new"},
        )

        assert pipeline._vector_backend_config["api_key"] == _SECRET
        assert pipeline._vector_backend_config["host"] == "new"
        # Et la sortie reste redactée.
        assert pipeline.get_config()["vector_backend_config"]["api_key"] is True

    asyncio.run(run())


def test_explicit_empty_string_clears_secret():
    """Un effacement explicite (chaîne vide) reste possible."""

    async def run():
        pipeline = _pipeline()
        await pipeline.configure(
            vector_backend="qdrant",
            vector_backend_config={"api_key": _SECRET, "host": "h"},
        )
        await pipeline.configure(
            vector_backend="qdrant",
            vector_backend_config={"api_key": ""},
        )
        assert pipeline._vector_backend_config.get("api_key") == ""

    asyncio.run(run())
