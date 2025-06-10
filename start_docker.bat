@echo off
setlocal enabledelayedexpansion

REM =================================================================
REM SCRIPT DE INICIALIZAÇÃO - SISTEMA DE CONTABILIDADE COM AGENTES
REM =================================================================

echo 🐳 Iniciando Sistema de Contabilidade com Agentes via Docker
echo ==============================================================

REM Verificar se Docker está rodando
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker não está rodando. Por favor, inicie o Docker Desktop primeiro.
    pause
    exit /b 1
)

REM Verificar se Docker Compose está disponível
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose não encontrado. Por favor, instale o Docker Desktop.
    pause
    exit /b 1
)

REM Verificar se arquivo .env existe
if not exist .env (
    echo ⚠️  Arquivo .env não encontrado. Criando a partir do exemplo...
    if exist env.example (
        copy env.example .env >nul
        echo ✅ Arquivo .env criado. EDITE o arquivo .env e configure sua OPENAI_API_KEY!
        echo 📝 Use: notepad .env ou code .env
        echo.
        echo 🔑 Configure pelo menos a OPENAI_API_KEY para usar o sistema completo.
        echo.
        pause
    ) else (
        echo ❌ Arquivo env.example não encontrado.
        pause
        exit /b 1
    )
)

REM Verificar se OPENAI_API_KEY está configurada
findstr /C:"OPENAI_API_KEY=sk-" .env >nul 2>&1
if errorlevel 1 (
    echo ⚠️  OPENAI_API_KEY não parece estar configurada no arquivo .env
    echo 🔑 Configure sua API Key da OpenAI para usar o sistema completo.
    echo.
    set /p "continue=Continuar mesmo assim? (y/N): "
    if /i not "!continue!"=="y" (
        echo Execução cancelada. Configure a API Key e tente novamente.
        pause
        exit /b 1
    )
)

echo 🔧 Verificando dependências...

REM Verificar se há containers antigos rodando
docker-compose ps | findstr "Up" >nul 2>&1
if not errorlevel 1 (
    echo 🔄 Parando containers existentes...
    docker-compose down
)

echo 📦 Construindo e iniciando containers...

REM Perguntar sobre monitoramento
echo.
set /p "monitoring=Incluir monitoramento (Prometheus + Grafana)? (y/N): "
if /i "!monitoring!"=="y" (
    echo 🚀 Iniciando com monitoramento...
    docker-compose --profile monitoring up --build -d
    set "MONITORING=true"
) else (
    echo 🚀 Iniciando aplicação principal...
    docker-compose up --build -d
    set "MONITORING=false"
)

echo.
echo ⏳ Aguardando containers inicializarem...
timeout /t 15 /nobreak >nul

REM Verificar status dos containers
echo 📊 Status dos containers:
docker-compose ps

echo.
echo 🏥 Verificando health checks...
timeout /t 10 /nobreak >nul

REM Verificar se backend está healthy
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 (
    echo ✅ Backend está funcionando
) else (
    echo ⚠️  Backend pode não estar totalmente pronto ainda
)

REM Verificar se frontend está acessível  
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8501/_stcore/health' -UseBasicParsing | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 (
    echo ✅ Frontend está funcionando
) else (
    echo ⚠️  Frontend pode não estar totalmente pronto ainda
)

echo.
echo 🎉 Sistema iniciado com sucesso!
echo ==============================================================
echo 🌐 Acessos:
echo    Frontend (Streamlit): http://localhost:8501
echo    Backend (FastAPI):    http://localhost:8000
echo    API Docs:             http://localhost:8000/docs

if "!MONITORING!"=="true" (
    echo    Prometheus:           http://localhost:9090
    echo    Grafana:              http://localhost:3000 (admin/admin123)
)

echo.
echo 📋 Comandos úteis:
echo    Ver logs:             docker-compose logs -f
echo    Parar sistema:        docker-compose down
echo    Reiniciar backend:    docker-compose restart backend
echo    Status containers:    docker-compose ps
echo.
echo 📚 Consulte DOCKER_GUIDE.md para mais informações.
echo.
echo ✨ Pronto para usar! Acesse http://localhost:8501
echo.

REM Perguntar se quer abrir o browser
set /p "open=Abrir browser automaticamente? (Y/n): "
if /i not "!open!"=="n" (
    start http://localhost:8501
)

pause

