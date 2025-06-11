# 🐳 Guia de Execução com Docker

## Sistema de Contabilidade com Agentes - Execução Containerizada

Este guia mostra como executar toda a solução usando Docker, incluindo o sistema de fallback LLM implementado.

---

## 📋 Pré-requisitos

### 1. Software Necessário
- **Docker** (versão 20.0+)
- **Docker Compose** (versão 2.0+)
- **Git** (para clonar o repositório)

### 2. Verificar Instalação
```bash
docker --version
docker-compose --version
```

---

## 🚀 Execução Rápida

### 1. Configurar Variáveis de Ambiente
```bash
# Copie o arquivo de exemplo
cp env.example .env

# Edite as variáveis (OBRIGATÓRIO configurar OPENAI_API_KEY)
nano .env
```

**⚠️ IMPORTANTE:** Configure pelo menos a `OPENAI_API_KEY` para o sistema funcionar completamente.

### 2. Executar com Docker Compose
```bash
# Construir e iniciar todos os serviços
docker-compose up --build -d

# Verificar status dos containers
docker-compose ps

# Acompanhar logs
docker-compose logs -f
```

### 3. Acessar a Aplicação
- **Frontend (Streamlit)**: http://localhost:8501
- **Backend (FastAPI)**: http://localhost:8000
- **Documentação API**: http://localhost:8000/docs

---

## 🔧 Configurações Avançadas

### Perfis Docker Compose

#### Apenas Aplicação Principal
```bash
docker-compose up --build -d
```

#### Com Monitoramento (Prometheus + Grafana)
```bash
docker-compose --profile monitoring up --build -d
```

Acesso ao monitoramento:
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)

---

## 📁 Estrutura dos Volumes

```
contabilidade_agentes/
├── data/                    # Documentos de exemplo (read-only)
├── backend_logs/           # Logs do backend (persistente)
├── prometheus_data/        # Dados do Prometheus (persistente)
└── grafana_data/          # Configurações do Grafana (persistente)
```

---

## ⚙️ Variáveis de Ambiente Principais

### Backend
| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `OPENAI_API_KEY` | Chave da API OpenAI | **OBRIGATÓRIA** |
| `ENVIRONMENT` | Ambiente de execução | `production` |
| `LOG_LEVEL` | Nível de log | `INFO` |
| `CORS_ORIGINS` | Origens CORS permitidas | `http://localhost:8501` |

### Frontend
| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `BACKEND_URL` | URL do backend | `http://backend:8000` |
| `STREAMLIT_SERVER_HEADLESS` | Modo headless | `true` |

---

## 🔍 Comandos Úteis

### Gerenciamento de Containers
```bash
# Parar todos os serviços
docker-compose down

# Parar e remover volumes
docker-compose down -v

# Reconstruir apenas um serviço
docker-compose build backend
docker-compose up -d backend

# Reiniciar um serviço
docker-compose restart frontend
```

### Logs e Debug
```bash
# Logs de um serviço específico
docker-compose logs backend
docker-compose logs frontend

# Logs em tempo real
docker-compose logs -f backend

# Executar comando dentro do container
docker-compose exec backend bash
docker-compose exec frontend bash
```

### Manutenção
```bash
# Remover containers parados
docker container prune

# Remover imagens não utilizadas
docker image prune

# Remover volumes não utilizados
docker volume prune

# Limpeza completa
docker system prune -a
```

---

## 🏥 Health Checks

Os containers incluem health checks automáticos:

### Backend
- **Endpoint**: `http://localhost:8000/health`
- **Intervalo**: 30s
- **Timeout**: 10s

### Frontend
- **Endpoint**: `http://localhost:8501/_stcore/health`
- **Intervalo**: 30s
- **Timeout**: 10s

### Verificar Status
```bash
docker-compose ps
```

---

## 📊 Monitoramento (Opcional)

### Prometheus
- **URL**: http://localhost:9090
- **Métricas**: Coleta automática do backend
- **Configuração**: `monitoring/prometheus.yml`

### Grafana
- **URL**: http://localhost:3000
- **Login**: admin / admin123
- **Dashboards**: Pré-configurados em `monitoring/grafana/`

---

## 🐛 Troubleshooting

### Container não inicia
```bash
# Verificar logs de erro
docker-compose logs backend

# Verificar portas em uso
netstat -tulpn | grep :8000
netstat -tulpn | grep :8501
```

### Erro de API Key
```bash
# Verificar se a variável está definida
docker-compose exec backend env | grep OPENAI_API_KEY

# Recriar container com nova configuração
docker-compose up -d --force-recreate backend
```

### Problemas de OCR
```bash
# Verificar se Tesseract está instalado
docker-compose exec backend tesseract --version

# Verificar idioma português
docker-compose exec backend tesseract --list-langs
```

### Performance
```bash
# Verificar recursos utilizados
docker stats

# Ajustar limites no docker-compose.yml
```

---

## 🔄 Processo de Update

### Atualizar Código
```bash
# Parar serviços
docker-compose down

# Atualizar código (git pull, etc.)
git pull origin main

# Reconstruir e iniciar
docker-compose up --build -d
```

### Backup de Dados
```bash
# Backup dos volumes
docker run --rm -v contabilidade_agentes_backend_logs:/data -v $(pwd):/backup alpine tar czf /backup/logs_backup.tar.gz -C /data .

# Backup do Grafana
docker run --rm -v contabilidade_agentes_grafana_data:/data -v $(pwd):/backup alpine tar czf /backup/grafana_backup.tar.gz -C /data .
```

---

## 🚀 Funcionalidades Incluídas

✅ **Processamento de Documentos**
- XML (NF-e nativa)
- PDF (OCR + Fallback LLM inteligente)
- Imagens (LLM Vision)

✅ **Sistema de Fallback Inteligente**
- OCR rápido como primeira tentativa
- LLM acionada automaticamente se OCR falha
- Mesclagem inteligente de dados

✅ **Interface Web Completa**
- Upload de documentos
- Visualização de resultados
- Análise de impostos
- Gráficos interativos

✅ **Monitoramento e Logs**
- Health checks automáticos
- Métricas Prometheus
- Dashboards Grafana
- Logs estruturados

✅ **Segurança**
- Containers com usuários não-root
- Variáveis de ambiente isoladas
- Rede Docker isolada
- CORS configurável

---

## 🎯 Próximos Passos

1. **Configure sua API Key** no arquivo `.env`
2. **Execute** `docker-compose up --build -d`
3. **Acesse** http://localhost:8501
4. **Teste** com os documentos em `/data/`
5. **Monitore** via http://localhost:3000 (se usando `--profile monitoring`)

---

## 💡 Dicas de Produção

- Use um reverse proxy (Nginx) na frente
- Configure SSL/TLS certificates
- Use Docker Swarm ou Kubernetes para escala
- Configure backup automático dos volumes
- Monitore uso de recursos com Grafana

**Para suporte, consulte os logs ou abra uma issue no repositório.** 