import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
import json
import io

from app.main import app
from app.models.document_models import ProcessingResult
from app.models.classification_models import ClassificationOutput

@pytest.fixture(scope="module")
async def test_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def mock_document_service_process_document():
    with patch("app.services.async_document_service.AsyncDocumentService.process_document", new_callable=AsyncMock) as mock_method:
        mock_method.return_value = ProcessingResult(
            document_id="mock_doc_id",
            document_type="xml",
            extracted_data={
                "chave_nfe": "mock_chave",
                "valor_total": 100.00,
                "itens": [{"descricao": "Serviço de Teste"}]
            },
            success=True,
            message="Documento processado com sucesso."
        )
        yield mock_method

@pytest.fixture
def mock_classification_agent_classify_document():
    with patch("app.classification_agent.ClassificationAgent.classify_document", new_callable=AsyncMock) as mock_method:
        mock_method.return_value = ClassificationOutput(
            conta_contabil="Receita de Serviços",
            centro_de_custo="Vendas",
            tipo_lancamento="Venda",
            justificativa="Classificado como serviço de teste.",
            document_id="mock_doc_id",
            document_type="xml"
        )
        yield mock_method

@pytest.mark.asyncio
async def test_process_document_full_flow_success(test_client, mock_document_service_process_document, mock_classification_agent_classify_document):
    file_content = b"<nfe>...</nfe>"
    files = {"file": ("test.xml", io.BytesIO(file_content), "application/xml")}

    response = await test_client.post("/process-document", files=files)

    assert response.status_code == 200
    response_data = response.json()

    assert response_data["success"] is True
    assert response_data["document_id"] == "mock_doc_id"
    assert response_data["document_type"] == "xml"
    assert "extracted_data" in response_data
    assert "classification_data" in response_data
    assert response_data["classification_data"]["conta_contabil"] == "Receita de Serviços"
    assert response_data["message"] == "Documento processado e classificado com sucesso."

    mock_document_service_process_document.assert_called_once()
    mock_classification_agent_classify_document.assert_called_once()

@pytest.mark.asyncio
async def test_process_document_extraction_failure(test_client, mock_document_service_process_document, mock_classification_agent_classify_document):
    mock_document_service_process_document.return_value = ProcessingResult(
        document_id="",
        document_type="",
        extracted_data={},
        success=False,
        error="Erro na extração de dados."
    )

    file_content = b"<nfe>...</nfe>"
    files = {"file": ("test.xml", io.BytesIO(file_content), "application/xml")}

    response = await test_client.post("/process-document", files=files)

    assert response.status_code == 422
    response_data = response.json()
    assert response_data["detail"] == "Erro na extração de dados."
    mock_document_service_process_document.assert_called_once()
    mock_classification_agent_classify_document.assert_not_called()

@pytest.mark.asyncio
async def test_process_document_classification_failure(test_client, mock_document_service_process_document, mock_classification_agent_classify_document):
    mock_classification_agent_classify_document.side_effect = Exception("Erro na classificação LLM.")

    file_content = b"<nfe>...</nfe>"
    files = {"file": ("test.xml", io.BytesIO(file_content), "application/xml")}

    response = await test_client.post("/process-document", files=files)

    assert response.status_code == 500 # Erro interno do servidor
    response_data = response.json()
    assert "Erro interno do servidor" in response_data["detail"]
    mock_document_service_process_document.assert_called_once()
    mock_classification_agent_classify_document.assert_called_once()


