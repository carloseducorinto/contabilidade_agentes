# Sistema de Logging - Contabilidade com Agentes de IA

## Visão Geral

O sistema implementa um sistema de logging abrangente e estruturado em JSON para monitoramento completo da aplicação, incluindo backend (FastAPI) e frontend (Streamlit).

## Características Principais

### ✅ **Logging Estruturado em JSON**
- Todos os logs são formatados em JSON para facilitar análise e parsing
- Campos padronizados: timestamp, level, logger, message, module, function, line
- Campos extras contextuais: request_id, operation, execution_time, file_info, etc.

### ✅ **Logging Centralizado**
- Configuração centralizada em `backend/app/logging_config.py`
- Logger global acessível em toda a aplicação
- Funções de conveniência para operações comuns

### ✅ **Middleware Automático**
- Logging automático de todas as requisições HTTP
- Request ID único para rastreamento
- Tempo de execução de cada endpoint
- Headers de resposta com informações de debug

### ✅ **Logging por Componente**
- **Backend API**: Logs de requisições, respostas, processamento
- **Document Agent**: Logs detalhados de processamento de documentos
- **Frontend**: Logs de ações do usuário e interações

## Estrutura de Arquivos

```
logs/
├── contabilidade_agentes.log    # Logs do backend
└── frontend.log                 # Logs do frontend

backend/app/
├── logging_config.py           # Configuração centralizada
├── middleware.py               # Middleware de logging
└── main.py                     # Endpoints com logging

frontend/
└── app.py                      # Frontend com logging
```

## Tipos de Logs

### 1. **Logs de Operação**
```json
{
  "timestamp": "2025-06-09T19:30:45.123456",
  "level": "INFO",
  "logger": "contabilidade_agentes.main",
  "message": "Iniciando operação: document_processing",
  "operation": "document_processing",
  "request_id": "uuid-1234-5678",
  "file_name": "exemplo.pdf",
  "file_size": 2048,
  "file_type": "pdf"
}
```

### 2. **Logs de API**
```json
{
  "timestamp": "2025-06-09T19:30:45.123456",
  "level": "INFO",
  "logger": "contabilidade_agentes.middleware",
  "message": "API Request: POST /process-document",
  "operation": "api_request",
  "request_id": "uuid-1234-5678",
  "endpoint": "/process-document",
  "method": "POST",
  "user_agent": "streamlit/1.0"
}
```

### 3. **Logs de Processamento**
```json
{
  "timestamp": "2025-06-09T19:30:47.456789",
  "level": "INFO",
  "logger": "contabilidade_agentes.DocumentIngestionAgent",
  "message": "Operação concluída com sucesso: xml_nfe_processing",
  "operation": "xml_nfe_processing",
  "execution_time": 2.34,
  "processing_result": "success",
  "agent": "DocumentIngestionAgent",
  "document_type": "nfe",
  "valor_total": 1500.00,
  "items_count": 3
}
```

### 4. **Logs de Erro**
```json
{
  "timestamp": "2025-06-09T19:30:48.789012",
  "level": "ERROR",
  "logger": "contabilidade_agentes.DocumentIngestionAgent",
  "message": "Erro na operação: pdf_nfe_processing - Unable to get page count",
  "operation": "pdf_nfe_processing",
  "execution_time": 1.23,
  "processing_result": "error",
  "exception": {
    "type": "ValueError",
    "message": "Unable to get page count. Is poppler installed and in PATH?",
    "traceback": "..."
  }
}
```

### 5. **Logs do Frontend**
```json
{
  "timestamp": "2025-06-09T19:30:45.123456",
  "component": "frontend",
  "level": "INFO",
  "message": "Ação do usuário: document_upload_start",
  "action": "document_upload_start",
  "session_id": "uuid-session-1234",
  "file_name": "nfe_exemplo.xml",
  "file_type": "application/xml",
  "file_size": 4096
}
```

## Funcionalidades Implementadas

### **Backend (FastAPI)**

#### Middleware de Logging
- **LoggingMiddleware**: Log automático de requisições/respostas
- **ErrorHandlingMiddleware**: Captura e log de erros não tratados
- Request ID único para rastreamento
- Headers de resposta com informações de debug

#### Endpoints com Logging
- `GET /`: Status da aplicação
- `GET /health`: Verificação de saúde
- `POST /process-document`: Processamento de documentos
- `GET /supported-formats`: Formatos suportados
- `GET /logs/recent`: Visualização de logs recentes

#### Document Agent Logging
- Log de início/fim de processamento
- Logs específicos por tipo (XML, PDF, Imagem)
- Métricas de performance
- Detalhes do resultado (valor total, itens, etc.)

### **Frontend (Streamlit)**

#### Logging de Ações do Usuário
- Carregamento de páginas
- Upload de arquivos
- Verificação de status da API
- Resultados de processamento
- Erros de conexão

#### Session Tracking
- ID de sessão único por usuário
- Rastreamento de ações por sessão
- Logs estruturados com contexto

## Configuração

### **Variáveis de Ambiente**
```bash
# Nível de logging (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Caminho personalizado para logs
LOG_FILE_PATH=logs/custom.log
```

### **Configuração Programática**
```python
from backend.app.logging_config import AppLogger

# Logger customizado
logger = AppLogger(
    name="meu_modulo",
    level=logging.DEBUG,
    log_to_file=True,
    log_file_path="logs/custom.log"
)
```

## Monitoramento

### **Endpoint de Logs**
```bash
# Últimos 100 logs
GET /logs/recent

# Últimos 50 logs
GET /logs/recent?limit=50
```

### **Análise de Logs**
```bash
# Filtrar por nível de erro
grep '"level":"ERROR"' logs/contabilidade_agentes.log

# Filtrar por operação específica
grep '"operation":"document_processing"' logs/contabilidade_agentes.log

# Análise de performance
grep '"execution_time"' logs/contabilidade_agentes.log | jq '.execution_time'
```

## Métricas Disponíveis

### **Performance**
- Tempo de execução por operação
- Tempo de resposta da API
- Tempo de processamento por tipo de documento

### **Uso**
- Número de documentos processados
- Tipos de arquivo mais utilizados
- Taxa de sucesso/erro

### **Erros**
- Tipos de erro mais comuns
- Operações com mais falhas
- Rastreamento de problemas por request_id

## Boas Práticas

### **Para Desenvolvedores**
1. Use as funções de conveniência: `log_operation_start()`, `log_operation_success()`, `log_operation_error()`
2. Inclua contexto relevante nos logs extras
3. Use request_id para rastreamento de requisições
4. Log tanto sucessos quanto falhas

### **Para Operações**
1. Monitore logs de ERROR regularmente
2. Analise métricas de performance
3. Use request_id para debug de problemas específicos
4. Configure alertas baseados em padrões de log

## Exemplos de Uso

### **Logging Básico**
```python
from backend.app.logging_config import log_operation_start, log_operation_success, log_operation_error

# Início de operação
log_operation_start("minha_operacao", user_id="123", extra_info="valor")

try:
    # Sua lógica aqui
    result = processar_algo()
    
    # Sucesso
    log_operation_success("minha_operacao", execution_time=1.23, result_count=5)
    
except Exception as e:
    # Erro
    log_operation_error("minha_operacao", e, execution_time=0.5)
```

### **Logging com Contexto**
```python
from backend.app.logging_config import get_logger

logger = get_logger("meu_modulo")

logger.info("Processando arquivo", extra={
    'operation': 'file_processing',
    'file_name': 'documento.pdf',
    'file_size': 2048,
    'user_id': '123'
})
```

## Troubleshooting

### **Logs não aparecem**
1. Verifique se o diretório `logs/` existe
2. Verifique permissões de escrita
3. Confirme configuração do nível de log

### **Performance**
1. Logs são assíncronos por padrão
2. Rotação automática de logs (implementar se necessário)
3. Considere usar log aggregation para produção

### **Análise**
1. Use ferramentas como `jq` para análise JSON
2. Considere ELK Stack para produção
3. Implemente dashboards para métricas

---

**Nota**: Este sistema de logging fornece visibilidade completa da aplicação, facilitando debug, monitoramento e análise de performance. 