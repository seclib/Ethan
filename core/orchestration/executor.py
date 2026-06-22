"""Executor — Ethan OS"""
import time
from core.capabilities import Capability, CapabilityContext, CapabilityResult, CapabilityStatus
from core.orchestration.registry import CapabilityRegistry

class Executor:
    def __init__(self, registry, timeout=30.0):
        self.registry = registry
        self.timeout = timeout

    async def run(self, capability_name, context, **kwargs):
        start = time.monotonic()
        cap = self.registry.get(capability_name)
        if not cap:
            return CapabilityResult(status=CapabilityStatus.FAILED, error=f"Not found: {capability_name}")
        try:
            if not await cap.validate(context):
                return CapabilityResult(status=CapabilityStatus.FAILED, error="Validation failed")
        except Exception as e:
            return CapabilityResult(status=CapabilityStatus.FAILED, error=str(e))
        try:
            result = await cap.execute(context, **kwargs)
            result.duration_ms = (time.monotonic() - start) * 1000
            return result
        except Exception as e:
            return CapabilityResult(status=CapabilityStatus.FAILED, error=str(e), duration_ms=(time.monotonic() - start) * 1000)