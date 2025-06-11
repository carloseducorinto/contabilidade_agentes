import logging
import json
from typing import Dict, Any

from openai import AsyncOpenAI
from pydantic import ValidationError

from app.config.settings import settings
from app.exceptions.custom_exceptions import ClassificationError, LLMIntegrationError
from app.models.document_models import DocumentProcessed
from app.models.classification_models import ClassificationOutput, ClassificationInput
from app.utils.retry_utils import retry_async, OPENAI_RETRY_CONFIG
from app.utils.cache import cached

logger = logging.getLogger(__name__)

class ClassificationAgent:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        logger.debug(f"🔐 Usando chave OpenAI: {settings.openai_api_key[:-10]}... (TESTANDO)")
        self.model = settings.openai_classification_model
        self.temperature = settings.openai_classification_temperature

    @retry_async(OPENAI_RETRY_CONFIG)
    @cached(ttl=settings.classification_cache_ttl, key_prefix="classification_agent")
    async def classify_document(self, doc_processed: DocumentProcessed) -> ClassificationOutput:
        logger.info(f"Iniciando classificação para documento ID: {doc_processed.document_id}")
        try:
            classification_input = ClassificationInput(
                document_id=doc_processed.document_id,
                document_type=doc_processed.document_type,
                extracted_data=doc_processed.extracted_data
            )
            
            prompt = self._build_classification_prompt(classification_input)
            
            response = await self._get_llm_response(prompt)
            
            classification_data = self._parse_llm_response(response)
            
            # Add required fields that OpenAI doesn't return
            classification_data['document_id'] = classification_input.document_id
            classification_data['document_type'] = classification_input.document_type
            
            classified_output = ClassificationOutput(**classification_data)
            logger.info(f"Documento ID: {doc_processed.document_id} classificado com sucesso.")
            return classified_output
        except ValidationError as e:
            logger.error(f"Erro de validação na saída da classificação para o documento ID {doc_processed.document_id}: {e}")
            raise ClassificationError(f"Dados de classificação inválidos: {e}")
        except LLMIntegrationError as e:
            logger.error(f"Erro na integração com LLM para classificação do documento ID {doc_processed.document_id}: {e}")
            raise ClassificationError(f"Falha na comunicação com o serviço de classificação: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado na classificação do documento ID {doc_processed.document_id}: {e}")
            raise ClassificationError(f"Erro inesperado durante a classificação: {e}")

    def _build_classification_prompt(self, classification_input: ClassificationInput) -> str:
        # Prompt para o LLM para classificação contábil
        # Este prompt pode ser ajustado e refinado conforme a necessidade
        prompt = f"""Você é um especialista em contabilidade e sua tarefa é classificar uma transação financeira com base nos dados extraídos de um documento. Forneça a conta contábil mais apropriada, o centro de custo, o tipo de lançamento e uma breve justificativa para a classificação.

Dados da Transação (formato JSON):
{json.dumps(classification_input.extracted_data, indent=2)}

Categorias Contábeis Sugeridas (use as mais relevantes ou crie novas se necessário, mas mantenha a consistência):
- Receita de Vendas
- Despesa Operacional (e.g., Aluguel, Salários, Energia, Água, Internet, Material de Escritório, Manutenção, Viagens, Marketing, Frete, Impostos sobre Vendas, Juros Passivos)
- Ativo Fixo (e.g., Imóveis, Veículos, Máquinas e Equipamentos)
- Passivo Circulante (e.g., Fornecedores, Impostos a Pagar, Salários a Pagar, Empréstimos Bancários)
- Receita Financeira (e.g., Juros Ativos, Rendimentos de Aplicações)
- Outras Receitas/Despesas (e.g., Venda de Ativo, Perdas/Ganhos Não Operacionais)

Centros de Custo Sugeridos (use os mais relevantes ou crie novos se necessário):
- Administrativo
- Vendas
- Produção
- Marketing
- Logística
- TI

Tipos de Lançamento Sugeridos (use os mais relevantes ou crie novos se necessário):
- Compra de Mercadoria/Serviço
- Venda de Mercadoria/Serviço
- Pagamento
- Recebimento
- Depreciação
- Provisão

Formato de Saída (JSON):
{{
  "conta_contabil": "<nome_da_conta>",
  "centro_de_custo": "<nome_do_centro_de_custo>",
  "tipo_lancamento": "<tipo_de_lancamento>",
  "justificativa": "<breve_justificativa_da_classificacao>"
}}

Certifique-se de que a saída seja um JSON válido e que todos os campos obrigatórios estejam preenchidos. Se um campo não for aplicável, use "N/A".
"""
        return prompt

    async def _get_llm_response(self, prompt: str) -> str:
        try:
            chat_completion = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um assistente de contabilidade experiente."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            raise LLMIntegrationError(f"Falha ao obter resposta do LLM: {e}")

    def _parse_llm_response(self, response_content: str) -> Dict[str, Any]:
        try:
            return json.loads(response_content)
        except json.JSONDecodeError as e:
            raise LLMIntegrationError(f"Falha ao decodificar JSON da resposta do LLM: {e}")

# Exemplo de uso (para testes ou demonstração)
async def main():
    # Este é um exemplo de dados processados que viriam do DocumentIngestionAgent
    sample_extracted_data = {
        "chave_nfe": "12345678901234567890123456789012345678901234",
        "numero": "12345",
        "serie": "1",
        "data_emissao": "2025-06-10",
        "valor_total": 1500.00,
        "emitente": {"cnpj": "11.222.333/0001-44", "nome": "Empresa Fornecedora LTDA"},
        "destinatario": {"cnpj": "55.666.777/0001-88", "nome": "Minha Empresa S.A."},
        "itens": [
            {"descricao": "Serviços de Consultoria em TI", "quantidade": 1, "valor_unitario": 1500.00, "valor_total": 1500.00}
        ],
        "impostos": {"icms_valor": 180.00, "ipi_valor": 0.00, "pis_valor": 24.75, "cofins_valor": 113.85}
    }

    sample_doc_processed = DocumentProcessed(
        document_id="doc_123",
        document_type="xml",
        extracted_data=sample_extracted_data
    )

    agent = ClassificationAgent()
    try:
        classified_doc = await agent.classify_document(sample_doc_processed)
        print("\nDocumento Classificado:")
        print(classified_doc.model_dump_json(indent=2))
    except ClassificationError as e:
        print(f"Erro na classificação: {e}")

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

