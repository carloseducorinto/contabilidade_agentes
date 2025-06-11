"""
Processador de documentos XML (NF-e)
"""
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from ..models import DocumentoFiscalModel, ImpostosModel, ItemModel
from ..exceptions import XMLProcessingError
from ..config import get_settings
from ..logging_config import get_logger, log_operation_start, log_operation_success, log_operation_error

settings = get_settings()
logger = get_logger("XMLProcessor")


class XMLProcessor:
    """Processador especializado para documentos XML de NF-e"""
    
    def __init__(self):
        self.logger = logger
        self.logger.info("XMLProcessor inicializado")
    
    def process(self, xml_content: bytes) -> DocumentoFiscalModel:
        """
        Processa um arquivo XML de NF-e e retorna dados estruturados
        
        Args:
            xml_content: Conteúdo do arquivo XML em bytes
            
        Returns:
            DocumentoFiscalModel com dados estruturados
            
        Raises:
            XMLProcessingError: Se houver erro no processamento
        """
        operation_id = log_operation_start(
            "xml_nfe_processing",
            agent="XMLProcessor",
            xml_size=len(xml_content)
        )
        self.logger.info(f"Iniciando processamento de XML, tamanho: {len(xml_content)} bytes")
        
        try:
            # Parse do XML
            root = ET.fromstring(xml_content)
            
            # Define namespaces
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            
            # Encontra o elemento infNFe
            inf_nfe = root.find('.//nfe:infNFe', ns)
            if inf_nfe is None:
                self.logger.error("Elemento infNFe não encontrado no XML")
                raise XMLProcessingError("Elemento infNFe não encontrado no XML")
            
            # Extrai dados básicos
            ide = inf_nfe.find('nfe:ide', ns)
            if ide is None:
                self.logger.error("Elemento ide não encontrado no XML")
                raise XMLProcessingError("Elemento ide não encontrado no XML")
            
            numero_nf = ide.find('nfe:nNF', ns).text if ide.find('nfe:nNF', ns) is not None else ""
            serie_nf = ide.find('nfe:serie', ns).text if ide.find('nfe:serie', ns) is not None else ""
            data_emissao = ide.find('nfe:dhEmi', ns).text if ide.find('nfe:dhEmi', ns) is not None else ""
            
            # Extrai dados do emitente
            emit = inf_nfe.find('nfe:emit', ns)
            emitente_cnpj = ""
            if emit is not None:
                cnpj_elem = emit.find('nfe:CNPJ', ns)
                if cnpj_elem is not None:
                    emitente_cnpj = cnpj_elem.text.replace('.', '').replace('/', '').replace('-', '')
            
            # Extrai dados do destinatário
            dest = inf_nfe.find('nfe:dest', ns)
            destinatario_cnpj = ""
            if dest is not None:
                cnpj_elem = dest.find('nfe:CNPJ', ns)
                if cnpj_elem is not None:
                    destinatario_cnpj = cnpj_elem.text.replace('.', '').replace('/', '').replace('-', '')
            
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
            
            self.logger.info(f"XML processado com sucesso: número {numero_nf}, valor {valor_total}")
            log_operation_success(
                operation_id,
                agent="XMLProcessor",
                xml_size=len(xml_content),
                numero_documento=numero_nf,
                valor_total=valor_total,
                items_count=len(itens),
                emitente=emitente_cnpj
            )
            
            return documento
            
        except ET.ParseError as e:
            self.logger.error(f"Erro de parse XML: {str(e)}", exc_info=True)
            log_operation_error(operation_id, f"Erro de parse XML: {str(e)}", agent="XMLProcessor")
            raise XMLProcessingError(f"Erro de parse XML: {str(e)}")
        except Exception as e:
            self.logger.error(f"Erro no processamento XML: {str(e)}", exc_info=True)
            log_operation_error(operation_id, f"Erro no processamento XML: {str(e)}", agent="XMLProcessor")
            raise XMLProcessingError(f"Erro no processamento XML: {str(e)}")
    
    def _extract_impostos(self, total_element, ns: Dict[str, str]) -> ImpostosModel:
        """Extrai informações de impostos do XML"""
        if total_element is None:
            self.logger.warning("Elemento total (ICMSTot) não encontrado no XML. Impostos zerados.")
            return ImpostosModel(
                icms_base=0.0,
                icms_valor=0.0,
                pis_valor=0.0,
                cofins_valor=0.0,
                iss_valor=None
            )
        
        # Extrai valores de impostos
        icms_base = float(total_element.find('nfe:vBC', ns).text) if total_element.find('nfe:vBC', ns) is not None else 0.0
        icms_valor = float(total_element.find('nfe:vICMS', ns).text) if total_element.find('nfe:vICMS', ns) is not None else 0.0
        pis_valor = float(total_element.find('nfe:vPIS', ns).text) if total_element.find('nfe:vPIS', ns) is not None else 0.0
        cofins_valor = float(total_element.find('nfe:vCOFINS', ns).text) if total_element.find('nfe:vCOFINS', ns) is not None else 0.0
        
        return ImpostosModel(
            icms_base=icms_base,
            icms_valor=icms_valor,
            pis_valor=pis_valor,
            cofins_valor=cofins_valor,
            iss_valor=None  # ISS não é comum em NF-e
        )
    
    def _extract_itens(self, inf_nfe, ns: Dict[str, str]) -> List[ItemModel]:
        """Extrai itens do XML"""
        itens = []
        
        # Busca todos os itens (det)
        for det in inf_nfe.findall('nfe:det', ns):
            prod = det.find('nfe:prod', ns)
            if prod is not None:
                # Dados básicos do produto
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
                        for icms_child in icms:
                            cst_elem = icms_child.find('nfe:CST', ns)
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
        
        # Se não encontrou itens, cria um item genérico
        if not itens:
            self.logger.warning("Nenhum item encontrado no XML. Adicionando item genérico.")
        
        return itens

