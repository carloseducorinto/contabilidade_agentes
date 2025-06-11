# 🤖 ClassificationAgent - Agente de Classificação Contábil

## ✅ Funcionalidade Implementada

O **ClassificationAgent** é um novo componente crucial que atua como elo entre a extração de dados e a geração dos lançamentos contábeis, proporcionando automação inteligente e garantindo compliance fiscal.

### 🎯 Objetivo
- **Classificação Automática**: Analisa os dados extraídos dos documentos fiscais e os classifica automaticamente em categorias contábeis apropriadas.
- **Compliance**: Garante que a classificação esteja em conformidade com as normas contábeis brasileiras.
- **Automação**: Reduz significativamente o trabalho manual de classificação contábil.

### 🔧 Funcionalidades
- **Análise Inteligente**: Utiliza LLM (Large Language Model) para analisar o contexto dos dados extraídos.
- **Classificação Contextual**: Determina a conta contábil, centro de custo e tipo de lançamento mais apropriados.
- **Justificativa**: Fornece explicação detalhada sobre o raciocínio por trás da classificação.
- **Validação**: Valida os dados de classificação usando modelos Pydantic rigorosos.

### 📊 Dados de Saída
O ClassificationAgent retorna as seguintes informações estruturadas:
- **Conta Contábil**: Classificação da conta contábil apropriada
- **Centro de Custo**: Departamento ou área responsável
- **Tipo de Lançamento**: Categoria do lançamento contábil
- **Justificativa**: Explicação detalhada da classificação
- **Metadados**: ID do documento e tipo para rastreabilidade

### 🏗️ Arquitetura
```
ClassificationAgent
├── classification_agent.py          # Agente principal de classificação
├── models/
│   └── classification_models.py     # Modelos Pydantic para classificação
├── tests/
│   ├── unit/
│   │   └── test_classification_agent.py     # Testes unitários
│   └── integration/
│       └── test_classification_flow.py      # Testes de integração
└── docs/
    └── classification_agent_research.md     # Documentação de pesquisa
```

### 🔄 Fluxo de Processamento Atualizado
1. **Upload do Documento** → Frontend Streamlit
2. **Extração de Dados** → DocumentIngestionAgent (XML/PDF/Imagem)
3. **🆕 Classificação Contábil** → ClassificationAgent (LLM)
4. **Exibição dos Resultados** → Frontend com dados extraídos + classificação

### 🎨 Interface Atualizada
O frontend foi atualizado para exibir os resultados da classificação:
- **Seção de Classificação Contábil**: Nova seção destacada com os resultados da classificação
- **Aba de Classificação**: Aba dedicada com detalhes completos da classificação
- **Justificativa**: Exibição da explicação fornecida pelo agente
- **Download**: Opção para baixar os dados de classificação em JSON

### 🧪 Testes Implementados
- **Testes Unitários**: Verificam o funcionamento isolado do ClassificationAgent
- **Testes de Integração**: Testam o fluxo completo de processamento + classificação
- **Cobertura de Código**: Incluído nas verificações de qualidade

### ⚙️ Configuração
O ClassificationAgent requer:
- **OPENAI_API_KEY**: Chave de API da OpenAI para o LLM
- **Configurações**: Definidas em `config/settings.py`

### 📈 Performance
- **Tempo de Classificação**: ~1-3 segundos (dependendo da complexidade)
- **Precisão**: Alta precisão contextual graças ao uso de LLM
- **Cache**: Resultados podem ser cacheados para documentos similares

### 🔮 Próximos Passos
O ClassificationAgent estabelece a base para:
- **Geração de Lançamentos**: Próximo agente para criar lançamentos contábeis automaticamente
- **Aprendizado**: Melhoria contínua baseada em feedback
- **Regras Customizadas**: Possibilidade de adicionar regras específicas da empresa

## 📝 Exemplo de Resultado com Classificação

### 📋 Resultado Completo (Extração + Classificação)
```json
{
  "success": true,
  "document_id": "doc_12345",
  "document_type": "xml",
  "extracted_data": {
    "documento": "nfe",
    "numero_documento": "12345",
    "serie": "1",
    "data_emissao": "2025-09-03",
    "chave_nfe": "35250944556677000199550010000123451234567890",
    "emitente": "EMPRESA TESTE LTDA",
    "destinatario": "CLIENTE TESTE LTDA",
    "valor_total": 3000.00,
    "moeda": "BRL",
    "cfop": "1102",
    "ncm": "94017900",
    "cst": "00",
    "impostos": {
      "icms_base": 3000.00,
      "icms_valor": 360.00,
      "pis_valor": 27.00,
      "cofins_valor": 124.20,
      "iss_valor": 0.0
    },
    "itens": [
      {
        "codigo": "001",
        "descricao": "Cadeira Gamer",
        "quantidade": 4.0,
        "valor_unitario": 750.00,
        "valor_total": 3000.00,
        "unidade": "UN",
        "cfop_item": "1102",
        "ncm": "94017900",
        "cst": "00"
      }
    ]
  },
  "classification_data": {
    "conta_contabil": "Receita de Vendas de Mercadorias",
    "centro_de_custo": "Vendas - Móveis",
    "tipo_lancamento": "Venda de Mercadoria",
    "justificativa": "Baseado no CFOP 1102 (Compra para comercialização) e na descrição do item 'Cadeira Gamer', esta operação representa uma venda de mercadoria no varejo. A classificação em 'Receita de Vendas de Mercadorias' é apropriada para este tipo de transação comercial.",
    "document_id": "doc_12345",
    "document_type": "xml"
  },
  "processing_time": 2.45,
  "message": "Documento processado e classificado com sucesso."
}
```

## 🔧 Implementação Técnica

### 📁 Estrutura de Arquivos
```
backend/app/
├── classification_agent.py          # Classe principal do agente
├── models/
│   └── classification_models.py     # Modelos Pydantic
└── config/
    └── settings.py                   # Configurações do agente
```

### 🧪 Testes
```
backend/tests/
├── unit/
│   └── test_classification_agent.py     # Testes unitários
└── integration/
    └── test_classification_flow.py      # Testes de integração
```

### 🚀 Como Usar

O ClassificationAgent é automaticamente executado após a extração bem-sucedida de dados de qualquer documento. Não requer configuração adicional além da chave OpenAI.

### 📊 Métricas e Monitoramento

O agente inclui métricas de performance e logging detalhado para monitoramento em produção:
- Tempo de processamento
- Taxa de sucesso/erro
- Tipos de classificação mais comuns
- Logs estruturados para auditoria 