import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path
import os


class StructuredFormatter(logging.Formatter):
    """Formatter para logs estruturados em JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Formata o log em JSON estruturado"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Adiciona informações extras se disponíveis
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'operation'):
            log_data['operation'] = record.operation
        if hasattr(record, 'execution_time'):
            log_data['execution_time'] = record.execution_time
        if hasattr(record, 'file_name'):
            log_data['file_name'] = record.file_name
        if hasattr(record, 'file_size'):
            log_data['file_size'] = record.file_size
        if hasattr(record, 'file_type'):
            log_data['file_type'] = record.file_type
        if hasattr(record, 'processing_result'):
            log_data['processing_result'] = record.processing_result
        
        # Adiciona informações de erro se for uma exceção
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info)
            }
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class AppLogger:
    """Gerenciador centralizado de logs da aplicação"""
    
    def __init__(self, 
                 name: str = "contabilidade_agentes",
                 level: int = logging.INFO,
                 log_to_file: bool = True,
                 log_file_path: Optional[str] = None):
        """
        Inicializa o sistema de logging
        
        Args:
            name: Nome do logger principal
            level: Nível mínimo de logging
            log_to_file: Se deve salvar logs em arquivo
            log_file_path: Caminho do arquivo de log
        """
        self.name = name
        self.level = level
        self.log_to_file = log_to_file
        
        # Define o caminho do arquivo de log
        if log_file_path:
            self.log_file_path = Path(log_file_path)
        else:
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            self.log_file_path = logs_dir / f"{name}.log"
        
        # Configura o logger principal
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Configura o logger com formatadores e handlers"""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.level)
        
        # Remove handlers existentes para evitar duplicação
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Formatter estruturado
        formatter = StructuredFormatter()
        
        # Handler para console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Handler para arquivo se habilitado
        if self.log_to_file:
            file_handler = logging.FileHandler(
                self.log_file_path, 
                mode='a', 
                encoding='utf-8'
            )
            file_handler.setLevel(self.level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        logger.propagate = False
        return logger
    
    def get_logger(self, module_name: str) -> logging.Logger:
        """Retorna um logger específico para um módulo"""
        return logging.getLogger(f"{self.name}.{module_name}")
    
    def log_operation_start(self, 
                          operation: str, 
                          request_id: Optional[str] = None,
                          user_id: Optional[str] = None,
                          **kwargs) -> None:
        """Log de início de operação"""
        extra = {
            'operation': operation,
            'request_id': request_id,
            'user_id': user_id,
            **kwargs
        }
        self.logger.info(f"Iniciando operação: {operation}", extra=extra)
    
    def log_operation_success(self, 
                            operation: str,
                            execution_time: Optional[float] = None,
                            request_id: Optional[str] = None,
                            **kwargs) -> None:
        """Log de sucesso de operação"""
        extra = {
            'operation': operation,
            'execution_time': execution_time,
            'request_id': request_id,
            'processing_result': 'success',
            **kwargs
        }
        message = f"Operação concluída com sucesso: {operation}"
        if execution_time:
            message += f" (tempo: {execution_time:.2f}s)"
        self.logger.info(message, extra=extra)
    
    def log_operation_error(self, 
                          operation: str,
                          error: Exception,
                          execution_time: Optional[float] = None,
                          request_id: Optional[str] = None,
                          **kwargs) -> None:
        """Log de erro de operação"""
        extra = {
            'operation': operation,
            'execution_time': execution_time,
            'request_id': request_id,
            'processing_result': 'error',
            **kwargs
        }
        message = f"Erro na operação: {operation} - {str(error)}"
        if execution_time:
            message += f" (tempo: {execution_time:.2f}s)"
        self.logger.error(message, extra=extra, exc_info=True)
    
    def log_file_processing(self, 
                           file_name: str,
                           file_size: int,
                           file_type: str,
                           operation: str = "file_processing",
                           **kwargs) -> None:
        """Log específico para processamento de arquivos"""
        extra = {
            'operation': operation,
            'file_name': file_name,
            'file_size': file_size,
            'file_type': file_type,
            **kwargs
        }
        self.logger.info(
            f"Processando arquivo: {file_name} ({file_size} bytes, tipo: {file_type})",
            extra=extra
        )
    
    def log_api_request(self, 
                       endpoint: str,
                       method: str,
                       request_id: Optional[str] = None,
                       user_agent: Optional[str] = None,
                       **kwargs) -> None:
        """Log de requisições API"""
        extra = {
            'operation': 'api_request',
            'request_id': request_id,
            'endpoint': endpoint,
            'method': method,
            'user_agent': user_agent,
            **kwargs
        }
        self.logger.info(f"API Request: {method} {endpoint}", extra=extra)
    
    def log_api_response(self, 
                        endpoint: str,
                        method: str,
                        status_code: int,
                        execution_time: float,
                        request_id: Optional[str] = None,
                        **kwargs) -> None:
        """Log de respostas API"""
        extra = {
            'operation': 'api_response',
            'request_id': request_id,
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'execution_time': execution_time,
            **kwargs
        }
        level = logging.INFO if status_code < 400 else logging.ERROR
        self.logger.log(
            level,
            f"API Response: {method} {endpoint} - {status_code} ({execution_time:.3f}s)",
            extra=extra
        )


# Instância global do logger
app_logger = AppLogger()

# Funções de conveniência
def get_logger(module_name: str = "main") -> logging.Logger:
    """Função de conveniência para obter um logger"""
    return app_logger.get_logger(module_name)

def log_operation_start(operation: str, **kwargs) -> None:
    """Função de conveniência para log de início de operação"""
    app_logger.log_operation_start(operation, **kwargs)

def log_operation_success(operation: str, **kwargs) -> None:
    """Função de conveniência para log de sucesso"""
    app_logger.log_operation_success(operation, **kwargs)

def log_operation_error(operation: str, error: Exception, **kwargs) -> None:
    """Função de conveniência para log de erro"""
    app_logger.log_operation_error(operation, error, **kwargs)

def log_file_processing(file_name: str, file_size: int, file_type: str, **kwargs) -> None:
    """Função de conveniência para log de processamento de arquivo"""
    app_logger.log_file_processing(file_name, file_size, file_type, **kwargs)

def log_api_request(endpoint: str, method: str, **kwargs) -> None:
    """Função de conveniência para log de requisição API"""
    app_logger.log_api_request(endpoint, method, **kwargs)

def log_api_response(endpoint: str, method: str, status_code: int, execution_time: float, **kwargs) -> None:
    """Função de conveniência para log de resposta API"""
    app_logger.log_api_response(endpoint, method, status_code, execution_time, **kwargs) 