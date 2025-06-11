"""
Modelos Pydantic para validação de requisições e respostas da API
"""
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class FileUploadRequest(BaseModel):
    """Modelo para validação de upload de arquivo"""
    filename: str = Field(..., description="Nome do arquivo")
    content_type: str = Field(..., description="Tipo de conteúdo do arquivo")
    size: int = Field(..., ge=1, description="Tamanho do arquivo em bytes")
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Nome do arquivo não pode estar vazio")
        return v.strip()
    
    @field_validator('size')
    @classmethod
    def validate_size(cls, v):
        max_size = 200 * 1024 * 1024  # 200MB
        if v > max_size:
            raise ValueError(f"Arquivo muito grande. Máximo: {max_size / (1024*1024):.1f}MB")
        return v


class ProcessDocumentRequest(BaseModel):
    """Modelo para requisição de processamento de documento"""
    file_type: str = Field(..., description="Tipo do arquivo (xml, pdf, jpg, etc.)")
    filename: Optional[str] = Field(None, description="Nome do arquivo (opcional)")
    
    @field_validator('file_type')
    @classmethod
    def validate_file_type(cls, v):
        allowed_types = ['xml', 'pdf', 'jpg', 'jpeg', 'png', 'webp', 'gif']
        if v.lower() not in allowed_types:
            raise ValueError(f"Tipo de arquivo não suportado: {v}. Tipos permitidos: {allowed_types}")
        return v.lower()


class ErrorResponse(BaseModel):
    """Modelo para respostas de erro"""
    success: bool = Field(default=False, description="Indica se a operação foi bem-sucedida")
    error: str = Field(..., description="Mensagem de erro")
    error_code: Optional[str] = Field(None, description="Código do erro")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalhes adicionais do erro")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp do erro")


class SuccessResponse(BaseModel):
    """Modelo para respostas de sucesso"""
    success: bool = Field(default=True, description="Indica se a operação foi bem-sucedida")
    message: str = Field(..., description="Mensagem de sucesso")
    data: Optional[Dict[str, Any]] = Field(None, description="Dados da resposta")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp da resposta")


class HealthCheckResponse(BaseModel):
    """Modelo para resposta do health check"""
    status: str = Field(..., description="Status da aplicação")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp da verificação")
    version: str = Field(..., description="Versão da aplicação")
    uptime: float = Field(..., description="Tempo de atividade em segundos")
    dependencies: Dict[str, str] = Field(..., description="Status das dependências")


class SupportedFormatsResponse(BaseModel):
    """Modelo para resposta de formatos suportados"""
    formats: List[Dict[str, Any]] = Field(..., description="Lista de formatos suportados")
    max_file_size_mb: float = Field(..., description="Tamanho máximo de arquivo em MB")
    allowed_extensions: List[str] = Field(..., description="Extensões de arquivo permitidas")


class ProcessingMetrics(BaseModel):
    """Modelo para métricas de processamento"""
    operation_id: str = Field(..., description="ID da operação")
    operation_type: str = Field(..., description="Tipo da operação")
    agent: str = Field(..., description="Agente responsável")
    start_time: datetime = Field(..., description="Tempo de início")
    end_time: Optional[datetime] = Field(None, description="Tempo de fim")
    duration_ms: Optional[float] = Field(None, description="Duração em milissegundos")
    success: bool = Field(..., description="Se a operação foi bem-sucedida")
    file_type: Optional[str] = Field(None, description="Tipo do arquivo processado")
    file_size: Optional[int] = Field(None, description="Tamanho do arquivo")
    error_message: Optional[str] = Field(None, description="Mensagem de erro, se houver")


class ValidationErrorDetail(BaseModel):
    """Modelo para detalhes de erro de validação"""
    field: str = Field(..., description="Campo que falhou na validação")
    message: str = Field(..., description="Mensagem de erro")
    invalid_value: Optional[Any] = Field(None, description="Valor inválido fornecido")


class ValidationErrorResponse(BaseModel):
    """Modelo para resposta de erro de validação"""
    success: bool = Field(default=False, description="Indica se a operação foi bem-sucedida")
    error: str = Field(default="Erro de validação", description="Mensagem de erro")
    error_code: str = Field(default="VALIDATION_ERROR", description="Código do erro")
    details: List[ValidationErrorDetail] = Field(..., description="Detalhes dos erros de validação")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp do erro")


class APIKeyValidationRequest(BaseModel):
    """Modelo para validação de chave de API"""
    api_key: str = Field(..., min_length=1, description="Chave da API")
    service: str = Field(..., description="Serviço da API (ex: openai)")
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Chave da API não pode estar vazia")
        return v.strip()


class ConfigurationRequest(BaseModel):
    """Modelo para requisições de configuração"""
    openai_api_key: Optional[str] = Field(None, description="Chave da API OpenAI")
    log_level: Optional[str] = Field(None, description="Nível de log")
    enable_caching: Optional[bool] = Field(None, description="Habilitar cache")
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        if v is not None:
            allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if v.upper() not in allowed_levels:
                raise ValueError(f"Nível de log inválido: {v}. Permitidos: {allowed_levels}")
        return v.upper() if v else v


class BatchProcessingRequest(BaseModel):
    """Modelo para processamento em lote"""
    files: List[FileUploadRequest] = Field(..., min_items=1, max_items=10, description="Lista de arquivos para processar")
    options: Optional[Dict[str, Any]] = Field(None, description="Opções de processamento")
    
    @field_validator('files')
    @classmethod
    def validate_files_count(cls, v):
        if len(v) > 10:
            raise ValueError("Máximo de 10 arquivos por lote")
        return v


class BatchProcessingResponse(BaseModel):
    """Modelo para resposta de processamento em lote"""
    success: bool = Field(..., description="Indica se o lote foi processado com sucesso")
    total_files: int = Field(..., description="Total de arquivos no lote")
    processed_files: int = Field(..., description="Arquivos processados com sucesso")
    failed_files: int = Field(..., description="Arquivos que falharam no processamento")
    results: List[Dict[str, Any]] = Field(..., description="Resultados individuais")
    processing_time: float = Field(..., description="Tempo total de processamento")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp do processamento")

