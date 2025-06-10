import xml.etree.ElementTree as ET
import json
from typing import Optional, Dict, Any
from datetime import datetime
import re
import io
import tempfile
import os
import base64
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
from .models import DocumentoFiscalModel, ImpostosModel, ItemModel, ProcessingResult
from .logging_config import get_logger, log_operation_start, log_operation_success, log_operation_error

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class DocumentIngestionAgent:
    """
    Agente responsável pela ingestão e processamento de documentos fiscais brasileiros.
    Suporta parsing de NF-e em formato XML e extração de dados estruturados.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.logger = get_logger("DocumentIngestionAgent")
        self.openai_api_key = openai_api_key
        
        # Inicializa cliente OpenAI se disponível
        if openai_api_key and OpenAI:
            self.openai_client = OpenAI(api_key=openai_api_key)
            self.logger.info("Cliente OpenAI inicializado com sucesso")
        else:
            self.openai_client = None
            self.logger.warning("Cliente OpenAI não inicializado - funcionalidade de imagem limitada")
    
    def process_document(self, file_content: bytes, file_type: str) -> ProcessingResult:
        """
        Processa um documento fiscal e retorna dados estruturados
        
        Args:
            file_content: Conteúdo do arquivo em bytes
            file_type: Tipo do arquivo ('xml', 'pdf', ou formatos de imagem)
            
        Returns:
            ProcessingResult com os dados extraídos ou erro
        """
        start_time = datetime.now()
        
        # Log de início do processamento
        log_operation_start(
            "agent_document_processing",
            file_type=file_type,
            file_size=len(file_content),
            agent="DocumentIngestionAgent"
        )
        
        try:
            if file_type.lower() == 'xml':
                result_data = self._process_xml_nfe(file_content)
            elif file_type.lower() == 'pdf':
                result_data = self._process_pdf_nfe(file_content)
            elif file_type.lower() in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                result_data = self._process_image_nfe(file_content, file_type.lower())
            else:
                raise ValueError(f"Tipo de arquivo não suportado: {file_type}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Log de sucesso com detalhes do resultado
            log_operation_success(
                "agent_document_processing",
                execution_time=processing_time,
                file_type=file_type,
                file_size=len(file_content),
                agent="DocumentIngestionAgent",
                document_type=result_data.documento,
                total_value=result_data.valor_total,
                items_count=len(result_data.itens) if result_data.itens else 0,
                emitente=result_data.emitente,
                destinatario=result_data.destinatario
            )
            
            return ProcessingResult(
                success=True,
                data=result_data,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Erro no processamento: {str(e)}"
            
            # Log de erro detalhado
            log_operation_error(
                "agent_document_processing",
                e,
                execution_time=processing_time,
                file_type=file_type,
                file_size=len(file_content),
                agent="DocumentIngestionAgent"
            )
            
            return ProcessingResult(
                success=False,
                error_message=error_msg,
                processing_time=processing_time
            )
    
    def _process_xml_nfe(self, xml_content: bytes) -> DocumentoFiscalModel:
        """
        Processa um arquivo XML de NF-e e extrai dados estruturados
        
        Args:
            xml_content: Conteúdo XML em bytes
            
        Returns:
            DocumentoFiscalModel com dados estruturados
        """
        log_operation_start("xml_nfe_processing", agent="DocumentIngestionAgent", xml_size=len(xml_content))
        
        try:
            # Parse do XML
            root = ET.fromstring(xml_content)
            
            # Namespace da NF-e
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            
            # Busca o elemento infNFe
            inf_nfe = root.find('.//nfe:infNFe', ns)
            if inf_nfe is None:
                raise ValueError("Elemento infNFe não encontrado no XML")
            
            # Extrai dados do emitente
            emit = inf_nfe.find('nfe:emit', ns)
            emitente_cnpj = emit.find('nfe:CNPJ', ns).text if emit is not None and emit.find('nfe:CNPJ', ns) is not None else ""
            
            # Extrai dados do destinatário
            dest = inf_nfe.find('nfe:dest', ns)
            destinatario_cnpj = dest.find('nfe:CNPJ', ns).text if dest is not None and dest.find('nfe:CNPJ', ns) is not None else ""
            
            # Extrai dados da identificação
            ide = inf_nfe.find('nfe:ide', ns)
            numero_nf = ide.find('nfe:nNF', ns).text if ide.find('nfe:nNF', ns) is not None else ""
            serie_nf = ide.find('nfe:serie', ns).text if ide.find('nfe:serie', ns) is not None else ""
            data_emissao = ide.find('nfe:dhEmi', ns).text if ide.find('nfe:dhEmi', ns) is not None else ""
            
            # Formatar data de emissão
            if data_emissao:
                data_emissao = data_emissao.split('T')[0]  # Remove a parte do tempo
            
            # Extrai chave da NF-e
            chave_nfe = inf_nfe.get('Id', '').replace('NFe', '') if inf_nfe.get('Id') else ""
            
            # Extrai dados totais
            total = inf_nfe.find('nfe:total/nfe:ICMSTot', ns)
            valor_total = float(total.find('nfe:vNF', ns).text) if total is not None and total.find('nfe:vNF', ns) is not None else 0.0
            
            # Extrai impostos
            impostos = self._extract_impostos(total, ns)
            
            # Extrai itens
            itens = self._extract_itens(inf_nfe, ns)
            
            # Determina CFOP e NCM principais (do primeiro item)
            cfop_principal = itens[0].cfop_item if itens else ""
            ncm_principal = itens[0].ncm if itens else ""
            cst_principal = itens[0].cst if itens else ""
            
            # Cria o modelo estruturado
            documento = DocumentoFiscalModel(
                documento="nfe",
                cfop=cfop_principal,
                cst=cst_principal,
                forma_pagamento="a_vista",  # Valor padrão, pode ser extraído se disponível
                ncm=ncm_principal,
                valor_total=valor_total,
                data_emissao=data_emissao,
                emitente=emitente_cnpj,
                destinatario=destinatario_cnpj,
                moeda="BRL",
                numero_documento=numero_nf,
                serie=serie_nf,
                chave_nfe=chave_nfe,
                impostos=impostos,
                itens=itens
            )
            
            log_operation_success(
                "xml_nfe_processing",
                agent="DocumentIngestionAgent",
                xml_size=len(xml_content),
                numero_documento=numero_nf,
                valor_total=valor_total,
                items_count=len(itens),
                emitente=emitente_cnpj
            )
            
            return documento
            
        except ET.ParseError as e:
            log_operation_error("xml_nfe_processing", e, agent="DocumentIngestionAgent", xml_size=len(xml_content))
            raise ValueError(f"Erro no parsing do XML: {str(e)}")
        except Exception as e:
            log_operation_error("xml_nfe_processing", e, agent="DocumentIngestionAgent", xml_size=len(xml_content))
            raise ValueError(f"Erro na extração de dados do XML: {str(e)}")
    
    def _extract_impostos(self, total_element, ns: Dict[str, str]) -> ImpostosModel:
        """Extrai informações de impostos do XML"""
        impostos = ImpostosModel()
        
        if total_element is not None:
            # ICMS
            icms_base_elem = total_element.find('nfe:vBC', ns)
            if icms_base_elem is not None:
                impostos.icms_base = float(icms_base_elem.text)
            
            icms_valor_elem = total_element.find('nfe:vICMS', ns)
            if icms_valor_elem is not None:
                impostos.icms_valor = float(icms_valor_elem.text)
            
            # PIS
            pis_elem = total_element.find('nfe:vPIS', ns)
            if pis_elem is not None:
                impostos.pis_valor = float(pis_elem.text)
            
            # COFINS
            cofins_elem = total_element.find('nfe:vCOFINS', ns)
            if cofins_elem is not None:
                impostos.cofins_valor = float(cofins_elem.text)
        
        return impostos
    
    def _extract_itens(self, inf_nfe, ns: Dict[str, str]) -> list[ItemModel]:
        """Extrai itens do XML da NF-e"""
        itens = []
        
        # Busca todos os elementos det (detalhes dos itens)
        det_elements = inf_nfe.findall('nfe:det', ns)
        
        for det in det_elements:
            prod = det.find('nfe:prod', ns)
            if prod is not None:
                # Dados do produto
                descricao = prod.find('nfe:xProd', ns).text if prod.find('nfe:xProd', ns) is not None else ""
                quantidade = float(prod.find('nfe:qCom', ns).text) if prod.find('nfe:qCom', ns) is not None else 0.0
                valor_unitario = float(prod.find('nfe:vUnCom', ns).text) if prod.find('nfe:vUnCom', ns) is not None else 0.0
                ncm = prod.find('nfe:NCM', ns).text if prod.find('nfe:NCM', ns) is not None else ""
                cfop = prod.find('nfe:CFOP', ns).text if prod.find('nfe:CFOP', ns) is not None else ""
                
                # CST do ICMS
                imposto = det.find('nfe:imposto', ns)
                cst = ""
                if imposto is not None:
                    icms = imposto.find('nfe:ICMS', ns)
                    if icms is not None:
                        # Pode ser ICMS00, ICMS10, etc.
                        for child in icms:
                            cst_elem = child.find('nfe:CST', ns)
                            if cst_elem is not None:
                                cst = cst_elem.text
                                break
                
                item = ItemModel(
                    descricao=descricao,
                    quantidade=quantidade,
                    valor_unitario=valor_unitario,
                    cfop_item=cfop,
                    ncm=ncm,
                    cst=cst
                )
                
                itens.append(item)
        
        return itens
    
    def _process_pdf_nfe(self, pdf_content: bytes) -> DocumentoFiscalModel:
        """
        Processa um arquivo PDF de NF-e usando OCR
        
        Args:
            pdf_content: Conteúdo PDF em bytes
            
        Returns:
            DocumentoFiscalModel com dados estruturados
        """
        log_operation_start("pdf_nfe_processing", agent="DocumentIngestionAgent", pdf_size=len(pdf_content))
        
        try:
            # Converte PDF para imagens
            self.logger.info("Convertendo PDF para imagens")
            images = convert_from_bytes(pdf_content, dpi=300)
            
            log_operation_success(
                "pdf_to_images_conversion",
                agent="DocumentIngestionAgent",
                pages_count=len(images),
                pdf_size=len(pdf_content)
            )
            
            # Extrai texto de todas as páginas usando OCR
            self.logger.info(f"Extraindo texto via OCR de {len(images)} páginas")
            full_text = ""
            for i, image in enumerate(images):
                # Configura o Tesseract para português
                custom_config = r'--oem 3 --psm 6 -l por'
                text = pytesseract.image_to_string(image, config=custom_config)
                full_text += text + "\n"
                
                self.logger.info(f"Página {i+1} processada via OCR")
            
            log_operation_success(
                "ocr_text_extraction",
                agent="DocumentIngestionAgent",
                pages_processed=len(images),
                text_length=len(full_text)
            )
            
            # Extrai dados estruturados do texto
            result = self._extract_data_from_text(full_text)
            
            log_operation_success(
                "pdf_nfe_processing",
                agent="DocumentIngestionAgent",
                pdf_size=len(pdf_content),
                pages_count=len(images),
                extracted_text_length=len(full_text)
            )
            
            return result
            
        except Exception as e:
            log_operation_error("pdf_nfe_processing", e, agent="DocumentIngestionAgent", pdf_size=len(pdf_content))
            raise ValueError(f"Erro no processamento de PDF via OCR: {str(e)}")
    
    def _extract_data_from_text(self, text: str) -> DocumentoFiscalModel:
        """
        Extrai dados estruturados do texto extraído via OCR
        
        Args:
            text: Texto extraído do PDF
            
        Returns:
            DocumentoFiscalModel com dados estruturados
        """
        # Normaliza o texto (remove quebras de linha desnecessárias, espaços extras)
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Padrões regex para extrair informações da NF-e
        patterns = {
            'numero_documento': r'(?:N[ºo°]?\s*|NÚMERO\s*|NUM\s*)[:\s]*(\d+)',
            'serie': r'(?:SÉRIE\s*|SER\s*)[:\s]*(\d+)',
            'chave_nfe': r'(\d{44})',
            'data_emissao': r'(?:DATA\s*DE\s*EMISSÃO\s*|EMISSÃO\s*)[:\s]*(\d{2}[\/\-]\d{2}[\/\-]\d{4})',
            'emitente_cnpj': r'(?:CNPJ\s*)[:\s]*(\d{2}\.?\d{3}\.?\d{3}\/?\d{4}\-?\d{2})',
            'destinatario_cnpj': r'(?:DESTINATÁRIO.*?CNPJ\s*)[:\s]*(\d{2}\.?\d{3}\.?\d{3}\/?\d{4}\-?\d{2})',
            'valor_total': r'(?:VALOR\s*TOTAL\s*|TOTAL\s*GERAL\s*|VL\s*TOTAL\s*)[:\s]*R?\$?\s*(\d+[,.]?\d*[,.]?\d{2})',
            'cfop': r'(?:CFOP\s*)[:\s]*(\d{4})',
            'ncm': r'(?:NCM\s*)[:\s]*(\d{8})',
            'cst': r'(?:CST\s*)[:\s]*(\d{2,3})',
            'icms_valor': r'(?:ICMS\s*)[:\s]*R?\$?\s*(\d+[,.]?\d*[,.]?\d{2})',
            'pis_valor': r'(?:PIS\s*)[:\s]*R?\$?\s*(\d+[,.]?\d*[,.]?\d{2})',
            'cofins_valor': r'(?:COFINS\s*)[:\s]*R?\$?\s*(\d+[,.]?\d*[,.]?\d{2})'
        }
        
        # Extrai dados usando regex
        extracted_data = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1)
                # Limpa e formata valores monetários
                if 'valor' in key and value:
                    value = value.replace('.', '').replace(',', '.')
                    try:
                        extracted_data[key] = float(value)
                    except ValueError:
                        extracted_data[key] = 0.0
                # Limpa CNPJs
                elif 'cnpj' in key and value:
                    extracted_data[key] = re.sub(r'[^\d]', '', value)
                # Formata data
                elif 'data' in key and value:
                    # Converte DD/MM/YYYY para YYYY-MM-DD
                    if '/' in value:
                        parts = value.split('/')
                        if len(parts) == 3:
                            extracted_data[key] = f"{parts[2]}-{parts[1]}-{parts[0]}"
                        else:
                            extracted_data[key] = value
                    else:
                        extracted_data[key] = value
                else:
                    extracted_data[key] = value
            else:
                # Valores padrão para campos não encontrados
                if 'valor' in key:
                    extracted_data[key] = 0.0
                else:
                    extracted_data[key] = ""
        
        # Extrai itens (busca por padrões de produtos/serviços)
        itens = self._extract_items_from_text(text)
        
        # Cria modelo de impostos
        impostos = ImpostosModel(
            icms_base=extracted_data.get('valor_total', 0.0),
            icms_valor=extracted_data.get('icms_valor', 0.0),
            pis_valor=extracted_data.get('pis_valor', 0.0),
            cofins_valor=extracted_data.get('cofins_valor', 0.0),
            iss_valor=None
        )
        
        # Cria o modelo estruturado
        documento = DocumentoFiscalModel(
            documento="nfe",
            cfop=extracted_data.get('cfop', ''),
            cst=extracted_data.get('cst', ''),
            forma_pagamento="a_vista",  # Valor padrão
            ncm=extracted_data.get('ncm', ''),
            valor_total=extracted_data.get('valor_total', 0.0),
            data_emissao=extracted_data.get('data_emissao', ''),
            emitente=extracted_data.get('emitente_cnpj', ''),
            destinatario=extracted_data.get('destinatario_cnpj', ''),
            moeda="BRL",
            numero_documento=extracted_data.get('numero_documento', ''),
            serie=extracted_data.get('serie', ''),
            chave_nfe=extracted_data.get('chave_nfe', ''),
            impostos=impostos,
            itens=itens
        )
        
        return documento
    
    def _extract_items_from_text(self, text: str) -> list[ItemModel]:
        """
        Extrai itens/produtos do texto da NF-e
        
        Args:
            text: Texto extraído do PDF
            
        Returns:
            Lista de ItemModel
        """
        itens = []
        
        # Padrão para encontrar seções de itens
        # Busca por padrões como "DESCRIÇÃO", "PRODUTO", "ITEM", etc.
        item_patterns = [
            r'(?:DESCRIÇÃO|PRODUTO|ITEM)\s*[:\s]*([^\n\r]+)',
            r'(\d+)\s+([A-Za-z][^\d\n\r]+?)\s+(\d+[,.]?\d*)\s+(\d+[,.]?\d*[,.]?\d{2})'
        ]
        
        for pattern in item_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                try:
                    if len(match.groups()) >= 4:
                        # Padrão: código, descrição, quantidade, valor
                        descricao = match.group(2).strip()
                        quantidade = float(match.group(3).replace(',', '.'))
                        valor_unitario = float(match.group(4).replace('.', '').replace(',', '.'))
                    else:
                        # Apenas descrição encontrada
                        descricao = match.group(1).strip()
                        quantidade = 1.0
                        valor_unitario = 0.0
                    
                    # Cria item básico
                    item = ItemModel(
                        descricao=descricao,
                        quantidade=quantidade,
                        valor_unitario=valor_unitario,
                        cfop_item="",  # Será preenchido se encontrado no texto
                        ncm="",        # Será preenchido se encontrado no texto
                        cst=""         # Será preenchido se encontrado no texto
                    )
                    
                    itens.append(item)
                    
                except (ValueError, IndexError):
                    continue
        
        # Se não encontrou itens, cria um item genérico
        if not itens:
            itens.append(ItemModel(
                descricao="Item extraído via OCR",
                quantidade=1.0,
                valor_unitario=0.0,
                cfop_item="",
                ncm="",
                cst=""
            ))
        
        return itens


    def _process_image_nfe(self, image_content: bytes, file_type: str) -> DocumentoFiscalModel:
        """
        Processa uma imagem de NF-e usando GPT-4 Vision
        
        Args:
            image_content: Conteúdo da imagem em bytes
            file_type: Tipo do arquivo de imagem
            
        Returns:
            DocumentoFiscalModel com dados estruturados
        """
        log_operation_start(
            "image_nfe_processing", 
            agent="DocumentIngestionAgent", 
            image_size=len(image_content),
            file_type=file_type
        )
        
        if not self.openai_client:
            error = ValueError("OpenAI API key não configurada. Configure OPENAI_API_KEY para usar processamento de imagem.")
            log_operation_error("image_nfe_processing", error, agent="DocumentIngestionAgent")
            raise error
        
        try:
            # Converte a imagem para base64
            base64_image = base64.b64encode(image_content).decode('utf-8')
            
            # Prompt específico para extração de dados de NF-e
            prompt = """
            Analise esta imagem de uma Nota Fiscal Eletrônica (NF-e) brasileira e extraia os seguintes dados em formato JSON:

            {
                "numero_documento": "número da nota fiscal",
                "serie": "série da nota fiscal",
                "chave_nfe": "chave de acesso de 44 dígitos",
                "data_emissao": "data de emissão no formato YYYY-MM-DD",
                "emitente_cnpj": "CNPJ do emitente (apenas números)",
                "emitente_nome": "nome/razão social do emitente",
                "destinatario_cnpj": "CNPJ do destinatário (apenas números)",
                "destinatario_nome": "nome/razão social do destinatário",
                "valor_total": "valor total da nota fiscal (número)",
                "cfop": "código CFOP",
                "ncm": "código NCM",
                "cst": "código CST",
                "icms_valor": "valor do ICMS (número)",
                "pis_valor": "valor do PIS (número)",
                "cofins_valor": "valor do COFINS (número)",
                "itens": [
                    {
                        "descricao": "descrição do produto/serviço",
                        "quantidade": "quantidade (número)",
                        "valor_unitario": "valor unitário (número)",
                        "cfop_item": "CFOP do item",
                        "ncm": "NCM do item",
                        "cst": "CST do item"
                    }
                ]
            }

            IMPORTANTE:
            - Retorne APENAS o JSON válido, sem texto adicional
            - Use valores numéricos para campos monetários e quantidades
            - Para CNPJs, remova pontos, barras e hífens
            - Para datas, use formato YYYY-MM-DD
            - Se algum campo não for encontrado, use string vazia "" ou 0 para números
            - Para itens, inclua todos os produtos/serviços listados na nota
            """
            
            self.logger.info("Enviando imagem para análise via GPT-4 Vision")
            
            # Chama a API do GPT-4 Vision
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Modelo com capacidades de visão
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
                                    "url": f"data:image/{file_type};base64,{base64_image}",
                                    "detail": "high"  # Alta resolução para melhor OCR
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1  # Baixa temperatura para respostas mais consistentes
            )
            
            # Extrai o JSON da resposta
            response_text = response.choices[0].message.content.strip()
            self.logger.info("Resposta recebida do GPT-4 Vision")
            
            log_operation_success(
                "openai_vision_api_call",
                agent="DocumentIngestionAgent",
                image_size=len(image_content),
                response_length=len(response_text),
                model="gpt-4o"
            )
            
            # Remove possíveis marcadores de código se existirem
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            # Parse do JSON
            extracted_data = json.loads(response_text)
            
            # Converte para o modelo estruturado
            result = self._convert_llm_response_to_model(extracted_data)
            
            log_operation_success(
                "image_nfe_processing",
                agent="DocumentIngestionAgent",
                image_size=len(image_content),
                file_type=file_type,
                document_type=result.documento,
                valor_total=result.valor_total,
                items_count=len(result.itens) if result.itens else 0
            )
            
            return result
            
        except json.JSONDecodeError as e:
            log_operation_error("image_nfe_processing", e, agent="DocumentIngestionAgent", image_size=len(image_content), file_type=file_type)
            raise ValueError(f"Resposta inválida do LLM: {str(e)}")
        except Exception as e:
            log_operation_error("image_nfe_processing", e, agent="DocumentIngestionAgent", image_size=len(image_content), file_type=file_type)
            raise ValueError(f"Erro no processamento de imagem via LLM: {str(e)}")
    
    def _convert_llm_response_to_model(self, data: Dict[str, Any]) -> DocumentoFiscalModel:
        """
        Converte a resposta do LLM para o modelo estruturado
        
        Args:
            data: Dados extraídos pelo LLM
            
        Returns:
            DocumentoFiscalModel estruturado
        """
        # Processa itens
        itens = []
        for item_data in data.get('itens', []):
            item = ItemModel(
                descricao=item_data.get('descricao', ''),
                quantidade=float(item_data.get('quantidade', 0)),
                valor_unitario=float(item_data.get('valor_unitario', 0)),
                cfop_item=item_data.get('cfop_item', ''),
                ncm=item_data.get('ncm', ''),
                cst=item_data.get('cst', '')
            )
            itens.append(item)
        
        # Se não há itens, cria um genérico
        if not itens:
            itens.append(ItemModel(
                descricao="Item extraído via LLM Vision",
                quantidade=1.0,
                valor_unitario=float(data.get('valor_total', 0)),
                cfop_item=data.get('cfop', ''),
                ncm=data.get('ncm', ''),
                cst=data.get('cst', '')
            ))
        
        # Cria modelo de impostos
        impostos = ImpostosModel(
            icms_base=float(data.get('valor_total', 0)),
            icms_valor=float(data.get('icms_valor', 0)),
            pis_valor=float(data.get('pis_valor', 0)),
            cofins_valor=float(data.get('cofins_valor', 0)),
            iss_valor=None
        )
        
        # Cria o modelo principal
        documento = DocumentoFiscalModel(
            documento="nfe",
            cfop=data.get('cfop', ''),
            cst=data.get('cst', ''),
            forma_pagamento="a_vista",  # Valor padrão
            ncm=data.get('ncm', ''),
            valor_total=float(data.get('valor_total', 0)),
            data_emissao=data.get('data_emissao', ''),
            emitente=data.get('emitente_cnpj', ''),
            destinatario=data.get('destinatario_cnpj', ''),
            moeda="BRL",
            numero_documento=data.get('numero_documento', ''),
            serie=data.get('serie', ''),
            chave_nfe=data.get('chave_nfe', ''),
            impostos=impostos,
            itens=itens
        )
        
        return documento

