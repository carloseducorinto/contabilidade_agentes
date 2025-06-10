#!/bin/bash

echo "🚀 Iniciando Sistema de Contabilidade com Agentes de IA v2.0"
echo "============================================================"

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado. Instale Python 3.11+ primeiro."
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"

# Instalar Tesseract OCR (Linux/Ubuntu)
if command -v apt &> /dev/null; then
    echo "📦 Instalando Tesseract OCR..."
    sudo apt update -qq
    sudo apt install -y tesseract-ocr tesseract-ocr-por poppler-utils
    echo "✅ Tesseract OCR instalado"
fi

# Instalar dependências do backend
echo "📦 Instalando dependências do backend..."
cd backend
pip3 install -q fastapi uvicorn langchain langchain-openai pydantic lxml pytesseract python-multipart pdf2image Pillow

# Instalar dependências do frontend
echo "📦 Instalando dependências do frontend..."
cd ../frontend
pip3 install -q streamlit requests pandas

cd ..

echo "🔧 Configurando ambiente..."

# Tornar scripts executáveis
chmod +x start_backend.sh start_frontend.sh

echo "✅ Instalação concluída!"
echo ""
echo "🚀 Para iniciar o sistema:"
echo "   Backend:  ./start_backend.sh"
echo "   Frontend: ./start_frontend.sh"
echo ""
echo "🌐 URLs:"
echo "   Frontend: http://localhost:8501"
echo "   API:      http://localhost:8000"
echo "   Docs:     http://localhost:8000/docs"
echo ""
echo "📄 Teste com:"
echo "   XML: curl -X POST http://localhost:8000/process-document -F 'file=@data/exemplo_nfe.xml'"
echo "   PDF: curl -X POST http://localhost:8000/process-document -F 'file=@data/exemplo_nfe.pdf'"
echo ""
echo "🎉 Sistema v2.0 com suporte completo a XML e PDF via OCR!"

