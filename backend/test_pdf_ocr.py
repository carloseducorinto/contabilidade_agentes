#!/usr/bin/env python3
"""
Script de teste para o processamento de PDF via OCR
"""

import sys
import os
import json

# Adiciona o diretório app ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.document_ingestion_agent import DocumentIngestionAgent


def test_pdf_processing():
    """Testa o processamento de PDF de NF-e via OCR"""
    print("=== Teste do DocumentIngestionAgent - PDF OCR ===")
    
    # Inicializa o agente
    agent = DocumentIngestionAgent()
    
    # Carrega o arquivo PDF de exemplo
    pdf_path = "../data/exemplo_nfe.pdf"
    
    try:
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        print(f"Arquivo PDF carregado: {len(pdf_content)} bytes")
        
        # Processa o documento
        print("🔍 Iniciando processamento via OCR...")
        result = agent.process_document(pdf_content, 'pdf')
        
        if result.success:
            print("✅ Processamento bem-sucedido!")
            print(f"⏱️  Tempo de processamento: {result.processing_time:.2f}s")
            print("\n📄 Dados extraídos via OCR:")
            
            # Converte para JSON para exibição formatada
            data_dict = result.data.model_dump()
            print(json.dumps(data_dict, indent=2, ensure_ascii=False))
            
        else:
            print("❌ Erro no processamento:")
            print(result.error_message)
            
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {pdf_path}")
        print("💡 Execute primeiro: python3 create_sample_pdf.py")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")


def test_both_formats():
    """Testa ambos os formatos (XML e PDF) para comparação"""
    print("\n" + "="*60)
    print("=== Comparação XML vs PDF OCR ===")
    
    agent = DocumentIngestionAgent()
    
    # Teste XML
    print("\n🔸 Testando XML:")
    try:
        with open("../data/exemplo_nfe.xml", 'rb') as f:
            xml_content = f.read()
        
        xml_result = agent.process_document(xml_content, 'xml')
        if xml_result.success:
            print(f"✅ XML processado em {xml_result.processing_time:.3f}s")
            print(f"📊 Valor total: R$ {xml_result.data.valor_total:,.2f}")
            print(f"📦 Itens: {len(xml_result.data.itens)}")
        else:
            print(f"❌ Erro XML: {xml_result.error_message}")
    except Exception as e:
        print(f"❌ Erro XML: {str(e)}")
    
    # Teste PDF
    print("\n🔸 Testando PDF OCR:")
    try:
        with open("../data/exemplo_nfe.pdf", 'rb') as f:
            pdf_content = f.read()
        
        pdf_result = agent.process_document(pdf_content, 'pdf')
        if pdf_result.success:
            print(f"✅ PDF processado em {pdf_result.processing_time:.3f}s")
            print(f"📊 Valor total: R$ {pdf_result.data.valor_total:,.2f}")
            print(f"📦 Itens: {len(pdf_result.data.itens)}")
        else:
            print(f"❌ Erro PDF: {pdf_result.error_message}")
    except Exception as e:
        print(f"❌ Erro PDF: {str(e)}")


if __name__ == "__main__":
    test_pdf_processing()
    test_both_formats()

