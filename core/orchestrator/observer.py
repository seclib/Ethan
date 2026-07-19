"""Observer — Ethan OS"""
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class Observation:
    summary: str
    details: Dict[str, Any]
    success: bool

class Observer:
    def analyze(self, result) -> Observation:
        from core.capabilities import CapabilityStatus
        status = "success" if result.status == CapabilityStatus.SUCCESS else "failed"
        capability_name = result.metadata.get("name", "unknown") if result.metadata else "unknown"
        return Observation(
            summary=f"Capability '{capability_name}' {status}",
            details={"output": result.output, "error": result.error, "duration_ms": result.duration_ms},
            success=result.status == CapabilityStatus.SUCCESS
        )
