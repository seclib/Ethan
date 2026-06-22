"""Planner — Ethan OS"""
from dataclasses import dataclass
from typing import List

@dataclass
class Step:
    capability: str
    args: dict

@dataclass
class Plan:
    steps: List[Step]

class Planner:
    def build(self, intent: str) -> Plan:
        return Plan(steps=[])