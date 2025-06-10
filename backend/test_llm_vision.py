#!/usr/bin/env python3
"""
Script de teste para o processamento de imagem via LLM Vision
"""

import sys
import os
import json

# Adiciona o diretório app ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.document_ingestion_agent import DocumentIngestionAgent


def test_image_processing():
    """Testa o processamento de imagem de NF-e via LLM Vision"""
    print("=== Teste do DocumentIngestionAgent - LLM Vision ===")
    
    # Verifica se a chave OpenAI está configurada
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY não configurada.")
        print("💡 Configure a variável de ambiente OPENAI_API_KEY para testar o processamento de imagem.")
        return
    
    # Inicializa o agente
    agent = DocumentIngestionAgent(openai_api_key=openai_key)
    
    # Carrega o arquivo de imagem de exemplo
    image_path = "../data/exemplo_nfe.png"
    
    try:
        with open(image_path, 'rb') as f:
            image_content = f.read()
        
        print(f"Arquivo de imagem carregado: {len(image_content)} bytes")
        
        # Processa o documento
        print("🔍 Iniciando processamento via LLM Vision...")
        result = agent.process_document(image_content, 'png')
        
        if result.success:
            print("✅ Processamento bem-sucedido!")
            print(f"⏱️  Tempo de processamento: {result.processing_time:.2f}s")
            print("\n📄 Dados extraídos via LLM Vision:")
            
            # Converte para JSON para exibição formatada
            data_dict = result.data.model_dump()
            print(json.dumps(data_dict, indent=2, ensure_ascii=False))
            
        else:
            print("❌ Erro no processamento:")
            print(result.error_message)
            
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {image_path}")
        print("💡 Execute primeiro: python3 create_sample_pdf.py")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")


def test_all_formats():
    """Testa todos os formatos (XML, PDF e Imagem) para comparação"""
    print("\n" + "="*60)
    print("=== Comparação XML vs PDF OCR vs LLM Vision ===")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    agent = DocumentIngestionAgent(openai_api_key=openai_key)
    
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
    
    # Teste Imagem
    print("\n🔸 Testando Imagem LLM Vision:")
    if not openai_key:
        print("❌ OPENAI_API_KEY não configurada - pulando teste de imagem")
    else:
        try:
            with open("../data/exemplo_nfe.png", 'rb') as f:
                image_content = f.read()
            
            image_result = agent.process_document(image_content, 'png')
            if image_result.success:
                print(f"✅ Imagem processada em {image_result.processing_time:.3f}s")
                print(f"📊 Valor total: R$ {image_result.data.valor_total:,.2f}")
                print(f"📦 Itens: {len(image_result.data.itens)}")
            else:
                print(f"❌ Erro Imagem: {image_result.error_message}")
        except Exception as e:
            print(f"❌ Erro Imagem: {str(e)}")


if __name__ == "__main__":
    test_image_processing()
    test_all_formats()

