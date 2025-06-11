from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date
from decimal import Decimal


class ImpostosModel(BaseModel):
    """Modelo para impostos da NF-e"""
    icms_base: Optional[float] = Field(None, description="Base de cálculo do ICMS")
    icms_valor: Optional[float] = Field(None, description="Valor do ICMS")
    pis_valor: Optional[float] = Field(None, description="Valor do PIS")
    cofins_valor: Optional[float] = Field(None, description="Valor do COFINS")
    iss_valor: Optional[float] = Field(None, description="Valor do ISS")


class ItemModel(BaseModel):
    """Modelo para itens da NF-e"""
    descricao: str = Field(..., description="Descrição do item")
    quantidade: float = Field(..., description="Quantidade do item")
    valor_unitario: float = Field(..., description="Valor unitário do item")
    cfop_item: str = Field(..., description="CFOP do item")
    ncm: str = Field(..., description="NCM do item")
    cst: str = Field(..., description="CST do item")


class DocumentoFiscalModel(BaseModel):
    """Modelo estruturado para documentos fiscais brasileiros"""
    documento: str = Field(..., description="Tipo do documento (nfe, nfse, etc.)")
    cfop: str = Field(..., description="Código Fiscal de Operações e Prestações")
    cst: str = Field(..., description="Código de Situação Tributária")
    forma_pagamento: str = Field(..., description="Forma de pagamento")
    ncm: str = Field(..., description="Nomenclatura Comum do Mercosul")
    valor_total: float = Field(..., description="Valor total do documento")
    data_emissao: str = Field(..., description="Data de emissão do documento")
    emitente: str = Field(..., description="CNPJ do emitente")
    destinatario: str = Field(..., description="CNPJ do destinatário")
    moeda: str = Field(default="BRL", description="Moeda do documento")
    numero_documento: str = Field(..., description="Número do documento")
    serie: str = Field(..., description="Série do documento")
    chave_nfe: Optional[str] = Field(None, description="Chave da NF-e")
    impostos: ImpostosModel = Field(..., description="Impostos do documento")
    itens: List[ItemModel] = Field(..., description="Itens do documento")


class ProcessingResult(BaseModel):
    """Resultado do processamento de um documento"""
    success: bool = Field(..., description="Indica se o processamento foi bem-sucedido")
    data: Optional[DocumentoFiscalModel] = Field(None, description="Dados extraídos do documento")
    error_message: Optional[str] = Field(None, description="Mensagem de erro, se houver")
    processing_time: Optional[float] = Field(None, description="Tempo de processamento em segundos")

