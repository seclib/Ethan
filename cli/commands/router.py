"""CLI command: ethan router <task> — Router LLM.

Usage:
    ethan router reasoning       # GPT / Claude (complexe)
    ethan router code           # Claude / GPT (code)
    ethan router fast           # Modèle rapide
    ethan router local          # Modèle local hors-ligne
"""

from __future__ import annotations

from cli.core import colors as clr
from cli.registry import register
from core.llm.router import LLMRouter
from core.llm.selector import LLMSelector
from core.llm.types import ModelInfo


# Modèles par défaut
DEFAULT_MODELS: list[ModelInfo] = [
    ModelInfo(
        id="claude-sonnet-4",
        provider="anthropic",
        name="claude",
        context_length=200000,
        quality_score=0.92,
        avg_latency_ms=3000,
        is_local=False,
        is_private=False,
        is_available=True,
    ),
    ModelInfo(
        id="gpt-4o",
        provider="openai",
        name="gpt",
        context_length=128000,
        quality_score=0.90,
        avg_latency_ms=2500,
        is_local=False,
        is_private=False,
        is_available=True,
    ),
    ModelInfo(
        id="mistral-small",
        provider="mistral",
        name="mistral",
        context_length=32000,
        quality_score=0.65,
        avg_latency_ms=800,
        is_local=False,
        is_private=False,
        is_available=True,
    ),
    ModelInfo(
        id="llama3.2-3b",
        provider="ollama",
        name="local",
        context_length=8192,
        quality_score=0.50,
        avg_latency_ms=500,
        is_local=True,
        is_private=True,
        is_available=True,
    ),
]


MODEL_MAP = {
    "reasoning": "claude",
    "code": "claude",
    "fast": "mistral",
    "local": "local",
}


@register(
    "router",
    group="core",
    description="Route LLM — choisit le meilleur modèle pour une tâche",
    usage="ethan router <reasoning|code|fast|local>",
)
def cmd_router(args: list[str]) -> int:
    """Affiche le meilleur modèle pour une catégorie de tâche.

    Args:
        args: [category]

    Returns:
        0 si succès, 1 si erreur
    """
    if not args:
        print(f"\n  {clr.C.CYAN}Usage:{clr.C.RESET} ethan router <task>")
        print(f"  {clr.C.CYAN}Tasks:{clr.C.RESET}  reasoning, code, fast, local")
        print()
        return 0

    task = args[0].lower()

    router = LLMRouter()
    model = router.route(task, DEFAULT_MODELS)

    if model == "unknown":
        # Fallback
        model = router.route_with_fallback(task, DEFAULT_MODELS)

    print(model)
    return 0