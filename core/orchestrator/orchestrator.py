"""ETHAN Orchestrator — Le cerveau central d'ETHAN.

L'Orchestrator est le composant principal qui contrôle tout le système.
Il coordonne tous les modules et constitue le véritable cœur d'ETHAN.

Architecture :
- Initialisation de tous les modules
- Coordination des flux cognitifs
- Gestion du cycle de vie des requêtes
- Orchestration cognition + mémoire + planner + tools + sécurité + events + LLM
"""

from __future__ import annotations

import logging
from typing import Any

from core.orchestrator.context import OrchestratorContext
from core.orchestrator.pipeline import Pipeline, PipelineStep
from core.orchestrator.router import RequestRouter

logger = logging.getLogger(__name__)


class Orchestrator:
    """Orchestrateur principal d'ETHAN.
    
    Responsabilités :
    - Initialiser tous les modules
    - Coordonner les flux cognitifs
    - Gérer le cycle de vie des requêtes
    - Orchestrer cognition, mémoire, planner, tools, sécurité, events, LLM
    """

    def __init__(self):
        self._context: OrchestratorContext | None = None
        self._router = RequestRouter()
        self._pipelines: dict[str, Pipeline] = {}
        self._modules: dict[str, Any] = {}

    def register_module(self, name: str, module: Any) -> None:
        """Enregistre un module.

        Args:
            name: Nom du module
            module: Instance du module
        """
        self._modules[name] = module
        logger.debug(f"Module registered: {name}")

    def get_module(self, name: str) -> Any | None:
        """Récupère un module.

        Args:
            name: Nom du module

        Returns:
            Module ou None
        """
        return self._modules.get(name)

    def register_pipeline(self, name: str, pipeline: Pipeline) -> None:
        """Enregistre un pipeline.

        Args:
            name: Nom du pipeline
            pipeline: Pipeline
        """
        self._pipelines[name] = pipeline

    async def initialize(self, context: OrchestratorContext) -> None:
        """Initialise l'orchestrateur.

        Args:
            context: Contexte d'exécution
        """
        self._context = context

        # Injecter les modules dans le contexte
        context.cognition = self._modules.get("cognition")
        context.memory = self._modules.get("memory")
        context.planner = self._modules.get("planner")
        context.tools = self._modules.get("tools")
        context.security = self._modules.get("security")
        context.events = self._modules.get("events")
        context.llm = self._modules.get("llm")
        context.skills = self._modules.get("skills")

        logger.info("Orchestrator initialized")

    async def process(self, request: dict[str, Any]) -> dict[str, Any]:
        """Traite une requête.

        Args:
            request: Requête

        Returns:
            Réponse
        """
        if not self._context:
            raise RuntimeError("Orchestrator not initialized")

        # Créer le contexte de requête
        context = OrchestratorContext(
            request_id=request.get("request_id", "unknown"),
            user_id=request.get("user_id", "default"),
            session_id=request.get("session_id", "default"),
        )

        # Copier les références des modules
        context.cognition = self._context.cognition
        context.memory = self._context.memory
        context.planner = self._context.planner
        context.tools = self._context.tools
        context.security = self._context.security
        context.events = self._context.events
        context.llm = self._context.llm
        context.skills = self._context.skills

        # Router la requête
        request_type = request.get("type", "intent")
        target_module = await self._router.route(context, request_type)

        # Exécuter le pipeline approprié
        pipeline_name = f"{target_module}_pipeline"
        pipeline = self._pipelines.get(pipeline_name)

        if pipeline:
            result = await pipeline.execute(context)
        else:
            # Fallback : exécuter directement via cognition
            result = await self._execute_default(context, request)

        return {
            "request_id": context.request_id,
            "status": "success",
            "result": result,
        }

    async def _execute_default(self, context: OrchestratorContext, request: dict[str, Any]) -> Any:
        """Exécution par défaut via cognition.

        Args:
            context: Contexte
            request: Requête

        Returns:
            Résultat
        """
        # TODO: Implémenter le flux cognitif par défaut
        return {"message": "Processed by default cognition pipeline"}

    def get_stats(self) -> dict[str, Any]:
        """Récupère les statistiques.

        Returns:
            Statistiques
        """
        return {
            "modules": list(self._modules.keys()),
            "pipelines": list(self._pipelines.keys()),
            "routes": self._router.get_available_routes(),
        }