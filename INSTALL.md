# 🚀 Guia de Instalação Rápida

## Instalação em Uma Linha

```bash
# Clone e execute
git clone <repo> && cd contabilidade_agentes && ./quick_start.sh
```

## Instalação Manual

### 1. Dependências do Sistema
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# Verificar versão do Python (requer 3.11+)
python3 --version
```

### 2. Dependências do Projeto
```bash
# Backend
cd backend
pip install fastapi uvicorn langchain langchain-openai pydantic lxml pytesseract python-multipart

# Frontend
cd ../frontend
pip install streamlit requests pandas
```

### 3. Executar
```bash
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### 4. Acessar
- **Frontend**: http://localhost:8501
- **API**: http://localhost:8000
- **Docs da API**: http://localhost:8000/docs

## Teste Rápido

```bash
# Teste da API
curl http://localhost:8000/health

# Teste com documento
curl -X POST "http://localhost:8000/process-document" \
     -F "file=@data/exemplo_nfe.xml"
```

## Solução de Problemas

### Erro de Porta em Uso
```bash
# Verificar processos
lsof -i :8000
lsof -i :8501

# Matar processo
kill -9 <PID>
```

### Erro de Dependências
```bash
# Reinstalar dependências
pip3 install --upgrade -r backend/requirements.txt
pip3 install --upgrade streamlit requests
```

### Erro de Permissão
```bash
# Tornar scripts executáveis
chmod +x start_backend.sh start_frontend.sh
```

