"""
Métricas Prometheus para a aplicação FastAPI
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match
import time
from typing import Callable
from ..config import get_settings
from ..logging_config import get_logger

settings = get_settings()
logger = get_logger("PrometheusMetrics")

# Define as métricas
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status_code"],
)
IN_PROGRESS_REQUESTS = Gauge(
    "http_requests_in_progress",
    "Number of in-progress HTTP requests",
    ["method", "endpoint"],
)
DOCUMENT_PROCESSING_COUNT = Counter(
    "document_processing_total",
    "Total document processing operations",
    ["file_type", "status"],
)
DOCUMENT_PROCESSING_DURATION = Histogram(
    "document_processing_duration_seconds",
    "Document processing duration in seconds",
    ["file_type", "status"],
)
CACHE_HITS = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["key_prefix"],
)
CACHE_MISSES = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["key_prefix"],
)


async def metrics_middleware(request: Request, call_next: Callable) -> Response:
    """Middleware para coletar métricas de requisições HTTP"""
    method = request.method
    endpoint = "unknown"

    # Tenta encontrar o endpoint correspondente
    for route in request.app.routes:
        match, scope = route.matches(request.scope)
        if match == Match.FULL:
            endpoint = route.path
            break

    IN_PROGRESS_REQUESTS.labels(method=method, endpoint=endpoint).inc()
    start_time = time.time()

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500  # Assume erro interno se a exceção não for tratada
        raise e
    finally:
        process_time = time.time() - start_time
        IN_PROGRESS_REQUESTS.labels(method=method, endpoint=endpoint).dec()
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint, status_code=status_code).observe(process_time)

    return response


def setup_metrics_endpoint(app):
    """Adiciona um endpoint /metrics para expor as métricas"""
    @app.get("/metrics", include_in_schema=False)
    async def get_metrics():
        if not settings.enable_metrics:
            logger.warning("Tentativa de acessar endpoint /metrics com métricas desabilitadas")
            return Response(status_code=404)
        
        logger.info("Servindo métricas Prometheus")
        return Response(content=generate_latest().decode("utf-8"), media_type="text/plain")


def record_document_processing_metrics(file_type: str, status: str, duration: float):
    """Registra métricas de processamento de documentos"""
    DOCUMENT_PROCESSING_COUNT.labels(file_type=file_type, status=status).inc()
    DOCUMENT_PROCESSING_DURATION.labels(file_type=file_type, status=status).observe(duration)


def record_cache_metrics(key_prefix: str, hit: bool):
    """Registra métricas de cache"""
    if hit:
        CACHE_HITS.labels(key_prefix=key_prefix).inc()
    else:
        CACHE_MISSES.labels(key_prefix=key_prefix).inc()

