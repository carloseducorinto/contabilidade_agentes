# Pesquisa sobre LLMs com Capacidades de Visão para Análise de Documentos

## Modelos Identificados

### 1. Modelos Comerciais (APIs)
- **GPT-4 Vision (OpenAI)**: Modelo robusto para análise de imagem e texto
- **Claude 3.7 Sonnet (Anthropic)**: Capacidades avançadas de visão
- **Gemini 2.5 Pro (Google)**: Processamento multimodal

### 2. Modelos Open Source
- **Llama 3.2 Vision**: Modelo da Meta com capacidades de visão
- **Qwen2-VL**: Modelo chinês com boa performance em OCR
- **InternVL 1.5**: Efetivo e relativamente rápido
- **Phi Vision**: Mais poderoso mas mais lento

### 3. Considerações para Documentos Fiscais
- Modelos com visão podem entender contexto completo do documento
- Melhor que OCR tradicional para documentos estruturados
- Capacidade de extrair dados específicos com prompts adequados

## Recomendação Inicial
Para o projeto, vou implementar suporte ao **GPT-4 Vision** via OpenAI API, pois:
- Já temos LangChain configurado
- Boa documentação e suporte
- Performance comprovada em extração de dados
- Facilidade de integração

