#!/bin/bash

echo "🧪 Executando testes e verificações de qualidade..."
echo

# Muda para o diretório do script
cd "$(dirname "$0")"

echo "📦 Instalando dependências de teste..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Erro ao instalar dependências"
    exit 1
fi

echo
echo "🔍 Executando verificações de qualidade..."
python3 run_quality_checks.py

if [ $? -eq 0 ]; then
    echo
    echo "🎉 Todas as verificações passaram!"
else
    echo
    echo "⚠️ Algumas verificações falharam. Verifique os logs acima."
fi

echo
echo "📊 Relatório de cobertura HTML gerado em: htmlcov/index.html"
echo

