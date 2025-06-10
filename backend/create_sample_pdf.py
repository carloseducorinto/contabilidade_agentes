#!/usr/bin/env python3
"""
Script para criar um PDF de exemplo de NF-e para testar o OCR
"""

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import os

def create_sample_nfe_pdf():
    """Cria um PDF de exemplo simulando uma NF-e"""
    
    output_path = "../data/exemplo_nfe.pdf"
    
    # Cria o canvas
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, height - 2*cm, "NOTA FISCAL ELETRÔNICA")
    
    # Informações básicas
    c.setFont("Helvetica", 12)
    y_pos = height - 3*cm
    
    # Dados da NF-e
    nfe_data = [
        "NÚMERO: 12345",
        "SÉRIE: 1",
        "DATA DE EMISSÃO: 03/09/2025",
        "CHAVE NFE: 35250944556677000199550010000123451234567890",
        "",
        "EMITENTE:",
        "CNPJ: 44.556.677/0001-99",
        "EMPRESA EXEMPLO LTDA",
        "",
        "DESTINATÁRIO:",
        "CNPJ: 77.665.544/0001-22",
        "CLIENTE EXEMPLO LTDA",
        "",
        "PRODUTOS/SERVIÇOS:",
        "DESCRIÇÃO: Cadeira Gamer",
        "QUANTIDADE: 4",
        "VALOR UNITÁRIO: R$ 750,00",
        "CFOP: 1102",
        "NCM: 94017900",
        "CST: 00",
        "",
        "IMPOSTOS:",
        "ICMS: R$ 360,00",
        "PIS: R$ 27,00",
        "COFINS: R$ 124,20",
        "",
        "VALOR TOTAL: R$ 3.000,00"
    ]
    
    for line in nfe_data:
        c.drawString(2*cm, y_pos, line)
        y_pos -= 0.6*cm
    
    # Salva o PDF
    c.save()
    
    print(f"PDF de exemplo criado: {output_path}")
    return output_path

if __name__ == "__main__":
    create_sample_nfe_pdf()

