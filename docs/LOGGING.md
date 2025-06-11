# 📝 Sistema de Logging e Monitoramento

Este documento detalha o sistema de logging implementado na solução de contabilidade com agentes de IA, com foco em segurança, estrutura e facilidade de integração com ferramentas de monitoramento.

## 📊 Estrutura do Logging

O sistema utiliza a biblioteca `logging` padrão do Python, configurada para gerar logs estruturados em formato JSON. Isso facilita a ingestão e análise por sistemas de gerenciamento de logs centralizados (LMS) como ELK Stack (Elasticsearch, Logstash, Kibana) ou Grafana Loki.

### Formato JSON

Cada linha de log é um objeto JSON contendo informações relevantes sobre o evento. O formato inclui campos como:

- `timestamp`: Data e hora exatas do evento.
- `level`: Nível do log (DEBUG, INFO, WARNING, ERROR, CRITICAL).
- `agent` / `module`: Nome do agente ou módulo que gerou o log.
- `message`: Descrição textual do evento.
- `operation_id`: ID único para rastrear operações de processamento de documentos.
- `file_type`: Tipo do arquivo processado (xml, pdf, image).
- `processing_time`: Tempo levado para processar um documento (em segundos).
- `error`: Detalhes do erro, se aplicável.
- `error_code`: Código customizado do erro, se aplicável.
- `extra`: Campos adicionais específicos do evento.

**Exemplo de Log:**

```json
{
  "timestamp": "2025-06-10 10:30:00,123",
  "level": "INFO",
  "module": "document_service",
  "message": "Iniciando processamento de documento",
  "operation_id": "abc-123",
  "file_type": "xml"
}
```

## 🔒 Segurança e Mascaramento de Dados

A segurança dos dados sensíveis nos logs é uma prioridade. O sistema implementa um mecanismo de mascaramento automático para evitar que informações confidenciais sejam expostas.

### DataMasker

Uma classe `DataMasker` foi criada para identificar e substituir padrões de dados sensíveis por marcadores genéricos (ex: `****`). Os padrões incluem, mas não se limitam a:

- Chaves de API (OpenAI, etc.)
- CNPJs e CPFs
- Endereços de e-mail
- Números de telefone
- Números de cartão de crédito

### SecureJSONFormatter

Um formatter customizado (`SecureJSONFormatter`) é utilizado para garantir que todos os campos do log sejam passados pelo `DataMasker` antes de serem serializados para JSON. Isso assegura que, mesmo que um dado sensível seja acidentalmente incluído em uma mensagem de log, ele será mascarado.

### Permissões de Arquivo

Os arquivos de log são configurados com permissões restritivas (modo `600` em sistemas Unix-like) para que apenas o proprietário do processo tenha acesso de leitura e escrita, protegendo contra acesso não autorizado.

## 🔄 Rotação de Logs

Para evitar que os arquivos de log cresçam indefinidamente e consumam todo o espaço em disco, a rotação de logs está configurada usando `logging.handlers.RotatingFileHandler`.

- **maxBytes**: Define o tamanho máximo de um arquivo de log antes que ele seja rotacionado.
- **backupCount**: Define quantos arquivos de log antigos serão mantidos.

Quando um arquivo de log atinge o tamanho máximo, ele é renomeado (ex: `app.log.1`, `app.log.2`, etc.) e um novo arquivo de log vazio (`app.log`) é criado. Os arquivos mais antigos são removidos após atingir o `backupCount`.

## 📈 Monitoramento com Prometheus

Além dos logs, a aplicação backend expõe métricas no formato Prometheus para monitoramento em tempo real do desempenho e saúde da API.

### Endpoint `/metrics`

Um endpoint `/metrics` está disponível na API (geralmente em `http://localhost:8000/metrics`) que fornece dados em um formato que pode ser coletado por um servidor Prometheus. As métricas incluem:

- `http_requests_total`: Contador do total de requisições HTTP recebidas.
- `http_request_duration_seconds`: Histograma da duração das requisições HTTP.
- `document_processing_total`: Contador do total de documentos processados (por tipo e status - sucesso/falha).
- `document_processing_duration_seconds`: Histograma da duração do processamento de documentos (por tipo).
- `cache_hits_total`: Contador de acertos no cache.
- `cache_misses_total`: Contador de falhas no cache.
- `api_health_status`: Gauge indicando a saúde da API (1 para saudável, 0 para não saudável).

### Integração com Prometheus e Grafana

Você pode configurar um servidor Prometheus para coletar métricas do endpoint `/metrics` da sua aplicação. Em seguida, usar o Grafana para criar dashboards visualizando essas métricas, permitindo monitorar:

- Taxa de requisições e latência.
- Número de documentos processados por tipo e status.
- Taxa de erros no processamento.
- Uso do cache.
- Saúde geral da API.

## ☁️ Integração com Ferramentas de Agregação de Logs

O formato de log JSON estruturado facilita a integração com ferramentas de agregação de logs baseadas em nuvem ou on-premise, como:

- **ELK Stack (Elasticsearch, Logstash, Kibana)**: Logstash pode coletar os arquivos de log, parsear o JSON e enviar para o Elasticsearch para indexação. Kibana é usado para visualização e análise.
- **Grafana Loki**: Loki é um sistema de agregação de logs otimizado para logs estruturados. Promtail (agente de coleta) pode enviar os logs JSON para o Loki, e o Grafana é usado para visualização com o LogQL.
- **Cloud Providers**: AWS CloudWatch Logs, Google Cloud Logging, Azure Monitor Logs, etc., todos suportam ingestão de logs JSON.

Para integrar, configure o agente de coleta da ferramenta escolhida para ler os arquivos de log gerados pela aplicação (`logs/app.log` por padrão) e enviar para o sistema centralizado.

## 🛠️ Configuração do Logging

O sistema de logging é configurado através do arquivo `logging_config.py` e utiliza as configurações definidas em `config/settings.py`. Você pode ajustar o nível de log, tamanho dos arquivos de rotação e número de backups através das variáveis de ambiente ou do arquivo `.env`.

- `LOG_LEVEL`: Define o nível mínimo de log a ser registrado (DEBUG, INFO, WARNING, ERROR, CRITICAL).
- `LOG_FILE_PATH`: Caminho para o arquivo de log.
- `LOG_FILE_MAX_BYTES`: Tamanho máximo do arquivo de log em bytes.
- `LOG_FILE_BACKUP_COUNT`: Número de arquivos de backup a serem mantidos.

## ⚠️ Considerações de Segurança

- **Não desabilite o mascaramento de dados sensíveis em produção.**
- **Monitore o acesso aos arquivos de log**, mesmo com permissões restritivas.
- **Considere criptografar os logs em repouso** se contiverem informações extremamente sensíveis.
- **Configure alertas** no seu sistema de monitoramento para erros críticos e picos de requisições/erros.

Com este sistema de logging e monitoramento, você terá visibilidade completa sobre o funcionamento da sua aplicação, facilitando a depuração, auditoria e garantia de segurança.

