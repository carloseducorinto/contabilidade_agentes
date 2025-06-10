from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import time
from dotenv import load_dotenv
from .document_ingestion_agent import DocumentIngestionAgent
from .models import ProcessingResult
from .logging_config import get_logger, log_operation_start, log_operation_success, log_operation_error, log_file_processing
from .middleware import setup_middleware

# Load environment variables from .env file
load_dotenv()

# Configuração do logging centralizado
logger = get_logger("main")

# Inicialização da aplicação FastAPI
app = FastAPI(
    title="Sistema de Contabilidade com Agentes de IA",
    description="API para processamento automatizado de documentos fiscais brasileiros",
    version="2.0.0"
)

# Configuração CORS para permitir acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração dos middlewares de logging
setup_middleware(app)

# Inicialização do agente de ingestão com chave OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")
document_agent = DocumentIngestionAgent(openai_api_key=openai_api_key)

# Log de inicialização
log_operation_start("application_startup", openai_configured=bool(openai_api_key))

@app.on_event("startup")
async def startup_event():
    """Evento de inicialização da aplicação"""
    # Garante que o diretório de logs existe
    import pathlib
    pathlib.Path("logs").mkdir(exist_ok=True)
    
    log_operation_success(
        "application_startup",
        openai_configured=bool(openai_api_key),
        api_version="2.0.0"
    )


@app.get("/")
async def root(request: Request = None):
    """Endpoint de status da API"""
    request_id = getattr(request.state, 'request_id', 'unknown') if request else 'unknown'
    
    log_operation_start("root_endpoint", request_id=request_id)
    
    response = {
        "message": "Sistema de Contabilidade com Agentes de IA",
        "status": "ativo",
        "version": "2.0.0",
        "request_id": request_id
    }
    
    log_operation_success("root_endpoint", request_id=request_id)
    return response


@app.get("/health")
async def health_check(request: Request = None):
    """Endpoint de verificação de saúde da API"""
    request_id = getattr(request.state, 'request_id', 'unknown') if request else 'unknown'
    
    log_operation_start("health_check", request_id=request_id)
    
    response = {
        "status": "healthy", 
        "timestamp": time.time(),
        "request_id": request_id,
        "openai_configured": bool(openai_api_key)
    }
    
    log_operation_success("health_check", request_id=request_id, openai_configured=bool(openai_api_key))
    return response


@app.post("/process-document", response_model=ProcessingResult)
async def process_document(file: UploadFile = File(...), request: Request = None):
    """
    Processa um documento fiscal (XML, PDF ou Imagem) e retorna dados estruturados
    
    Args:
        file: Arquivo de documento fiscal (NF-e XML, PDF ou imagem JPG/PNG)
        request: Objeto da requisição FastAPI
        
    Returns:
        ProcessingResult com dados estruturados ou erro
    """
    start_time = time.time()
    request_id = getattr(request.state, 'request_id', 'unknown') if request else 'unknown'
    
    try:
        # Validação do tipo de arquivo
        if not file.filename:
            log_operation_error(
                "document_validation", 
                ValueError("Nome do arquivo não fornecido"),
                request_id=request_id
            )
            raise HTTPException(status_code=400, detail="Nome do arquivo não fornecido")
        
        # Determina o tipo do arquivo pela extensão
        file_extension = file.filename.lower().split('.')[-1]
        supported_types = ['xml', 'pdf', 'jpg', 'jpeg', 'png', 'webp', 'gif']
        
        if file_extension not in supported_types:
            log_operation_error(
                "document_validation",
                ValueError(f"Tipo de arquivo não suportado: {file_extension}"),
                request_id=request_id,
                file_name=file.filename,
                file_type=file_extension
            )
            raise HTTPException(
                status_code=400, 
                detail=f"Tipo de arquivo não suportado: {file_extension}. Suportados: {', '.join(supported_types).upper()}"
            )
        
        # Lê o conteúdo do arquivo
        file_content = await file.read()
        file_size = len(file_content)
        
        if not file_content:
            log_operation_error(
                "document_validation",
                ValueError("Arquivo vazio"),
                request_id=request_id,
                file_name=file.filename
            )
            raise HTTPException(status_code=400, detail="Arquivo vazio")
        
        # Log de processamento de arquivo
        log_file_processing(
            file_name=file.filename,
            file_size=file_size,
            file_type=file_extension,
            request_id=request_id
        )
        
        # Log de início do processamento
        log_operation_start(
            "document_processing",
            request_id=request_id,
            file_name=file.filename,
            file_size=file_size,
            file_type=file_extension
        )
        
        # Processa o documento usando o agente
        result = document_agent.process_document(file_content, file_extension)
        
        execution_time = time.time() - start_time
        
        if result.success:
            # Log de sucesso
            log_operation_success(
                "document_processing",
                execution_time=execution_time,
                request_id=request_id,
                file_name=file.filename,
                file_size=file_size,
                file_type=file_extension,
                document_type=result.data.documento if result.data else None,
                total_value=result.data.valor_total if result.data else None,
                items_count=len(result.data.itens) if result.data and result.data.itens else 0
            )
            return result
        else:
            # Log de erro no processamento
            log_operation_error(
                "document_processing",
                Exception(result.error_message),
                execution_time=execution_time,
                request_id=request_id,
                file_name=file.filename,
                file_size=file_size,
                file_type=file_extension
            )
            raise HTTPException(status_code=422, detail=result.error_message)
            
    except HTTPException:
        raise
    except Exception as e:
        execution_time = time.time() - start_time
        log_operation_error(
            "document_processing",
            e,
            execution_time=execution_time,
            request_id=request_id,
            file_name=file.filename if file else "unknown",
            file_size=file_size if 'file_size' in locals() else 0
        )
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@app.get("/supported-formats")
async def get_supported_formats(request: Request = None):
    """Retorna os formatos de documento suportados"""
    request_id = getattr(request.state, 'request_id', 'unknown') if request else 'unknown'
    
    log_operation_start("supported_formats", request_id=request_id)
    
    response = {
        "supported_formats": [
            {
                "format": "XML",
                "description": "Nota Fiscal Eletrônica (NF-e) em formato XML",
                "status": "implementado"
            },
            {
                "format": "PDF", 
                "description": "Nota Fiscal Eletrônica (NF-e) em formato PDF (via OCR)",
                "status": "implementado"
            },
            {
                "format": "IMAGE",
                "description": "Nota Fiscal Eletrônica (NF-e) em formato de imagem (JPG, PNG, WEBP, GIF via LLM Vision)",
                "status": "implementado" if openai_api_key else "requer_configuracao"
            }
        ],
        "request_id": request_id
    }
    
    log_operation_success(
        "supported_formats", 
        request_id=request_id, 
        formats_count=len(response["supported_formats"]),
        openai_configured=bool(openai_api_key)
    )
    
    return response


@app.get("/logs/recent")
async def get_recent_logs(request: Request = None, limit: int = 100):
    """Retorna os logs mais recentes da aplicação"""
    request_id = getattr(request.state, 'request_id', 'unknown') if request else 'unknown'
    
    log_operation_start("logs_retrieval", request_id=request_id, limit=limit)
    
    try:
        import pathlib
        log_file = pathlib.Path("logs/contabilidade_agentes.log")
        
        if not log_file.exists():
            return {"logs": [], "message": "Arquivo de log não encontrado"}
        
        # Lê as últimas linhas do arquivo
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            recent_lines = lines[-limit:] if len(lines) > limit else lines
        
        # Tenta fazer parse das linhas como JSON
        logs = []
        for line in recent_lines:
            try:
                log_entry = json.loads(line.strip())
                logs.append(log_entry)
            except json.JSONDecodeError:
                # Se não for JSON válido, adiciona como texto simples
                logs.append({"message": line.strip(), "level": "INFO"})
        
        log_operation_success(
            "logs_retrieval", 
            request_id=request_id, 
            logs_count=len(logs),
            limit=limit
        )
        
        return {
            "logs": logs,
            "count": len(logs),
            "request_id": request_id
        }
        
    except Exception as e:
        log_operation_error("logs_retrieval", e, request_id=request_id, limit=limit)
        raise HTTPException(status_code=500, detail=f"Erro ao recuperar logs: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

