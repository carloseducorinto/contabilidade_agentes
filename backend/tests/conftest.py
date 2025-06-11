"""
Configuração do pytest para o projeto
"""
import pytest
import asyncio
import sys
import os
from pathlib import Path

# Adiciona o diretório app ao path para imports
sys.path.insert(0, str(Path(__file__).parent / "app"))

# Configuração para testes assíncronos
@pytest.fixture(scope="session")
def event_loop():
    """Cria um event loop para toda a sessão de testes"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Configuração de ambiente para testes
@pytest.fixture(autouse=True)
def setup_test_env():
    """Configura variáveis de ambiente para testes"""
    os.environ["ENVIRONMENT"] = "test"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["CACHE_TTL"] = "60"
    os.environ["MAX_CONCURRENT_PROCESSING"] = "2"
    
    # Mock da chave OpenAI para testes
    if "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = "test-key-mock"
    
    yield
    
    # Cleanup após os testes
    test_vars = ["ENVIRONMENT", "LOG_LEVEL", "CACHE_TTL", "MAX_CONCURRENT_PROCESSING"]
    for var in test_vars:
        if var in os.environ:
            del os.environ[var]

