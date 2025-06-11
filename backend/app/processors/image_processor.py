"""
Processador de imagens via LLM Vision
"""
import base64
import json
import re
from typing import List, Dict, Any, Optional
from ..models import DocumentoFiscalModel, ImpostosModel, ItemModel
from ..exceptions import ImageProcessingError, ExternalAPIError
from ..config import get_settings
from ..logging_config import get_logger, log_operation_start, log_operation_success, log_operation_error

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

settings = get_settings()
logger = get_logger("ImageProcessor")


class ImageProcessor:
    """Processador especializado para imagens via LLM Vision"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.logger = logger
        self.openai_api_key = openai_api_key or settings.openai_api_key
        
        # Inicializa cliente OpenAI se disponível
        if self.openai_api_key and OpenAI:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            self.logger.info("Cliente OpenAI inicializado com sucesso")
        else:
            self.openai_client = None
            self.logger.warning("Cliente OpenAI não inicializado - chave API não fornecida")
    
    def process(self, image_content: bytes, file_type: str) -> DocumentoFiscalModel:
        """
        Processa uma imagem via LLM Vision e retorna dados estruturados
        
        Args:
            image_content: Conteúdo da imagem em bytes
            file_type: Tipo do arquivo de imagem
            
        Returns:
            DocumentoFiscalModel com dados estruturados
            
        Raises:
            ImageProcessingError: Se houver erro no processamento
        """
        if not self.openai_client:
            raise ImageProcessingError(
                "Cliente OpenAI não inicializado. Verifique a chave da API.",
                error_code="OPENAI_CLIENT_NOT_INITIALIZED"
            )
        
        operation_id = log_operation_start(
            "image_llm_processing",
            agent="ImageProcessor",
            image_size=len(image_content),
            file_type=file_type
        )
        
        try:
            # Codifica imagem em base64
            image_base64 = base64.b64encode(image_content).decode('utf-8')
            
            # Determina o tipo MIME
            mime_type = self._get_mime_type(file_type)
            
            # Cria prompt especializado para NF-e brasileira
            prompt = self._create_nfe_prompt()
            
            # Chama GPT-4 Vision
            response = self.openai_client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens
            )
            
            # Extrai resposta
            if not response.choices:
                raise ImageProcessingError("Resposta vazia do LLM")
            
            llm_response = response.choices[0].message.content
            
            # Processa resposta do LLM
            documento = self._parse_llm_response(llm_response)
            
            log_operation_success(
                operation_id,
                agent="ImageProcessor",
                image_size=len(image_content),
                file_type=file_type,
                llm_model=settings.llm_model,
                tokens_used=response.usage.total_tokens if response.usage else 0,
                numero_documento=documento.numero_documento
            )
            
            return documento
            
        except Exception as e:
            log_operation_error(operation_id, f"Erro no processamento de imagem: {str(e)}", agent="ImageProcessor")
            if "openai" in str(e).lower():
                raise ExternalAPIError(f"Erro na API OpenAI: {str(e)}")
            else:
                raise ImageProcessingError(f"Erro no processamento de imagem: {str(e)}")
    
    def _get_mime_type(self, file_type: str) -> str:
        """Retorna o tipo MIME baseado na extensão do arquivo"""
        mime_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'webp': 'image/webp',
            'gif': 'image/gif'
        }
        return mime_types.get(file_type.lower(), 'image/jpeg')
    
    def _create_nfe_prompt(self) -> str:
        """Cria prompt especializado para extração de dados de NF-e"""
        return """
Analise esta imagem de uma Nota Fiscal Eletrônica (NF-e) brasileira e extraia os seguintes dados em formato JSON:

{
  "numero_documento": "número da nota fiscal",
  "serie": "série da nota fiscal",
  "data_emissao": "data de emissão no formato YYYY-MM-DD",
  "emitente": "CNPJ do emitente (apenas números)",
  "destinatario": "CNPJ do destinatário (apenas números)",
  "chave_nfe": "chave de acesso da NF-e (44 dígitos)",
  "valor_total": valor_total_como_numero,
  "cfop": "código CFOP",
  "ncm": "código NCM",
  "cst": "código CST",
  "impostos": {
    "icms_base": valor_base_icms,
    "icms_valor": valor_icms,
    "pis_valor": valor_pis,
    "cofins_valor": valor_cofins
  },
  "itens": [
    {
      "descricao": "descrição do produto/serviço",
      "quantidade": quantidade_como_numero,
      "valor_unitario": valor_unitario_como_numero,
      "cfop_item": "CFOP do item",
      "ncm": "NCM do item",
      "cst": "CST do item"
    }
  ]
}

Instruções importantes:
1. Extraia apenas dados visíveis na imagem
2. Use valores numéricos para campos de valor (sem símbolos de moeda)
3. Para CNPJs, remova pontuação e mantenha apenas números
4. Se um campo não estiver visível, use string vazia "" ou null
5. Para impostos não visíveis, use 0.0
6. Retorne APENAS o JSON, sem texto adicional
7. Se houver múltiplos itens, inclua todos no array "itens"
"""
    
    def _parse_llm_response(self, response: str) -> DocumentoFiscalModel:
        """Processa a resposta do LLM e cria o modelo estruturado"""
        try:
            # Tenta extrair JSON da resposta
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                raise ImageProcessingError("Resposta do LLM não contém JSON válido")
            
            json_str = json_match.group(0)
            data = json.loads(json_str)
            
            # Valida e processa dados
            numero_documento = str(data.get('numero_documento', ''))
            serie = str(data.get('serie', '1'))
            data_emissao = str(data.get('data_emissao', ''))
            emitente = str(data.get('emitente', ''))
            destinatario = str(data.get('destinatario', ''))
            chave_nfe = str(data.get('chave_nfe', ''))
            valor_total = float(data.get('valor_total', 0.0))
            cfop = str(data.get('cfop', ''))
            ncm = str(data.get('ncm', ''))
            cst = str(data.get('cst', ''))
            
            # Processa impostos
            impostos_data = data.get('impostos', {})
            impostos = ImpostosModel(
                icms_base=float(impostos_data.get('icms_base', 0.0)),
                icms_valor=float(impostos_data.get('icms_valor', 0.0)),
                pis_valor=float(impostos_data.get('pis_valor', 0.0)),
                cofins_valor=float(impostos_data.get('cofins_valor', 0.0)),
                iss_valor=None
            )
            
            # Processa itens
            itens_data = data.get('itens', [])
            itens = []
            for item_data in itens_data:
                item = ItemModel(
                    descricao=str(item_data.get('descricao', '')),
                    quantidade=float(item_data.get('quantidade', 1.0)),
                    valor_unitario=float(item_data.get('valor_unitario', 0.0)),
                    cfop_item=str(item_data.get('cfop_item', cfop)),
                    ncm=str(item_data.get('ncm', ncm)),
                    cst=str(item_data.get('cst', cst))
                )
                itens.append(item)
            
            # Se não há itens, cria um genérico
            if not itens:
                itens.append(ItemModel(
                    descricao="Item extraído via LLM Vision",
                    quantidade=1.0,
                    valor_unitario=valor_total,
                    cfop_item=cfop,
                    ncm=ncm,
                    cst=cst
                ))
            
            return DocumentoFiscalModel(
                documento="nfe",
                cfop=cfop,
                cst=cst,
                forma_pagamento="a_vista",
                ncm=ncm,
                valor_total=valor_total,
                data_emissao=data_emissao,
                emitente=emitente,
                destinatario=destinatario,
                moeda="BRL",
                numero_documento=numero_documento,
                serie=serie,
                chave_nfe=chave_nfe,
                impostos=impostos,
                itens=itens
            )
            
        except json.JSONDecodeError as e:
            raise ImageProcessingError(f"Erro ao decodificar JSON da resposta do LLM: {str(e)}")
        except Exception as e:
            raise ImageProcessingError(f"Erro ao processar resposta do LLM: {str(e)}")

