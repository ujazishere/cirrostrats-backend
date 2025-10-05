"""
OpenTelemetry distributed tracing setup for Cirrostrats Backend.

This module configures:
- Trace provider with OTLP exporter
- Auto-instrumentation for FastAPI, aiohttp, pymongo, redis
- Resource attributes (service name, version, environment)
"""
import os
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION, DEPLOYMENT_ENVIRONMENT
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

logger = logging.getLogger(__name__)


def setup_tracing(service_name: str = "cirrostrats-backend-api", app=None) -> trace.Tracer:
    """
    Initialize OpenTelemetry distributed tracing.

    Args:
        service_name: Name of the service for trace attribution
        app: FastAPI app instance to instrument (optional, but recommended)

    Returns:
        Configured tracer instance
    """
    # Define service resource attributes
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: os.getenv("SERVICE_VERSION", "0.1.0"),
        DEPLOYMENT_ENVIRONMENT: os.getenv("ENV", "dev"),
    })

    # Create trace provider
    provider = TracerProvider(resource=resource)

    # Configure OTLP exporter to send traces to OTel Collector
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    otlp_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=True,  # Use insecure for local dev; set False + configure TLS for production
    )

    # Add batch span processor for efficient export
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Set as global tracer provider
    trace.set_tracer_provider(provider)

    # Auto-instrument libraries
    # Note: Other instrumentors called without app instance
    AioHttpClientInstrumentor().instrument()
    PymongoInstrumentor().instrument()
    RedisInstrumentor().instrument()

    # FastAPI instrumentation - instrument specific app if provided
    if app is not None:
        FastAPIInstrumentor.instrument_app(app)
    else:
        FastAPIInstrumentor().instrument()

    logger.info(
        f"OpenTelemetry tracing initialized for {service_name}",
        extra={"otlp_endpoint": otlp_endpoint, "environment": os.getenv("ENV", "dev")}
    )

    return trace.get_tracer(__name__)
