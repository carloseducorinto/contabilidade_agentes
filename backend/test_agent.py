#!/usr/bin/env python3
"""
Script de teste para o DocumentIngestionAgent
"""

import sys
import os
import json

# Adiciona o diretório app ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.document_ingestion_agent import DocumentIngestionAgent


def test_xml_processing():
    """Testa o processamento de XML de NF-e"""
    print("=== Teste do DocumentIngestionAgent ===")
    
    # Inicializa o agente
    agent = DocumentIngestionAgent()
    
    # Carrega o arquivo XML de exemplo
    xml_path = "../data/exemplo_nfe.xml"
    
    try:
        with open(xml_path, 'rb') as f:
            xml_content = f.read()
        
        print(f"Arquivo XML carregado: {len(xml_content)} bytes")
        
        # Processa o documento
        result = agent.process_document(xml_content, 'xml')
        
        if result.success:
            print("✅ Processamento bem-sucedido!")
            print(f"⏱️  Tempo de processamento: {result.processing_time:.2f}s")
            print("\n📄 Dados extraídos:")
            
            # Converte para JSON para exibição formatada
            data_dict = result.data.model_dump()
            print(json.dumps(data_dict, indent=2, ensure_ascii=False))
            
        else:
            print("❌ Erro no processamento:")
            print(result.error_message)
            
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {xml_path}")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")


if __name__ == "__main__":
    test_xml_processing()

