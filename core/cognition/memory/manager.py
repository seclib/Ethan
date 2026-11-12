"""Memory Manager — Gère les mémoires multiples."""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class MemoryOutcome(StrEnum):
    """Statut d'un résultat d'action mémorisé (Phase 07).

    Une procédure ne devient **connaissance fiable** qu'après validation :
    - ``TENTATIVE`` : action tentée, résultat non vérifié.
    - ``FAILED``    : action échouée (à ne pas promouvoir).
    - ``SUCCESS``   : action réussie (résultat observé, non encore validé).
    - ``VERIFIED``  : résultat vérifié (reproductible).
    - ``VALIDATED`` : procédure validée → seule connaissance fiable.
    """

    TENTATIVE = "tentative"
    FAILED = "failed"
    SUCCESS = "success"
    VERIFIED = "verified"
    VALIDATED = "validated"

    @property
    def is_reliable(self) -> bool:
        """True si le statut produit une connaissance fiable."""
        return self is MemoryOutcome.VALIDATED



class MemoryManager:
    """Gestionnaire de mémoire multi-niveaux pour le Cognition.

    Mémoires :
    - Working : état temporaire (RAM)
    - Episodic : historique des interactions
    - Semantic : connaissances apprises
    """

    def __init__(self, store=None):
        self._store = store
        self._working_memory: dict[str, Any] = {}

    async def recall(self, query: str, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Rappel associatif depuis les mémoires.

        Args:
            query: Requête de recherche
            context: Contexte actuel

        Returns:
            Liste d'items de mémoire
        """
        results = []

        # 1. Chercher dans la mémoire de travail
        working = self._search_working(query)
        results.extend(working)

        # 2. Chercher dans le store persistant
        if self._store:
            try:
                stored = await self._store.search("cognition:memory", query, limit=5)
                results.extend([
                    {"type": "stored", "content": r.value, "score": r.score}
                    for r in stored
                ])
            except Exception as e:
                logger.warning(f"Memory recall failed: {e}")

        # Trier par pertinence
        results.sort(key=lambda x: x.get("score", 0), reverse=True)

        return results[:10]

    def _search_working(self, query: str) -> list[dict[str, Any]]:
        """Recherche dans la mémoire de travail."""
        results = []
        query_lower = query.lower()

        for key, value in self._working_memory.items():
            if isinstance(value, str) and query_lower in value.lower():
                results.append({
                    "type": "working",
                    "key": key,
                    "content": value,
                    "score": 0.8,
                })

        return results

    async def store_interaction(self, session_id: str, query: str, response: str, success: bool) -> None:
        """Stocke une interaction en mémoire.

        Args:
            session_id: ID de session
            query: Requête utilisateur
            response: Réponse du système
            success: Succès ou échec
        """
        # Mémoire de travail
        self._working_memory[f"last_query:{session_id}"] = query
        self._working_memory[f"last_response:{session_id}"] = response

        # Stockage persistant
        if self._store:
            try:
                await self._store.store(
                    f"cognition:session:{session_id}",
                    f"interaction:{len(query)}",
                    {
                        "query": query,
                        "response": response,
                        "success": success,
                    },
                    ttl=86400,  # 24 heures
                )
            except Exception as e:
                logger.warning(f"Failed to store interaction: {e}")

    def set_working(self, key: str, value: Any) -> None:
        """Définit une valeur en mémoire de travail."""
        self._working_memory[key] = value

    def get_working(self, key: str, default: Any = None) -> Any:
        """Récupère une valeur de la mémoire de travail."""
        return self._working_memory.get(key, default)

    def clear_working(self) -> None:
        """Vide la mémoire de travail."""
        self._working_memory.clear()

    # ── Résultats d'action & procédures (Phase 07) ───────────────────────

    def store_outcome(
        self,
        session_id: str,
        action: str,
        resource: str,
        outcome: MemoryOutcome | str,
        details: dict[str, Any] | None = None,
    ) -> str:
        """Mémorise le résultat d'une action avec son statut de fiabilité.

        Une tentative, un échec, un succès ou un résultat vérifié sont
        enregistrés distinctement. Seul un statut ``VALIDATED`` est fiable.
        """
        status = (
            outcome if isinstance(outcome, MemoryOutcome) else MemoryOutcome(outcome)
        )
        key = f"outcome:{session_id}:{action}:{resource}"
        record = {
            "action": action,
            "resource": resource,
            "outcome": status.value,
            "reliable": status.is_reliable,
            "details": details or {},
        }
        self._working_memory[key] = record
        if self._store is not None:
            try:
                self._store.store(
                    f"cognition:memory:{session_id}",
                    f"outcome:{action}:{resource}",
                    record,
                    ttl=604800,  # 7 jours
                )
            except Exception as exc:
                logger.warning("Memory: store_outcome failed: %s", exc)
        return key

    def store_procedure(
        self,
        session_id: str,
        procedure_name: str,
        steps: list[str],
        outcome: MemoryOutcome | str = MemoryOutcome.TENTATIVE,
    ) -> str:
        """Enregistre une procédure **non encore fiable** (validation requise).

        Une procédure reste en ``TENTATIVE`` (ou échec/succès non validé)
        tant qu'elle n'a pas été explicitement validée. Elle n'est jamais
        promue connaissance fiable automatiquement.
        """
        status = (
            outcome if isinstance(outcome, MemoryOutcome) else MemoryOutcome(outcome)
        )
        key = f"procedure:{session_id}:{procedure_name}"
        record = {
            "name": procedure_name,
            "steps": steps,
            "outcome": status.value,
            "reliable": status.is_reliable,
            "validated": False,
        }
        self._working_memory[key] = record
        if self._store is not None:
            try:
                self._store.store(
                    f"cognition:memory:{session_id}",
                    f"procedure:{procedure_name}",
                    record,
                    ttl=None,
                )
            except Exception as exc:
                logger.warning("Memory: store_procedure failed: %s", exc)
        return key

    def promote_procedure(
        self, session_id: str, procedure_name: str, *, verified_by: str = "human"
    ) -> bool:
        """Valide une procédure → devient connaissance fiable.

        La validation doit venir d'une autorité hors-LLM (humain ou système de
        vérification) — jamais d'une décision de LLM seule (Loi Fondamentale).
        """
        key = f"procedure:{session_id}:{procedure_name}"
        record = self._working_memory.get(key)
        if record is None:
            return False
        if record.get("outcome") == MemoryOutcome.FAILED.value:
            logger.info("Memory: refus de valider une procédure en échec")
            return False
        record = {
            **record,
            "outcome": MemoryOutcome.VALIDATED.value,
            "reliable": True,
            "validated": True,
            "verified_by": verified_by,
        }
        self._working_memory[key] = record
        if self._store is not None:
            try:
                self._store.store(
                    f"cognition:memory:{session_id}",
                    f"procedure:{procedure_name}",
                    record,
                    ttl=None,
                )
            except Exception as exc:
                logger.warning("Memory: promote_procedure failed: %s", exc)
        return True

    def reliable_procedures(self, session_id: str) -> list[dict[str, Any]]:
        """Retourne les seules procédures fiables (VALIDATED).

        Les tentatives, échecs et succès non validés ne sont **pas** exposés
        comme connaissances : seule une procédure validée l'est.
        """
        prefix = f"procedure:{session_id}:"
        return [
            record
            for key, record in self._working_memory.items()
            if key.startswith(prefix)
            and record.get("reliable")
            and record.get("outcome") == MemoryOutcome.VALIDATED.value
        ]
