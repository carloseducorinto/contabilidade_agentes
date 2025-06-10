#!/bin/bash

echo "🚀 Iniciando o backend da aplicação..."
echo "📍 Diretório: $(pwd)"
echo "🌐 URL: http://localhost:8000"
echo ""

cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

