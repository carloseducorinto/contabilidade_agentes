"""
Exceções customizadas para o sistema de contabilidade
"""
from typing import Optional, Dict, Any


class ContabilidadeBaseException(Exception):
    """Exceção base para o sistema de contabilidade"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class DocumentProcessingError(ContabilidadeBaseException):
    """Erro no processamento de documentos"""
    pass


class XMLProcessingError(DocumentProcessingError):
    """Erro específico no processamento de XML"""
    pass


class PDFProcessingError(DocumentProcessingError):
    """Erro específico no processamento de PDF via OCR"""
    pass


class ImageProcessingError(DocumentProcessingError):
    """Erro específico no processamento de imagem via LLM"""
    pass


class ValidationError(ContabilidadeBaseException):
    """Erro de validação de dados"""
    pass


class ConfigurationError(ContabilidadeBaseException):
    """Erro de configuração"""
    pass


class ExternalAPIError(ContabilidadeBaseException):
    """Erro em chamadas para APIs externas"""
    pass


class FileUploadError(ContabilidadeBaseException):
    """Erro no upload de arquivos"""
    pass


class UnsupportedFileTypeError(FileUploadError):
    """Tipo de arquivo não suportado"""
    pass


class FileSizeExceededError(FileUploadError):
    """Tamanho de arquivo excedido"""
    pass

