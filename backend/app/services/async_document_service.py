"""
Serviço assíncrono de processamento de documentos com BackgroundTasks
"""
import asyncio
from typing import Dict, Any, Optional
from fastapi import BackgroundTasks
from ..models import ProcessingResult, ProcessingMetrics
from ..processors import XMLProcessor, PDFProcessor
from ..processors.async_image_processor import AsyncImageProcessor
from ..exceptions import (
    DocumentProcessingError, 
    UnsupportedFileTypeError,
    FileSizeExceededError,
    ConfigurationError
)
from ..config import get_settings
from ..logging_config import get_logger, log_operation_start, log_operation_success, log_operation_error
from ..utils.cache import cached, get_cache_stats
import time

settings = get_settings()
logger = get_logger("AsyncDocumentService")


class AsyncDocumentService:
    """Serviço assíncrono para processamento de documentos fiscais"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.logger = logger
        self.openai_api_key = openai_api_key or settings.openai_api_key
        
        # Inicializa processadores
        self.xml_processor = XMLProcessor()
        self.pdf_processor = PDFProcessor(openai_api_key)
        self.async_image_processor = AsyncImageProcessor(self.openai_api_key)
        
        # Mapeamento de tipos de arquivo para processadores
        self.sync_processors = {
            'xml': self.xml_processor
        }
        
        self.async_processors = {
            'pdf': self.pdf_processor,  # PDF agora é async devido ao fallback LLM
            'jpg': self.async_image_processor,
            'jpeg': self.async_image_processor,
            'png': self.async_image_processor,
            'webp': self.async_image_processor,
            'gif': self.async_image_processor
        }
        
        # Semáforo para controlar concorrência
        self.processing_semaphore = asyncio.Semaphore(settings.max_concurrent_processing)
    
    async def process_document(
        self, 
        file_content: bytes, 
        file_type: str,
        filename: Optional[str] = None,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> ProcessingResult:
        """
        Processa um documento fiscal de forma assíncrona
        
        Args:
            file_content: Conteúdo do arquivo em bytes
            file_type: Tipo do arquivo (xml, pdf, jpg, etc.)
            filename: Nome do arquivo (opcional)
            background_tasks: Tarefas em background (opcional)
            
        Returns:
            ProcessingResult com os dados extraídos ou erro
        """
        operation_id = log_operation_start(
            "async_document_processing",
            agent="AsyncDocumentService",
            file_type=file_type,
            file_size=len(file_content),
            file_name=filename
        )
        
        start_time = time.time()
        
        try:
            # Validações
            await self._validate_file(file_content, file_type)
            
            # Processa documento com controle de concorrência
            async with self.processing_semaphore:
                documento = await self._process_document_internal(file_content, file_type)
            
            processing_time = time.time() - start_time
            
            # Cria resultado de sucesso
            result = ProcessingResult(
                success=True,
                data=documento,
                error=None,
                processing_time=processing_time,
                metadata={
                    "operation_id": operation_id,
                    "file_type": file_type,
                    "file_size": len(file_content),
                    "processor_type": "async" if file_type in self.async_processors else "sync"
                }
            )
            
            # Adiciona métricas em background se disponível
            if background_tasks:
                background_tasks.add_task(
                    self._log_processing_metrics,
                    operation_id,
                    file_type,
                    len(file_content),
                    processing_time,
                    True,
                    documento.numero_documento
                )
            
            log_operation_success(
                operation_id,
                agent="AsyncDocumentService",
                file_type=file_type,
                file_size=len(file_content),
                processing_time=processing_time,
                numero_documento=documento.numero_documento,
                valor_total=documento.valor_total
            )
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            log_operation_error(
                operation_id, 
                f"Erro no processamento: {str(e)}", 
                agent="AsyncDocumentService",
                file_type=file_type,
                processing_time=processing_time
            )
            
            # Adiciona métricas de erro em background se disponível
            if background_tasks:
                background_tasks.add_task(
                    self._log_processing_metrics,
                    operation_id,
                    file_type,
                    len(file_content),
                    processing_time,
                    False,
                    None,
                    str(e)
                )
            
            # Cria resultado de erro
            result = ProcessingResult(
                success=False,
                data=None,
                error=str(e),
                processing_time=processing_time,
                metadata={
                    "operation_id": operation_id,
                    "file_type": file_type,
                    "error_type": type(e).__name__
                }
            )
            
            return result
    
    async def _process_document_internal(self, file_content: bytes, file_type: str):
        """Processa documento internamente, escolhendo o processador apropriado"""
        
        # Processadores assíncronos (PDF, imagens via LLM)
        if file_type.lower() in self.async_processors:
            processor = self.async_processors[file_type.lower()]
            if file_type.lower() == 'pdf':
                return await processor.process(file_content)
            else:
                return await processor.process(file_content, file_type)
        
        # Processadores síncronos (XML, PDF)
        elif file_type.lower() in self.sync_processors:
            processor = self.sync_processors[file_type.lower()]
            # Executa em thread pool para não bloquear o event loop
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, processor.process, file_content)
        
        else:
            raise UnsupportedFileTypeError(f"Processador não encontrado para tipo: {file_type}")
    
    async def _validate_file(self, file_content: bytes, file_type: str) -> None:
        """Valida o arquivo antes do processamento"""
        
        # Verifica tamanho do arquivo
        if len(file_content) > settings.max_file_size:
            raise FileSizeExceededError(
                f"Arquivo muito grande. Tamanho máximo: {settings.max_file_size / (1024*1024):.1f}MB",
                details={"file_size": len(file_content), "max_size": settings.max_file_size}
            )
        
        # Verifica tipo de arquivo
        if file_type.lower() not in settings.allowed_file_types:
            raise UnsupportedFileTypeError(
                f"Tipo de arquivo não suportado: {file_type}",
                details={"file_type": file_type, "allowed_types": settings.allowed_file_types}
            )
        
        # Verifica se o arquivo não está vazio
        if len(file_content) == 0:
            raise DocumentProcessingError("Arquivo vazio")
        
        # Validação específica para processador de imagem
        if file_type.lower() in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
            if not self.openai_api_key:
                raise ConfigurationError(
                    "Chave da API OpenAI não configurada para processamento de imagem",
                    error_code="OPENAI_API_KEY_MISSING"
                )
    
    async def _log_processing_metrics(
        self,
        operation_id: str,
        file_type: str,
        file_size: int,
        processing_time: float,
        success: bool,
        numero_documento: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Log de métricas de processamento em background"""
        try:
            metrics = ProcessingMetrics(
                operation_id=operation_id,
                operation_type="document_processing",
                agent="AsyncDocumentService",
                start_time=time.time() - processing_time,
                end_time=time.time(),
                duration_ms=processing_time * 1000,
                success=success,
                file_type=file_type,
                file_size=file_size,
                error_message=error_message
            )
            
            # Em produção, isso seria enviado para um sistema de métricas
            self.logger.info(f"Métricas de processamento: {metrics.dict()}")
            
        except Exception as e:
            self.logger.error(f"Erro ao registrar métricas: {str(e)}")
    
    async def process_batch(
        self,
        files: list,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> Dict[str, Any]:
        """
        Processa múltiplos documentos em paralelo
        
        Args:
            files: Lista de arquivos para processar
            background_tasks: Tarefas em background
            
        Returns:
            Resultado do processamento em lote
        """
        start_time = time.time()
        
        # Limita o número de arquivos processados simultaneamente
        semaphore = asyncio.Semaphore(settings.max_batch_size)
        
        async def process_single_file(file_data):
            async with semaphore:
                return await self.process_document(
                    file_data['content'],
                    file_data['type'],
                    file_data.get('filename'),
                    background_tasks
                )
        
        # Processa arquivos em paralelo
        tasks = [process_single_file(file_data) for file_data in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analisa resultados
        successful = sum(1 for r in results if isinstance(r, ProcessingResult) and r.success)
        failed = len(results) - successful
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "total_files": len(files),
            "processed_files": successful,
            "failed_files": failed,
            "results": [r.dict() if isinstance(r, ProcessingResult) else {"error": str(r)} for r in results],
            "processing_time": processing_time
        }
    
    @cached(ttl=300, key_prefix="service_stats")  # Cache por 5 minutos
    async def get_service_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do serviço"""
        cache_stats = await get_cache_stats()
        
        return {
            "service": "AsyncDocumentService",
            "processors": {
                "sync": list(self.sync_processors.keys()),
                "async": list(self.async_processors.keys())
            },
            "cache": cache_stats,
            "settings": {
                "max_concurrent_processing": settings.max_concurrent_processing,
                "max_batch_size": settings.max_batch_size,
                "max_file_size_mb": settings.max_file_size / (1024 * 1024),
                "cache_enabled": settings.enable_caching
            }
        }
    
    async def get_supported_formats(self) -> Dict[str, Any]:
        """Retorna informações sobre os formatos suportados"""
        return {
            "formats": [
                {
                    "format": "XML",
                    "description": "Nota Fiscal Eletrônica (NF-e) em formato XML",
                    "status": "implementado",
                    "processor": "XMLProcessor",
                    "async": False
                },
                {
                    "format": "PDF", 
                    "description": "Nota Fiscal Eletrônica (NF-e) em formato PDF (via OCR + LLM fallback)",
                    "status": "implementado",
                    "processor": "PDFProcessor",
                    "async": True,
                    "features": ["OCR", "LLM_Enhancement"]
                },
                {
                    "format": "Imagem",
                    "description": "Nota Fiscal Eletrônica (NF-e) em formato de imagem (via LLM Vision)",
                    "status": "implementado",
                    "processor": "AsyncImageProcessor",
                    "async": True,
                    "supported_types": ["JPG", "JPEG", "PNG", "WEBP", "GIF"]
                }
            ],
            "max_file_size_mb": settings.max_file_size / (1024 * 1024),
            "allowed_extensions": settings.allowed_file_types,
            "max_concurrent_processing": settings.max_concurrent_processing,
            "max_batch_size": settings.max_batch_size
        }

