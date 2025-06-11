"""
Processador de documentos PDF via OCR com fallback LLM
"""
import re
import tempfile
import os
import base64
import io
from typing import List, Dict, Any, Optional
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
from ..models import DocumentoFiscalModel, ImpostosModel, ItemModel
from ..exceptions import PDFProcessingError
from ..config import get_settings
from ..logging_config import get_logger, log_operation_start, log_operation_success, log_operation_error
from .async_image_processor import AsyncImageProcessor

settings = get_settings()
logger = get_logger("PDFProcessor")


class PDFProcessor:
    """Processador especializado para documentos PDF via OCR"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.logger = logger
        self.image_processor = AsyncImageProcessor(openai_api_key) if openai_api_key else None
    
    async def process(self, pdf_content: bytes) -> DocumentoFiscalModel:
        """
        Processa um arquivo PDF via OCR e retorna dados estruturados
        
        Args:
            pdf_content: Conteúdo do arquivo PDF em bytes
            
        Returns:
            DocumentoFiscalModel com dados estruturados
            
        Raises:
            PDFProcessingError: Se houver erro no processamento
        """
        operation_id = log_operation_start(
            "pdf_ocr_processing",
            agent="PDFProcessor",
            pdf_size=len(pdf_content)
        )
        
        try:
            # Converte PDF para imagens
            images = convert_from_bytes(
                pdf_content, 
                dpi=settings.pdf_dpi,
                first_page=1,
                last_page=3  # Limita a 3 páginas para performance
            )
            
            if not images:
                raise PDFProcessingError("Não foi possível converter o PDF em imagens")
            
            # Processa cada página via OCR
            all_text = ""
            for i, image in enumerate(images, 1):
                self.logger.info(f"Processando página {i} via OCR")
                
                # Configura OCR
                custom_config = f'--oem 3 --psm {settings.tesseract_psm} -l {settings.tesseract_lang}'
                
                # Extrai texto da imagem
                page_text = pytesseract.image_to_string(image, config=custom_config)
                all_text += f"\n--- PÁGINA {i} ---\n{page_text}\n"
                
                self.logger.info(f"Página {i} processada via OCR")
            
            # Extrai dados estruturados do texto
            documento = self._extract_data_from_text(all_text)
            
            # Verifica se o resultado está completo e aciona LLM se necessário
            documento = await self._verify_and_enhance_with_llm(documento, images, all_text)
            
            log_operation_success(
                operation_id,
                agent="PDFProcessor",
                pdf_size=len(pdf_content),
                pages_processed=len(images),
                text_length=len(all_text),
                numero_documento=documento.numero_documento,
                llm_fallback_used=hasattr(documento, '_llm_enhanced')
            )
            
            return documento
            
        except Exception as e:
            log_operation_error(operation_id, f"Erro no processamento PDF: {str(e)}", agent="PDFProcessor")
            raise PDFProcessingError(f"Erro no processamento PDF: {str(e)}")
    
    def _extract_data_from_text(self, text: str) -> DocumentoFiscalModel:
        """Extrai dados estruturados do texto extraído via OCR"""
        
        # Patterns para extração de dados - melhorados
        patterns = {
            'numero_nf': r'(?:N[úu]mero|N[°º]|NF-e)\s*:?\s*(\d+)',
            'serie': r'S[ée]rie\s*:?\s*(\d+)',
            'data_emissao': r'(?:Data|Emiss[ãa]o|DATA\s+DE\s+EMISS[ÃA]O)\s*:?\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})',
            'cnpj_emitente': r'CNPJ\s*:?\s*(\d{2}\.?\d{3}\.?\d{3}\/?\d{4}\-?\d{2})',
            'valor_total': r'(?:VALOR\s+TOTAL|Total|Valor\s+Total)\s*:?\s*R?\$?\s*([\d\.,]+)',
            'cfop': r'CFOP\s*:?\s*(\d{4})',
            'ncm': r'NCM\s*:?\s*(\d{8})',
            'chave_nfe': r'(?:Chave|NFe|CHAVE\s+NFE)\s*:?\s*([0-9]{44})',
            'descricao_item': r'(?:DESCRI[ÇC][ÃA]O|Descri[çc][ãa]o)\s*:?\s*([^\n\r]+)',
            'quantidade': r'(?:QUANTIDADE|Quantidade)\s*:?\s*([\d\.,]+)',
            'valor_unitario': r'(?:VALOR\s+UNIT[ÁA]RIO|Valor\s+Unit[áa]rio)\s*:?\s*R?\$?\s*([\d\.,]+)'
        }
        
        # Extrai dados usando regex
        extracted_data = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted_data[key] = match.group(1).strip()
        
        # Processa e limpa os dados extraídos
        numero_nf = extracted_data.get('numero_nf', '')
        serie_nf = extracted_data.get('serie', '1')
        data_emissao = self._format_date(extracted_data.get('data_emissao', ''))
        
        # Limpa CNPJ
        cnpj_emitente = extracted_data.get('cnpj_emitente', '')
        if cnpj_emitente:
            cnpj_emitente = re.sub(r'[^\d]', '', cnpj_emitente)
        
        # Processa valor total
        valor_total_str = extracted_data.get('valor_total', '0')
        valor_total = self._parse_currency(valor_total_str)
        
        # Dados básicos
        cfop = extracted_data.get('cfop', '')
        ncm = extracted_data.get('ncm', '')
        chave_nfe = extracted_data.get('chave_nfe', '')
        
        # Extrai dados de itens do texto
        itens = self._extract_items_from_text(text, cfop, ncm, valor_total)
        
        # Extrai impostos do texto ou estima baseado no valor total
        impostos = self._extract_taxes_from_text(text, valor_total)
        
        return DocumentoFiscalModel(
            documento="nfe",
            cfop=cfop,
            cst="00",
            forma_pagamento="a_vista",
            ncm=ncm,
            valor_total=valor_total,
            data_emissao=data_emissao,
            emitente=cnpj_emitente,
            destinatario="",  # Difícil extrair via OCR
            moeda="BRL",
            numero_documento=numero_nf,
            serie=serie_nf,
            chave_nfe=chave_nfe,
            impostos=impostos,
            itens=itens
        )
    
    def _format_date(self, date_str: str) -> str:
        """Formata data para o padrão YYYY-MM-DD"""
        if not date_str:
            return ""
        
        # Tenta diferentes formatos
        date_patterns = [
            r'(\d{2})[\/\-](\d{2})[\/\-](\d{4})',  # DD/MM/YYYY
            r'(\d{4})[\/\-](\d{2})[\/\-](\d{2})',  # YYYY/MM/DD
        ]
        
        for pattern in date_patterns:
            match = re.match(pattern, date_str)
            if match:
                if len(match.group(1)) == 4:  # YYYY-MM-DD
                    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                else:  # DD/MM/YYYY -> YYYY-MM-DD
                    return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
        
        return date_str
    
    def _parse_currency(self, value_str: str) -> float:
        """Converte string de moeda para float com suporte a formato brasileiro"""
        if not value_str:
            return 0.0
        
        # Remove símbolos, espaços e caracteres especiais
        clean_value = re.sub(r'[R$\s]', '', value_str.strip())
        
        # Lida com formato brasileiro (ex: 3.000,00)
        if '.' in clean_value and ',' in clean_value:
            # Formato brasileiro: 3.000,00 -> 3000.00
            parts = clean_value.rsplit(',', 1)  # Separa na última vírgula
            if len(parts) == 2:
                integer_part = parts[0].replace('.', '')  # Remove pontos de milhares
                decimal_part = parts[1]
                clean_value = f"{integer_part}.{decimal_part}"
        elif ',' in clean_value and '.' not in clean_value:
            # Apenas vírgula decimal: 750,00 -> 750.00
            clean_value = clean_value.replace(',', '.')
        elif clean_value.count('.') == 1:
            # Apenas ponto: pode ser decimal (750.00) ou milhar (3.000)
            parts = clean_value.split('.')
            if len(parts[1]) <= 2:  # Provavelmente decimal
                pass  # Mantém como está
            else:  # Provavelmente separador de milhares
                clean_value = clean_value.replace('.', '')
        
        try:
            return float(clean_value)
        except ValueError:
            self.logger.warning(f"Não foi possível converter valor monetário: '{value_str}' -> '{clean_value}'")
            return 0.0
    
    def _extract_items_from_text(self, text: str, default_cfop: str, default_ncm: str, total_value: float) -> List[ItemModel]:
        """Extrai itens reais do texto OCR"""
        itens = []
        
        # Procura por descrição, quantidade e valor unitário no texto
        descricao_match = re.search(r'(?:DESCRI[ÇC][ÃA]O|Descri[çc][ãa]o)\s*:?\s*([^\n\r]+)', text, re.IGNORECASE)
        quantidade_match = re.search(r'(?:QUANTIDADE|Quantidade)\s*:?\s*([\d\.,]+)', text, re.IGNORECASE)
        valor_unitario_match = re.search(r'(?:VALOR\s+UNIT[ÁA]RIO|Valor\s+Unit[áa]rio)\s*:?\s*R?\$?\s*([\d\.,]+)', text, re.IGNORECASE)
        
        if descricao_match:
            descricao = descricao_match.group(1).strip()
            quantidade = 1.0
            valor_unitario = total_value
            
            # Extrai quantidade se encontrada
            if quantidade_match:
                try:
                    quantidade = float(quantidade_match.group(1).replace(',', '.'))
                except ValueError:
                    quantidade = 1.0
            
            # Extrai valor unitário se encontrado
            if valor_unitario_match:
                valor_unitario = self._parse_currency(valor_unitario_match.group(1))
            
            # Calcula valor unitário se temos quantidade e valor total
            if quantidade > 0 and total_value > 0 and not valor_unitario_match:
                valor_unitario = total_value / quantidade
            
            # Cria item com dados extraídos
            item = ItemModel(
                descricao=descricao,
                quantidade=quantidade,
                valor_unitario=valor_unitario,
                cfop_item=default_cfop,
                ncm=default_ncm,
                cst="00"
            )
            itens.append(item)
        
        # Se não conseguiu extrair nenhum item, cria um genérico
        if not itens:
            itens.append(ItemModel(
                descricao="Item extraído via OCR",
                quantidade=1.0,
                valor_unitario=total_value,
                cfop_item=default_cfop,
                ncm=default_ncm,
                cst="00"
            ))
        
        return itens

    async def _verify_and_enhance_with_llm(self, documento: DocumentoFiscalModel, images: List[Image.Image], ocr_text: str) -> DocumentoFiscalModel:
        """Verifica se o documento está completo e usa LLM para preencher lacunas"""
        
        # Verifica se há informações críticas faltando
        is_incomplete = self._is_document_incomplete(documento)
        
        if is_incomplete and self.image_processor:
            self.logger.info("Documento incompleto detectado. Acionando LLM para complementar informações...")
            
            try:
                # Usa a primeira página do PDF como imagem para a LLM
                enhanced_documento = await self._enhance_with_llm(documento, images[0], ocr_text)
                enhanced_documento._llm_enhanced = True  # Marca que foi melhorado pela LLM
                
                self.logger.info("Documento aprimorado com sucesso pela LLM")
                return enhanced_documento
                
            except Exception as e:
                self.logger.warning(f"Falha no aprimoramento LLM: {str(e)}. Usando dados do OCR.")
                return documento
        else:
            if not self.image_processor:
                self.logger.debug("LLM não disponível. Usando apenas dados do OCR.")
            else:
                self.logger.debug("Documento completo pelo OCR. LLM não necessária.")
            return documento

    def _is_document_incomplete(self, documento: DocumentoFiscalModel) -> bool:
        """Verifica se o documento tem informações críticas faltando"""
        
        critical_fields_missing = 0
        total_critical_fields = 0
        
        # Campos críticos para verificar
        checks = [
            ("valor_total", documento.valor_total == 0.0),
            ("numero_documento", not documento.numero_documento or documento.numero_documento == ""),
            ("data_emissao", not documento.data_emissao or documento.data_emissao == ""),
            ("cfop", not documento.cfop or documento.cfop == ""),
            ("emitente", not documento.emitente or documento.emitente == ""),
            ("itens_genericos", len(documento.itens) == 1 and documento.itens[0].descricao == "Item extraído via OCR")
        ]
        
        for field_name, is_missing in checks:
            total_critical_fields += 1
            if is_missing:
                critical_fields_missing += 1
                self.logger.debug(f"Campo crítico faltando/inadequado: {field_name}")
        
        # Considera incompleto se mais de 30% dos campos críticos estão faltando
        incompleteness_ratio = critical_fields_missing / total_critical_fields
        is_incomplete = incompleteness_ratio > 0.3
        
        self.logger.debug(f"Análise de completude: {critical_fields_missing}/{total_critical_fields} campos faltando ({incompleteness_ratio:.1%})")
        
        return is_incomplete

    async def _enhance_with_llm(self, base_documento: DocumentoFiscalModel, image: Image.Image, ocr_text: str) -> DocumentoFiscalModel:
        """Usa LLM Vision para extrair/validar informações do documento"""
        
        # Converte imagem para base64
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        base64_image = base64.b64encode(img_byte_arr).decode('utf-8')
        
        # Cria prompt inteligente baseado no que está faltando
        missing_fields = self._identify_missing_fields(base_documento)
        
        prompt = self._create_enhancement_prompt(base_documento, missing_fields, ocr_text)
        
        # Converte imagem para bytes sem arquivo temporário
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_content = img_byte_arr.getvalue()
        
        # Chama LLM Vision usando o método process padrão
        documento_llm = await self.image_processor.process(img_content, 'png')
        
        # Mescla dados do OCR com dados da LLM
        enhanced_documento = self._merge_document_data(base_documento, documento_llm.dict())
        return enhanced_documento

    def _identify_missing_fields(self, documento: DocumentoFiscalModel) -> List[str]:
        """Identifica quais campos estão faltando ou inadequados"""
        missing = []
        
        if documento.valor_total == 0.0:
            missing.append("valor_total")
        if not documento.numero_documento:
            missing.append("numero_documento")
        if not documento.data_emissao:
            missing.append("data_emissao")
        if not documento.cfop:
            missing.append("cfop")
        if not documento.emitente:
            missing.append("emitente")
        if not documento.destinatario:
            missing.append("destinatario")
        if len(documento.itens) == 1 and documento.itens[0].descricao == "Item extraído via OCR":
            missing.append("itens_detalhados")
        
        return missing

    def _create_enhancement_prompt(self, base_documento: DocumentoFiscalModel, missing_fields: List[str], ocr_text: str) -> str:
        """Cria prompt direcionado para completar informações faltantes"""
        
        prompt = """Analise este documento fiscal brasileiro e extraia/valide as seguintes informações que estão faltando ou incompletas:

DADOS JÁ EXTRAÍDOS VIA OCR (para referência):
"""
        
        # Adiciona dados já extraídos
        prompt += f"- Número: {base_documento.numero_documento or 'NÃO ENCONTRADO'}\n"
        prompt += f"- Valor Total: R$ {base_documento.valor_total}\n"
        prompt += f"- Data: {base_documento.data_emissao or 'NÃO ENCONTRADA'}\n"
        prompt += f"- CFOP: {base_documento.cfop or 'NÃO ENCONTRADO'}\n"
        prompt += f"- Emitente: {base_documento.emitente or 'NÃO ENCONTRADO'}\n"
        
        prompt += f"\nCAMPOS QUE PRECISAM SER VALIDADOS/COMPLETADOS: {', '.join(missing_fields)}\n"
        
        prompt += f"\nTEXTO OCR (para referência):\n{ocr_text[:500]}...\n"
        
        prompt += """
INSTRUÇÕES:
1. Valide e corrija os dados já extraídos se necessário
2. Complete as informações faltantes observando a imagem
3. Para itens, extraia TODOS os produtos/serviços visíveis
4. Mantenha valores monetários no formato brasileiro (use . para milhares e , para decimais)
5. Retorne APENAS dados reais visíveis no documento

Retorne em JSON com a estrutura de nota fiscal brasileira."""
        
        return prompt

    def _merge_document_data(self, base_documento: DocumentoFiscalModel, llm_data) -> DocumentoFiscalModel:
        """Mescla dados do OCR com dados da LLM de forma inteligente"""
        
        # Converte DocumentoFiscalModel para dict se necessário
        if hasattr(llm_data, 'dict'):
            llm_dict = llm_data.dict()
        elif isinstance(llm_data, dict):
            llm_dict = llm_data
        else:
            # Se é um DocumentoFiscalModel, usa os atributos diretamente
            llm_dict = {
                'valor_total': llm_data.valor_total,
                'numero_documento': llm_data.numero_documento,
                'data_emissao': llm_data.data_emissao,
                'cfop': llm_data.cfop,
                'emitente': llm_data.emitente,
                'destinatario': llm_data.destinatario,
                'itens': [item.dict() for item in llm_data.itens] if llm_data.itens else [],
                'impostos': llm_data.impostos.dict() if llm_data.impostos else {}
            }
        
        # Prioriza dados da LLM para campos críticos se eles foram melhorados
        valor_total = llm_dict.get('valor_total', base_documento.valor_total)
        if isinstance(valor_total, str):
            valor_total = self._parse_currency(valor_total)
        
        numero_documento = llm_dict.get('numero_documento') or base_documento.numero_documento
        data_emissao = llm_dict.get('data_emissao') or base_documento.data_emissao
        cfop = llm_dict.get('cfop') or base_documento.cfop
        emitente = llm_dict.get('emitente') or base_documento.emitente
        destinatario = llm_dict.get('destinatario') or base_documento.destinatario
        
        # Mescla itens - prioriza LLM se trouxe itens melhores
        llm_itens = llm_dict.get('itens', [])
        if llm_itens and len(llm_itens) > 0:
            # Se LLM trouxe itens detalhados, usa eles
            itens = []
            for item_data in llm_itens:
                if isinstance(item_data, dict):
                    item = ItemModel(
                        descricao=item_data.get('descricao', 'Item'),
                        quantidade=float(item_data.get('quantidade', 1.0)),
                        valor_unitario=self._parse_currency(str(item_data.get('valor_unitario', 0))),
                        cfop_item=item_data.get('cfop_item') or cfop,
                        ncm=item_data.get('ncm') or base_documento.ncm,
                        cst=item_data.get('cst', '00')
                    )
                    itens.append(item)
        else:
            # Mantém itens do OCR
            itens = base_documento.itens
        
        # Mescla impostos
        llm_impostos = llm_dict.get('impostos', {})
        if llm_impostos:
            impostos = ImpostosModel(
                icms_valor=self._parse_currency(str(llm_impostos.get('icms_valor', base_documento.impostos.icms_valor if base_documento.impostos else 0))),
                pis_valor=self._parse_currency(str(llm_impostos.get('pis_valor', base_documento.impostos.pis_valor if base_documento.impostos else 0))),
                cofins_valor=self._parse_currency(str(llm_impostos.get('cofins_valor', base_documento.impostos.cofins_valor if base_documento.impostos else 0))),
                iss_valor=llm_impostos.get('iss_valor') if llm_impostos.get('iss_valor') else (base_documento.impostos.iss_valor if base_documento.impostos else None),
                icms_base=valor_total,
                pis_base=valor_total,
                cofins_base=valor_total
            )
        else:
            impostos = base_documento.impostos
        
        # Cria documento mesclado
        return DocumentoFiscalModel(
            documento=base_documento.documento,
            cfop=cfop,
            cst=base_documento.cst,
            forma_pagamento=base_documento.forma_pagamento,
            ncm=llm_dict.get('ncm') or base_documento.ncm,
            valor_total=valor_total,
            data_emissao=data_emissao,
            emitente=emitente,
            destinatario=destinatario,
            moeda=base_documento.moeda,
            numero_documento=numero_documento,
            serie=llm_dict.get('serie') or base_documento.serie,
            chave_nfe=llm_dict.get('chave_nfe') or base_documento.chave_nfe,
            impostos=impostos,
            itens=itens
        )

    def _extract_taxes_from_text(self, text: str, valor_total: float) -> ImpostosModel:
        """Extrai impostos do texto OCR ou estima baseado no valor total"""
        
        # Patterns para extrair valores de impostos
        tax_patterns = {
            'icms': r'ICMS\s*:?\s*R?\$?\s*([\d\.,]+)',
            'pis': r'PIS\s*:?\s*R?\$?\s*([\d\.,]+)',
            'cofins': r'COFINS\s*:?\s*R?\$?\s*([\d\.,]+)',
            'iss': r'ISS\s*:?\s*R?\$?\s*([\d\.,]+)'
        }
        
        # Extrai valores dos impostos do texto
        tax_values = {}
        for tax_name, pattern in tax_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tax_values[tax_name] = self._parse_currency(match.group(1))
        
        # Se encontrou impostos no texto, usa os valores extraídos
        if tax_values:
            return ImpostosModel(
                icms_valor=tax_values.get('icms', 0.0),
                pis_valor=tax_values.get('pis', 0.0),
                cofins_valor=tax_values.get('cofins', 0.0),
                iss_valor=tax_values.get('iss', 0.0) if 'iss' in tax_values else None,
                # Estima bases de cálculo baseadas nos valores
                icms_base=tax_values.get('icms', 0.0) / 0.12 if tax_values.get('icms', 0.0) > 0 else valor_total,
                pis_base=valor_total,
                cofins_base=valor_total
            )
        else:
            # Fallback para estimativa se não encontrou impostos no texto
            return self._estimate_taxes(valor_total)

    def _estimate_taxes(self, valor_total: float) -> ImpostosModel:
        """Estima impostos baseado no valor total (aproximação)"""
        # Estimativas baseadas em alíquotas típicas
        icms_aliquota = 0.12  # 12%
        pis_aliquota = 0.0165  # 1.65%
        cofins_aliquota = 0.076  # 7.6%
        
        icms_base = valor_total
        icms_valor = valor_total * icms_aliquota
        pis_valor = valor_total * pis_aliquota
        cofins_valor = valor_total * cofins_aliquota
        
        return ImpostosModel(
            icms_base=icms_base,
            icms_valor=icms_valor,
            pis_valor=pis_valor,
            cofins_valor=cofins_valor,
            iss_valor=None
        )

