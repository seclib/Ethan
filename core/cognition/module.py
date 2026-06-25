"""Cognition Module — Le cerveau d'ETHAN.

Module principal qui orchestre tous les sous-modules cognitifs.
Reçoit des requêtes abstraites et produit des réponses intelligentes.
"""

from __future__ import annotations

import logging
from typing import Any

from core.agents.base import Agent, AgentConfig
from core.cognition.types import (
    CognitionRequest,
    CognitionResponse,
    CognitiveState,
    Intent,
    IntentType,
    Reasoning,
)
from core.types.event import Event, EventType
from core.types.result import Result

logger = logging.getLogger(__name__)


class CognitionModule(Agent):
    """Module Cognition — cerveau d'ETHAN.

    Orchestre :
    - Intention Analyzer : comprendre la requête
    - Context Manager : assembler le contexte
    - Memory Manager : gérer les mémoires
    - Reasoner : raisonner (LLM)
    - Planner : planifier (DAG)
    - Executor : exécuter les actions
    - Reflector : réfléchir et évaluer
    """

    def __init__(self, config: AgentConfig, bus=None):
        super().__init__(config, bus)
        self._states: dict[str, CognitiveState] = {}

    async def _on_init(self) -> None:
        """Initialise le module Cognition."""
        logger.info("🧠 Cognition module initializing...")

    async def _subscribe_events(self) -> None:
        """S'abonne aux événements."""
        await self.subscribe("ethan.cognition.request", self._handle_request)

    async def _handle_request(self, event: Event) -> None:
        """Traite une requête cognitive."""
        query = event.payload.get("query", "")
        session_id = event.payload.get("session_id", "default")
        context = event.payload.get("context", {})
        constraints = event.payload.get("constraints", {})
        expected_output = event.payload.get("expected_output", "text")

        logger.info(f"🧠 Cognition received: {query[:50]}...")

        # Créer la requête
        request = CognitionRequest(
            query=query,
            context=context,
            session_id=session_id,
            constraints=constraints,
            expected_output=expected_output,
        )

        # Traiter la requête
        response = await self.process(request)

        # Publier la réponse
        await self.publish(
            EventType.COGNITION_RESPONSE,
            {
                "success": response.success,
                "output": response.output,
                "reasoning": response.reasoning,
                "confidence": response.confidence,
                "needs_clarification": response.needs_clarification,
                "clarification_questions": response.clarification_questions,
                "metadata": response.metadata,
            },
            correlation_id=event.correlation_id,
        )

        logger.info(f"🧠 Cognition responded: success={response.success}")

    async def process(self, request: CognitionRequest) -> CognitionResponse:
        """Traite une requête cognitive.

        Flux :
        1. Comprendre (Intention Analyzer)
        2. Contextualiser (Context Manager)
        3. Raisonner (Reasoner)
        4. Planifier (Planner)
        5. Exécuter (Executor)
        6. Réfléchir (Reflector)
        7. Mémoriser (Memory Manager)

        Args:
            request: Requête cognitive

        Returns:
            Réponse cognitive
        """
        # Récupérer ou créer l'état cognitif
        state = self._get_or_create_state(request.session_id)

        try:
            # 1. Comprendre
            intent = await self._analyze_intent(request.query)
            state.current_intent = intent

            if intent.confidence < 0.7:
                questions = await self._generate_clarification(request.query)
                return CognitionResponse(
                    success=False,
                    needs_clarification=True,
                    clarification_questions=questions,
                    metadata={"intent_confidence": intent.confidence},
                )

            # 2. Contextualiser
            context = await self._assemble_context(request.session_id, request.query, intent)
            state.context_window = context.get("messages", [])

            # 3. Raisonner
            reasoning = await self._reason(request.query, intent, context)
            state.last_reasoning = reasoning

            # 4. Planifier
            plan = await self._plan(reasoning.goal, reasoning.required_capabilities)

            # 5. Exécuter
            results = await self._execute(plan)

            # 6. Réfléchir
            evaluation = await self._reflect(request.query, plan, results)

            # 7. Mémoriser
            await self._memorize(request.session_id, request.query, evaluation)

            return CognitionResponse(
                success=evaluation["success"],
                output=evaluation["output"],
                reasoning=reasoning.chain_of_thought,
                confidence=evaluation["confidence"],
                metadata={
                    "tokens_used": reasoning.tokens_used,
                    "latency_ms": evaluation["latency_ms"],
                    "plan_id": plan.get("id"),
                    "intent": intent.type.value,
                },
            )

        except Exception as e:
            logger.error(f"Cognition error: {e}", exc_info=True)
            return CognitionResponse(
                success=False,
                output=None,
                reasoning=f"Error: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e)},
            )

    def _get_or_create_state(self, session_id: str) -> CognitiveState:
        """Récupère ou crée un état cognitif."""
        if session_id not in self._states:
            self._states[session_id] = CognitiveState(session_id=session_id)
        return self._states[session_id]

    # ─── Sous-modules (à implémenter) ────────────────────────────────

    async def _analyze_intent(self, query: str) -> Intent:
        """Analyse l'intention de la requête.

        MVP : heuristique simple.
        Production : LLM + NER.
        """
        query_lower = query.lower()

        # Heuristiques simples
        if query_lower.startswith("!"):
            return Intent(
                type=IntentType.COMMAND,
                entities={"command": query[1:]},
                confidence=0.9,
                raw_query=query,
            )
        elif "?" in query or query_lower.startswith(("quoi", "qui", "où", "quand", "comment", "pourquoi")):
            return Intent(
                type=IntentType.QUERY,
                entities={},
                confidence=0.85,
                raw_query=query,
            )
        elif any(word in query_lower for word in ["aide", "help", "?"]):
            return Intent(
                type=IntentType.CONVERSATION,
                entities={},
                confidence=0.8,
                raw_query=query,
            )
        else:
            return Intent(
                type=IntentType.TASK,
                entities={"description": query},
                confidence=0.7,
                raw_query=query,
                ambiguity_score=0.3,
            )

    async def _generate_clarification(self, query: str) -> list[str]:
        """Génère des questions de clarification."""
        return [
            "Pourriez-vous préciser ce que vous attendez ?",
            "S'agit-il d'une question ou d'une tâche à accomplir ?",
        ]

    async def _assemble_context(self, session_id: str, query: str, intent: Intent) -> dict[str, Any]:
        """Assemble le contexte pour le raisonnement.

        MVP : contexte minimal.
        Production : MemoryManager + RAG.
        """
        return {
            "session_id": session_id,
            "query": query,
            "intent": intent.type.value,
            "messages": [],
            "memory_items": [],
        }

    async def _reason(self, query: str, intent: Intent, context: dict[str, Any]) -> Reasoning:
        """Raisonnement sur la requête.

        MVP : simulation.
        Production : appel LLM avec prompt engineering.
        """
        # Simulation d'un raisonnement
        return Reasoning(
            chain_of_thought=f"Analyzing: {query}\nIntent: {intent.type.value}\nContext: {len(context.get('messages', []))} items",
            goal=query,
            required_capabilities=[],
            tokens_used=100,
            model="simulated",
            latency_ms=50.0,
        )

    async def _plan(self, goal: str, capabilities: list[str]) -> dict[str, Any]:
        """Planifie les actions.

        MVP : plan simple.
        Production : Planner avec DAG.
        """
        return {
            "id": f"plan-{hash(goal) % 10000}",
            "goal": goal,
            "tasks": [
                {
                    "id": "t1",
                    "capability": "generic.execute",
                    "params": {"description": goal},
                    "depends_on": [],
                }
            ],
        }

    async def _execute(self, plan: dict[str, Any]) -> list[dict[str, Any]]:
        """Exécute le plan.

        MVP : simulation.
        Production : Executor avec capabilities.
        """
        tasks = plan.get("tasks", [])
        results = []

        for task in tasks:
            # Simulation d'exécution
            results.append({
                "task_id": task["id"],
                "capability": task["capability"],
                "status": "completed",
                "result": f"Executed: {task['params'].get('description', '')}",
            })

        return results

    async def _reflect(self, query: str, plan: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
        """Réflexion sur les résultats.

        MVP : évaluation simple.
        Production : Reflector avec auto-évaluation.
        """
        success = all(r.get("status") == "completed" for r in results)

        return {
            "success": success,
            "output": results[0]["result"] if results else "No output",
            "confidence": 0.9 if success else 0.5,
            "latency_ms": 100.0,
        }

    async def _memorize(self, session_id: str, query: str, evaluation: dict[str, Any]) -> None:
        """Mémorise l'interaction.

        MVP : log seulement.
        Production : MemoryManager avec stockage.
        """
        logger.debug(f"Memorizing interaction for session {session_id}")

    async def run(self, input_data: dict[str, Any] | None = None) -> Result:
        """Point d'entrée standalone."""
        if input_data and "query" in input_data:
            request = CognitionRequest(
                query=input_data["query"],
                session_id=input_data.get("session_id", "default"),
            )
            response = await self.process(request)
            return Result.ok(data=response.output)

        return Result.ok(data={"status": "cognition ready"})