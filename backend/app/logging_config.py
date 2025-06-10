"""
Sistema de logging seguro com mascaramento de dados sensíveis
"""
import json
import logging
import logging.handlers
import sys
import time
from typing import Any, Dict, Optional
from pathlib import Path
from .config import get_settings, is_production
from .utils.security import DataMasker, mask_sensitive_data

settings = get_settings()


class SecureJSONFormatter(logging.Formatter):
    """Formatter JSON que mascara dados sensíveis"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Cria dicionário base do log
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Adiciona informações extras se disponíveis
        if hasattr(record, 'extra') and record.extra:
            log_data.update(record.extra)
        
        # Adiciona informações de exceção se disponível
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Adiciona stack trace se disponível
        if record.stack_info:
            log_data["stack_info"] = record.stack_info
        
        # Mascara dados sensíveis
        masked_data = DataMasker.mask_log_record(log_data)
        
        return json.dumps(masked_data, ensure_ascii=False, default=str)


class SecureTextFormatter(logging.Formatter):
    """Formatter de texto que mascara dados sensíveis"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def format(self, record: logging.LogRecord) -> str:
        # Formata usando o formatter padrão
        formatted = super().format(record)
        
        # Mascara dados sensíveis na mensagem formatada
        return DataMasker.mask_string(formatted)


class SecureRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Handler de arquivo rotativo com segurança aprimorada"""
    
    def __init__(self, filename: str, mode: str = 'a', maxBytes: int = 0, 
                 backupCount: int = 0, encoding: Optional[str] = None, delay: bool = False):
        
        # Cria diretório se não existir
        log_path = Path(filename)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
        
        # Define permissões seguras para o arquivo de log
        if log_path.exists():
            log_path.chmod(0o600)  # Apenas o proprietário pode ler/escrever


def setup_secure_logging():
    """Configura sistema de logging seguro"""
    
    # Remove handlers existentes
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Configura nível de log
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    
    if settings.log_format.lower() == "json":
        console_handler.setFormatter(SecureJSONFormatter())
    else:
        console_handler.setFormatter(SecureTextFormatter())
    
    root_logger.addHandler(console_handler)
    
    # Handler para arquivo (se configurado)
    if settings.log_file:
        try:
            # Parse do tamanho máximo do arquivo
            max_bytes = _parse_size(settings.log_max_size)
            
            file_handler = SecureRotatingFileHandler(
                filename=settings.log_file,
                maxBytes=max_bytes,
                backupCount=settings.log_backup_count,
                encoding='utf-8'
            )
            
            if settings.log_format.lower() == "json":
                file_handler.setFormatter(SecureJSONFormatter())
            else:
                file_handler.setFormatter(SecureTextFormatter())
            
            root_logger.addHandler(file_handler)
            
        except Exception as e:
            # Se falhar ao configurar arquivo, continua apenas com console
            console_handler.setFormatter(SecureTextFormatter())
            root_logger.error(f"Erro ao configurar log em arquivo: {str(e)}")
    
    # Configura loggers específicos
    _configure_specific_loggers()
    
    # Log inicial
    logger = logging.getLogger("SecureLogging")
    logger.info("Sistema de logging seguro inicializado", extra={
        "log_level": settings.log_level,
        "log_format": settings.log_format,
        "log_file": settings.log_file,
        "production": is_production()
    })


def _parse_size(size_str: str) -> int:
    """Converte string de tamanho para bytes"""
    size_str = size_str.upper().strip()
    
    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        return int(size_str)


def _configure_specific_loggers():
    """Configura loggers específicos com níveis apropriados"""
    
    # Logger para bibliotecas externas
    external_loggers = [
        'urllib3.connectionpool',
        'requests.packages.urllib3',
        'openai',
        'httpx',
        'httpcore'
    ]
    
    for logger_name in external_loggers:
        logger = logging.getLogger(logger_name)
        if is_production():
            logger.setLevel(logging.WARNING)
        else:
            logger.setLevel(logging.INFO)
    
    # Logger para FastAPI
    uvicorn_logger = logging.getLogger("uvicorn")
    if is_production():
        uvicorn_logger.setLevel(logging.INFO)
    else:
        uvicorn_logger.setLevel(logging.DEBUG)


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger configurado com mascaramento de dados sensíveis
    
    Args:
        name: Nome do logger
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


def log_operation_start(operation_type: str, agent: str, **kwargs) -> str:
    """
    Registra o início de uma operação
    
    Args:
        operation_type: Tipo da operação
        agent: Nome do agente
        **kwargs: Dados adicionais
        
    Returns:
        ID da operação para rastreamento
    """
    import uuid
    operation_id = str(uuid.uuid4())
    
    logger = get_logger(agent)
    
    # Mascara dados sensíveis nos kwargs
    safe_kwargs = mask_sensitive_data(kwargs)
    
    logger.info(f"Iniciando operação: {operation_type}", extra={
        "operation_id": operation_id,
        "operation_type": operation_type,
        "agent": agent,
        "start_time": time.time(),
        **safe_kwargs
    })
    
    return operation_id


def log_operation_success(operation_id: str, agent: str, **kwargs):
    """
    Registra o sucesso de uma operação
    
    Args:
        operation_id: ID da operação
        agent: Nome do agente
        **kwargs: Dados adicionais
    """
    logger = get_logger(agent)
    
    # Mascara dados sensíveis nos kwargs
    safe_kwargs = mask_sensitive_data(kwargs)
    
    logger.info(f"Operação concluída com sucesso", extra={
        "operation_id": operation_id,
        "agent": agent,
        "end_time": time.time(),
        "status": "success",
        **safe_kwargs
    })


def log_operation_error(operation_id: str, error_message: str, agent: str, **kwargs):
    """
    Registra erro em uma operação
    
    Args:
        operation_id: ID da operação
        error_message: Mensagem de erro
        agent: Nome do agente
        **kwargs: Dados adicionais
    """
    logger = get_logger(agent)
    
    # Mascara dados sensíveis na mensagem de erro e kwargs
    safe_error_message = DataMasker.mask_string(error_message)
    safe_kwargs = mask_sensitive_data(kwargs)
    
    logger.error(f"Erro na operação: {safe_error_message}", extra={
        "operation_id": operation_id,
        "agent": agent,
        "end_time": time.time(),
        "status": "error",
        **safe_kwargs
    })


def log_security_event(event_type: str, details: Dict[str, Any], severity: str = "WARNING"):
    """
    Registra eventos de segurança
    
    Args:
        event_type: Tipo do evento de segurança
        details: Detalhes do evento
        severity: Severidade (INFO, WARNING, ERROR, CRITICAL)
    """
    logger = get_logger("SecurityEvents")
    
    # Mascara dados sensíveis nos detalhes
    safe_details = mask_sensitive_data(details)
    
    log_method = getattr(logger, severity.lower(), logger.warning)
    log_method(f"Evento de segurança: {event_type}", extra={
        "event_type": event_type,
        "security_event": True,
        "timestamp": time.time(),
        **safe_details
    })


# Inicializa o sistema de logging ao importar o módulo
setup_secure_logging()

