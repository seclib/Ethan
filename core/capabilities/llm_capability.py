"""LLM Capability — Ethan OS"""
from typing import Any

from core.capabilities import Capability, CapabilityContext, CapabilityResult, CapabilityStatus, RiskLevel


class LLMCapability(Capability):
    name = "llm"
    description = "Capacité de raisonnement via LLM"
    version = "1.0.0"
    risk_level = RiskLevel.LOW

    def __init__(self, provider):
        self.provider = provider

    async def validate(self, context: CapabilityContext) -> bool:
        return True

    async def execute(self, context: CapabilityContext, **kwargs) -> CapabilityResult:
        prompt = kwargs.get("prompt", "")
        try:
            response = await self.provider.reason(prompt, context)
            return CapabilityResult(status=CapabilityStatus.SUCCESS, output=response)
        except Exception as e:
            return CapabilityResult(status=CapabilityStatus.FAILED, error=str(e))

    async def observe(self, result: CapabilityResult) -> dict:
        return {"type": "llm", "success": result.status == CapabilityStatus.SUCCESS}