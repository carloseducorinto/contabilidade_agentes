from typing import Dict, Any
from pydantic import BaseModel, Field

class ClassificationInput(BaseModel):
    document_id: str = Field(..., description="ID único do documento.")
    document_type: str = Field(..., description="Tipo do documento (e.g., xml, pdf, image).")
    extracted_data: Dict[str, Any] = Field(..., description="Dados extraídos do documento pelo DocumentIngestionAgent.")

class ClassificationOutput(BaseModel):
    conta_contabil: str = Field(..., description="Conta contábil classificada para a transação.")
    centro_de_custo: str = Field(..., description="Centro de custo associado à transação.")
    tipo_lancamento: str = Field(..., description="Tipo de lançamento contábil (e.g., Compra, Venda, Pagamento).")
    justificativa: str = Field(..., description="Breve justificativa para a classificação.")
    document_id: str = Field(..., description="ID único do documento original.")
    document_type: str = Field(..., description="Tipo do documento original.")
    # Opcional: incluir os dados extraídos originais ou um resumo
    # extracted_data_summary: Dict[str, Any] = Field(None, description="Resumo dos dados extraídos.")


