from fastapi import FastAPI, File, UploadFile, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
import uvicorn
import os
import time
from dotenv import load_dotenv

from .config import get_settings, is_production, get_cors_config
from .services.async_document_service import AsyncDocumentService
from .classification_agent import ClassificationAgent # Importar o ClassificationAgent
from .models.document_models import ProcessingResult, DocumentProcessed # Importar DocumentProcessed
from .models.classification_models import ClassificationOutput # Importar ClassificationOutput
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
logger.info("Iniciando aplicação FastAPI com configurações carregadas", extra={
    "environment": settings.environment,
    "version": settings.app_version
})

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

# Inicialização dos serviços
try:
    document_service = AsyncDocumentService(openai_api_key=settings.openai_api_key)
    classification_agent = ClassificationAgent() # Inicializar o ClassificationAgent
    logger.info("Serviços de documentos e classificação inicializados com sucesso")
except Exception as e:
    logger.critical(f"Falha ao inicializar serviços: {e}")
    raise

@app.on_event("shutdown")
async def shutdown_event():
    """Evento de desligamento da aplicação"""
    logger.info("Aplicação desligando...")
    # TODO: Adicionar lógica para fechar conexões externas, liberar recursos, etc.

@app.get("/")
async def root():
    """Endpoint de status da API"""
    logger.debug("Recebida requisição GET / (root)")
    return {
        "message": settings.app_name,
        "status": "ativo",
        "version": settings.app_version,
        "environment": settings.environment
    }

@app.get("/health")
async def health_check():
    """Endpoint de verificação de saúde da API"""
    logger.debug("Recebida requisição GET /health (health check)")
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
    Processa um documento fiscal (XML, PDF ou Imagem) e retorna dados estruturados e classificados
    """
    request_id = getattr(request.state, 'request_id', 'unknown') if request else 'unknown'
    logger.info(f"Recebida requisição POST /process-document para arquivo: {file.filename}", extra={"request_id": request_id})
    operation_id = log_operation_start("process_document_endpoint", agent="main", request_id=request_id, file_name=file.filename)
    try:
        file_content = await file.read()
        file_type = file.filename.split(".")[-1].lower() if file.filename else "unknown"
        logger.debug(f"Arquivo recebido: {file.filename} ({file_type}), tamanho: {len(file_content)} bytes")
        
        # 1. Processamento do Documento (Extração de Dados)
        processing_result = await document_service.process_document(
            file_content=file_content,
            file_type=file_type,
            filename=file.filename,
            background_tasks=background_tasks
        )

        if not processing_result.success:
            logger.warning(f"Processamento de extração falhou para {file.filename}: {processing_result.error}", extra={"request_id": request_id})
            log_operation_error(operation_id, processing_result.error, agent="main", request_id=request_id, file_name=file.filename, status="extraction_failed")
            raise HTTPException(status_code=422, detail=processing_result.error)

        # Converter o resultado para DocumentProcessed para passar ao ClassificationAgent
        doc_processed = DocumentProcessed(
            document_id=processing_result.document_id,
            document_type=processing_result.document_type,
            extracted_data=processing_result.extracted_data
        )

        # 2. Classificação do Documento
        logger.info(f"Iniciando classificação para documento ID: {doc_processed.document_id}", extra={"request_id": request_id})
        classified_output = await classification_agent.classify_document(doc_processed)
        logger.info(f"Classificação bem-sucedida para {file.filename}", extra={"request_id": request_id})

        # 3. Combinar resultados e retornar
        final_result = ProcessingResult(
            document_id=processing_result.document_id,
            document_type=processing_result.document_type,
            extracted_data=processing_result.extracted_data,
            classification_data=classified_output.model_dump(), # Adicionar dados de classificação
            success=True,
            message="Documento processado e classificado com sucesso."
        )

        logger.info(f"Processamento e classificação bem-sucedidos para {file.filename}", extra={"request_id": request_id})
        log_operation_success(operation_id, agent="main", request_id=request_id, file_name=file.filename, status="success")
        return final_result

    except HTTPException as e:
        logger.error(f"HTTPException ao processar {file.filename}: {e.detail}", extra={"request_id": request_id})
        log_operation_error(operation_id, str(e.detail), agent="main", request_id=request_id, file_name=file.filename, status="failed")
        raise e
    except Exception as e:
        logger.critical(f"Erro inesperado ao processar {file.filename}: {e}", extra={"request_id": request_id})
        log_operation_error(operation_id, str(e), agent="main", request_id=request_id, file_name=file.filename, status="failed")
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

@app.get("/supported-formats", response_model=SupportedFormatsResponse)
async def get_supported_formats(request: Request):
    """Retorna os formatos de documento suportados"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.info("Recebida requisição GET /supported-formats", extra={"request_id": request_id})
    log_operation_start("supported_formats_endpoint", agent="main", request_id=request_id)
    formats_info = await document_service.get_supported_formats()
    logger.debug(f"Formatos suportados retornados: {formats_info['formats']}")
    log_operation_success("supported_formats_endpoint", agent="main", request_id=request_id, formats_count=len(formats_info["formats"]))
    return SupportedFormatsResponse(**formats_info)

@app.get("/cache/clear")
async def clear_app_cache(request: Request):
    """Limpa o cache da aplicação"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.info("Recebida requisição GET /cache/clear", extra={"request_id": request_id})
    log_operation_start("clear_cache_endpoint", agent="main", request_id=request_id)
    await clear_cache()
    logger.info("Cache limpo com sucesso", extra={"request_id": request_id})
    log_operation_success("clear_cache_endpoint", agent="main", request_id=request_id)
    return {"message": "Cache limpo com sucesso!", "request_id": request_id}

# Configura o endpoint de métricas Prometheus
setup_metrics_endpoint(app)

# NOTE: O evento de startup está comentado, mas pode ser reativado para inicializações avançadas
# @app.on_event("startup")
# async def startup_event():
#     ...

if __name__ == "__main__":
    logger.info("Iniciando servidor Uvicorn via main.py (__main__)")
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.api_workers,
        log_level=settings.log_level.lower()
    )

