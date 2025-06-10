"""
Handler global de exceções para FastAPI
"""
from typing import Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import traceback
from ..exceptions import (
    ContabilidadeBaseException,
    DocumentProcessingError,
    XMLProcessingError,
    PDFProcessingError,
    ImageProcessingError,
    ValidationError as CustomValidationError,
    ConfigurationError,
    ExternalAPIError,
    FileUploadError,
    UnsupportedFileTypeError,
    FileSizeExceededError
)
from ..models import ErrorResponse, ValidationErrorResponse, ValidationErrorDetail
from ..config import get_settings
from ..logging_config import get_logger

settings = get_settings()
logger = get_logger("ExceptionHandler")


def create_error_response(
    error_message: str,
    error_code: str = "INTERNAL_ERROR",
    details: Dict[str, Any] = None,
    status_code: int = 500
) -> JSONResponse:
    """Cria uma resposta de erro padronizada"""
    
    error_response = ErrorResponse(
        error=error_message,
        error_code=error_code,
        details=details or {}
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.dict()
    )


def create_validation_error_response(
    validation_errors: list,
    status_code: int = 422
) -> JSONResponse:
    """Cria uma resposta de erro de validação padronizada"""
    
    error_details = []
    for error in validation_errors:
        detail = ValidationErrorDetail(
            field=".".join(str(loc) for loc in error.get("loc", [])),
            message=error.get("msg", "Erro de validação"),
            invalid_value=error.get("input")
        )
        error_details.append(detail)
    
    validation_response = ValidationErrorResponse(
        details=error_details
    )
    
    return JSONResponse(
        status_code=status_code,
        content=validation_response.dict()
    )


async def contabilidade_exception_handler(request: Request, exc: ContabilidadeBaseException) -> JSONResponse:
    """Handler para exceções customizadas do sistema de contabilidade"""
    
    logger.error(f"Exceção customizada: {type(exc).__name__}: {str(exc)}")
    
    # Mapeia tipos de exceção para códigos de status HTTP
    status_code_map = {
        DocumentProcessingError: 422,
        XMLProcessingError: 422,
        PDFProcessingError: 422,
        ImageProcessingError: 422,
        CustomValidationError: 400,
        ConfigurationError: 500,
        ExternalAPIError: 502,
        FileUploadError: 400,
        UnsupportedFileTypeError: 415,
        FileSizeExceededError: 413
    }
    
    status_code = status_code_map.get(type(exc), 500)
    
    return create_error_response(
        error_message=exc.message,
        error_code=exc.error_code,
        details=exc.details,
        status_code=status_code
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler para erros de validação do Pydantic/FastAPI"""
    
    logger.warning(f"Erro de validação: {str(exc)}")
    
    return create_validation_error_response(exc.errors())


async def pydantic_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handler para erros de validação do Pydantic"""
    
    logger.warning(f"Erro de validação Pydantic: {str(exc)}")
    
    return create_validation_error_response(exc.errors())


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handler para exceções HTTP do FastAPI"""
    
    logger.warning(f"Exceção HTTP {exc.status_code}: {exc.detail}")
    
    return create_error_response(
        error_message=exc.detail,
        error_code=f"HTTP_{exc.status_code}",
        status_code=exc.status_code
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler geral para exceções não tratadas"""
    
    logger.error(f"Exceção não tratada: {type(exc).__name__}: {str(exc)}")
    
    # Em modo debug, inclui o traceback
    details = {}
    if settings.debug:
        details["traceback"] = traceback.format_exc()
        details["exception_type"] = type(exc).__name__
    
    return create_error_response(
        error_message="Erro interno do servidor",
        error_code="INTERNAL_SERVER_ERROR",
        details=details,
        status_code=500
    )


# Mapeamento de handlers de exceção
EXCEPTION_HANDLERS = {
    ContabilidadeBaseException: contabilidade_exception_handler,
    RequestValidationError: validation_exception_handler,
    ValidationError: pydantic_validation_exception_handler,
    HTTPException: http_exception_handler,
    Exception: general_exception_handler
}

