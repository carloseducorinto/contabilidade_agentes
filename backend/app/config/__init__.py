"""
Configuração do módulo config
"""
from .settings import settings, get_settings, is_production, get_cors_config

__all__ = ["settings", "get_settings", "is_production", "get_cors_config"]

