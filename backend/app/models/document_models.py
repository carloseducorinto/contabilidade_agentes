"""
Modelos de dados para documentos fiscais
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import date, datetime
from decimal import Decimal


class ImpostosModel(BaseModel):
    """Modelo para impostos da NF-e"""
    icms_base: Optional[float] = Field(None, ge=0, description="Base de cálculo do ICMS")
    icms_valor: Optional[float] = Field(None, ge=0, description="Valor do ICMS")
    pis_valor: Optional[float] = Field(None, ge=0, description="Valor do PIS")
    cofins_valor: Optional[float] = Field(None, ge=0, description="Valor do COFINS")
    iss_valor: Optional[float] = Field(None, ge=0, description="Valor do ISS")
    
    @field_validator("*", mode="before")
    @classmethod
    def validate_positive_values(cls, v):
        """Valida que todos os valores são positivos ou None"""
        if v is not None and v < 0:
            raise ValueError("Valores de impostos devem ser positivos")
        return v


class ItemModel(BaseModel):
    """Modelo para itens da NF-e"""
    descricao: str = Field(..., min_length=1, max_length=500, description="Descrição do item")
    quantidade: float = Field(..., gt=0, description="Quantidade do item")
    valor_unitario: float = Field(..., ge=0, description="Valor unitário do item")
    cfop_item: Optional[str] = Field(None, description="CFOP do item (código original)")
    ncm: Optional[str] = Field(None, description="NCM do item (código original)")
    cst: Optional[str] = Field(None, description="CST do item (código original)")
    
    @field_validator("descricao")
    @classmethod
    def validate_descricao(cls, v):
        """Valida e limpa a descrição do item"""
        if not v or len(v.strip()) == 0:
            raise ValueError("Descrição do item não pode estar vazia")
        return v.strip()
    
    @field_validator("cfop_item", "cst")
    @classmethod
    def validate_cfop_cst_codes(cls, v, info):
        """Valida códigos CFOP e CST preservando valor original"""
        if v is None or v == "":
            return None  # Permite valores vazios ou None
        # Preserva o valor original, apenas remove espaços
        return v.strip() if isinstance(v, str) else str(v)
    
    @field_validator("ncm")
    @classmethod
    def validate_ncm_code(cls, v):
        """Valida código NCM preservando valor original"""
        if v is None or v == "":
            return None  # Permite valores vazios ou None
        # Preserva o valor original, apenas remove espaços
        return v.strip() if isinstance(v, str) else str(v)


class DocumentoFiscalModel(BaseModel):
    """Modelo estruturado para documentos fiscais brasileiros"""
    documento: str = Field(..., pattern=r"^(nfe|nfse|nfce)$", description="Tipo do documento")
    cfop: Optional[str] = Field(None, description="Código Fiscal de Operações e Prestações (código original)")
    cst: Optional[str] = Field(None, description="Código de Situação Tributária (código original)")
    forma_pagamento: Optional[str] = Field(None, description="Forma de pagamento")
    ncm: Optional[str] = Field(None, description="Nomenclatura Comum do Mercosul (código original)")
    valor_total: float = Field(..., ge=0, description="Valor total do documento")
    data_emissao: Optional[str] = Field(None, description="Data de emissão")
    emitente: Optional[str] = Field(None, description="CNPJ do emitente (valor original)")
    destinatario: Optional[str] = Field(None, description="CNPJ do destinatário")
    moeda: str = Field(default="BRL", pattern=r"^[A-Z]{3}$", description="Código da moeda (ISO 4217)")
    numero_documento: str = Field(..., min_length=1, description="Número do documento")
    serie: str = Field(..., min_length=1, description="Série do documento")
    chave_nfe: Optional[str] = Field(None, description="Chave da NF-e (valor original)")
    impostos: ImpostosModel = Field(..., description="Impostos do documento")
    itens: List[ItemModel] = Field(..., description="Itens do documento")
    
    @field_validator("data_emissao")
    @classmethod
    def validate_data_emissao(cls, v):
        """Valida formato da data de emissão"""
        if v is None or v == "":
            return None  # Permite valores vazios ou None
        
        # Tenta diferentes formatos de data
        date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(v, fmt)
                return parsed_date.strftime("%Y-%m-%d")  # Normaliza para formato padrão
            except ValueError:
                continue
        
        # Se nenhum formato funcionou, retorna o valor original
        return v
    
    @field_validator("cfop", "cst")
    @classmethod
    def validate_document_cfop_cst(cls, v, info):
        """Valida códigos CFOP e CST do documento preservando valor original"""
        if v is None or v == "":
            return None  # Permite valores vazios ou None
        # Preserva o valor original, apenas remove espaços
        return v.strip() if isinstance(v, str) else str(v)
    
    @field_validator("ncm")
    @classmethod
    def validate_document_ncm(cls, v):
        """Valida código NCM do documento preservando valor original"""
        if v is None or v == "":
            return None  # Permite valores vazios ou None
        # Preserva o valor original, apenas remove espaços
        return v.strip() if isinstance(v, str) else str(v)
    
    @field_validator("chave_nfe")
    @classmethod
    def validate_chave_nfe(cls, v):
        """Valida chave da NF-e preservando valor original"""
        if v is None or v == "":
            return None  # Permite valores vazios ou None
        # Preserva o valor original, incluindo asteriscos de mascaramento
        return v.strip() if isinstance(v, str) else str(v)
    
    @field_validator("emitente", "destinatario")
    @classmethod
    def validate_cnpj(cls, v, info):
        """Valida CNPJ preservando valor original"""
        if v is None or v == "":
            return None  # Permite valores vazios ou None
        # Preserva o valor original, incluindo formatação ou mascaramento
        return v.strip() if isinstance(v, str) else str(v)
    
    @field_validator("itens")
    @classmethod
    def validate_itens_list(cls, v):
        """Valida lista de itens"""
        if v is None:
            return []  # Converte None para lista vazia
        return v


class DocumentProcessed(BaseModel):
    """Modelo para os dados de um documento após o processamento inicial (extração)."""
    document_id: str = Field(..., description="ID único do documento.")
    document_type: str = Field(..., description="Tipo do documento (e.g., xml, pdf, image).")
    extracted_data: Dict[str, Any] = Field(..., description="Dados brutos extraídos do documento.")


class ProcessingResult(BaseModel):
    """Resultado do processamento de um documento"""
    success: bool = Field(..., description="Indica se o processamento foi bem-sucedido")
    document_id: str = Field(..., description="ID único do documento.")
    document_type: str = Field(..., description="Tipo do documento (e.g., xml, pdf, image).")
    extracted_data: Optional[Dict[str, Any]] = Field(None, description="Dados extraídos do documento")
    classification_data: Optional[Dict[str, Any]] = Field(None, description="Dados de classificação do documento")
    error: Optional[str] = Field(None, description="Mensagem de erro, se houver")
    processing_time: Optional[float] = Field(None, ge=0, description="Tempo de processamento em segundos")
    message: Optional[str] = Field(None, description="Mensagem de sucesso ou informação")
    metadata: Optional[dict] = Field(None, description="Metadados adicionais do processamento")
    
    @model_validator(mode="after")
    def validate_success_consistency(self):
        """Valida consistência entre success, error e data"""
        if not self.success and not self.error:
            raise ValueError("Mensagem de erro é obrigatória quando success=False")
        if self.success and not self.extracted_data:
            raise ValueError("Dados extraídos são obrigatórios quando success=True")
        return self


