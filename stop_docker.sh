#!/bin/bash

# =================================================================
# SCRIPT DE PARADA - SISTEMA DE CONTABILIDADE COM AGENTES
# =================================================================

echo "🛑 Parando Sistema de Contabilidade com Agentes"
echo "==============================================="

# Verificar se Docker Compose está disponível
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ Docker Compose não encontrado."
    exit 1
fi

echo "🔄 Parando todos os containers..."
docker-compose --profile monitoring down

echo "📊 Verificando se todos os containers foram parados..."
CONTAINERS=$(docker-compose ps -q)

if [ -z "$CONTAINERS" ]; then
    echo "✅ Todos os containers foram parados com sucesso"
else
    echo "⚠️  Alguns containers ainda estão rodando:"
    docker-compose ps
fi

echo ""
echo "🧹 Deseja remover volumes de dados? (dados persistentes serão perdidos)"
read -p "Remover volumes? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Removendo volumes..."
    docker-compose down -v
    echo "✅ Volumes removidos"
else
    echo "💾 Volumes preservados"
fi

echo ""
echo "🧹 Deseja limpar imagens Docker não utilizadas?"
read -p "Limpar imagens? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Removendo imagens não utilizadas..."
    docker image prune -f
    echo "✅ Imagens limpas"
fi

echo ""
echo "✅ Sistema parado com sucesso!"
echo ""
echo "📋 Para reiniciar: ./start_docker.sh"
echo "📚 Consulte DOCKER_GUIDE.md para mais informações" 