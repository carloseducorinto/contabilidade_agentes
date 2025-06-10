@echo off
setlocal enabledelayedexpansion

REM =================================================================
REM SCRIPT DE PARADA - SISTEMA DE CONTABILIDADE COM AGENTES
REM =================================================================

echo 🛑 Parando Sistema de Contabilidade com Agentes
echo ===============================================

REM Verificar se Docker Compose está disponível
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose não encontrado.
    pause
    exit /b 1
)

echo 🔄 Parando todos os containers...
docker-compose --profile monitoring down

echo 📊 Verificando se todos os containers foram parados...
for /f %%i in ('docker-compose ps -q 2^>nul') do set CONTAINERS=1

if not defined CONTAINERS (
    echo ✅ Todos os containers foram parados com sucesso
) else (
    echo ⚠️  Alguns containers ainda estão rodando:
    docker-compose ps
)

echo.
echo 🧹 Deseja remover volumes de dados? (dados persistentes serão perdidos)
set /p "remove_volumes=Remover volumes? (y/N): "
if /i "!remove_volumes!"=="y" (
    echo 🗑️  Removendo volumes...
    docker-compose down -v
    echo ✅ Volumes removidos
) else (
    echo 💾 Volumes preservados
)

echo.
echo 🧹 Deseja limpar imagens Docker não utilizadas?
set /p "clean_images=Limpar imagens? (y/N): "
if /i "!clean_images!"=="y" (
    echo 🗑️  Removendo imagens não utilizadas...
    docker image prune -f
    echo ✅ Imagens limpas
)

echo.
echo ✅ Sistema parado com sucesso!
echo.
echo 📋 Para reiniciar: start_docker.bat
echo 📚 Consulte DOCKER_GUIDE.md para mais informações
echo.
pause 