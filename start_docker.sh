#!/bin/bash

# =================================================================
# SCRIPT DE INICIALIZAÇÃO - SISTEMA DE CONTABILIDADE COM AGENTES
# =================================================================

set -e  # Parar em caso de erro

echo "🐳 Iniciando Sistema de Contabilidade com Agentes via Docker"
echo "=============================================================="

# Verificar se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker não está rodando. Por favor, inicie o Docker primeiro."
    exit 1
fi

# Verificar se Docker Compose está disponível
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ Docker Compose não encontrado. Por favor, instale o Docker Compose."
    exit 1
fi

# Verificar se arquivo .env existe
if [ ! -f .env ]; then
    echo "⚠️  Arquivo .env não encontrado. Criando a partir do exemplo..."
    if [ -f env.example ]; then
        cp env.example .env
        echo "✅ Arquivo .env criado. EDITE o arquivo .env e configure sua OPENAI_API_KEY!"
        echo "📝 Use: nano .env ou code .env"
        echo ""
        read -p "Pressione Enter após configurar o arquivo .env..."
    else
        echo "❌ Arquivo env.example não encontrado."
        exit 1
    fi
fi

# Verificar se OPENAI_API_KEY está configurada
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "⚠️  OPENAI_API_KEY não parece estar configurada no arquivo .env"
    echo "🔑 Configure sua API Key da OpenAI para usar o sistema completo."
    echo ""
    read -p "Continuar mesmo assim? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Execução cancelada. Configure a API Key e tente novamente."
        exit 1
    fi
fi

echo "🔧 Verificando dependências..."

# Verificar se há containers antigos rodando
if docker-compose ps | grep -q "Up"; then
    echo "🔄 Parando containers existentes..."
    docker-compose down
fi

echo "📦 Construindo e iniciando containers..."

# Perguntar sobre monitoramento
echo ""
read -p "Incluir monitoramento (Prometheus + Grafana)? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Iniciando com monitoramento..."
    docker-compose --profile monitoring up --build -d
    MONITORING=true
else
    echo "🚀 Iniciando aplicação principal..."
    docker-compose up --build -d
    MONITORING=false
fi

echo ""
echo "⏳ Aguardando containers inicializarem..."
sleep 10

# Verificar status dos containers
echo "📊 Status dos containers:"
docker-compose ps

echo ""
echo "🏥 Verificando health checks..."
sleep 5

# Verificar se backend está healthy
if docker-compose exec -T backend curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend está funcionando"
else
    echo "⚠️  Backend pode não estar totalmente pronto ainda"
fi

# Verificar se frontend está acessível
if curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    echo "✅ Frontend está funcionando"
else
    echo "⚠️  Frontend pode não estar totalmente pronto ainda"
fi

echo ""
echo "🎉 Sistema iniciado com sucesso!"
echo "=============================================================="
echo "🌐 Acessos:"
echo "   Frontend (Streamlit): http://localhost:8501"
echo "   Backend (FastAPI):    http://localhost:8000"
echo "   API Docs:             http://localhost:8000/docs"

if [ "$MONITORING" = true ]; then
    echo "   Prometheus:           http://localhost:9090"
    echo "   Grafana:              http://localhost:3000 (admin/admin123)"
fi

echo ""
echo "📋 Comandos úteis:"
echo "   Ver logs:             docker-compose logs -f"
echo "   Parar sistema:        docker-compose down"
echo "   Reiniciar backend:    docker-compose restart backend"
echo "   Status containers:    docker-compose ps"
echo ""
echo "📚 Consulte DOCKER_GUIDE.md para mais informações."
echo ""
echo "✨ Pronto para usar! Acesse http://localhost:8501"

