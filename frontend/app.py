import streamlit as st
import requests
import json
import time
import logging
import os
from typing import Optional, Dict, Any, List
import io
from datetime import datetime
import uuid
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


# Configuração da página
st.set_page_config(
    page_title="Contabilidade com IA",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para melhorar a aparência e acessibilidade
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .sub-header {
        font-size: 1.5rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }
    
    .success-box {
        background-color: #d4edda;
        border: 2px solid #c3e6cb;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .error-box {
        background-color: #f8d7da;
        border: 2px solid #f5c6cb;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .warning-box {
        background-color: #fff3cd;
        border: 2px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .info-box {
        background-color: #d1ecf1;
        border: 2px solid #bee5eb;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    .progress-container {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 2rem;
        margin: 1rem 0;
        text-align: center;
        border: 1px solid #dee2e6;
    }
    
    .error-details {
        background-color: #fff5f5;
        border: 1px solid #fed7d7;
        border-radius: 0.375rem;
        padding: 1rem;
        margin-top: 1rem;
        font-family: monospace;
        font-size: 0.9rem;
    }
    
    .suggestion-box {
        background-color: #f0f9ff;
        border: 1px solid #bae6fd;
        border-radius: 0.375rem;
        padding: 1rem;
        margin-top: 1rem;
    }
    
    /* Melhorias de acessibilidade */
    .stButton > button {
        transition: all 0.3s ease;
        border-radius: 0.5rem;
        font-weight: 600;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .stButton > button:focus {
        outline: 3px solid #4285f4;
        outline-offset: 2px;
    }
    
    /* Contraste melhorado para texto */
    .stMarkdown {
        color: #2d3748;
    }
    
    /* Indicadores de carregamento */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #3498db;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)


class ContabilidadeApp:
    """
    Aplicação principal do sistema de contabilidade com IA
    """
    
    def __init__(self):
        # Use environment variable for backend URL, fallback to localhost for development
        self.api_base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        self.setup_logging()
        self.setup_session_state()
        # Log the backend URL being used for debugging
        self.log_user_action("app_initialization", {
            "backend_url": self.api_base_url,
            "environment": os.getenv("ENVIRONMENT", "unknown")
        })
        self.logger.info(f"Frontend iniciado. Backend URL: {self.api_base_url}")
        
    def setup_session_state(self):
        """Inicializa o estado da sessão"""
        if 'session_id' not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
            self.logger.debug(f"Nova sessão iniciada: {st.session_state.session_id}")
        if 'processing_history' not in st.session_state:
            st.session_state.processing_history = []
        if 'last_result' not in st.session_state:
            st.session_state.last_result = None
        if 'api_health_cache' not in st.session_state:
            st.session_state.api_health_cache = {'status': None, 'timestamp': 0}
        
    def setup_logging(self):
        """Configura o sistema de logging do frontend"""
        import pathlib
        pathlib.Path("logs").mkdir(exist_ok=True)
        
        self.logger = logging.getLogger("frontend_app")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            file_handler = logging.FileHandler("logs/frontend.log", encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "component": "frontend", '
                '"level": "%(levelname)s", "message": "%(message)s", '
                '"module": "%(module)s", "function": "%(funcName)s"}'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
        self.logger.info("Sistema de logging do frontend configurado.")
        
    def log_user_action(self, action: str, details: Optional[Dict] = None):
        """Registra uma ação do usuário no log"""
        msg = f"Ação do usuário: {action}"
        if details:
            msg += f" | Detalhes: {json.dumps(details, ensure_ascii=False)}"
        self.logger.info(msg)
        
    def check_api_health(self, use_cache: bool = True) -> Dict[str, Any]:
        """Verifica a saúde da API do backend"""
        now = time.time()
        cache = st.session_state.api_health_cache
        if use_cache and cache['status'] is not None and now - cache['timestamp'] < 10:
            self.logger.debug("Usando cache de health check da API")
            return cache['status']
        try:
            self.logger.info(f"Verificando saúde da API em {self.api_base_url}/health")
            resp = requests.get(f"{self.api_base_url}/health", timeout=5)
            resp.raise_for_status()
            health = resp.json()
            cache['status'] = health
            cache['timestamp'] = now
            self.logger.info("API backend saudável")
            return health
        except Exception as e:
            self.logger.error(f"Falha ao verificar saúde da API: {e}")
            cache['status'] = {'status': 'unhealthy', 'error': str(e)}
            cache['timestamp'] = now
            return cache['status']
    
    def get_error_suggestions(self, error_message: str, file_type: str) -> List[str]:
        """Retorna sugestões baseadas no tipo de erro"""
        suggestions = []
        error_lower = error_message.lower()
        
        # Sugestões baseadas no tipo de arquivo
        if file_type in ['pdf']:
            suggestions.extend([
                "🔍 Verifique se o PDF contém texto legível (não apenas imagens)",
                "📄 Tente converter o PDF para uma imagem de alta qualidade",
                "🖨️ Certifique-se de que o Tesseract OCR está instalado corretamente"
            ])
        
        elif file_type in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
            suggestions.extend([
                "🔑 Verifique se a variável OPENAI_API_KEY está configurada",
                "🖼️ Use imagens com boa resolução e contraste",
                "💡 Certifique-se de que o texto na imagem está legível",
                "🔄 Tente uma imagem com melhor qualidade"
            ])
        
        elif file_type == 'xml':
            suggestions.extend([
                "📋 Verifique se o XML é uma NF-e válida",
                "🔍 Confirme se o arquivo não está corrompido",
                "📝 Teste com um XML de exemplo conhecido"
            ])
        
        # Sugestões baseadas no conteúdo do erro
        if "timeout" in error_lower or "connection" in error_lower:
            suggestions.extend([
                "🔄 Tente novamente em alguns segundos",
                "🌐 Verifique sua conexão com a internet",
                "⚙️ Reinicie o backend se necessário"
            ])
        
        if "openai" in error_lower or "api key" in error_lower:
            suggestions.extend([
                "🔑 Configure a variável de ambiente OPENAI_API_KEY",
                "💳 Verifique se sua conta OpenAI tem créditos disponíveis",
                "🔐 Confirme se a chave da API está correta"
            ])
        
        if "file size" in error_lower or "too large" in error_lower:
            suggestions.extend([
                "📏 Reduza o tamanho do arquivo",
                "🗜️ Comprima a imagem antes do upload",
                "✂️ Corte partes desnecessárias do documento"
            ])
        
        # Sugestões gerais se nenhuma específica foi encontrada
        if not suggestions:
            suggestions.extend([
                "🔄 Tente fazer o upload novamente",
                "📞 Entre em contato com o suporte se o problema persistir",
                "🔍 Verifique se o arquivo está no formato correto"
            ])
        
        return suggestions[:5]  # Limita a 5 sugestões
    
    def process_document_with_progress(self, uploaded_file) -> Optional[Dict[str, Any]]:
        """Processa documento com feedback visual detalhado"""
        start_time = time.time()
        file_size = len(uploaded_file.getvalue())
        file_type = uploaded_file.name.split('.')[-1].lower() if uploaded_file.name else 'unknown'
        
        # Log do início do processamento
        self.log_user_action("document_upload_start", {
            "file_name": uploaded_file.name,
            "file_type": file_type,
            "file_size": file_size
        })
        
        # Container para feedback visual
        progress_container = st.container()
        
        with progress_container:
            st.markdown('<div class="progress-container">', unsafe_allow_html=True)
            
            # Barra de progresso
            progress_bar = st.progress(0)
            status_text = st.empty()
            time_text = st.empty()
            
            # Etapas do processamento
            steps = [
                ("📤 Preparando upload...", 10),
                ("📖 Enviando arquivo...", 30),
                ("🔍 Processando documento...", 70),
                ("✅ Finalizando...", 90),
                ("🎯 Concluído!", 100)
            ]
            
            try:
                for i, (step_text, progress) in enumerate(steps[:-1]):
                    status_text.markdown(f"**{step_text}**")
                    progress_bar.progress(progress)
                    time_text.text(f"Tempo decorrido: {time.time() - start_time:.1f}s")
                    
                    if i == 0:  # Preparando upload
                        time.sleep(0.5)
                    elif i == 1:  # Enviando arquivo
                        # Aqui faz o upload real
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        response = requests.post(
                            f"{self.api_base_url}/process-document",
                            files=files,
                            timeout=60  # Timeout aumentado para arquivos grandes
                        )
                        time.sleep(0.5)
                    elif i == 2:  # Processando
                        # Simula tempo de processamento baseado no tipo de arquivo
                        if file_type in ['pdf']:
                            time.sleep(1.5)  # OCR demora mais
                        elif file_type in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                            time.sleep(2.0)  # LLM Vision demora mais
                        else:
                            time.sleep(0.5)  # XML é mais rápido
                
                # Etapa final
                final_step, final_progress = steps[-1]
                status_text.markdown(f"**{final_step}**")
                progress_bar.progress(final_progress)
                execution_time = time.time() - start_time
                time_text.text(f"Processamento concluído em {execution_time:.1f}s")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Processa a resposta
                if response.status_code == 200:
                    result = response.json()
                    
                    # Log de sucesso
                    self.log_user_action("document_processing_success", {
                        "file_name": uploaded_file.name,
                        "file_type": file_type,
                        "file_size": file_size,
                        "execution_time": execution_time,
                        "processing_time": result.get("processing_time"),
                        "document_type": result.get("data", {}).get("documento") if result.get("data") else None
                    })
                    
                    # Adiciona ao histórico
                    st.session_state.processing_history.append({
                        "timestamp": datetime.now(),
                        "filename": uploaded_file.name,
                        "file_type": file_type,
                        "success": True,
                        "execution_time": execution_time
                    })
                    
                    self.logger.info(f"Documento processado com sucesso em {execution_time:.2f}s")
                    
                    # Limpa o container de progresso
                    progress_container.empty()
                    
                    return result
                else:
                    # Trata erro da API
                    error_data = None
                    try:
                        error_data = response.json()
                    except:
                        pass
                    
                    error_message = error_data.get('detail', response.text) if error_data else response.text
                    
                    # Log de erro
                    self.log_user_action("document_processing_error", {
                        "file_name": uploaded_file.name,
                        "file_type": file_type,
                        "file_size": file_size,
                        "execution_time": execution_time,
                        "status_code": response.status_code,
                        "error_message": error_message
                    })
                    
                    # Adiciona ao histórico
                    st.session_state.processing_history.append({
                        "timestamp": datetime.now(),
                        "filename": uploaded_file.name,
                        "file_type": file_type,
                        "success": False,
                        "error": error_message,
                        "execution_time": execution_time
                    })
                    
                    # Limpa o container de progresso
                    progress_container.empty()
                    
                    # Mostra erro detalhado
                    self.show_detailed_error(error_message, file_type, response.status_code)
                    
                    return None
                    
            except requests.exceptions.Timeout:
                execution_time = time.time() - start_time
                error_msg = "Timeout: O processamento demorou mais que o esperado"
                
                progress_container.empty()
                self.show_detailed_error(error_msg, file_type, None)
                
                self.log_user_action("document_processing_timeout", {
                    "file_name": uploaded_file.name,
                    "file_type": file_type,
                    "file_size": file_size,
                    "execution_time": execution_time
                })
                
                return None
                
            except requests.exceptions.ConnectionError:
                execution_time = time.time() - start_time
                error_msg = "Erro de conexão: Não foi possível conectar à API"
                
                progress_container.empty()
                self.show_detailed_error(error_msg, file_type, None)
                
                self.log_user_action("document_processing_connection_error", {
                    "file_name": uploaded_file.name,
                    "file_type": file_type,
                    "file_size": file_size,
                    "execution_time": execution_time
                })
                
                return None
                
            except Exception as e:
                execution_time = time.time() - start_time
                error_msg = f"Erro inesperado: {str(e)}"
                
                progress_container.empty()
                self.show_detailed_error(error_msg, file_type, None)
                
                self.log_user_action("document_processing_unexpected_error", {
                    "file_name": uploaded_file.name,
                    "file_type": file_type,
                    "file_size": file_size,
                    "execution_time": execution_time,
                    "error": str(e)
                })
                
                return None
    
    def show_detailed_error(self, error_message: str, file_type: str, status_code: Optional[int]):
        """Mostra erro detalhado com sugestões"""
        st.markdown('<div class="error-box">', unsafe_allow_html=True)
        
        # Título do erro
        if status_code:
            st.error(f"❌ Erro {status_code}: Falha no processamento")
        else:
            st.error("❌ Erro: Falha no processamento")
        
        # Detalhes do erro
        with st.expander("🔍 Detalhes do erro", expanded=True):
            st.markdown('<div class="error-details">', unsafe_allow_html=True)
            st.code(error_message, language=None)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Sugestões
        suggestions = self.get_error_suggestions(error_message, file_type)
        if suggestions:
            st.markdown('<div class="suggestion-box">', unsafe_allow_html=True)
            st.markdown("### 💡 Sugestões para resolver o problema:")
            for suggestion in suggestions:
                st.markdown(f"• {suggestion}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Botões de ação
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Tentar Novamente", key="retry_btn"):
                st.rerun()
        
        with col2:
            if st.button("🏥 Verificar API", key="health_btn"):
                health = self.check_api_health(use_cache=False)
                if health['healthy']:
                    st.success("✅ API está funcionando")
                else:
                    st.error(f"❌ API com problemas: {health['error']}")
        
        with col3:
            if st.button("📞 Reportar Problema", key="report_btn"):
                st.info("📧 Entre em contato com o suporte técnico com os detalhes do erro acima.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_header(self):
        """Renderiza o cabeçalho da aplicação"""
        self.log_user_action("page_load", {"page": "main"})
        
        st.markdown('<h1 class="main-header">🧾 Contabilidade com Agentes de IA</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Processamento automatizado de documentos fiscais brasileiros</p>', unsafe_allow_html=True)
        
        # Status da API com cache
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            health = self.check_api_health()
            if health['healthy']:
                health_data = health['data']
                st.success("✅ API conectada e funcionando")
                
                # Mostra informações adicionais se disponíveis
                if health_data:
                    with st.expander("ℹ️ Informações da API"):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("OpenAI", "✅ Configurado" if health_data.get('openai_configured') else "❌ Não configurado")
                        with col_b:
                            cache_stats = health_data.get('cache_stats', {})
                            if cache_stats:
                                hit_rate = cache_stats.get('hit_rate', 0) * 100
                                st.metric("Cache Hit Rate", f"{hit_rate:.1f}%")
                
                self.log_user_action("api_status_check", {"status": "healthy"})
            else:
                st.error(f"❌ {health['error']}")
                
                # Instruções específicas baseadas no erro
                if "conectar" in health['error']:
                    st.markdown('<div class="warning-box">', unsafe_allow_html=True)
                    st.warning("💡 **Como iniciar o backend:**")
                    st.code("""
# Windows (PowerShell/CMD)
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Ou use o Docker
docker-compose up
                    """, language="bash")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                self.log_user_action("api_status_check", {"status": "unhealthy", "error": health['error']})
    
    def render_sidebar(self):
        """Renderiza a barra lateral com informações"""
        st.sidebar.title("📋 Informações")
        
        # Status da sessão
        st.sidebar.markdown("### 🔗 Sessão")
        st.sidebar.text(f"ID: {st.session_state.session_id[:8]}...")
        
        # Histórico de processamento
        history = st.session_state.processing_history
        if history:
            st.sidebar.markdown("### 📊 Histórico")
            total_docs = len(history)
            successful_docs = sum(1 for h in history if h['success'])
            success_rate = (successful_docs / total_docs) * 100 if total_docs > 0 else 0
            
            st.sidebar.metric("Documentos processados", total_docs)
            st.sidebar.metric("Taxa de sucesso", f"{success_rate:.1f}%")
            
            # Últimos processamentos
            with st.sidebar.expander("📝 Últimos processamentos"):
                for item in history[-5:]:  # Últimos 5
                    status_icon = "✅" if item['success'] else "❌"
                    time_str = item['timestamp'].strftime("%H:%M:%S")
                    st.sidebar.text(f"{status_icon} {time_str} - {item['filename'][:20]}...")
        
        st.sidebar.markdown("---")
        
        st.sidebar.markdown("### 🎯 Funcionalidades")
        st.sidebar.markdown("""
        - ✅ Processamento de NF-e XML
        - ✅ OCR para documentos PDF
        - ✅ LLM Vision para imagens
        - ✅ Extração de dados estruturados
        - ✅ Validação de impostos
        - ✅ Logs estruturados
        - ✅ Cache inteligente
        - ✅ Métricas de performance
        """)
        
        st.sidebar.markdown("### 📄 Formatos Suportados")
        st.sidebar.markdown("""
        - **XML**: NF-e nativa ⚡
        - **PDF**: Via OCR (Tesseract) 🔍
        - **Imagem**: Via LLM Vision (GPT-4) 🤖
          - JPG, PNG, WEBP, GIF
        """)
        
        st.sidebar.markdown("### 🔧 Tecnologias")
        st.sidebar.markdown("""
        - **Backend**: FastAPI + LangChain
        - **Validação**: Pydantic v2
        - **Frontend**: Streamlit
        - **OCR**: Tesseract
        - **LLM**: OpenAI GPT-4 Vision
        - **Cache**: In-Memory
        - **Métricas**: Prometheus
        """)
        
        st.sidebar.markdown("---")
        
        # Botões de ação
        if st.sidebar.button("🗑️ Limpar Histórico"):
            st.session_state.processing_history = []
            st.rerun()
        
        if st.sidebar.button("🔄 Atualizar Status API"):
            st.session_state.api_health_cache = {'status': None, 'timestamp': 0}
            st.rerun()
        
        # Debug information
        st.sidebar.markdown("### 🔧 Debug Info")
        with st.sidebar.expander("Configuração"):
            st.text(f"Backend URL: {self.api_base_url}")
            st.text(f"Environment: {os.getenv('ENVIRONMENT', 'not set')}")
        
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
                help="Formatos suportados: XML (NF-e), PDF (OCR), Imagens (JPG, PNG, WEBP, GIF via LLM Vision)",
                key="file_uploader"
            )
            
            if uploaded_file is not None:
                # Validação de tamanho
                file_size = len(uploaded_file.getvalue())
                max_size = 10 * 1024 * 1024  # 10MB
                
                if file_size > max_size:
                    st.error(f"❌ Arquivo muito grande ({file_size:,} bytes). Máximo permitido: {max_size:,} bytes (10MB)")
                    return None
                
                # Informações do arquivo
                st.markdown('<div class="info-box">', unsafe_allow_html=True)
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    st.markdown(f"**📁 Arquivo:** {uploaded_file.name}")
                
                with col_b:
                    st.markdown(f"**📏 Tamanho:** {file_size:,} bytes")
                
                with col_c:
                    file_type = uploaded_file.name.split('.')[-1].lower() if uploaded_file.name else 'unknown'
                    type_emoji = {
                        'xml': '📄', 'pdf': '📋', 
                        'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 
                        'webp': '🖼️', 'gif': '🖼️'
                    }.get(file_type, '📎')
                    st.markdown(f"**🏷️ Tipo:** {type_emoji} {file_type.upper()}")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Botão de processamento
                if st.button("🚀 Processar Documento", type="primary", use_container_width=True, key="process_btn"):
                    return self.process_document_with_progress(uploaded_file)
        
        with col2:
            st.markdown("### 💡 Dicas")
            st.info("""
            **Para melhores resultados:**
            
            **📄 XML:**
            • Use arquivos NF-e válidos
            • Verifique se não está corrompido
            
            **📋 PDF:**
            • Texto deve estar legível
            • Evite PDFs apenas com imagens
            • Tesseract OCR deve estar instalado
            
            **🖼️ Imagens:**
            • Configure OPENAI_API_KEY
            • Use boa resolução e contraste
            • Texto deve estar nítido
            • Formatos: JPG, PNG, WEBP, GIF
            
            **⚡ Performance:**
            • XML: ~0.1s
            • PDF: ~1-3s (OCR)
            • Imagem: ~2-5s (LLM)
            """)
            
            # Estatísticas de processamento
            if st.session_state.processing_history:
                st.markdown("### 📊 Estatísticas")
                history = st.session_state.processing_history
                
                # Agrupa por tipo de arquivo
                type_stats = {}
                for item in history:
                    file_type = item['file_type']
                    if file_type not in type_stats:
                        type_stats[file_type] = {'count': 0, 'success': 0, 'avg_time': 0}
                    
                    type_stats[file_type]['count'] += 1
                    if item['success']:
                        type_stats[file_type]['success'] += 1
                        # Safe execution time handling
                        exec_time = item.get('execution_time', 0)
                        try:
                            exec_time = float(exec_time or 0)
                        except (ValueError, TypeError):
                            exec_time = 0
                        type_stats[file_type]['avg_time'] += exec_time
                
                for file_type, stats in type_stats.items():
                    success_rate = (stats['success'] / stats['count']) * 100 if stats['count'] > 0 else 0
                    avg_time = (stats['avg_time'] / stats['success']) if stats['success'] > 0 else 0
                    
                    st.metric(
                        f"{file_type.upper()}",
                        f"{success_rate:.0f}% sucesso",
                        f"{avg_time:.1f}s médio"
                    )
        
        return None
    
    def render_results(self, result: Dict[str, Any]):
        """Renderiza os resultados do processamento"""
        if not result or not result.get('success'):
            error_msg = result.get('error', 'Erro desconhecido') if result else 'Resultado inválido'
            st.markdown('<div class="error-box">', unsafe_allow_html=True)
            st.error(f"❌ Erro no processamento: {error_msg}")
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        data = result.get('data', {})
        processing_time = result.get('processing_time', 0)
        
        # Salva resultado na sessão
        st.session_state.last_result = result
        
        # Cabeçalho de sucesso
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.success(f"✅ Documento processado com sucesso em {processing_time:.2f}s")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Métricas principais com visualização melhorada
        st.markdown("## 📊 Resumo do Documento")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            valor_total = data.get('valor_total', 0)
            # Safe formatting for valor_total
            try:
                valor_total = float(valor_total or 0)
                valor_display = f"R$ {valor_total:,.2f}"
            except (ValueError, TypeError):
                valor_display = "R$ 0,00"
            
            st.metric(
                label="💰 Valor Total",
                value=valor_display,
                delta=None,
                help="Valor total da nota fiscal"
            )
        
        with col2:
            data_emissao = data.get('data_emissao', 'N/A')
            st.metric(
                label="📅 Data Emissão",
                value=data_emissao,
                delta=None,
                help="Data de emissão do documento"
            )
        
        with col3:
            cfop = data.get('cfop', 'N/A')
            st.metric(
                label="🏷️ CFOP",
                value=cfop,
                delta=None,
                help="Código Fiscal de Operações e Prestações"
            )
        
        with col4:
            itens_count = len(data.get('itens', []))
            st.metric(
                label="📦 Itens",
                value=itens_count,
                delta=None,
                help="Número de itens no documento"
            )
        
        # Detalhes em abas
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Dados Gerais", 
            "💸 Impostos", 
            "📦 Itens", 
            "📊 Gráficos",
            "🔍 JSON Completo"
        ])
        
        with tab1:
            self.render_general_data(data)
        
        with tab2:
            self.render_tax_data(data.get('impostos', {}))
        
        with tab3:
            self.render_items_data(data.get('itens', []))
        
        with tab4:
            self.render_charts(data)
        
        with tab5:
            self.render_json_data(data)
    
    def render_general_data(self, data: Dict[str, Any]):
        """Renderiza dados gerais do documento"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📄 Informações do Documento")
            
            info_data = [
                ("Tipo", data.get('documento', 'N/A').upper()),
                ("Número", data.get('numero_documento', 'N/A')),
                ("Série", data.get('serie', 'N/A')),
                ("Moeda", data.get('moeda', 'N/A')),
                ("Forma Pagamento", data.get('forma_pagamento', 'N/A'))
            ]
            
            for label, value in info_data:
                st.markdown(f"**{label}:** {value}")
            
            # Chave NF-e em formato especial
            chave_nfe = data.get('chave_nfe', 'N/A')
            if chave_nfe != 'N/A':
                st.markdown("**Chave NF-e:**")
                st.code(chave_nfe, language=None)
        
        with col2:
            st.markdown("### 🏢 Partes Envolvidas")
            
            emitente = data.get('emitente', 'N/A')
            destinatario = data.get('destinatario', 'N/A')
            
            st.markdown(f"**Emitente:** {emitente}")
            st.markdown(f"**Destinatário:** {destinatario}")
            
            st.markdown("### 🏷️ Classificação Fiscal")
            
            fiscal_data = [
                ("CFOP", data.get('cfop', 'N/A')),
                ("NCM", data.get('ncm', 'N/A')),
                ("CST", data.get('cst', 'N/A'))
            ]
            
            for label, value in fiscal_data:
                st.markdown(f"**{label}:** {value}")
    
    def render_tax_data(self, impostos: Dict[str, Any]):
        """Renderiza dados de impostos com visualização melhorada"""
        st.markdown("### 💸 Detalhamento dos Impostos")
        
        if not impostos:
            st.info("ℹ️ Nenhuma informação de impostos encontrada no documento.")
            return
        
        # Métricas de impostos
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            icms_valor = impostos.get('icms_valor', 0)
            try:
                icms_valor = float(icms_valor or 0)
                icms_display = f"R$ {icms_valor:,.2f}"
            except (ValueError, TypeError):
                icms_display = "R$ 0,00"
            st.metric("ICMS", icms_display)
        
        with col2:
            pis_valor = impostos.get('pis_valor', 0)
            try:
                pis_valor = float(pis_valor or 0)
                pis_display = f"R$ {pis_valor:,.2f}"
            except (ValueError, TypeError):
                pis_display = "R$ 0,00"
            st.metric("PIS", pis_display)
        
        with col3:
            cofins_valor = impostos.get('cofins_valor', 0)
            try:
                cofins_valor = float(cofins_valor or 0)
                cofins_display = f"R$ {cofins_valor:,.2f}"
            except (ValueError, TypeError):
                cofins_display = "R$ 0,00"
            st.metric("COFINS", cofins_display)
        
        with col4:
            iss_valor = impostos.get('iss_valor', 0)
            try:
                iss_valor = float(iss_valor or 0)
                iss_display = f"R$ {iss_valor:,.2f}"
            except (ValueError, TypeError):
                iss_display = "R$ 0,00"
            st.metric("ISS", iss_display)
        
        # Detalhes expandidos
        with st.expander("🔍 Detalhes dos Impostos", expanded=False):
            col_a, col_b = st.columns(2)
            
            def safe_format_currency(value):
                try:
                    return f"R$ {float(value or 0):,.2f}"
                except (ValueError, TypeError):
                    return "R$ 0,00"
            
            def safe_format_percent(value):
                try:
                    return f"{float(value or 0):.2f}%"
                except (ValueError, TypeError):
                    return "0,00%"
            
            with col_a:
                st.markdown("#### ICMS")
                st.markdown(f"**Base de Cálculo:** {safe_format_currency(impostos.get('icms_base', 0))}")
                st.markdown(f"**Alíquota:** {safe_format_percent(impostos.get('icms_aliquota', 0))}")
                st.markdown(f"**Valor:** {safe_format_currency(impostos.get('icms_valor', 0))}")
                
                st.markdown("#### PIS")
                st.markdown(f"**Base de Cálculo:** {safe_format_currency(impostos.get('pis_base', 0))}")
                st.markdown(f"**Alíquota:** {safe_format_percent(impostos.get('pis_aliquota', 0))}")
                st.markdown(f"**Valor:** {safe_format_currency(impostos.get('pis_valor', 0))}")
            
            with col_b:
                st.markdown("#### COFINS")
                st.markdown(f"**Base de Cálculo:** {safe_format_currency(impostos.get('cofins_base', 0))}")
                st.markdown(f"**Alíquota:** {safe_format_percent(impostos.get('cofins_aliquota', 0))}")
                st.markdown(f"**Valor:** {safe_format_currency(impostos.get('cofins_valor', 0))}")
                
                st.markdown("#### ISS")
                st.markdown(f"**Base de Cálculo:** {safe_format_currency(impostos.get('iss_base', 0))}")
                st.markdown(f"**Alíquota:** {safe_format_percent(impostos.get('iss_aliquota', 0))}")
                st.markdown(f"**Valor:** {safe_format_currency(impostos.get('iss_valor', 0))}")
    
    def render_items_data(self, itens: List[Dict[str, Any]]):
        """Renderiza dados dos itens com tabela melhorada"""
        st.markdown("### 📦 Itens do Documento")
        
        if not itens:
            st.info("ℹ️ Nenhum item encontrado no documento.")
            return
        
        # Estatísticas dos itens
        total_items = len(itens)
        total_value = 0
        for item in itens:
            try:
                quantidade = float(item.get('quantidade', 0) or 0)
                valor_unitario = float(item.get('valor_unitario', 0) or 0)
                total_value += quantidade * valor_unitario
            except (ValueError, TypeError):
                continue
        avg_value = total_value / total_items if total_items > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Itens", total_items)
        
        with col2:
            st.metric("Valor Total", f"R$ {total_value:,.2f}")
        
        with col3:
            st.metric("Valor Médio", f"R$ {avg_value:,.2f}")
        
        # Tabela de itens
        if itens:
            # Prepara dados para a tabela
            table_data = []
            for i, item in enumerate(itens, 1):
                try:
                    quantidade = float(item.get('quantidade', 0) or 0)
                    valor_unitario = float(item.get('valor_unitario', 0) or 0)
                    valor_total = quantidade * valor_unitario
                except (ValueError, TypeError):
                    quantidade = 0
                    valor_unitario = 0
                    valor_total = 0
                
                # Safe string handling for None values
                descricao = item.get('descricao') or 'N/A'
                ncm = item.get('ncm') or 'N/A'
                cfop = item.get('cfop_item') or 'N/A'
                
                # Safe description truncation
                desc_display = descricao[:50] + ('...' if descricao and len(descricao) > 50 else '')
                
                table_data.append({
                    "Item": i,
                    "Descrição": desc_display,
                    "Quantidade": f"{quantidade:,.2f}",
                    "Valor Unit.": f"R$ {valor_unitario:,.2f}",
                    "Valor Total": f"R$ {valor_total:,.2f}",
                    "NCM": ncm,
                    "CFOP": cfop
                })
            
            # Cria DataFrame
            df = pd.DataFrame(table_data)
            
            # Mostra tabela
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Item": st.column_config.NumberColumn("Item", width="small"),
                    "Descrição": st.column_config.TextColumn("Descrição", width="large"),
                    "Quantidade": st.column_config.TextColumn("Qtd", width="small"),
                    "Valor Unit.": st.column_config.TextColumn("Valor Unit.", width="medium"),
                    "Valor Total": st.column_config.TextColumn("Valor Total", width="medium"),
                    "NCM": st.column_config.TextColumn("NCM", width="small"),
                    "CFOP": st.column_config.TextColumn("CFOP", width="small")
                }
            )
            
            # Opção de download
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Baixar tabela como CSV",
                data=csv,
                file_name=f"itens_nfe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    def render_charts(self, data: Dict[str, Any]):
        """Renderiza gráficos dos dados"""
        st.markdown("### 📊 Visualizações")
        
        itens = data.get('itens', [])
        impostos = data.get('impostos', {})
        
        if not itens and not impostos:
            st.info("ℹ️ Dados insuficientes para gerar gráficos.")
            return
        
        col1, col2 = st.columns(2)
        
        # Gráfico de impostos
        with col1:
            if impostos:
                st.markdown("#### 💸 Distribuição de Impostos")
                
                # Safe tax data collection
                def safe_float(value):
                    try:
                        return float(value or 0)
                    except (ValueError, TypeError):
                        return 0
                
                tax_data = {
                    'ICMS': safe_float(impostos.get('icms_valor', 0)),
                    'PIS': safe_float(impostos.get('pis_valor', 0)),
                    'COFINS': safe_float(impostos.get('cofins_valor', 0)),
                    'ISS': safe_float(impostos.get('iss_valor', 0))
                }
                
                # Remove impostos com valor zero - safe comparison
                tax_data = {k: v for k, v in tax_data.items() if v and v > 0}
                
                if tax_data:
                    fig_pie = px.pie(
                        values=list(tax_data.values()),
                        names=list(tax_data.keys()),
                        title="Distribuição de Impostos"
                    )
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("Nenhum imposto com valor > 0")
        
        # Gráfico de itens
        with col2:
            if itens and len(itens) > 1:
                st.markdown("#### 📦 Valor por Item")
                
                # Prepara dados dos itens (top 10)
                items_data = []
                for i, item in enumerate(itens[:10], 1):
                    try:
                        quantidade = float(item.get('quantidade', 0) or 0)
                        valor_unitario = float(item.get('valor_unitario', 0) or 0)
                        valor_total = quantidade * valor_unitario
                    except (ValueError, TypeError):
                        valor_total = 0
                    
                    descricao = item.get('descricao') or 'N/A'
                    # Safe description truncation for chart
                    desc_chart = descricao[:30] + ('...' if descricao and len(descricao) > 30 else '')
                    
                    items_data.append({
                        'Item': f"Item {i}",
                        'Valor': valor_total,
                        'Descrição': desc_chart
                    })
                
                df_items = pd.DataFrame(items_data)
                
                fig_bar = px.bar(
                    df_items,
                    x='Item',
                    y='Valor',
                    title="Valor por Item (Top 10)",
                    hover_data=['Descrição']
                )
                fig_bar.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Dados insuficientes para gráfico de itens")
        
        # Gráfico de linha temporal (se houver múltiplos processamentos)
        if len(st.session_state.processing_history) > 1:
            st.markdown("#### ⏱️ Histórico de Processamento")
            
            history_data = []
            for item in st.session_state.processing_history:
                if item['success']:
                    history_data.append({
                        'Timestamp': item['timestamp'],
                        'Tempo (s)': item.get('execution_time', 0),
                        'Arquivo': item['filename'],
                        'Tipo': item['file_type'].upper()
                    })
            
            if history_data:
                df_history = pd.DataFrame(history_data)
                
                fig_line = px.line(
                    df_history,
                    x='Timestamp',
                    y='Tempo (s)',
                    color='Tipo',
                    title="Tempo de Processamento por Tipo de Arquivo",
                    hover_data=['Arquivo']
                )
                st.plotly_chart(fig_line, use_container_width=True)
    
    def render_json_data(self, data: Dict[str, Any]):
        """Renderiza dados JSON completos"""
        st.markdown("### 🔍 Dados Estruturados Completos")
        
        # Opções de visualização
        col1, col2 = st.columns([3, 1])
        
        with col2:
            view_mode = st.selectbox(
                "Modo de visualização:",
                ["JSON Formatado", "JSON Compacto", "Python Dict"],
                key="json_view_mode"
            )
        
        with col1:
            if view_mode == "JSON Formatado":
                st.json(data)
            elif view_mode == "JSON Compacto":
                json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
                st.code(json_str, language="json")
            else:  # Python Dict
                st.code(str(data), language="python")
        
        # Botão de download
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 Baixar JSON",
            data=json_str,
            file_name=f"dados_nfe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    def render_results_compact(self, result: Dict[str, Any]):
        """Renderiza os resultados do processamento de forma compacta (sem expanders internos)"""
        if not result or not result.get('success'):
            error_msg = result.get('error', 'Erro desconhecido') if result else 'Resultado inválido'
            st.error(f"❌ Erro no processamento: {error_msg}")
            return
        
        data = result.get('data', {})
        processing_time = result.get('processing_time', 0)
        
        # Cabeçalho de sucesso
        st.success(f"✅ Documento processado com sucesso em {processing_time:.2f}s")
        
        # Métricas principais compactas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            valor_total = data.get('valor_total', 0)
            try:
                valor_total = float(valor_total or 0)
                valor_display = f"R$ {valor_total:,.2f}"
            except (ValueError, TypeError):
                valor_display = "R$ 0,00"
            st.metric("💰 Valor Total", valor_display)
        
        with col2:
            data_emissao = data.get('data_emissao', 'N/A')
            st.metric("📅 Data Emissão", data_emissao)
        
        with col3:
            cfop = data.get('cfop', 'N/A')
            st.metric("🏷️ CFOP", cfop)
        
        with col4:
            itens_count = len(data.get('itens', []))
            st.metric("📦 Itens", itens_count)
        
        # Dados básicos sem abas
        st.markdown("#### 📋 Dados Gerais")
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown(f"**Emitente:** {data.get('emitente', 'N/A')}")
            st.markdown(f"**Número:** {data.get('numero_documento', 'N/A')}")
            st.markdown(f"**Série:** {data.get('serie', 'N/A')}")
        
        with col_b:
            st.markdown(f"**Destinatário:** {data.get('destinatario', 'N/A')}")
            st.markdown(f"**Tipo:** {data.get('documento', 'N/A').upper()}")
            st.markdown(f"**NCM:** {data.get('ncm', 'N/A')}")
        
        # Impostos compactos (sem expander)
        impostos = data.get('impostos', {})
        if impostos:
            st.markdown("#### 💸 Impostos")
            tax_col1, tax_col2, tax_col3, tax_col4 = st.columns(4)
            
            def safe_format_currency(value):
                try:
                    return f"R$ {float(value or 0):,.2f}"
                except (ValueError, TypeError):
                    return "R$ 0,00"
            
            with tax_col1:
                st.metric("ICMS", safe_format_currency(impostos.get('icms_valor', 0)))
            with tax_col2:
                st.metric("PIS", safe_format_currency(impostos.get('pis_valor', 0)))
            with tax_col3:
                st.metric("COFINS", safe_format_currency(impostos.get('cofins_valor', 0)))
            with tax_col4:
                st.metric("ISS", safe_format_currency(impostos.get('iss_valor', 0)))
        
        # Resumo dos itens (sem tabela completa)
        itens = data.get('itens', [])
        if itens:
            st.markdown(f"#### 📦 Itens ({len(itens)} encontrados)")
            
            # Mostra apenas os primeiros 3 itens
            for i, item in enumerate(itens[:3], 1):
                descricao = item.get('descricao', 'N/A')
                try:
                    quantidade = float(item.get('quantidade', 0) or 0)
                    valor_unitario = float(item.get('valor_unitario', 0) or 0)
                    valor_total = quantidade * valor_unitario
                    valor_str = f"R$ {valor_total:,.2f}"
                except (ValueError, TypeError):
                    valor_str = "R$ 0,00"
                
                desc_short = descricao[:40] + ('...' if descricao and len(descricao) > 40 else '')
                st.markdown(f"**{i}.** {desc_short} - {valor_str}")
            
            if len(itens) > 3:
                st.markdown(f"... e mais {len(itens) - 3} itens")

    def run(self):
        """Executa a aplicação principal"""
        try:
            self.render_header()
            self.render_sidebar()
            
            # Seção principal
            result = self.render_upload_section()
            
            # Mostra resultados se houver
            if result:
                self.render_results(result)
            elif st.session_state.last_result:
                # Mostra último resultado se disponível
                with st.expander("📋 Último resultado processado", expanded=False):
                    self.render_results_compact(st.session_state.last_result)
            
        except Exception as e:
            self.logger.error(f"Erro na aplicação: {str(e)}")
            st.error(f"❌ Erro na aplicação: {str(e)}")
            
            # Botão para reiniciar
            if st.button("🔄 Reiniciar Aplicação"):
                st.session_state.clear()
                st.rerun()


# Execução da aplicação
if __name__ == "__main__":
    app = ContabilidadeApp()
    app.run()

