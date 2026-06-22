"""Learning primitive -- router policies, reward functions, learning."""

from __future__ import annotations

from ethan.learning._stubs import (
    QueryAnalyzer,
    RewardFunction,
    RouterPolicy,
    RoutingContext,
)
from ethan.learning.agents.agent_evolver import AgentConfigEvolver
from ethan.learning.learning_orchestrator import LearningOrchestrator
from ethan.learning.optimize.llm_optimizer import LLMOptimizer
from ethan.learning.optimize.optimizer import OptimizationEngine
from ethan.learning.optimize.store import OptimizationStore
from ethan.learning.routing.complexity import (
    ComplexityQueryAnalyzer,
    score_complexity,
)
from ethan.learning.routing.heuristic_reward import HeuristicRewardFunction
from ethan.learning.routing.router import (
    HeuristicRouter,
    build_routing_context,
)
from ethan.learning.training.data import TrainingDataMiner
from ethan.learning.training.lora import HAS_TORCH, LoRATrainer, LoRATrainingConfig


def ensure_registered() -> None:
    """Ensure all learning policies are registered in RouterPolicyRegistry."""
    from ethan.learning.routing.heuristic_policy import (
        ensure_registered as _reg_heuristic,
    )

    _reg_heuristic()

    from ethan.learning.routing.learned_router import (
        ensure_registered as _reg_learned,
    )

    _reg_learned()

    # Intelligence training (optional deps)
    try:
        import ethan.learning.intelligence  # noqa: F401
    except ImportError:
        pass

    # Orchestrator-specific training (optional deps)
    try:
        import ethan.learning.intelligence.orchestrator  # noqa: F401
    except ImportError:
        pass

    # Agent optimizers (optional deps)
    try:
        import ethan.learning.agents.dspy_optimizer  # noqa: F401
    except ImportError:
        pass
    try:
        import ethan.learning.agents.gepa_optimizer  # noqa: F401
    except ImportError:
        pass
    try:
        import ethan.learning.agents.ace_optimizer  # noqa: F401
    except ImportError:
        pass


__all__ = [
    "AgentConfigEvolver",
    "ComplexityQueryAnalyzer",
    "HAS_TORCH",
    "HeuristicRewardFunction",
    "HeuristicRouter",
    "LLMOptimizer",
    "LearningOrchestrator",
    "LoRATrainer",
    "LoRATrainingConfig",
    "OptimizationEngine",
    "OptimizationStore",
    "QueryAnalyzer",
    "RewardFunction",
    "RouterPolicy",
    "RoutingContext",
    "TrainingDataMiner",
    "build_routing_context",
    "ensure_registered",
    "score_complexity",
]
