"""Example: Utilisation de la couche d'orchestration"""

from core.capabilities import CapabilityContext, CapabilityStatus
from core.context.intent import Intent
from core.orchestration import CapabilityRegistry, Executor, Observer, Planner
from core.safety import SafetyValidator


async def main():
    # 1. Créer le Registry
    registry = CapabilityRegistry()

    # 2. Enregistrer des Capabilities
    # registry.register(LLMCapability(provider=...))
    # registry.register(MemoryCapability(memory_manager=...))

    # 3. Créer les services d'orchestration
    planner = Planner()
    executor = Executor(registry)
    observer = Observer()
    safety = SafetyValidator()

    # 4. Exécuter un flux complet
    from core.context.intent import IntentRouter
    router = IntentRouter()

    user_input = "Analyze this code and suggest improvements"

    # Normaliser via IntentRouter (ADR-1003)
    intent = await router.parse("text", user_input)

    # Validation Safety
    from core.safety import SafetyContext
    safety_ctx = SafetyContext(
        user_id="user_123",
        session_id="sess_abc",
        trace_id="trace_xyz",
        permissions=["read", "write"],
    )
    if not safety.validate(safety_ctx):
        raise Exception("Safety validation failed")

    # Contexte d'exécution
    context = CapabilityContext(
        user_id="user_123",
        session_id="sess_abc",
        trace_id="trace_xyz",
        permissions=["read", "write"],
    )

    # Planning
    plan = planner.build(intent)
    print(f"Plan: {len(plan.steps)} steps")

    # Execution
    for step in plan.steps:
        result = await executor.run(step.capability, context, **step.args)
        if result.status == CapabilityStatus.SUCCESS:
            observation = observer.analyze(result)
            print(f"✓ {observation.summary}")
        else:
            print(f"✗ {result.error}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())