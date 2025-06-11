"""
Módulo de métricas para a aplicação
"""
from .prometheus_metrics import (
    REQUEST_COUNT,
    REQUEST_DURATION,
    IN_PROGRESS_REQUESTS,
    DOCUMENT_PROCESSING_COUNT,
    DOCUMENT_PROCESSING_DURATION,
    CACHE_HITS,
    CACHE_MISSES,
    metrics_middleware,
    setup_metrics_endpoint,
    record_document_processing_metrics,
    record_cache_metrics
)

__all__ = [
    "REQUEST_COUNT",
    "REQUEST_DURATION",
    "IN_PROGRESS_REQUESTS",
    "DOCUMENT_PROCESSING_COUNT",
    "DOCUMENT_PROCESSING_DURATION",
    "CACHE_HITS",
    "CACHE_MISSES",
    "metrics_middleware",
    "setup_metrics_endpoint",
    "record_document_processing_metrics",
    "record_cache_metrics"
]

