# 🐳 Guia de Deployment com Docker

## 📋 Visão Geral

Este guia explica como implantar o Sistema de Contabilidade com Agentes de IA usando Docker e Docker Compose, facilitando o deployment em qualquer ambiente.

## 🛠️ Pré-requisitos

### Para Desenvolvimento Local
- **Docker Desktop** (Windows/Mac) ou **Docker Engine** (Linux)
- **Docker Compose** (geralmente incluído no Docker Desktop)
- **Chave da API OpenAI** (para processamento de imagem)

### Para Produção
- **Servidor VPS** ou **Cloud Provider** (AWS, Google Cloud, Azure, DigitalOcean, etc.)
- **Docker** e **Docker Compose** instalados no servidor
- **Domínio** (opcional, mas recomendado)
- **Certificado SSL** (para HTTPS em produção)

## 🚀 Deployment Local

### 1. Preparação
```bash
# Extrair o projeto
tar -xzf contabilidade_agentes_v3.0_final.tar.gz
cd contabilidade_agentes

# Configurar variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env e configure sua OPENAI_API_KEY
```

### 2. Inicialização Rápida

#### Windows
```cmd
start_docker.bat
```

#### Linux/Mac
```bash
./start_docker.sh
```

### 3. Inicialização Manual
```bash
# Construir imagens
docker-compose build

# Iniciar serviços
docker-compose up -d

# Verificar status
docker-compose ps
```

### 4. Acesso
- **Frontend**: http://localhost:8501
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🌐 Deployment em Produção

### 1. Preparação do Servidor

#### Instalar Docker (Ubuntu/Debian)
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Configuração para Produção

#### Arquivo .env para Produção
```bash
# Configurações de produção
OPENAI_API_KEY=sua_chave_real_aqui
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_HOST=0.0.0.0
FRONTEND_PORT=8501
LOG_LEVEL=INFO

# Configurações de segurança
CORS_ORIGINS=https://seudominio.com
SECRET_KEY=sua_chave_secreta_muito_forte_aqui
```

#### Docker Compose para Produção
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: contabilidade_backend_prod
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LOG_LEVEL=${LOG_LEVEL}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./frontend
    container_name: contabilidade_frontend_prod
    ports:
      - "8501:8501"
    environment:
      - BACKEND_URL=http://backend:8000
    depends_on:
      - backend
    restart: always

  nginx:
    image: nginx:alpine
    container_name: contabilidade_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: always
```

### 3. Configuração do Nginx (Opcional)

#### nginx.conf
```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:8501;
    }

    server {
        listen 80;
        server_name seudominio.com;

        location /api/ {
            proxy_pass http://backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location / {
            proxy_pass http://frontend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### 4. Deploy em Produção
```bash
# Fazer upload dos arquivos para o servidor
scp -r contabilidade_agentes/ usuario@servidor:/home/usuario/

# Conectar ao servidor
ssh usuario@servidor

# Navegar para o diretório
cd contabilidade_agentes

# Configurar variáveis de ambiente
cp .env.example .env
nano .env  # Configurar OPENAI_API_KEY e outras variáveis

# Iniciar em produção
docker-compose -f docker-compose.prod.yml up -d
```

## ☁️ Deployment em Cloud Providers

### AWS (Amazon Web Services)

#### EC2 + Docker
1. **Criar instância EC2** (Ubuntu 20.04 LTS)
2. **Configurar Security Groups** (portas 80, 443, 22)
3. **Instalar Docker** na instância
4. **Fazer upload do projeto** via SCP ou Git
5. **Executar docker-compose**

#### ECS (Elastic Container Service)
1. **Criar repositório ECR** para as imagens
2. **Fazer push das imagens** para o ECR
3. **Criar task definition** no ECS
4. **Configurar service** e **load balancer**

### Google Cloud Platform

#### Compute Engine + Docker
1. **Criar VM** no Compute Engine
2. **Configurar firewall** (portas 80, 443)
3. **Instalar Docker** na VM
4. **Deploy via docker-compose**

#### Cloud Run
1. **Fazer push das imagens** para Container Registry
2. **Deploy cada serviço** no Cloud Run
3. **Configurar load balancer** para roteamento

### Azure

#### Virtual Machine + Docker
1. **Criar VM** no Azure
2. **Configurar Network Security Group**
3. **Instalar Docker** na VM
4. **Deploy via docker-compose**

#### Container Instances
1. **Fazer push das imagens** para Container Registry
2. **Criar container groups**
3. **Configurar networking**

### DigitalOcean

#### Droplet + Docker
1. **Criar Droplet** (Ubuntu)
2. **Instalar Docker** (pode usar imagem pré-configurada)
3. **Deploy via docker-compose**

#### App Platform
1. **Conectar repositório Git**
2. **Configurar build specs**
3. **Deploy automático**

## 🔧 Comandos Úteis

### Gerenciamento de Containers
```bash
# Ver status dos serviços
docker-compose ps

# Ver logs
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f backend

# Parar serviços
docker-compose down

# Reiniciar serviços
docker-compose restart

# Atualizar serviços
docker-compose pull
docker-compose up -d
```

### Manutenção
```bash
# Limpar containers parados
docker container prune

# Limpar imagens não utilizadas
docker image prune

# Limpar volumes não utilizados
docker volume prune

# Backup de dados
docker-compose exec backend tar -czf /app/backup.tar.gz /app/data
```

## 🔒 Segurança

### Configurações Recomendadas
1. **Usar HTTPS** em produção
2. **Configurar firewall** adequadamente
3. **Manter Docker atualizado**
4. **Usar secrets** para variáveis sensíveis
5. **Implementar rate limiting**
6. **Configurar logs de auditoria**

### Variáveis de Ambiente Sensíveis
```bash
# Use Docker secrets em produção
echo "sua_chave_openai" | docker secret create openai_api_key -
```

## 📊 Monitoramento

### Health Checks
Os containers incluem health checks automáticos:
- **Backend**: `GET /health`
- **Frontend**: `GET /_stcore/health`

### Logs
```bash
# Logs estruturados em JSON
docker-compose logs backend | jq .

# Monitoramento em tempo real
docker-compose logs -f --tail=100
```

## 🚨 Troubleshooting

### Problemas Comuns

#### Container não inicia
```bash
# Verificar logs
docker-compose logs nome_do_servico

# Verificar configuração
docker-compose config
```

#### Erro de conexão entre serviços
```bash
# Verificar rede
docker network ls
docker network inspect contabilidade_network
```

#### Problemas de permissão
```bash
# Verificar volumes
docker-compose exec backend ls -la /app/data
```

### Performance
```bash
# Monitorar recursos
docker stats

# Limitar recursos (docker-compose.yml)
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
```

## 📈 Escalabilidade

### Load Balancing
```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
    ports:
      - "8000-8002:8000"
```

### Banco de Dados Externo
Para produção, considere usar banco de dados externo:
- **PostgreSQL** para dados estruturados
- **Redis** para cache
- **MongoDB** para logs

## 🎯 Próximos Passos

1. **Configurar CI/CD** (GitHub Actions, GitLab CI)
2. **Implementar monitoramento** (Prometheus, Grafana)
3. **Configurar backup automático**
4. **Implementar autenticação** (OAuth, JWT)
5. **Adicionar rate limiting**
6. **Configurar CDN** para assets estáticos

---

**Este guia fornece uma base sólida para deployment em qualquer ambiente. Adapte conforme suas necessidades específicas!** 🚀

