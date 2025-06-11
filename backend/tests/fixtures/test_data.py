"""
Fixtures para testes - dados de exemplo e mocks
"""
import pytest
from typing import Dict, Any
import json
from unittest.mock import Mock, AsyncMock

@pytest.fixture
def sample_xml_nfe():
    """XML de NF-e de exemplo para testes"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
    <NFe>
        <infNFe Id="NFe35200714200166000187550010000000046550000046">
            <ide>
                <cUF>35</cUF>
                <cNF>55000004</cNF>
                <natOp>Venda</natOp>
                <mod>55</mod>
                <serie>1</serie>
                <nNF>46</nNF>
                <dhEmi>2020-07-01T10:00:00-03:00</dhEmi>
                <tpNF>1</tpNF>
                <idDest>1</idDest>
                <cMunFG>3550308</cMunFG>
                <tpImp>1</tpImp>
                <tpEmis>1</tpEmis>
                <cDV>5</cDV>
                <tpAmb>2</tpAmb>
                <finNFe>1</finNFe>
                <indFinal>1</indFinal>
                <indPres>1</indPres>
            </ide>
            <emit>
                <CNPJ>14200166000187</CNPJ>
                <xNome>EMPRESA TESTE LTDA</xNome>
                <enderEmit>
                    <xLgr>RUA TESTE</xLgr>
                    <nro>123</nro>
                    <xBairro>CENTRO</xBairro>
                    <cMun>3550308</cMun>
                    <xMun>SAO PAULO</xMun>
                    <UF>SP</UF>
                    <CEP>01000000</CEP>
                </enderEmit>
                <IE>123456789</IE>
            </emit>
            <dest>
                <CNPJ>11222333000144</CNPJ>
                <xNome>CLIENTE TESTE LTDA</xNome>
                <enderDest>
                    <xLgr>AV CLIENTE</xLgr>
                    <nro>456</nro>
                    <xBairro>VILA TESTE</xBairro>
                    <cMun>3550308</cMun>
                    <xMun>SAO PAULO</xMun>
                    <UF>SP</UF>
                    <CEP>02000000</CEP>
                </enderDest>
                <IE>987654321</IE>
            </dest>
            <det nItem="1">
                <prod>
                    <cProd>001</cProd>
                    <cEAN></cEAN>
                    <xProd>PRODUTO TESTE</xProd>
                    <NCM>12345678</NCM>
                    <CFOP>5102</CFOP>
                    <uCom>UN</uCom>
                    <qCom>1.0000</qCom>
                    <vUnCom>100.0000</vUnCom>
                    <vProd>100.00</vProd>
                    <cEANTrib></cEANTrib>
                    <uTrib>UN</uTrib>
                    <qTrib>1.0000</qTrib>
                    <vUnTrib>100.0000</vUnTrib>
                </prod>
                <imposto>
                    <ICMS>
                        <ICMS00>
                            <orig>0</orig>
                            <CST>00</CST>
                            <modBC>3</modBC>
                            <vBC>100.00</vBC>
                            <pICMS>18.00</pICMS>
                            <vICMS>18.00</vICMS>
                        </ICMS00>
                    </ICMS>
                    <PIS>
                        <PISAliq>
                            <CST>01</CST>
                            <vBC>100.00</vBC>
                            <pPIS>1.65</pPIS>
                            <vPIS>1.65</vPIS>
                        </PISAliq>
                    </PIS>
                    <COFINS>
                        <COFINSAliq>
                            <CST>01</CST>
                            <vBC>100.00</vBC>
                            <pCOFINS>7.60</pCOFINS>
                            <vCOFINS>7.60</vCOFINS>
                        </COFINSAliq>
                    </COFINS>
                </imposto>
            </det>
            <total>
                <ICMSTot>
                    <vBC>100.00</vBC>
                    <vICMS>18.00</vICMS>
                    <vICMSDeson>0.00</vICMSDeson>
                    <vFCP>0.00</vFCP>
                    <vBCST>0.00</vBCST>
                    <vST>0.00</vST>
                    <vFCPST>0.00</vFCPST>
                    <vFCPSTRet>0.00</vFCPSTRet>
                    <vProd>100.00</vProd>
                    <vFrete>0.00</vFrete>
                    <vSeg>0.00</vSeg>
                    <vDesc>0.00</vDesc>
                    <vII>0.00</vII>
                    <vIPI>0.00</vIPI>
                    <vIPIDevol>0.00</vIPIDevol>
                    <vPIS>1.65</vPIS>
                    <vCOFINS>7.60</vCOFINS>
                    <vOutro>0.00</vOutro>
                    <vNF>100.00</vNF>
                </ICMSTot>
            </total>
        </infNFe>
    </NFe>
</nfeProc>"""

@pytest.fixture
def expected_xml_result():
    """Resultado esperado do processamento XML"""
    return {
        "documento": "nfe",
        "numero_documento": "46",
        "serie": "1",
        "data_emissao": "2020-07-01",
        "chave_nfe": "NFe35200714200166000187550010000000046550000046",
        "emitente": "EMPRESA TESTE LTDA",
        "destinatario": "CLIENTE TESTE LTDA",
        "valor_total": 100.00,
        "moeda": "BRL",
        "cfop": "5102",
        "ncm": "12345678",
        "cst": "00",
        "impostos": {
            "icms_base": 100.00,
            "icms_valor": 18.00,
            "icms_aliquota": 18.00,
            "pis_base": 100.00,
            "pis_valor": 1.65,
            "pis_aliquota": 1.65,
            "cofins_base": 100.00,
            "cofins_valor": 7.60,
            "cofins_aliquota": 7.60,
            "iss_valor": 0.0,
            "iss_base": 0.0,
            "iss_aliquota": 0.0
        },
        "itens": [
            {
                "codigo": "001",
                "descricao": "PRODUTO TESTE",
                "ncm": "12345678",
                "cfop": "5102",
                "quantidade": 1.0,
                "valor_unitario": 100.0,
                "valor_total": 100.0,
                "unidade": "UN"
            }
        ]
    }

@pytest.fixture
def sample_pdf_content():
    """Conteúdo de PDF simulado para testes"""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(NF-e Teste) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000206 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n299\n%%EOF"

@pytest.fixture
def sample_image_content():
    """Conteúdo de imagem simulado para testes"""
    # PNG mínimo válido (1x1 pixel transparente)
    return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'

@pytest.fixture
def mock_openai_response():
    """Mock da resposta do OpenAI para testes"""
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "documento": "nfe",
                        "numero_documento": "123",
                        "serie": "1",
                        "data_emissao": "2024-01-01",
                        "emitente": "EMPRESA TESTE",
                        "destinatario": "CLIENTE TESTE",
                        "valor_total": 150.00,
                        "cfop": "5102",
                        "impostos": {
                            "icms_valor": 27.00,
                            "pis_valor": 2.48,
                            "cofins_valor": 11.40
                        },
                        "itens": [
                            {
                                "descricao": "PRODUTO TESTE",
                                "quantidade": 1.0,
                                "valor_unitario": 150.0,
                                "valor_total": 150.0
                            }
                        ]
                    })
                }
            }
        ]
    }

@pytest.fixture
def mock_tesseract_output():
    """Mock da saída do Tesseract OCR para testes"""
    return """
    NOTA FISCAL ELETRÔNICA
    NF-e: 123
    Série: 1
    Data: 01/01/2024
    
    EMITENTE: EMPRESA TESTE LTDA
    CNPJ: 12.345.678/0001-90
    
    DESTINATÁRIO: CLIENTE TESTE LTDA
    CNPJ: 98.765.432/0001-10
    
    PRODUTO: PRODUTO TESTE
    QUANTIDADE: 1,00
    VALOR UNITÁRIO: R$ 150,00
    VALOR TOTAL: R$ 150,00
    
    CFOP: 5102
    
    IMPOSTOS:
    ICMS: R$ 27,00
    PIS: R$ 2,48
    COFINS: R$ 11,40
    
    VALOR TOTAL DA NOTA: R$ 150,00
    """

@pytest.fixture
def mock_file_upload():
    """Mock de arquivo upload para testes"""
    class MockFile:
        def __init__(self, filename: str, content: bytes, content_type: str):
            self.filename = filename
            self.content = content
            self.content_type = content_type
            
        def read(self):
            return self.content
            
        def seek(self, position):
            pass
    
    return MockFile

@pytest.fixture
def mock_async_client():
    """Mock do cliente assíncrono para testes"""
    mock = AsyncMock()
    mock.chat.completions.create = AsyncMock()
    return mock

@pytest.fixture
def mock_cache():
    """Mock do sistema de cache para testes"""
    cache_data = {}
    
    class MockCache:
        async def get(self, key: str):
            return cache_data.get(key)
        
        async def set(self, key: str, value: Any, ttl: int = 3600):
            cache_data[key] = value
        
        async def delete(self, key: str):
            cache_data.pop(key, None)
        
        async def clear(self):
            cache_data.clear()
        
        def get_stats(self):
            return {
                "hits": 0,
                "misses": 0,
                "hit_rate": 0.0,
                "size": len(cache_data)
            }
    
    return MockCache()

@pytest.fixture
def mock_logger():
    """Mock do logger para testes"""
    return Mock()

@pytest.fixture
def test_config():
    """Configuração de teste"""
    return {
        "openai_api_key": "test-key",
        "environment": "test",
        "log_level": "DEBUG",
        "cache_ttl": 60,
        "max_concurrent_processing": 2,
        "max_batch_size": 5,
        "request_timeout": 30
    }

