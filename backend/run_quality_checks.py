#!/usr/bin/env python3
"""
Script para executar testes e verificações de qualidade de código
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command: str, description: str) -> bool:
    """Executa um comando e retorna True se bem-sucedido"""
    print(f"\n🔍 {description}")
    print(f"Executando: {command}")
    print("-" * 50)
    
    result = subprocess.run(command, shell=True, capture_output=False)
    
    if result.returncode == 0:
        print(f"✅ {description} - SUCESSO")
        return True
    else:
        print(f"❌ {description} - FALHOU")
        return False

def main():
    """Executa todas as verificações de qualidade"""
    print("🚀 Iniciando verificações de qualidade de código...")
    
    # Muda para o diretório do backend
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    success_count = 0
    total_checks = 0
    
    # Lista de verificações
    checks = [
        ("black --check --diff .", "Verificação de formatação (Black)"),
        ("flake8 app/ tests/", "Verificação de estilo (Flake8)"),
        ("mypy app/", "Verificação de tipos (MyPy)"),
        ("pytest tests/unit/ -v", "Testes unitários"),
        ("pytest tests/integration/ -v", "Testes de integração"),
        ("pytest --cov=app --cov-report=term-missing", "Cobertura de código"),
    ]
    
    # Executa cada verificação
    for command, description in checks:
        total_checks += 1
        if run_command(command, description):
            success_count += 1
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL")
    print("=" * 60)
    print(f"✅ Verificações bem-sucedidas: {success_count}")
    print(f"❌ Verificações falharam: {total_checks - success_count}")
    print(f"📈 Taxa de sucesso: {(success_count/total_checks)*100:.1f}%")
    
    if success_count == total_checks:
        print("\n🎉 Todas as verificações passaram! Código pronto para produção.")
        return 0
    else:
        print(f"\n⚠️  {total_checks - success_count} verificação(ões) falharam. Revise o código.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

