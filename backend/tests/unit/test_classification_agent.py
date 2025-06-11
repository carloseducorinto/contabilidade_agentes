import pytest
import json
from unittest.mock import AsyncMock, patch
from app.classification_agent import ClassificationAgent
from app.models.document_models import DocumentProcessed
from app.models.classification_models import ClassificationOutput
from app.exceptions.custom_exceptions import ClassificationError, LLMIntegrationError

@pytest.fixture
def mock_openai_client():
    with patch('app.classification_agent.OpenAI') as mock_openai:
        mock_client = mock_openai.return_value
        mock_client.chat.completions.create = AsyncMock()
        yield mock_client

@pytest.fixture
def sample_document_processed():
    return DocumentProcessed(
        document_id="test_doc_123",
        document_type="xml",
        extracted_data={
            "chave_nfe": "12345",
            "valor_total": 100.00,
            "itens": [{"descricao": "Serviço de consultoria"}]
        }
    )

@pytest.fixture
def mock_llm_response_content():
    return json.dumps({
        "conta_contabil": "Receita de Vendas",
        "centro_de_custo": "Vendas",
        "tipo_lancamento": "Venda de Serviço",
        "justificativa": "Serviço de consultoria prestado."
    })

@pytest.mark.asyncio
async def test_classify_document_success(mock_openai_client, sample_document_processed, mock_llm_response_content):
    mock_openai_client.chat.completions.create.return_value.choices = [
        AsyncMock(message=AsyncMock(content=mock_llm_response_content))
    ]
    agent = ClassificationAgent()
    result = await agent.classify_document(sample_document_processed)

    assert isinstance(result, ClassificationOutput)
    assert result.conta_contabil == "Receita de Vendas"
    assert result.document_id == sample_document_processed.document_id
    mock_openai_client.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_classify_document_llm_integration_error(mock_openai_client, sample_document_processed):
    mock_openai_client.chat.completions.create.side_effect = Exception("LLM API error")
    agent = ClassificationAgent()

    with pytest.raises(ClassificationError) as excinfo:
        await agent.classify_document(sample_document_processed)
    assert "Falha na comunicação com o serviço de classificação" in str(excinfo.value)

@pytest.mark.asyncio
async def test_classify_document_invalid_llm_response(mock_openai_client, sample_document_processed):
    mock_openai_client.chat.completions.create.return_value.choices = [
        AsyncMock(message=AsyncMock(content="invalid json"))
    ]
    agent = ClassificationAgent()

    with pytest.raises(ClassificationError) as excinfo:
        await agent.classify_document(sample_document_processed)
    assert "Dados de classificação inválidos" in str(excinfo.value)

@pytest.mark.asyncio
async def test_classify_document_missing_fields_in_llm_response(mock_openai_client, sample_document_processed):
    mock_openai_client.chat.completions.create.return_value.choices = [
        AsyncMock(message=AsyncMock(content=json.dumps({"conta_contabil": "Receita"})))
    ]
    agent = ClassificationAgent()

    with pytest.raises(ClassificationError) as excinfo:
        await agent.classify_document(sample_document_processed)
    assert "Dados de classificação inválidos" in str(excinfo.value)


