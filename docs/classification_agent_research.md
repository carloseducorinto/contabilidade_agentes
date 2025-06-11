## ClassificationAgent: Requisitos e Arquitetura

### Requisitos de Classificação

O `ClassificationAgent` será responsável por categorizar os dados extraídos de documentos fiscais (como NF-e) em informações relevantes para lançamentos contábeis e compliance. Os principais requisitos incluem:

1.  **Categorização Contábil**: Classificar o documento em uma ou mais categorias contábeis predefinidas (e.g., 'Despesa Operacional', 'Receita de Vendas', 'Ativo Fixo', 'Passivo Circulante').
2.  **Centro de Custo/Lucro**: Identificar o centro de custo ou lucro associado à transação, se aplicável.
3.  **Tipo de Lançamento**: Determinar o tipo de lançamento contábil (e.g., 'Compra de Mercadoria', 'Venda de Serviço', 'Pagamento de Salário').
4.  **Compliance**: Ajudar a garantir que a classificação esteja em conformidade com as normas contábeis e fiscais brasileiras.
5.  **Flexibilidade**: Permitir a adição ou modificação de categorias de classificação de forma fácil.
6.  **Utilização de LLM**: Aproveitar a capacidade de compreensão contextual dos LLMs para realizar classificações complexas e inferir categorias a partir de descrições textuais.

### Arquitetura do ClassificationAgent

O `ClassificationAgent` será implementado como um novo serviço ou módulo dentro da estrutura `backend/app/`. Ele seguirá o padrão de design já estabelecido, utilizando Pydantic para validação de dados e integrando-se com o `DocumentIngestionAgent` e, futuramente, com o `AccountingEntryAgent`.

**Componentes Principais:**

1.  **`classification_agent.py`**: Contém a lógica principal do agente, incluindo a interação com o LLM para a classificação.
2.  **`classification_models.py`**: Define os modelos Pydantic para a entrada (dados extraídos) e saída (dados classificados) do agente.
3.  **`classification_service.py` (opcional)**: Se a lógica de classificação se tornar muito complexa, um serviço dedicado pode ser criado para encapsular a lógica de negócios, similar ao `DocumentService`.
4.  **Integração com LLM**: Utilizará a API da OpenAI (ou outro LLM configurado) para realizar a classificação baseada em prompts bem definidos.
5.  **Configuração**: As categorias de classificação e outras configurações específicas do agente serão gerenciadas via `settings.py`.

**Fluxo de Processamento:**

`DocumentIngestionAgent` (extração) -> `ClassificationAgent` (classificação) -> `AccountingEntryAgent` (lançamento contábil)

O `ClassificationAgent` receberá o `DocumentProcessed` (ou um modelo similar contendo os dados extraídos) como entrada e retornará um `DocumentClassified` (ou um modelo similar) que incluirá as categorias contábeis, centro de custo, tipo de lançamento, etc.

**Exemplo de Prompt para LLM (conceitual):**

```
Você é um especialista em contabilidade. Classifique a seguinte transação, extraída de uma Nota Fiscal Eletrônica, nas categorias contábeis mais apropriadas. Forneça a conta contábil, centro de custo e tipo de lançamento.

Dados da NF-e:
<dados_extraidos_do_documento>

Categorias Contábeis Disponíveis:
- Receita de Vendas
- Despesa Operacional (Subcategorias: Aluguel, Salários, Energia, Água, Internet, Material de Escritório, Manutenção, Viagens, Marketing, etc.)
- Ativo Fixo (Subcategorias: Imóveis, Veículos, Máquinas e Equipamentos)
- Passivo Circulante (Subcategorias: Fornecedores, Impostos a Pagar, Salários a Pagar)
- Outras Receitas/Despesas

Formato de Saída:
{
  "conta_contabil": "<nome_da_conta>",
  "centro_de_custo": "<nome_do_centro_de_custo>",
  "tipo_lancamento": "<tipo_de_lancamento>",
  "justificativa": "<breve_justificativa_da_classificacao>"
}
```

Esta arquitetura permitirá um sistema flexível e escalável para a classificação contábil.

