"""Cognitive Loop — ADR-1004

Cycle cognitif complet:
Perception → Reasoning → Planning → Execution → Observation → Memory Update → Reflection
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.context.intent import Intent, IntentRouter
from core.orchestration import Executor, Observer, Planner
from core.orchestration.registry import CapabilityRegistry

logger = logging.getLogger(__name__)


@dataclass
class CognitiveState:
    """État global du système cognitif."""
    session_id: str
    history: List[Dict[str, Any]] = field(default_factory=list)
    memory: Dict[str, Any] = field(default_factory=dict)
    reflections: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CognitiveResult:
    """Résultat d'un cycle cognitif complet."""
    intent: Intent
    plan: Any  # Plan
    observations: List[Any]  # List[Observation]
    reflection: str
    success: bool
    duration_ms: float


class CognitiveLoop:
    """Orchestre le cycle cognitif complet."""

    def __init__(
        self,
        registry: CapabilityRegistry,
        intent_router: Optional[IntentRouter] = None,
    ):
        self.registry = registry
        self.intent_router = intent_router or IntentRouter()
        self.planner = Planner()
        self.executor = Executor(registry)
        self.observer = Observer()
        self._states: Dict[str, CognitiveState] = {}

    def _get_state(self, session_id: str) -> CognitiveState:
        if session_id not in self._states:
            self._states[session_id] = CognitiveState(session_id=session_id)
        return self._states[session_id]

    async def _perceive(self, source: str, raw_input: Any) -> Intent:
        """Perception: normaliser l'entrée en Intent."""
        logger.info(f"[Perception] source={source}")
        intent = await self.intent_router.parse(source, raw_input)
        logger.info(f"[Perception] intent={intent.source}:{intent.user_input[:50]}")
        return intent

    def _reason(self, intent: Intent, state: CognitiveState) -> Dict[str, Any]:
        """Reasoning: analyser l'intent et le contexte."""
        logger.info("[Reasoning] Analyzing intent and context")
        
        # Analyse basique: vérifier le contexte et l'historique
        reasoning = {
            "intent_type": intent.source,
            "has_context": bool(intent.context),
            "history_length": len(state.history),
            "memory_keys": list(state.memory.keys()),
        }
        
        # Raisonnement simple basé sur l'historique
        if state.history:
            last_interaction = state.history[-1]
            reasoning["last_success"] = last_interaction.get("success", False)
        
        logger.info(f"[Reasoning] {reasoning}")
        return reasoning

    def _plan(self, intent: Intent, reasoning: Dict[str, Any]) -> Any:
        """Planning: générer un plan d'action."""
        logger.info("[Planning] Generating plan")
        plan = self.planner.build(intent)
        logger.info(f"[Planning] {len(plan.steps)} steps generated")
        return plan

    async def _execute(self, plan: Any, context: Any) -> List[Any]:
        """Execution: exécuter les étapes du plan."""
        logger.info(f"[Execution] Executing {len(plan.steps)} steps")
        observations = []
        for step in plan.steps:
            result = await self.executor.run(step.capability, context, **step.args)
            observation = self.observer.analyze(result)
            observations.append(observation)
            logger.info(f"[Execution] {observation.summary}")
        return observations

    def _update_memory(self, intent: Intent, observations: List[Any], state: CognitiveState):
        """Memory Update: stocker l'interaction en mémoire."""
        logger.info("[Memory] Updating memory")
        
        interaction = {
            "timestamp": datetime.utcnow().isoformat(),
            "intent_source": intent.source,
            "intent_input": intent.user_input,
            "intent_context": intent.context,
            "observations": [
                {
                    "summary": obs.summary,
                    "success": obs.success,
                    "details": obs.details,
                }
                for obs in observations
            ],
            "success": all(obs.success for obs in observations),
        }
        
        state.history.append(interaction)
        
        # Stocker dans la mémoire structurée
        key = f"interaction_{len(state.history)}"
        state.memory[key] = interaction
        
        logger.info(f"[Memory] Stored interaction #{len(state.history)}")

    def _reflect(self, intent: Intent, observations: List[Any], state: CognitiveState) -> str:
        """Reflection: analyser le résultat et générer un apprentissage."""
        logger.info("[Reflection] Analyzing outcome")
        
        success = all(obs.success for obs in observations)
        
        if success:
            reflection = f"Successfully processed {intent.source} input: '{intent.user_input[:50]}'"
        else:
            failures = [obs.summary for obs in observations if not obs.success]
            reflection = f"Partial failure processing {intent.source} input: {', '.join(failures)}"
        
        # Ajouter la réflexion à l'historique
        state.reflections.append(reflection)
        
        # Apprentissage: si échec, marquer pour amélioration
        if not success:
            state.memory["last_failure"] = {
                "intent": intent.user_input,
                "source": intent.source,
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        logger.info(f"[Reflection] {reflection}")
        return reflection

    async def run(
        self,
        source: str,
        raw_input: Any,
        session_id: str,
        context: Any,
    ) -> CognitiveResult:
        """Exécuter le cycle cognitif complet."""
        import time
        start = time.monotonic()
        
        state = self._get_state(session_id)
        
        # 1. Perception
        intent = await self._perceive(source, raw_input)
        
        # 2. Reasoning
        reasoning = self._reason(intent, state)
        
        # 3. Planning
        plan = self._plan(intent, reasoning)
        
        # 4. Execution
        observations = await self._execute(plan, context)
        
        # 5. Observation (déjà fait dans execute)
        
        # 6. Memory Update
        self._update_memory(intent, observations, state)
        
        # 7. Reflection
        reflection = self._reflect(intent, observations, state)
        
        duration_ms = (time.monotonic() - start) * 1000
        
        return CognitiveResult(
            intent=intent,
            plan=plan,
            observations=observations,
            reflection=reflection,
            success=all(obs.success for obs in observations),
            duration_ms=duration_ms,
        )

    def get_state(self, session_id: str) -> Optional[CognitiveState]:
        """Récupérer l'état cognitif d'une session."""
        return self._states.get(session_id)

    def clear_state(self, session_id: str):
        """Nettoyer l'état d'une session."""
        if session_id in self._states:
            del self._states[session_id]