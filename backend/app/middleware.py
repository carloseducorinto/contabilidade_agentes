import time
import uuid
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from .logging_config import get_logger, log_api_request, log_api_response, log_operation_error


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging automático de requisições e respostas"""
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.logger = get_logger("middleware")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Processa as requisições e adiciona logging"""
        # Gera um ID único para a requisição
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Extrai informações da requisição
        method = request.method
        url = str(request.url)
        path = request.url.path
        user_agent = request.headers.get("user-agent", "unknown")
        content_length = request.headers.get("content-length", "0")
        
        # Log da requisição
        log_api_request(
            endpoint=path,
            method=method,
            request_id=request_id,
            user_agent=user_agent,
            url=url,
            content_length=content_length
        )
        
        # Adiciona o request_id ao contexto da requisição
        request.state.request_id = request_id
        
        try:
            # Processa a requisição
            response = await call_next(request)
            
            # Calcula o tempo de execução
            execution_time = time.time() - start_time
            
            # Log da resposta
            log_api_response(
                endpoint=path,
                method=method,
                status_code=response.status_code,
                execution_time=execution_time,
                request_id=request_id
            )
            
            # Adiciona headers de resposta com informações de debug
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Execution-Time"] = f"{execution_time:.3f}s"
            
            return response
            
        except Exception as e:
            # Calcula o tempo de execução mesmo em caso de erro
            execution_time = time.time() - start_time
            
            # Log do erro
            log_operation_error(
                operation="request_processing",
                error=e,
                execution_time=execution_time,
                request_id=request_id,
                endpoint=path,
                method=method
            )
            
            # Retorna uma resposta de erro estruturada
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "Ocorreu um erro interno no servidor",
                    "request_id": request_id,
                    "timestamp": time.time()
                },
                headers={
                    "X-Request-ID": request_id,
                    "X-Execution-Time": f"{execution_time:.3f}s"
                }
            )


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware para tratamento de erros e logging"""
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.logger = get_logger("error_handler")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Trata erros não capturados"""
        try:
            return await call_next(request)
        except Exception as e:
            # Obtém o request_id se disponível
            request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
            
            # Log detalhado do erro
            self.logger.error(
                f"Erro não tratado na requisição {request.method} {request.url.path}",
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                },
                exc_info=True
            )
            
            # Retorna erro estruturado
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "Erro interno do servidor",
                    "request_id": request_id,
                    "timestamp": time.time()
                },
                headers={"X-Request-ID": request_id}
            )


def setup_middleware(app: FastAPI) -> None:
    """Configura todos os middlewares da aplicação"""
    # Middleware de tratamento de erros (deve ser o primeiro)
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Middleware de logging
    app.add_middleware(LoggingMiddleware) 