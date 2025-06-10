# Arquitetura da Solução Multiagente

## Visão Geral
A solução será composta por uma orquestração de agentes de IA especializados, cada um com responsabilidades bem definidas no fluxo de trabalho de lançamento contábil. A comunicação entre os agentes será baseada em mensagens e a persistência de dados será gerenciada por um `MemoryAgent`.

## Componentes Principais
- **Backend (FastAPI)**: Servirá como a API principal para interação com o frontend e orquestração dos agentes. Utilizará LangChain para a gestão dos LLMs e Pydantic v2 para validação de dados.
- **Frontend (Streamlit)**: Interface de usuário para upload de documentos e visualização do status do processamento.
- **Agentes de IA**: Módulos Python independentes, cada um responsável por uma etapa específica do processo contábil.

## Fluxo de Processamento (Alto Nível)
1. **Upload de Documento**: O usuário faz o upload de um documento (XML ou PDF) via Streamlit.
2. **Ingestão de Documento**: O `DocumentIngestionAgent` processa o documento, extrai e normaliza os dados para um formato JSON estruturado.
3. **Classificação**: O `ClassificationAgent` classifica a operação contábil com base nos dados extraídos e regras predefinidas (CFOP, NCM, CST). Se a classificação falhar, um LLM será consultado.
4. **Geração de Lançamento**: O `AccountingEntryAgent` gera o lançamento contábil formal (débito/crédito).
5. **Validação**: O `ValidationAgent` valida a consistência, regras de negócio e conformidade fiscal do lançamento.
6. **Postagem**: O `PostingAgent` integra o lançamento validado ao sistema ERP.
7. **Revisão Humana**: Casos incertos são escalados para o `HumanReviewAgent`.
8. **Auditoria**: O `AuditTrailAgent` registra todas as decisões dos agentes.
9. **Memória**: O `MemoryAgent` mantém um histórico para consistência e aprendizado.
10. **Priorização**: O `PrioritizationAgent` gerencia a fila de documentos.

## Design do `DocumentIngestionAgent`

### Responsabilidades
- Aceitar documentos nos formatos XML e PDF.
- Realizar parsing de Nota Fiscal Eletrônica (NF-e) brasileira.
- Extrair dados fiscais estruturados.
- Normalizar os dados para o formato JSON especificado.

### Entradas
- Arquivo XML (NF-e).
- Arquivo PDF (NF-e, que será processado via OCR).

### Saídas
- Objeto JSON estruturado contendo os dados fiscais extraídos, conforme o modelo:

```json
{
  "documento": "nfe",
  "cfop": "1102",
  "cst": "00",
  "forma_pagamento": "a_vista",
  "ncm": "94017900",
  "valor_total": 3000.00,
  "data_emissao": "2025-09-03",
  "emitente": "44556677000199",
  "destinatario": "77665544000122",
  "moeda": "BRL",
  "numero_documento": "12345",
  "serie": "1",
  "chave_nfe": "35250944556677000199550010000123451234567890",
  "impostos": {
    "icms_base": 3000.00,
    "icms_valor": 360.00,
    "pis_valor": 27.00,
    "cofins_valor": 124.20,
    "iss_valor": null
  },
  "itens": [
    {
      "descricao": "Cadeira Gamer",
      "quantidade": 4,
      "valor_unitario": 750.00,
      "cfop_item": "1102",
      "ncm": "94017900",
      "cst": "00"
    }
  ]
}
```

### Tecnologias
- **Parsing XML**: Bibliotecas Python como `xml.etree.ElementTree` ou `lxml`.
- **OCR para PDF**: Ferramentas como `Tesseract` (com `pytesseract`) ou serviços de OCR baseados em nuvem (se necessário para maior precisão).
- **Validação de Saída**: Pydantic v2 para garantir o formato JSON correto.

### Considerações
- Tratamento de erros para documentos inválidos ou incompletos.
- Suporte a diferentes versões de schemas de NF-e (se aplicável).
- Otimização para desempenho no processamento de grandes volumes de documentos.


