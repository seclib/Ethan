"""Memory Capability — Ethan OS"""
from core.capabilities import Capability, CapabilityContext, CapabilityResult, CapabilityStatus, RiskLevel

class MemoryCapability(Capability):
    name = "memory"
    description = "Capacité d'accès à la mémoire"
    version = "1.0.0"
    risk_level = RiskLevel.LOW

    def __init__(self, memory_manager):
        self.memory_manager = memory_manager

    async def validate(self, context: CapabilityContext) -> bool:
        return True

    async def execute(self, context: CapabilityContext, **kwargs) -> CapabilityResult:
        action = kwargs.get("action", "retrieve")
        try:
            if action == "store":
                result = await self.memory_manager.store(kwargs.get("content"), **kwargs)
            elif action == "retrieve":
                result = await self.memory_manager.retrieve(kwargs.get("memory_id"))
            elif action == "search":
                result = await self.memory_manager.search(kwargs.get("query"), **kwargs)
            else:
                return CapabilityResult(status=CapabilityStatus.FAILED, error=f"Unknown action: {action}")
            return CapabilityResult(status=CapabilityStatus.SUCCESS, output=result)
        except Exception as e:
            return CapabilityResult(status=CapabilityStatus.FAILED, error=str(e))

    async def observe(self, result: CapabilityResult) -> dict:
        return {"type": "memory", "success": result.status == CapabilityStatus.SUCCESS}