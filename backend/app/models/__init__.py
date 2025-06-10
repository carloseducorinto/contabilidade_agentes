"""
Módulo de modelos Pydantic
"""
from .document_models import (
    ImpostosModel,
    ItemModel, 
    DocumentoFiscalModel,
    ProcessingResult
)
from .api_models import (
    FileUploadRequest,
    ProcessDocumentRequest,
    ErrorResponse,
    SuccessResponse,
    HealthCheckResponse,
    SupportedFormatsResponse,
    ProcessingMetrics,
    ValidationErrorDetail,
    ValidationErrorResponse,
    APIKeyValidationRequest,
    ConfigurationRequest,
    BatchProcessingRequest,
    BatchProcessingResponse
)

__all__ = [
    # Document models
    "ImpostosModel",
    "ItemModel",
    "DocumentoFiscalModel", 
    "ProcessingResult",
    # API models
    "FileUploadRequest",
    "ProcessDocumentRequest",
    "ErrorResponse",
    "SuccessResponse",
    "HealthCheckResponse",
    "SupportedFormatsResponse",
    "ProcessingMetrics",
    "ValidationErrorDetail",
    "ValidationErrorResponse",
    "APIKeyValidationRequest",
    "ConfigurationRequest",
    "BatchProcessingRequest",
    "BatchProcessingResponse"
]

