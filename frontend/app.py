import streamlit as st
import requests
import json
import time
import logging
from typing import Optional, Dict, Any
import io
from datetime import datetime
import uuid


# Configuração da página
st.set_page_config(
    page_title="Contabilidade com IA",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para melhorar a aparência
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .sub-header {
        font-size: 1.5rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }
    
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)


class ContabilidadeApp:
    """Aplicação principal do sistema de contabilidade com IA"""
    
    def __init__(self):
        self.api_base_url = "http://localhost:8000"
        self.setup_logging()
        
    def setup_logging(self):
        """Configura o sistema de logging do frontend"""
        # Garante que o diretório de logs existe
        import pathlib
        pathlib.Path("logs").mkdir(exist_ok=True)
        
        # Cria logger específico para o frontend
        self.logger = logging.getLogger("frontend_app")
        self.logger.setLevel(logging.INFO)
        
        # Se não há handlers, configura um
        if not self.logger.handlers:
            # Handler para arquivo
            file_handler = logging.FileHandler("logs/frontend.log", encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # Formatter JSON estruturado
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "component": "frontend", '
                '"level": "%(levelname)s", "message": "%(message)s", '
                '"module": "%(module)s", "function": "%(funcName)s"}'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
        # Log de inicialização
        self.logger.info("Frontend da aplicação de contabilidade inicializado")
        
    def log_user_action(self, action: str, details: Optional[Dict] = None):
        """Log de ações do usuário"""
        session_id = st.session_state.get('session_id', str(uuid.uuid4()))
        if 'session_id' not in st.session_state:
            st.session_state.session_id = session_id
            
        log_data = {
            "action": action,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            **(details or {})
        }
        
        self.logger.info(f"Ação do usuário: {action}", extra=log_data)
        
    def check_api_health(self) -> bool:
        """Verifica se a API está funcionando"""
        try:
            self.logger.info("Verificando saúde da API")
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            is_healthy = response.status_code == 200
            
            if is_healthy:
                self.logger.info("API está funcionando corretamente")
            else:
                self.logger.error(f"API retornou status code: {response.status_code}")
                
            return is_healthy
        except Exception as e:
            self.logger.error(f"Erro ao verificar saúde da API: {str(e)}")
            return False
    
    def process_document(self, uploaded_file) -> Optional[Dict[str, Any]]:
        """Envia documento para processamento na API"""
        start_time = time.time()
        file_size = len(uploaded_file.getvalue())
        
        # Log do início do processamento
        self.log_user_action("document_upload_start", {
            "file_name": uploaded_file.name,
            "file_type": uploaded_file.type,
            "file_size": file_size
        })
        
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            
            self.logger.info(f"Enviando documento para API: {uploaded_file.name} ({file_size} bytes)")
            
            response = requests.post(
                f"{self.api_base_url}/process-document",
                files=files,
                timeout=30
            )
            
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # Log de sucesso
                self.log_user_action("document_processing_success", {
                    "file_name": uploaded_file.name,
                    "file_type": uploaded_file.type,
                    "file_size": file_size,
                    "execution_time": execution_time,
                    "processing_time": result.get("processing_time"),
                    "document_type": result.get("data", {}).get("documento") if result.get("data") else None
                })
                
                self.logger.info(f"Documento processado com sucesso em {execution_time:.2f}s")
                return result
            else:
                # Log de erro da API
                self.log_user_action("document_processing_error", {
                    "file_name": uploaded_file.name,
                    "file_type": uploaded_file.type,
                    "file_size": file_size,
                    "execution_time": execution_time,
                    "status_code": response.status_code,
                    "error_message": response.text
                })
                
                self.logger.error(f"Erro na API: {response.status_code} - {response.text}")
                st.error(f"Erro na API: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            execution_time = time.time() - start_time
            
            # Log de erro de conexão
            self.log_user_action("document_processing_connection_error", {
                "file_name": uploaded_file.name,
                "file_type": uploaded_file.type,
                "file_size": file_size,
                "execution_time": execution_time,
                "error_message": str(e)
            })
            
            self.logger.error(f"Erro de conexão com a API: {str(e)}")
            st.error(f"Erro de conexão com a API: {str(e)}")
            return None
    
    def render_header(self):
        """Renderiza o cabeçalho da aplicação"""
        self.log_user_action("page_load", {"page": "main"})
        
        st.markdown('<h1 class="main-header">🧾 Contabilidade com Agentes de IA</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Processamento automatizado de documentos fiscais brasileiros</p>', unsafe_allow_html=True)
        
        # Status da API
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            api_healthy = self.check_api_health()
            if api_healthy:
                st.success("✅ API conectada e funcionando")
                self.log_user_action("api_status_check", {"status": "healthy"})
            else:
                st.error("❌ API não está disponível. Verifique se o backend está rodando.")
                st.info("💡 Execute: `cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`")
                self.log_user_action("api_status_check", {"status": "unhealthy"})
    
    def render_sidebar(self):
        """Renderiza a barra lateral com informações"""
        st.sidebar.title("📋 Informações")
        
        st.sidebar.markdown("### 🎯 Funcionalidades")
        st.sidebar.markdown("""
        - ✅ Processamento de NF-e XML
        - 🔄 Extração de dados estruturados
        - 📊 Validação de impostos
        - 🏷️ Classificação automática
        - 📝 Log estruturado
        """)
        
        st.sidebar.markdown("### 📄 Formatos Suportados")
        st.sidebar.markdown("""
        - **XML**: Nota Fiscal Eletrônica (NF-e) ✅
        - **PDF**: Nota Fiscal Eletrônica (NF-e via OCR) ✅
        - **Imagem**: JPG, PNG, WEBP, GIF (via LLM Vision) ✅
        """)
        
        st.sidebar.markdown("### 🔧 Tecnologias")
        st.sidebar.markdown("""
        - FastAPI + LangChain
        - Pydantic v2
        - Streamlit
        - Agentes especializados
        """)
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📞 Suporte")
        st.sidebar.info("Sistema desenvolvido com foco em conformidade fiscal brasileira")
    
    def render_upload_section(self):
        """Renderiza a seção de upload de documentos"""
        st.markdown("## 📤 Upload de Documento")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "Selecione um documento fiscal",
                type=['xml', 'pdf', 'jpg', 'jpeg', 'png', 'webp', 'gif'],
                help="Formatos suportados: XML (NF-e), PDF (OCR), Imagens (JPG, PNG, WEBP, GIF via LLM Vision)"
            )
            
            if uploaded_file is not None:
                # Informações do arquivo
                st.markdown('<div class="info-box">', unsafe_allow_html=True)
                st.markdown(f"**📁 Arquivo:** {uploaded_file.name}")
                st.markdown(f"**📏 Tamanho:** {len(uploaded_file.getvalue()):,} bytes")
                st.markdown(f"**🏷️ Tipo:** {uploaded_file.type}")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Botão de processamento
                if st.button("🚀 Processar Documento", type="primary", use_container_width=True):
                    return self.process_document_with_ui(uploaded_file)
        
        with col2:
            st.markdown("### 💡 Dicas")
            st.info("""
            **Para melhores resultados:**
            - Use arquivos XML de NF-e válidos
            - Verifique se o arquivo não está corrompido
            - Arquivos PDF são processados via OCR (Tesseract)
            - PDFs com texto claro têm melhor precisão
            - Imagens são processadas via LLM Vision (GPT-4)
            - Para imagens: use boa resolução e contraste
            - Configure OPENAI_API_KEY para usar processamento de imagem
            """)
        
        return None
    
    def process_document_with_ui(self, uploaded_file):
        """Processa documento com feedback visual"""
        # Barra de progresso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Simulação de progresso
        for i in range(100):
            progress_bar.progress(i + 1)
            if i < 30:
                status_text.text("📖 Lendo arquivo...")
            elif i < 60:
                status_text.text("🔍 Extraindo dados...")
            elif i < 90:
                status_text.text("✅ Validando informações...")
            else:
                status_text.text("🎯 Finalizando processamento...")
            time.sleep(0.01)
        
        # Processamento real
        result = self.process_document(uploaded_file)
        
        # Limpa a barra de progresso
        progress_bar.empty()
        status_text.empty()
        
        return result
    
    def render_results(self, result: Dict[str, Any]):
        """Renderiza os resultados do processamento"""
        if not result or not result.get('success'):
            st.markdown('<div class="error-box">', unsafe_allow_html=True)
            st.error(f"❌ Erro no processamento: {result.get('error_message', 'Erro desconhecido')}")
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        data = result.get('data', {})
        processing_time = result.get('processing_time', 0)
        
        # Cabeçalho de sucesso
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.success(f"✅ Documento processado com sucesso em {processing_time:.2f}s")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Métricas principais
        st.markdown("## 📊 Resumo do Documento")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💰 Valor Total",
                value=f"R$ {data.get('valor_total', 0):,.2f}",
                delta=None
            )
        
        with col2:
            st.metric(
                label="📅 Data Emissão",
                value=data.get('data_emissao', 'N/A'),
                delta=None
            )
        
        with col3:
            st.metric(
                label="🏷️ CFOP",
                value=data.get('cfop', 'N/A'),
                delta=None
            )
        
        with col4:
            st.metric(
                label="📦 Itens",
                value=len(data.get('itens', [])),
                delta=None
            )
        
        # Detalhes em abas
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Dados Gerais", "💸 Impostos", "📦 Itens", "🔍 JSON Completo"])
        
        with tab1:
            self.render_general_data(data)
        
        with tab2:
            self.render_tax_data(data.get('impostos', {}))
        
        with tab3:
            self.render_items_data(data.get('itens', []))
        
        with tab4:
            self.render_json_data(data)
    
    def render_general_data(self, data: Dict[str, Any]):
        """Renderiza dados gerais do documento"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📄 Informações do Documento")
            st.markdown(f"**Tipo:** {data.get('documento', 'N/A').upper()}")
            st.markdown(f"**Número:** {data.get('numero_documento', 'N/A')}")
            st.markdown(f"**Série:** {data.get('serie', 'N/A')}")
            st.markdown(f"**Chave NF-e:** `{data.get('chave_nfe', 'N/A')}`")
            st.markdown(f"**Moeda:** {data.get('moeda', 'N/A')}")
            st.markdown(f"**Forma Pagamento:** {data.get('forma_pagamento', 'N/A')}")
        
        with col2:
            st.markdown("### 🏢 Partes Envolvidas")
            st.markdown(f"**Emitente:** {data.get('emitente', 'N/A')}")
            st.markdown(f"**Destinatário:** {data.get('destinatario', 'N/A')}")
            
            st.markdown("### 🏷️ Classificação Fiscal")
            st.markdown(f"**CFOP:** {data.get('cfop', 'N/A')}")
            st.markdown(f"**NCM:** {data.get('ncm', 'N/A')}")
            st.markdown(f"**CST:** {data.get('cst', 'N/A')}")
    
    def render_tax_data(self, impostos: Dict[str, Any]):
        """Renderiza dados de impostos"""
        st.markdown("### 💸 Detalhamento dos Impostos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ICMS")
            st.markdown(f"**Base de Cálculo:** R$ {impostos.get('icms_base', 0):,.2f}")
            st.markdown(f"**Valor:** R$ {impostos.get('icms_valor', 0):,.2f}")
            
            st.markdown("#### PIS")
            st.markdown(f"**Valor:** R$ {impostos.get('pis_valor', 0):,.2f}")
        
        with col2:
            st.markdown("#### COFINS")
            st.markdown(f"**Valor:** R$ {impostos.get('cofins_valor', 0):,.2f}")
            
            st.markdown("#### ISS")
            iss_valor = impostos.get('iss_valor')
            if iss_valor is not None:
                st.markdown(f"**Valor:** R$ {iss_valor:,.2f}")
            else:
                st.markdown("**Valor:** Não aplicável")
        
        # Gráfico de impostos
        if any(impostos.values()):
            import pandas as pd
            
            tax_data = []
            if impostos.get('icms_valor'):
                tax_data.append({"Imposto": "ICMS", "Valor": impostos['icms_valor']})
            if impostos.get('pis_valor'):
                tax_data.append({"Imposto": "PIS", "Valor": impostos['pis_valor']})
            if impostos.get('cofins_valor'):
                tax_data.append({"Imposto": "COFINS", "Valor": impostos['cofins_valor']})
            if impostos.get('iss_valor'):
                tax_data.append({"Imposto": "ISS", "Valor": impostos['iss_valor']})
            
            if tax_data:
                df = pd.DataFrame(tax_data)
                st.markdown("#### 📊 Distribuição dos Impostos")
                st.bar_chart(df.set_index('Imposto'))
    
    def render_items_data(self, itens: list):
        """Renderiza dados dos itens"""
        st.markdown("### 📦 Itens do Documento")
        
        if not itens:
            st.info("Nenhum item encontrado no documento.")
            return
        
        # Tabela de itens
        import pandas as pd
        
        items_data = []
        for i, item in enumerate(itens, 1):
            items_data.append({
                "Item": i,
                "Descrição": item.get('descricao', 'N/A'),
                "Quantidade": item.get('quantidade', 0),
                "Valor Unit.": f"R$ {item.get('valor_unitario', 0):,.2f}",
                "CFOP": item.get('cfop_item', 'N/A'),
                "NCM": item.get('ncm', 'N/A'),
                "CST": item.get('cst', 'N/A')
            })
        
        df = pd.DataFrame(items_data)
        st.dataframe(df, use_container_width=True)
        
        # Resumo dos itens
        total_items = len(itens)
        total_quantity = sum(item.get('quantidade', 0) for item in itens)
        total_value = sum(item.get('quantidade', 0) * item.get('valor_unitario', 0) for item in itens)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Itens", total_items)
        with col2:
            st.metric("Quantidade Total", f"{total_quantity:,.0f}")
        with col3:
            st.metric("Valor Total dos Itens", f"R$ {total_value:,.2f}")
    
    def render_json_data(self, data: Dict[str, Any]):
        """Renderiza dados em formato JSON"""
        st.markdown("### 🔍 Dados Estruturados (JSON)")
        st.markdown("Dados extraídos e estruturados pelo agente de ingestão:")
        
        # JSON formatado
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        st.code(json_str, language='json')
        
        # Botão para download
        st.download_button(
            label="📥 Baixar JSON",
            data=json_str,
            file_name=f"documento_processado_{data.get('numero_documento', 'unknown')}.json",
            mime="application/json"
        )
    
    def run(self):
        """Executa a aplicação principal"""
        self.render_header()
        self.render_sidebar()
        
        # Seção principal
        result = self.render_upload_section()
        
        # Renderiza resultados se houver
        if result:
            st.markdown("---")
            self.render_results(result)


# Execução da aplicação
if __name__ == "__main__":
    app = ContabilidadeApp()
    app.run()

