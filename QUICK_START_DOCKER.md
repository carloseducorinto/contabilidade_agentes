# 🚀 Início Rápido com Docker

## Sistema de Contabilidade com Agentes + Fallback LLM

### 📋 Pré-requisitos
- Docker Desktop instalado e rodando
- Chave da API OpenAI (para funcionalidade completa)

### ⚡ Execução em 3 Passos

#### 1. Configure a API Key
```bash
# Copie o arquivo de exemplo
cp env.example .env

# Edite e configure sua OPENAI_API_KEY
nano .env  # ou notepad .env no Windows
```

#### 2. Execute o Sistema
**Linux/Mac:**
```bash
./start_docker.sh
```

**Windows:**
```batch
start_docker.bat
```

#### 3. Acesse a Aplicação
- 🌐 **Frontend**: http://localhost:8501
- 🔧 **API**: http://localhost:8000
- 📚 **Docs**: http://localhost:8000/docs

### 🛑 Para Parar
**Linux/Mac:**
```bash
./stop_docker.sh
```

**Windows:**
```batch
stop_docker.bat
```

### 🎯 Funcionalidades Testadas
✅ **Processamento XML**: Nativo  
✅ **Processamento PDF**: OCR + Fallback LLM inteligente  
✅ **Processamento Imagem**: LLM Vision direto  
✅ **Interface Web**: Upload e visualização completa  
✅ **Monitoramento**: Prometheus + Grafana (opcional)  

### 📊 Sistema de Fallback Inteligente
- **OCR Rápido**: Primeira tentativa de extração
- **Detecção Automática**: Identifica quando dados estão incompletos
- **LLM Acionada**: Automaticamente quando >30% dos campos críticos faltam
- **Mesclagem Inteligente**: Combina melhor resultado de OCR + LLM

### 🔍 Documentos de Teste
Coloque seus documentos na pasta `data/` e teste:
- `exemplo_nfe.xml` - XML funcional
- `exemplo_nfe.pdf` - PDF com fallback LLM
- Imagens JPG/PNG - Processamento direto via LLM

---
**💡 Para guia completo**: Consulte `DOCKER_GUIDE.md` 