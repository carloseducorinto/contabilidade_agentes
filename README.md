# 🧾 Sistema de Contabilidade com Agentes de IA

## 📋 Visão Geral

Este sistema é uma solução multiagente avançada para automatizar o fluxo de trabalho de lançamentos contábeis, focando no processamento inteligente de documentos fiscais brasileiros. Ele suporta a ingestão e extração de dados estruturados de Notas Fiscais Eletrônicas (NF-e) em múltiplos formatos: XML, PDF (via OCR) e Imagem (via LLM Vision).

A arquitetura foi refatorada para ser modular, escalável, segura e de alta performance, com foco em uma excelente experiência do usuário e facilidade de deployment via Docker.

## 🎯 Funcionalidades Implementadas

### ✅ Processamento de Documentos (Backend - FastAPI)
- **XML**: Parse nativo e extração completa de NF-e, garantindo 100% de precisão.
- **PDF (via OCR)**: Extração de dados de PDFs usando Tesseract OCR (com suporte a português brasileiro), incluindo pré-processamento de imagem e regex para alta precisão (~85-95%).
- **Imagem (via LLM Vision)**: Análise e extração de dados de imagens (JPG, PNG, WEBP, GIF) utilizando modelos de linguagem grandes (LLMs) como GPT-4 Vision, ideal para documentos digitalizados ou fotos, com compreensão contextual avançada.
- **Validação de Dados**: Todos os dados extraídos são validados rigorosamente usando modelos Pydantic v2, garantindo integridade e tipagem forte.
- **Performance Otimizada**: Processamento assíncrono (`async/await`), uso de `BackgroundTasks` para operações pesadas e um sistema de cache em memória para resultados de operações custosas.

### ✅ API Backend (FastAPI)
- **Endpoints Robustos**: 
  - `/process-document`: Endpoint principal para upload e processamento de documentos em todos os formatos suportados.
  - `/health`: Verificação de status da aplicação.
  - `/supported-formats`: Lista dinâmica dos formatos de documento suportados.
  - `/metrics`: Exposição de métricas Prometheus para monitoramento (requisições, erros, tempos de processamento).
- **Segurança Avançada**: 
  - **CORS**: Configuração restritiva em produção, permissiva em desenvolvimento.
  - **Mascaramento de Dados Sensíveis**: Chaves de API e informações pessoais são automaticamente mascaradas em logs.
  - **Validação de Entrada**: Sanitização e validação rigorosa de todos os inputs do usuário, incluindo uploads de arquivos.
  - **Rate Limiting**: Proteção contra abuso de API.
- **Tratamento de Erros**: Exceções customizadas e handlers globais que retornam mensagens de erro descritivas e códigos HTTP apropriados.
- **Retry Logic**: Implementação de retry com exponential backoff para chamadas a APIs externas (ex: OpenAI).

### ✅ Interface Frontend (Streamlit)
- **Experiência do Usuário (UX) Aprimorada**: 
  - **Upload Intuitivo**: Interface drag-and-drop que aceita XML, PDF e imagens.
  - **Feedback em Tempo Real**: Barras de progresso detalhadas e mensagens de status durante o processamento.
  - **Mensagens de Erro Inteligentes**: Erros detalhados com sugestões contextuais para resolução de problemas.
  - **Visualização Rica**: Exibição clara e organizada dos dados extraídos, incluindo tabelas interativas e gráficos (impostos, itens).
  - **Histórico de Sessão**: Acompanhamento dos documentos processados na sessão atual.
- **Design Responsivo**: Interface moderna e adaptável a diferentes tamanhos de tela.

### ✅ Qualidade de Código e Testes
- **Testes Automatizados**: Cobertura abrangente com testes unitários e de integração usando `pytest`.
- **Ferramentas de Qualidade**: Integração com `black` (formatação), `flake8` (linting) e `mypy` (verificação de tipos).
- **Cobertura de Código**: Monitoramento com `pytest-cov` para garantir alta cobertura.
- **CI/CD**: Pipeline de Integração Contínua/Entrega Contínua (CI/CD) configurado com GitHub Actions para automação de testes, linting e build de imagens Docker.

### ✅ Deployment e Containerização
- **Docker**: `Dockerfile`s otimizados para o backend e frontend, permitindo empacotamento e isolamento da aplicação.
- **Docker Compose**: Arquivo `docker-compose.yml` para orquestração e inicialização fácil de todos os serviços com um único comando.
- **Scripts de Inicialização**: Scripts simplificados para iniciar a aplicação localmente (com ou sem Docker) em ambientes Linux/Mac e Windows.

## 🏗️ Arquitetura Detalhada

```
contabilidade_agentes/
├── .github/                  # Configurações do GitHub (CI/CD)
│   └── workflows/
│       └── ci-cd.yml         # Pipeline de CI/CD com GitHub Actions
├── backend/                    # API FastAPI
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # Aplicação principal FastAPI (endpoints, middlewares)
│   │   ├── config/           # Gerenciamento de configuração
│   │   │   └── settings.py   # Configurações do ambiente (Pydantic BaseSettings)
│   │   ├── exceptions/       # Classes de exceção customizadas e handlers
│   │   │   ├── custom_exceptions.py
│   │   │   └── handlers.py
│   │   ├── middleware/       # Middlewares de segurança (CORS, Rate Limit, Headers)
│   │   │   └── security.py
│   │   ├── models/           # Modelos Pydantic para API e dados de documentos
│   │   │   ├── api_models.py
│   │   │   └── document_models.py
│   │   ├── processors/       # Lógica de processamento modularizada
│   │   │   ├── xml_processor.py
│   │   │   ├── pdf_processor.py
│   │   │   └── image_processor.py
│   │   ├── services/         # Camada de serviço com lógica de negócio
│   │   │   └── document_service.py
│   │   ├── utils/            # Utilitários (retry, cache, segurança, validação)
│   │   │   ├── retry_utils.py
│   │   │   ├── cache.py
│   │   │   ├── security.py
│   │   │   └── validators.py
│   │   ├── metrics/          # Métricas Prometheus
│   │   │   └── prometheus_metrics.py
│   │   └── logging_config.py # Configuração de logging estruturado e seguro
│   ├── Dockerfile            # Dockerfile para o backend
│   ├── requirements.txt      # Dependências do backend
│   ├── pyproject.toml        # Configurações de ferramentas (pytest, black, mypy)
│   ├── run_quality_checks.py # Script para rodar verificações de qualidade
│   ├── run_tests.sh          # Script Linux/Mac para rodar testes
│   ├── run_tests.bat         # Script Windows para rodar testes
│   └── tests/                # Testes automatizados
│       ├── unit/             # Testes unitários
│       ├── integration/      # Testes de integração
│       └── fixtures/         # Fixtures de teste (dados, mocks)
├── frontend/                  # Interface Streamlit
│   ├── .streamlit/           # Configuração do Streamlit
│   │   └── config.toml
│   ├── app.py                # Aplicação principal Streamlit
│   ├── Dockerfile            # Dockerfile para o frontend
│   └── requirements.txt      # Dependências do frontend
├── data/                     # Dados de exemplo e testes
│   ├── exemplo_nfe.xml       # NF-e XML de exemplo
│   ├── exemplo_nfe.pdf       # NF-e PDF de exemplo
│   └── exemplo_nfe.png       # NF-e Imagem de exemplo
├── docs/                     # Documentação
│   ├── architecture.md       # Documentação da arquitetura
│   └── LOGGING.md            # Detalhes do sistema de logging
├── .env.example              # Exemplo de arquivo de variáveis de ambiente
├── docker-compose.yml        # Orquestração Docker Compose
├── .dockerignore             # Arquivos/pastas a ignorar no build Docker
├── start_backend.sh          # Script Linux/Mac para iniciar backend (sem Docker)
├── start_frontend.sh         # Script Linux/Mac para iniciar frontend (sem Docker)
├── quick_start.sh            # Script Linux/Mac de instalação rápida (sem Docker)
├── start_docker.sh           # Script Linux/Mac para iniciar com Docker Compose
├── start_docker.bat          # Script Windows para iniciar com Docker Compose
└── DEPLOYMENT.md             # Guia de Deployment para produção
```

## 🚀 Como Executar (Localmente)

### Pré-requisitos
- Python 3.11+
- `pip` (gerenciador de pacotes Python)
- **Tesseract OCR**: Necessário para processamento de PDF. 
  - **Linux**: `sudo apt install tesseract-ocr tesseract-ocr-por poppler-utils`
  - **Windows**: Baixe o instalador em [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki) e adicione o diretório de instalação ao PATH do sistema. Certifique-se de instalar o pacote de idioma `por` (Português).
- **Docker e Docker Compose**: (Opcional, mas recomendado para deployment) Instale o Docker Desktop (Windows/Mac) ou Docker Engine (Linux).

### 1. Configuração da Chave OpenAI
Para o processamento de imagens via LLM Vision, você precisará de uma chave de API da OpenAI. Configure-a como uma variável de ambiente:

```bash
# Linux/Mac
export OPENAI_API_KEY="sua_chave_aqui"

# Windows (Prompt de Comando)
set OPENAI_API_KEY=sua_chave_aqui

# Windows (PowerShell)
$env:OPENAI_API_KEY="sua_chave_aqui"
```

Alternativamente, crie um arquivo `.env` na raiz do projeto (baseado no `.env.example`) e defina `OPENAI_API_KEY=sua_chave_aqui`.

### 2. Opção A: Executar sem Docker (Desenvolvimento Local)

#### Instalação das Dependências
```bash
# Navegue para o diretório raiz do projeto
cd contabilidade_agentes

# Instalar dependências do backend
cd backend
pip install -r requirements.txt

# Instalar dependências do frontend
cd ../frontend
pip install -r requirements.txt
```

#### Iniciar o Backend (em um terminal)
```bash
# Linux/Mac
./start_backend.sh

# Windows (Prompt de Comando)
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

O backend estará disponível em: [http://localhost:8000](http://localhost:8000)

#### Iniciar o Frontend (em outro terminal)
```bash
# Linux/Mac
./start_frontend.sh

# Windows (Prompt de Comando)
cd frontend
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

O frontend estará disponível em: [http://localhost:8501](http://localhost:8501)

### 3. Opção B: Executar com Docker Compose (Recomendado para Deployment Local)

Certifique-se de ter o Docker e Docker Compose instalados.

#### Iniciar a Aplicação
```bash
# Navegue para o diretório raiz do projeto
cd contabilidade_agentes

# Crie o arquivo .env a partir do .env.example e configure OPENAI_API_KEY
cp .env.example .env
# Edite o .env para adicionar sua chave OpenAI

# Iniciar os serviços (backend e frontend)
# Linux/Mac
./start_docker.sh

# Windows (Prompt de Comando)
start_docker.bat
```

Isso construirá as imagens Docker (se ainda não existirem) e iniciará os contêineres. Pode levar alguns minutos na primeira vez.

O backend estará disponível em: [http://localhost:8000](http://localhost:8000)
O frontend estará disponível em: [http://localhost:8501](http://localhost:8501)

Para parar os serviços:
```bash
docker-compose down
```

## 📊 Exemplo de Uso

### 1. Via Interface Web (Frontend)
1. Acesse [http://localhost:8501](http://localhost:8501) no seu navegador.
2. Faça upload de um arquivo XML, PDF ou Imagem de NF-e (você pode usar os exemplos na pasta `data/`).
3. Observe o feedback de progresso e as mensagens de status.
4. Visualize os resultados estruturados, impostos, itens e gráficos interativos.
5. Baixe os dados processados em JSON ou CSV.

### 2. Via API Direta (Backend)
Você pode testar a API diretamente usando `curl` ou uma ferramenta como Postman/Insomnia.

```bash
# Teste de Saúde
curl http://localhost:8000/health

# Teste de Formatos Suportados
curl http://localhost:8000/supported-formats

# Teste com XML
curl -X POST "http://localhost:8000/process-document" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@data/exemplo_nfe.xml"

# Teste com PDF
curl -X POST "http://localhost:8000/process-document" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@data/exemplo_nfe.pdf"

# Teste com Imagem (PNG)
curl -X POST "http://localhost:8000/process-document" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@data/exemplo_nfe.png"
```

### 3. Resultado Esperado (Exemplo)
```json
{
  "success": true,
  "data": {
    "documento": "nfe",
    "numero_documento": "12345",
    "serie": "1",
    "data_emissao": "2025-09-03",
    "chave_nfe": "35250944556677000199550010000123451234567890",
    "emitente": "EMPRESA TESTE LTDA",
    "destinatario": "CLIENTE TESTE LTDA",
    "valor_total": 3000.00,
    "moeda": "BRL",
    "cfop": "1102",
    "ncm": "94017900",
    "cst": "00",
    "impostos": {
      "icms_base": 3000.00,
      "icms_valor": 360.00,
      "pis_valor": 27.00,
      "cofins_valor": 124.20,
      "iss_valor": 0.0
    },
    "itens": [
      {
        "codigo": "001",
        "descricao": "Cadeira Gamer",
        "quantidade": 4.0,
        "valor_unitario": 750.00,
        "valor_total": 3000.00,
        "unidade": "UN",
        "cfop_item": "1102",
        "ncm": "94017900",
        "cst": "00"
      }
    ]
  },
  "processing_time": 0.001  // Varia conforme o tipo de documento e complexidade
}
```

## 🔧 Tecnologias Utilizadas

### Backend (FastAPI)
- **FastAPI**: Framework web moderno e de alta performance.
- **Pydantic v2**: Validação de dados, tipagem e gerenciamento de configurações (`BaseSettings`).
- **LangChain**: (Base para futuros agentes e orquestração de LLMs).
- **OpenAI**: Integração com modelos GPT (especialmente GPT-4 Vision).
- **lxml**: Parsing eficiente de XML.
- **Tesseract OCR**: Reconhecimento óptico de caracteres.
- **pdf2image**: Conversão de PDF para imagem.
- **pytesseract**: Interface Python para Tesseract.
- **uvicorn**: Servidor ASGI de alta performance.
- **Prometheus Client**: Exposição de métricas para monitoramento.
- **pytest**: Framework de testes.
- **pytest-cov**: Cobertura de código.
- **black, flake8, mypy**: Ferramentas de qualidade de código (formatação, linting, type checking).

### Frontend (Streamlit)
- **Streamlit**: Framework para criação rápida de aplicações web interativas em Python.
- **Pandas**: Manipulação e análise de dados para visualizações.
- **Plotly**: Geração de gráficos interativos.
- **Requests**: Cliente HTTP para comunicação com a API.

## 📈 Performance e Precisão

### Métricas de Performance (Valores Aproximados)
- **XML**: < 1ms para arquivos típicos.
- **PDF OCR**: ~1.5s - 3s para arquivos de 1 página (depende da complexidade e qualidade).
- **Imagem (LLM Vision)**: ~2s - 5s (depende da complexidade da imagem e da latência da API OpenAI).

### Precisão
- **XML**: 100% para campos obrigatórios da NF-e.
- **PDF OCR**: 85-95% dependendo da qualidade do documento (resolução, fonte, layout).
- **Imagem (LLM Vision)**: Alta precisão e compreensão contextual, superando o OCR tradicional em documentos complexos ou de baixa qualidade.

### Otimizações Implementadas
- **Processamento Assíncrono**: Uso de `async/await` para operações I/O-bound.
- **Background Tasks**: Para operações que não precisam bloquear a resposta da API.
- **Cache em Memória**: Reduz processamento redundante para operações custosas.
- **Controle de Concorrência**: Semáforos para limitar o número de processamentos simultâneos.
- **DPI para OCR**: 300 DPI para melhor qualidade de reconhecimento em PDFs.
- **Idioma Tesseract**: Configurado para português brasileiro (`por`).
- **Modo PSM**: Page Segmentation Mode otimizado para documentos no Tesseract.

## 🧪 Testes e Qualidade de Código

O projeto possui uma suíte de testes robusta e ferramentas de qualidade de código para garantir a confiabilidade e manutenibilidade.

### Estrutura de Testes
- **`tests/unit/`**: Testes focados em componentes isolados (ex: `XMLProcessor`, `PDFProcessor`).
- **`tests/integration/`**: Testes que verificam a interação entre múltiplos componentes (ex: `API Endpoints`).
- **`tests/fixtures/`**: Dados de exemplo e mocks para uso nos testes.

### Como Executar os Testes
Navegue até o diretório `backend/` e execute:

```bash
# Linux/Mac
./run_tests.sh

# Windows (Prompt de Comando)
run_tests.bat
```

Este script executará:
- Instalação de dependências de teste.
- Verificação de formatação (`black --check`).
- Verificação de estilo (`flake8`).
- Verificação de tipos (`mypy`).
- Testes unitários e de integração (`pytest`).
- Relatório de cobertura de código (`pytest-cov`).

### Ferramentas de Qualidade
- **`black`**: Formatador de código Python para garantir consistência.
- **`flake8`**: Linter para verificar conformidade com PEP8 e erros comuns.
- **`mypy`**: Verificador de tipos estático para Python.
- **`pytest-cov`**: Extensão do Pytest para medir a cobertura de código.

### CI/CD (Integração Contínua / Entrega Contínua)
Um pipeline de CI/CD está configurado usando GitHub Actions (`.github/workflows/ci-cd.yml`). Ele automatiza:
- **Testes**: Executa todos os testes unitários e de integração.
- **Linting e Type Checking**: Garante a qualidade do código.
- **Análise de Segurança**: Com ferramentas como `bandit`.
- **Build de Imagens Docker**: Cria e publica imagens Docker no Docker Hub.
- **Deployment (Exemplo)**: Placeholder para scripts de deployment em produção.

## 🔒 Segurança

O sistema foi projetado com foco em segurança:
- **Gerenciamento de Segredos**: Chaves de API (ex: OpenAI) são carregadas via variáveis de ambiente.
- **Mascaramento de Logs**: Dados sensíveis (chaves, PII) são automaticamente mascarados nos logs.
- **CORS Configurable**: Restrições de Cross-Origin Resource Sharing podem ser configuradas para produção.
- **Validação de Entrada**: Validação rigorosa de todos os dados de entrada para prevenir ataques (ex: injeção).
- **Middlewares de Segurança**: Implementação de cabeçalhos de segurança HTTP e rate limiting.

## 📝 Logs e Monitoramento

O sistema utiliza um sistema de logging estruturado e seguro para facilitar a auditoria e o monitoramento.

- **Logs Estruturados**: Todos os logs são gerados em formato JSON, facilitando a ingestão por ferramentas de agregação de logs (ELK Stack, Grafana Loki, etc.).
- **Mascaramento de Dados**: Informações sensíveis são automaticamente mascaradas antes de serem escritas nos logs.
- **Rotação de Logs**: Implementado `SecureRotatingFileHandler` para gerenciar o tamanho dos arquivos de log e garantir a segurança.
- **Níveis de Log**: Configuração flexível de níveis de log (DEBUG, INFO, WARNING, ERROR) por ambiente.
- **Métricas Prometheus**: Um endpoint `/metrics` está disponível na API para expor métricas de desempenho e saúde da aplicação, que podem ser coletadas por ferramentas como Prometheus e visualizadas no Grafana.

Para mais detalhes sobre o sistema de logging, consulte o arquivo `docs/LOGGING.md`.

## 🇧🇷 Conformidade

O sistema foi desenvolvido com foco na conformidade fiscal brasileira:
- Suporte a padrões de NF-e (versão 4.00).
- Extração de dados fiscais obrigatórios.
- Validação de estruturas de impostos.
- Preparado para regras contábeis brasileiras (NBC TG, ITG 2000).
- Processamento de documentos em múltiplos formatos.

## 📈 Próximos Passos (Roadmap)

### Agentes Planejados
1. **ClassificationAgent**: Classificação automática de documentos e transações usando regras e/ou LLMs.
2. **AccountingEntryAgent**: Geração automatizada de lançamentos contábeis com base nos dados extraídos.
3. **ValidationAgent**: Validação de regras de negócio e conformidade contábil.
4. **PostingAgent**: Integração com sistemas ERP e sistemas contábeis.
5. **MemoryAgent**: Criação de uma base de conhecimento para aprendizado contínuo e contexto.
6. **HumanReviewAgent**: Escalação inteligente para revisão humana quando a confiança do processamento for baixa.
7. **AuditTrailAgent**: Geração de trilhas de auditoria detalhadas para conformidade.
8. **PrioritizationAgent**: Priorização de documentos com base em urgência ou complexidade.

### Melhorias Técnicas e Funcionais
- Suporte a outros tipos de documentos fiscais (NFS-e, CT-e, recibos, etc.).
- Integração com bancos de dados para persistência de dados processados.
- Dashboard de monitoramento mais avançado (além do Prometheus/Grafana).
- Otimização contínua da precisão do OCR e LLM Vision com modelos mais recentes ou fine-tuning.
- Implementação de um sistema de filas (ex: Celery, RabbitMQ) para processamento assíncrono em larga escala.

## 🤝 Contribuição

Contribuições são bem-vindas! Para contribuir com o projeto:
1. Faça um fork do repositório.
2. Crie uma branch para sua feature (`git checkout -b feature/sua-feature`).
3. Implemente os testes necessários e garanta que todos os testes passem.
4. Siga os padrões de qualidade de código (black, flake8, mypy).
5. Envie um pull request detalhado.

## 📞 Suporte

Para dúvidas ou suporte:
- Consulte a documentação completa neste `README.md` e em `docs/`.
- Verifique os logs da aplicação para mensagens de erro.
- Teste os endpoints da API diretamente.
- Para problemas de OCR, verifique a instalação e configuração do Tesseract.
- Para problemas com LLM Vision, verifique sua chave de API OpenAI e créditos.

---

**Desenvolvido com foco em automação contábil e conformidade fiscal brasileira** 🇧🇷

**Versão 3.0 - Completa com XML, PDF (OCR), Imagem (LLM Vision), Testes, Segurança e Docker!** 🚀✨

