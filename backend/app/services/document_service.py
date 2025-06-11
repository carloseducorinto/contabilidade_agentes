"""
Serviço principal de processamento de documentos
"""
from typing import Dict, Any, Optional
from ..models import ProcessingResult
from ..processors import XMLProcessor, PDFProcessor, ImageProcessor
from ..exceptions import (
    DocumentProcessingError, 
    UnsupportedFileTypeError,
    FileSizeExceededError,
    ConfigurationError
)
from ..config import get_settings
from ..logging_config import get_logger, log_operation_start, log_operation_success, log_operation_error

settings = get_settings()
logger = get_logger("DocumentService")


class DocumentService:
    """Serviço principal para processamento de documentos fiscais"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.logger = logger
        self.openai_api_key = openai_api_key or settings.openai_api_key
        
        # Inicializa processadores
        self.xml_processor = XMLProcessor()
        self.pdf_processor = PDFProcessor()
        self.image_processor = ImageProcessor(self.openai_api_key)
        
        # Mapeamento de tipos de arquivo para processadores
        self.processors = {
            'xml': self.xml_processor,
            'pdf': self.pdf_processor,
            'jpg': self.image_processor,
            'jpeg': self.image_processor,
            'png': self.image_processor,
            'webp': self.image_processor,
            'gif': self.image_processor
        }
    
    def process_document(
        self, 
        file_content: bytes, 
        file_type: str,
        filename: Optional[str] = None
    ) -> ProcessingResult:
        """
        Processa um documento fiscal e retorna dados estruturados
        
        Args:
            file_content: Conteúdo do arquivo em bytes
            file_type: Tipo do arquivo (xml, pdf, jpg, etc.)
            filename: Nome do arquivo (opcional)
            
        Returns:
            ProcessingResult com os dados extraídos ou erro
        """
        operation_id = log_operation_start(
            "document_processing",
            agent="DocumentService",
            file_type=file_type,
            file_size=len(file_content),
            filename=filename
        )
        
        try:
            # Validações
            self._validate_file(file_content, file_type)
            
            # Seleciona processador apropriado
            processor = self._get_processor(file_type)
            
            # Processa documento
            documento = processor.process(file_content)
            
            # Cria resultado de sucesso
            result = ProcessingResult(
                success=True,
                document_id=operation_id,  # Use operation_id as document_id
                document_type=file_type,
                extracted_data=documento.model_dump(),  # Convert to dict and use correct field name
                error=None,
                processing_time=0.0  # Será calculado pelo middleware
            )
            
            log_operation_success(
                operation_id,
                agent="DocumentService",
                file_type=file_type,
                file_size=len(file_content),
                numero_documento=documento.numero_documento,
                valor_total=documento.valor_total
            )
            
            return result
            
        except Exception as e:
            log_operation_error(
                operation_id, 
                f"Erro no processamento: {str(e)}", 
                agent="DocumentService",
                file_type=file_type
            )
            
            # Cria resultado de erro
            result = ProcessingResult(
                success=False,
                document_id=operation_id,  # Use operation_id as document_id
                document_type=file_type,
                extracted_data=None,
                error=str(e),
                processing_time=0.0
            )
            
            return result
    
    def _validate_file(self, file_content: bytes, file_type: str) -> None:
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
    
    def _get_processor(self, file_type: str):
        """Retorna o processador apropriado para o tipo de arquivo"""
        processor = self.processors.get(file_type.lower())
        
        if not processor:
            raise UnsupportedFileTypeError(f"Processador não encontrado para tipo: {file_type}")
        
        # Validação específica para processador de imagem
        if file_type.lower() in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
            if not self.openai_api_key:
                raise ConfigurationError(
                    "Chave da API OpenAI não configurada para processamento de imagem",
                    error_code="OPENAI_API_KEY_MISSING"
                )
        
        return processor
    
    def get_supported_formats(self) -> Dict[str, Any]:
        """Retorna informações sobre os formatos suportados"""
        return {
            "formats": [
                {
                    "format": "XML",
                    "description": "Nota Fiscal Eletrônica (NF-e) em formato XML",
                    "status": "implementado",
                    "processor": "XMLProcessor"
                },
                {
                    "format": "PDF", 
                    "description": "Nota Fiscal Eletrônica (NF-e) em formato PDF (via OCR)",
                    "status": "implementado",
                    "processor": "PDFProcessor"
                },
                {
                    "format": "Imagem",
                    "description": "Nota Fiscal Eletrônica (NF-e) em formato de imagem (via LLM Vision)",
                    "status": "implementado",
                    "processor": "ImageProcessor",
                    "supported_types": ["JPG", "JPEG", "PNG", "WEBP", "GIF"]
                }
            ],
            "max_file_size_mb": settings.max_file_size / (1024 * 1024),
            "allowed_extensions": settings.allowed_file_types
        }

