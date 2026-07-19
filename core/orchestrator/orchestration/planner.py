"""Planner — Ethan OS"""
from dataclasses import dataclass
from typing import List

from core.context.intent import Intent

@dataclass
class Step:
    capability: str
    args: dict

@dataclass
class Plan:
    steps: List[Step]

class Planner:
    def build(self, intent: Intent) -> Plan:
        return Plan(steps=[])
