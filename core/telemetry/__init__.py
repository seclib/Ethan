"""Telemetry — Logging, metrics, tracing."""

import os
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def init_telemetry(service_name: str = "ethan-core"):
    """Initialize OpenTelemetry tracing."""
    provider = TracerProvider(
        resource=Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0",
        })
    )
    
    # Add OTLP exporter to OTel Collector
    otel_host = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
    otlp_exporter = OTLPSpanExporter(
        endpoint=otel_host,
        insecure=True
    )
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # Set global provider
    trace.set_tracer_provider(provider)
    
    return trace.get_tracer(__name__)