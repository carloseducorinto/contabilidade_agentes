#!/bin/bash

echo "🎨 Iniciando o frontend da aplicação..."
echo "📍 Diretório: $(pwd)"
echo "🌐 URL: http://localhost:8501"
echo ""

cd frontend
streamlit run app.py --server.port 8501 --server.address 0.0.0.0

