"""
Configuração centralizada da aplicação usando Pydantic BaseSettings
"""
from typing import Optional, List, Union
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import os


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # API Configuration
    app_name: str = Field(default="Sistema de Contabilidade com Agentes de IA", env="APP_NAME")
    app_version: str = Field(default="3.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    
    # External APIs
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # CORS Configuration - using Union to allow both string and list
    cors_origins: Union[str, List[str]] = Field(
        default="*", 
        env="CORS_ORIGINS",
        description="Lista de origens permitidas para CORS"
    )
    cors_methods: Union[str, List[str]] = Field(
        default="GET,POST,PUT,DELETE,OPTIONS",
        env="CORS_METHODS"
    )
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            # If it's a comma-separated string, split it
            if ',' in v:
                return [origin.strip() for origin in v.split(',')]
            # If it's a single string, return as list
            return [v.strip()]
        return v
    
    @field_validator('cors_methods', mode='before')
    @classmethod
    def parse_cors_methods(cls, v):
        """Parse CORS methods from string or list"""
        if isinstance(v, str):
            # If it's a comma-separated string, split it
            if ',' in v:
                return [method.strip() for method in v.split(',')]
            # If it's a single string, return as list
            return [v.strip()]
        return v
    
    # File Processing
    max_file_size: int = Field(default=200 * 1024 * 1024, env="MAX_FILE_SIZE")  # 200MB
    allowed_file_types: Union[str, List[str]] = Field(
        default="xml,pdf,jpg,jpeg,png,webp,gif",
        env="ALLOWED_FILE_TYPES"
    )
    
    @field_validator('allowed_file_types', mode='before')
    @classmethod
    def parse_allowed_file_types(cls, v):
        """Parse allowed file types from string or list"""
        if isinstance(v, str):
            # If it's a comma-separated string, split it
            if ',' in v:
                return [file_type.strip() for file_type in v.split(',')]
            # If it's a single string, return as list
            return [v.strip()]
        return v
    
    # Performance & Scalability
    max_concurrent_processing: int = Field(default=5, env="MAX_CONCURRENT_PROCESSING")
    max_batch_size: int = Field(default=10, env="MAX_BATCH_SIZE")
    request_timeout: int = Field(default=300, env="REQUEST_TIMEOUT")  # 5 minutes
    
    # OCR Configuration
    tesseract_lang: str = Field(default="por", env="TESSERACT_LANG")
    tesseract_psm: int = Field(default=6, env="TESSERACT_PSM")
    pdf_dpi: int = Field(default=300, env="PDF_DPI")
    
    # LLM Configuration
    llm_model: str = Field(default="gpt-4o", env="LLM_MODEL")
    llm_temperature: float = Field(default=0.1, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2000, env="LLM_MAX_TOKENS")
    llm_retry_attempts: int = Field(default=3, env="LLM_RETRY_ATTEMPTS")
    llm_retry_delay: float = Field(default=1.0, env="LLM_RETRY_DELAY")
    llm_retry_backoff: float = Field(default=2.0, env="LLM_RETRY_BACKOFF")
    
    # Logging Configuration
    log_level: str = Field(default="DEBUG", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    log_file: Optional[str] = Field(default="logs/log_app.log", env="LOG_FILE")
    log_rotation: bool = Field(default=True, env="LOG_ROTATION")
    log_max_size: str = Field(default="10MB", env="LOG_MAX_SIZE")
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # Security
    secret_key: str = Field(default="dev-secret-key", env="SECRET_KEY")
    
    # Performance
    enable_caching: bool = Field(default=True, env="ENABLE_CACHING")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    
    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    
    # Classification Agent Settings
    openai_classification_model: str = Field(default="gpt-4o", env="OPENAI_CLASSIFICATION_MODEL")
    openai_classification_temperature: float = Field(default=0.7, env="OPENAI_CLASSIFICATION_TEMPERATURE")
    classification_cache_ttl: int = Field(default=3600, env="CLASSIFICATION_CACHE_TTL")  # 1 hour
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Disable JSON parsing for specific fields to allow string input
        env_parse_none_str = None
        # Parse all env vars as strings, let validators handle the conversion
        json_encoders = {}


# Instância global das configurações
settings = Settings()


def get_settings() -> Settings:
    """Retorna a instância das configurações"""
    return settings


def is_production() -> bool:
    """Verifica se está em ambiente de produção"""
    return settings.environment.lower() == "production"


def is_development() -> bool:
    """Verifica se está em ambiente de desenvolvimento"""
    return settings.environment.lower() == "development"


def get_cors_config() -> dict:
    """Retorna configuração de CORS"""
    return {
        "allow_origins": settings.cors_origins,
        "allow_methods": settings.cors_methods,
        "allow_headers": ["*"],
        "allow_credentials": True
    }


