from fastapi import FastAPI, File, UploadFile, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
import uvicorn
import os
import time
from dotenv import load_dotenv

from .config import get_settings, is_production, get_cors_config
from .services.async_document_service import AsyncDocumentService
from .models.document_models import ProcessingResult
from .models.api_models import SupportedFormatsResponse
from .logging_config import get_logger, log_operation_start, log_operation_success, log_operation_error
from .middleware import setup_security_middleware
from .metrics import setup_metrics_endpoint, metrics_middleware, record_document_processing_metrics, record_cache_metrics
from .utils.cache import start_cache_cleanup_task, get_cache_stats, clear_cache

# Carrega variáveis de ambiente do .env
load_dotenv()

# Carrega configurações
settings = get_settings()

# Configuração do logging centralizado
logger = get_logger("main")

# Inicialização da aplicação FastAPI
app = FastAPI(
    title=settings.app_name,
    description="API para processamento automatizado de documentos fiscais brasileiros",
    version=settings.app_version,
    debug=settings.debug
)

# Configura middlewares de segurança (CORS, Rate Limit, Headers)
# setup_security_middleware(app)  # Temporarily disabled

# Adiciona middleware de métricas
# app.middleware("http")(metrics_middleware)  # Temporarily disabled

# Inicialização do serviço de documentos
document_service = AsyncDocumentService(openai_api_key=settings.openai_api_key)

# @app.on_event("startup")
# async def startup_event():
#     """Evento de inicialização da aplicação"""
#     # Garante que o diretório de logs existe
#     import pathlib
#     pathlib.Path("logs").mkdir(exist_ok=True)
#     
#     log_operation_start("application_startup", agent="main", 
#                         openai_configured=bool(settings.openai_api_key),
#                         api_version=settings.app_version)
#     
#     # Inicia a tarefa de limpeza de cache em background
#     await start_cache_cleanup_task()
#     
#     log_operation_success("application_startup", agent="main", 
#                           openai_configured=bool(settings.openai_api_key),
#                           api_version=settings.app_version)


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de desligamento da aplicação"""
    logger.info("Aplicação desligando...")
    # Aqui você pode adicionar lógica para fechar conexões, etc.


@app.get("/")
async def root():
    """Endpoint de status da API"""
    return {
        "message": settings.app_name,
        "status": "ativo",
        "version": settings.app_version,
        "environment": settings.environment
    }


@app.get("/health")
async def health_check():
    """Endpoint de verificação de saúde da API"""
    return {
        "status": "healthy", 
        "timestamp": time.time(),
        "openai_configured": bool(settings.openai_api_key),
        "environment": settings.environment,
        "version": settings.app_version
    }


@app.post("/process-document", response_model=ProcessingResult)
async def process_document(file: UploadFile = File(...), request: Request = None, background_tasks: BackgroundTasks = None):
    """
    Processa um documento fiscal (XML, PDF ou Imagem) e retorna dados estruturados
    
    Args:
        file: Arquivo de documento fiscal (NF-e XML, PDF ou imagem JPG/PNG)
        request: Objeto da requisição FastAPI
        background_tasks: Objeto para tarefas em background
        
    Returns:
        ProcessingResult com dados estruturados ou erro
    """
    request_id = getattr(request.state, 'request_id', 'unknown') if request else 'unknown'
    
    operation_id = log_operation_start("process_document_endpoint", agent="main", request_id=request_id, file_name=file.filename)
    
    try:
        file_content = await file.read()
        file_type = file.filename.split(".")[-1].lower() if file.filename else "unknown"
        
        result = await document_service.process_document(
            file_content=file_content,
            file_type=file_type,
            filename=file.filename,
            background_tasks=background_tasks
        )
        
        if result.success:
            log_operation_success(operation_id, agent="main", request_id=request_id, 
                                  file_name=file.filename, status="success")
            return result
        else:
            log_operation_error(operation_id, result.error, agent="main", request_id=request_id, 
                                file_name=file.filename, status="failed")
            raise HTTPException(status_code=422, detail=result.error)
            
    except HTTPException as e:
        log_operation_error(operation_id, str(e.detail), agent="main", request_id=request_id, 
                            file_name=file.filename, status="failed")
        raise e
    except Exception as e:
        log_operation_error(operation_id, str(e), agent="main", request_id=request_id, 
                            file_name=file.filename, status="failed")
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")


@app.get("/supported-formats", response_model=SupportedFormatsResponse)
async def get_supported_formats(request: Request):
    """Retorna os formatos de documento suportados"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    log_operation_start("supported_formats_endpoint", agent="main", request_id=request_id)
    
    formats_info = await document_service.get_supported_formats()
    
    log_operation_success("supported_formats_endpoint", agent="main", request_id=request_id,
                          formats_count=len(formats_info["formats"]))
    
    return SupportedFormatsResponse(**formats_info)


@app.get("/cache/clear")
async def clear_app_cache(request: Request):
    """Limpa o cache da aplicação"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    log_operation_start("clear_cache_endpoint", agent="main", request_id=request_id)
    
    await clear_cache()
    
    log_operation_success("clear_cache_endpoint", agent="main", request_id=request_id)
    return {"message": "Cache limpo com sucesso!", "request_id": request_id}


# Configura o endpoint de métricas Prometheus
setup_metrics_endpoint(app)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.api_workers,
        log_level=settings.log_level.lower()
    )

