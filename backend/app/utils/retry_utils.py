"""
Utilitários para retry com exponential backoff
"""
import asyncio
import logging
import time
import random
from typing import Callable, Any, Optional, Type, Union, List
from functools import wraps
from ..exceptions import ExternalAPIError
from ..config import get_settings

settings = get_settings()
logger = logging.getLogger("RetryUtils")


class RetryConfig:
    """Configuração para retry com exponential backoff"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[List[Type[Exception]]] = None
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or [
            ExternalAPIError,
            ConnectionError,
            TimeoutError
        ]


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calcula o delay para uma tentativa específica"""
    delay = config.base_delay * (config.exponential_base ** (attempt - 1))
    delay = min(delay, config.max_delay)
    
    if config.jitter:
        # Adiciona jitter para evitar thundering herd
        delay = delay * (0.5 + random.random() * 0.5)
    
    return delay


def retry_sync(config: RetryConfig = None):
    """
    Decorator para retry síncrono com exponential backoff
    
    Args:
        config: Configuração de retry
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Verifica se a exceção é retryable
                    if not any(isinstance(e, exc_type) for exc_type in config.retryable_exceptions):
                        logger.warning(f"Exceção não retryable: {type(e).__name__}: {str(e)}")
                        raise e
                    
                    if attempt == config.max_attempts:
                        logger.error(f"Todas as {config.max_attempts} tentativas falharam. Última exceção: {str(e)}")
                        raise e
                    
                    delay = calculate_delay(attempt, config)
                    logger.warning(
                        f"Tentativa {attempt}/{config.max_attempts} falhou: {str(e)}. "
                        f"Tentando novamente em {delay:.2f}s"
                    )
                    time.sleep(delay)
            
            # Nunca deveria chegar aqui, mas por segurança
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def retry_async(config: RetryConfig = None):
    """
    Decorator para retry assíncrono com exponential backoff
    
    Args:
        config: Configuração de retry
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Verifica se a exceção é retryable
                    if not any(isinstance(e, exc_type) for exc_type in config.retryable_exceptions):
                        logger.warning(f"Exceção não retryable: {type(e).__name__}: {str(e)}")
                        raise e
                    
                    if attempt == config.max_attempts:
                        logger.error(f"Todas as {config.max_attempts} tentativas falharam. Última exceção: {str(e)}")
                        raise e
                    
                    delay = calculate_delay(attempt, config)
                    logger.warning(
                        f"Tentativa {attempt}/{config.max_attempts} falhou: {str(e)}. "
                        f"Tentando novamente em {delay:.2f}s"
                    )
                    await asyncio.sleep(delay)
            
            # Nunca deveria chegar aqui, mas por segurança
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


# Configurações pré-definidas para diferentes cenários
OPENAI_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True,
    retryable_exceptions=[ExternalAPIError, ConnectionError, TimeoutError]
)

NETWORK_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    base_delay=0.5,
    max_delay=10.0,
    exponential_base=1.5,
    jitter=True,
    retryable_exceptions=[ConnectionError, TimeoutError]
)

FILE_OPERATION_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=0.1,
    max_delay=1.0,
    exponential_base=2.0,
    jitter=False,
    retryable_exceptions=[OSError, IOError]
)

