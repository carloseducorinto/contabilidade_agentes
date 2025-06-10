"""
Sistema de cache para otimização de performance
"""
import asyncio
import hashlib
import json
import logging
import time
from typing import Any, Optional, Dict, Callable, Union
from functools import wraps
from ..config import get_settings

settings = get_settings()
logger = logging.getLogger("CacheSystem")


class InMemoryCache:
    """Cache em memória simples com TTL"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Recupera um valor do cache"""
        async with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # Verifica se expirou
            if time.time() > entry['expires_at']:
                del self._cache[key]
                return None
            
            entry['last_accessed'] = time.time()
            return entry['value']
    
    async def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Armazena um valor no cache"""
        if ttl is None:
            ttl = settings.cache_ttl
        
        async with self._lock:
            self._cache[key] = {
                'value': value,
                'created_at': time.time(),
                'last_accessed': time.time(),
                'expires_at': time.time() + ttl
            }
    
    async def delete(self, key: str) -> bool:
        """Remove um valor do cache"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self) -> None:
        """Limpa todo o cache"""
        async with self._lock:
            self._cache.clear()
    
    async def cleanup_expired(self) -> int:
        """Remove entradas expiradas e retorna quantas foram removidas"""
        current_time = time.time()
        expired_keys = []
        
        async with self._lock:
            for key, entry in self._cache.items():
                if current_time > entry['expires_at']:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
        
        if expired_keys:
            logger.info(f"Removidas {len(expired_keys)} entradas expiradas do cache")
        
        return len(expired_keys)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        async with self._lock:
            total_entries = len(self._cache)
            current_time = time.time()
            
            expired_count = sum(
                1 for entry in self._cache.values() 
                if current_time > entry['expires_at']
            )
            
            return {
                'total_entries': total_entries,
                'active_entries': total_entries - expired_count,
                'expired_entries': expired_count,
                'memory_usage_estimate': len(str(self._cache))
            }


# Instância global do cache
cache = InMemoryCache()


def generate_cache_key(*args, **kwargs) -> str:
    """Gera uma chave de cache baseada nos argumentos"""
    # Cria um hash dos argumentos
    key_data = {
        'args': args,
        'kwargs': kwargs
    }
    
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def cached(ttl: int = None, key_prefix: str = ""):
    """
    Decorator para cache de funções assíncronas
    
    Args:
        ttl: Tempo de vida em segundos (usa configuração padrão se None)
        key_prefix: Prefixo para a chave do cache
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            if not settings.enable_caching:
                return await func(*args, **kwargs)
            
            # Gera chave do cache
            cache_key = f"{key_prefix}:{func.__name__}:{generate_cache_key(*args, **kwargs)}"
            
            # Tenta recuperar do cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit para {func.__name__}")
                return cached_result
            
            # Executa função e armazena resultado
            logger.debug(f"Cache miss para {func.__name__}")
            result = await func(*args, **kwargs)
            
            # Armazena no cache apenas se o resultado for válido
            if result is not None:
                await cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


async def start_cache_cleanup_task():
    """Inicia tarefa de limpeza periódica do cache"""
    async def cleanup_loop():
        while True:
            try:
                await asyncio.sleep(300)  # 5 minutos
                await cache.cleanup_expired()
            except Exception as e:
                logger.error(f"Erro na limpeza do cache: {str(e)}")
    
    if settings.enable_caching:
        asyncio.create_task(cleanup_loop())
        logger.info("Tarefa de limpeza do cache iniciada")


# Funções utilitárias para cache
async def get_cache_stats() -> Dict[str, Any]:
    """Retorna estatísticas do cache"""
    return await cache.get_stats()


async def clear_cache() -> None:
    """Limpa todo o cache"""
    await cache.clear()
    logger.info("Cache limpo manualmente")


async def invalidate_cache_pattern(pattern: str) -> int:
    """Invalida entradas do cache que correspondem a um padrão"""
    # Implementação simples - em produção, considere usar Redis com pattern matching
    stats = await cache.get_stats()
    await cache.clear()  # Por simplicidade, limpa tudo
    logger.info(f"Cache invalidado para padrão: {pattern}")
    return stats['total_entries']

