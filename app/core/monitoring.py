"""
Monitoring and observability configuration
Cloud-agnostic monitoring using OpenTelemetry and Prometheus
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

logger = logging.getLogger(__name__)

# Prometheus metrics
transaction_counter = Counter(
    'ims_transactions_total',
    'Total number of transactions processed',
    ['transaction_type', 'source', 'status']
)

transaction_duration = Histogram(
    'ims_transaction_duration_seconds',
    'Duration of transaction processing',
    ['transaction_type', 'source']
)

active_transactions = Gauge(
    'ims_active_transactions',
    'Number of active transactions being processed'
)

ims_connection_status = Gauge(
    'ims_connection_status',
    'IMS connection status (1=connected, 0=disconnected)'
)

error_counter = Counter(
    'ims_errors_total',
    'Total number of errors',
    ['error_type', 'source']
)

# Health check status
health_status = {
    "status": "healthy",
    "last_check": datetime.utcnow(),
    "checks": {
        "database": {"status": "healthy", "message": "Database connection active"},
        "ims_connection": {"status": "healthy", "message": "IMS connection active"},
        "disk_space": {"status": "healthy", "message": "Sufficient disk space"},
        "memory": {"status": "healthy", "message": "Memory usage normal"}
    }
}


def setup_monitoring(app_name: str = "ims-integration-service", app_version: str = "1.0.0"):
    """
    Setup OpenTelemetry monitoring
    Can be configured to send to different backends via OTEL_EXPORTER_OTLP_ENDPOINT
    """
    # Resource info shared between traces and metrics
    resource = Resource.create({
        SERVICE_NAME: app_name,
        SERVICE_VERSION: app_version,
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        "cloud.provider": os.getenv("CLOUD_PROVIDER", "aws"),  # Will change to "azure" later
    })
    
    # Setup tracing if endpoint is configured
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        logger.info(f"Setting up OpenTelemetry tracing to {otlp_endpoint}")
        
        # Setup tracing
        trace.set_tracer_provider(TracerProvider(resource=resource))
        tracer_provider = trace.get_tracer_provider()
        
        span_processor = BatchSpanProcessor(
            OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        )
        tracer_provider.add_span_processor(span_processor)
        
        # Setup metrics
        metric_reader = OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
        metrics.set_meter_provider(
            MeterProvider(resource=resource, metric_readers=[metric_reader])
        )
        
        # Instrument libraries
        FastAPIInstrumentor.instrument(tracer_provider=tracer_provider)
        RequestsInstrumentor().instrument(tracer_provider=tracer_provider)
        
        logger.info("OpenTelemetry instrumentation completed")
    else:
        logger.info("OTEL_EXPORTER_OTLP_ENDPOINT not set, OpenTelemetry disabled")


def update_health_check(check_name: str, status: str, message: str):
    """Update health check status"""
    health_status["checks"][check_name] = {
        "status": status,
        "message": message,
        "last_update": datetime.utcnow().isoformat()
    }
    
    # Update overall status
    all_healthy = all(check["status"] == "healthy" for check in health_status["checks"].values())
    health_status["status"] = "healthy" if all_healthy else "unhealthy"
    health_status["last_check"] = datetime.utcnow()


def get_health_status() -> Dict[str, Any]:
    """Get current health status"""
    return {
        "status": health_status["status"],
        "timestamp": health_status["last_check"].isoformat(),
        "checks": health_status["checks"],
        "metrics": {
            "active_transactions": active_transactions._value.get(),
            "ims_connected": bool(ims_connection_status._value.get())
        }
    }


def get_prometheus_metrics():
    """Generate Prometheus metrics in text format"""
    return generate_latest()


# Utility functions for tracking metrics
def track_transaction_start(transaction_type: str, source: str):
    """Track when a transaction starts"""
    active_transactions.inc()
    

def track_transaction_complete(transaction_type: str, source: str, status: str, duration: float):
    """Track when a transaction completes"""
    active_transactions.dec()
    transaction_counter.labels(
        transaction_type=transaction_type,
        source=source,
        status=status
    ).inc()
    transaction_duration.labels(
        transaction_type=transaction_type,
        source=source
    ).observe(duration)


def track_error(error_type: str, source: str):
    """Track errors"""
    error_counter.labels(error_type=error_type, source=source).inc()


def update_ims_connection_status(connected: bool):
    """Update IMS connection status"""
    ims_connection_status.set(1 if connected else 0)
    update_health_check(
        "ims_connection",
        "healthy" if connected else "unhealthy",
        "IMS connection active" if connected else "IMS connection lost"
    )