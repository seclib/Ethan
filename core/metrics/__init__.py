"""ETHAN Core — Metrics & Telemetry.

Collecte de métriques pour monitoring :
- Prometheus metrics
- Event latency tracking
- Module health
- System resources
"""

from .telemetry import MetricPoint, TelemetryCollector

__all__ = ["TelemetryCollector", "MetricPoint"]
