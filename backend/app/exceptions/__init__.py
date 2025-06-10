"""
Módulo de exceções customizadas
"""
from .custom_exceptions import (
    ContabilidadeBaseException,
    DocumentProcessingError,
    XMLProcessingError,
    PDFProcessingError,
    ImageProcessingError,
    ValidationError,
    ConfigurationError,
    ExternalAPIError,
    FileUploadError,
    UnsupportedFileTypeError,
    FileSizeExceededError
)
from .handlers import (
    EXCEPTION_HANDLERS,
    contabilidade_exception_handler,
    validation_exception_handler,
    pydantic_validation_exception_handler,
    http_exception_handler,
    general_exception_handler,
    create_error_response,
    create_validation_error_response
)

__all__ = [
    # Exceções
    "ContabilidadeBaseException",
    "DocumentProcessingError",
    "XMLProcessingError",
    "PDFProcessingError",
    "ImageProcessingError",
    "ValidationError",
    "ConfigurationError",
    "ExternalAPIError",
    "FileUploadError",
    "UnsupportedFileTypeError",
    "FileSizeExceededError",
    # Handlers
    "EXCEPTION_HANDLERS",
    "contabilidade_exception_handler",
    "validation_exception_handler",
    "pydantic_validation_exception_handler",
    "http_exception_handler",
    "general_exception_handler",
    "create_error_response",
    "create_validation_error_response"
]

