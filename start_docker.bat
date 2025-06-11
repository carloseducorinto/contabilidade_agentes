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
findstr /C:"OPENAI_API_KEY=" .env | findstr /V /C:"OPENAI_API_KEY=$" | findstr /V /C:"OPENAI_API_KEY= " >nul 2>&1
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

REM Limpeza completa de containers e redes antigas
echo 🧹 Limpando containers e redes antigas...
docker-compose down --volumes --remove-orphans 2>nul
docker network prune -f 2>nul

echo 📦 Construindo e iniciando containers...

REM Configurar variável de ambiente para Docker networking
set "BACKEND_URL=http://backend:8000"

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

REM Verificar se houve erro na inicialização
if errorlevel 1 (
    echo ❌ Erro na inicialização dos containers. Forçando reinicialização limpa...
    docker-compose down --volumes --remove-orphans
    docker network prune -f >nul
    timeout /t 3 /nobreak >nul
    REM Manter a variável de ambiente definida
    set "BACKEND_URL=http://backend:8000"
    if /i "!monitoring!"=="y" (
        docker-compose --profile monitoring up --build -d
    ) else (
        docker-compose up --build -d
    )
)

echo.
echo ⏳ Aguardando containers inicializarem...
timeout /t 20 /nobreak >nul

REM Verificar status dos containers
echo 📊 Status dos containers:
docker-compose ps

REM Mostrar redes Docker criadas
echo 🌐 Redes Docker criadas:
docker network ls | findstr "contabilidade"

echo.
echo 🏥 Verificando health checks...

timeout /t 15 /nobreak >nul

set "backend_ok=false"
for /l %%i in (1,1,3) do (
    powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing -TimeoutSec 10; if ($response.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
    if not errorlevel 1 (
        set "backend_ok=true"
        goto :backend_check_done
    )
    echo 🔄 Tentativa %%i/3: Aguardando backend...
    timeout /t 10 /nobreak >nul
)
:backend_check_done

if "!backend_ok!"=="true" (
    echo ✅ Backend está funcionando
) else (
    echo ⚠️  Backend ainda não está respondendo. Verifique os logs com: docker-compose logs backend
)

REM Aguardar mais tempo para o frontend inicializar
timeout /t 20 /nobreak >nul

set "frontend_ok=false"
for /l %%i in (1,1,5) do (
    powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8501/_stcore/health' -UseBasicParsing -TimeoutSec 10; if ($response.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
    if not errorlevel 1 (
        set "frontend_ok=true"
        goto :frontend_check_done
    )
    echo 🔄 Tentativa %%i/5: Aguardando frontend...
    timeout /t 15 /nobreak >nul
)
:frontend_check_done

if "!frontend_ok!"=="true" (
    echo ✅ Frontend está funcionando
) else (
    echo ⚠️  Frontend ainda não está respondendo. Verifique os logs com: docker-compose logs frontend
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
echo    Reiniciar frontend:   docker-compose restart frontend
echo    Status containers:    docker-compose ps
echo    Limpar tudo:          docker-compose down --volumes --remove-orphans
echo.
echo 📚 Consulte DOCKER_GUIDE.md para mais informações.
echo.

if "!backend_ok!"=="true" if "!frontend_ok!"=="true" (
    echo ✨ Pronto para usar! Acesse http://localhost:8501
    echo.
    set /p "open=Abrir browser automaticamente? (Y/n): "
    if /i not "!open!"=="n" (
        start http://localhost:8501
    )
) else (
    echo ⚠️  Alguns serviços podem não estar funcionando corretamente.
    echo 💡 Dicas de troubleshooting:
    echo    1. Verifique os logs: docker-compose logs
    echo    2. Reinicie os serviços: docker-compose restart
    echo    3. Se persistir, pare tudo e reinicie: docker-compose down ^&^& docker-compose up -d
    echo.
)

pause
