@echo off
echo 🧪 Executando testes e verificações de qualidade...
echo.

cd /d "%~dp0"

echo 📦 Instalando dependências de teste...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Erro ao instalar dependências
    pause
    exit /b 1
)

echo.
echo 🔍 Executando verificações de qualidade...
python run_quality_checks.py

if %errorlevel% equ 0 (
    echo.
    echo 🎉 Todas as verificações passaram!
) else (
    echo.
    echo ⚠️ Algumas verificações falharam. Verifique os logs acima.
)

echo.
echo 📊 Relatório de cobertura HTML gerado em: htmlcov/index.html
echo.
pause

