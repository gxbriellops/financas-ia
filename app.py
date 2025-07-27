from agno.agent import Agent, RunResponse
from agno.models.google import Gemini
from agno.tools.sql import SQLTools
from datetime import datetime
import streamlit as st
import time
import json
import re

# Importar módulos customizados
from auth import check_auth, login_page, logout, get_user_info
from database import get_database_engine, carregar_dados, invalidate_cache
from config import get_api_keys, get_app_config, get_system_instructions
from helpers import speetch_to_text, extract_text_from_transcription

# Configuração inicial
config = get_app_config()

# Cache do agente AI
@st.cache_resource
def get_ai_agent():
    """Inicializa e retorna o agente AI com cache"""
    api_keys = get_api_keys()
    engine = get_database_engine()
    
    agente = Agent(
        model=Gemini(id='gemini-2.0-flash-001', api_key=api_keys['GEMINI_API_KEY']),
        add_history_to_messages=True,
        markdown=False,
        show_tool_calls=True,
        retries=3,
        system_message=get_system_instructions(),
        tools=[SQLTools(db_engine=engine)],
        store_events=True
    )
    return agente

# Configuração do Streamlit
st.set_page_config(
    page_icon=config['app_icon'], 
    page_title=config['app_name'], 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Verificar autenticação
if not check_auth():
    login_page()
    st.stop()

# Inicializar estado da sessão
if "messages" not in st.session_state:
    st.session_state.messages = []

# Função para processar áudio
def processar_audio(audio_file):
    """Processa áudio e retorna transcrição"""
    try:
        audio_transcrito = speetch_to_text(audio=audio_file)
        return extract_text_from_transcription(audio_transcrito)
    except Exception as e:
        st.error(f"Erro ao processar áudio: {e}")
        return "Erro na transcrição do áudio"

# Função para renderizar mensagem
def renderizar_mensagem(msg):
    """Renderiza uma mensagem no chat"""
    with st.chat_message(msg["role"]):
        # Indicador de tipo de input
        if msg.get("input_type") and msg["role"] == "user":
            icons = {"text": "💬", "audio": "🎤"}
            st.caption(f"{icons.get(msg['input_type'], '💬')} via {msg['input_type']}")
        
        # Query do assistente
        if msg["role"] == "assistant" and msg.get("query"):
            with st.expander("🔍 Ver SQL executado"):
                st.code(msg['query'], language='sql')
        
        # Conteúdo principal
        st.write(msg["content"])

# Função para processar resposta do agente
def processar_resposta(content, input_type="text"):
    """Processa input e gera resposta do agente"""
    # Adicionar mensagem do usuário
    user_msg = {
        "role": "user",
        "content": content,
        "input_type": input_type
    }
    st.session_state.messages.append(user_msg)
    
    # Gerar resposta do assistente
    with st.chat_message("assistant"):
        try:
            # Obter agente
            agente = get_ai_agent()
            
            # Obter resposta
            response = agente.run(content)
            
            # Extrair query SQL se houver
            query = ""
            if hasattr(response, 'tools') and response.tools:
                query = response.tools[0].tool_args.get('query', '')
                with st.expander("🔍 Ver SQL executado"):
                    st.code(query, language='sql')
                
                # Invalidar cache se for operação de escrita
                if any(cmd in query.upper() for cmd in ['INSERT', 'UPDATE', 'DELETE']):
                    invalidate_cache()
            
            # Extrair conteúdo da resposta
            response_content = response.content if hasattr(response, 'content') else str(response)
            
            # Adicionar prefixo se for áudio
            if input_type == "audio":
                response_content = "🎤 Áudio processado: " + response_content
            
            # Mostrar resposta com efeito de streaming
            placeholder = st.empty()
            full_text = ""
            for chunk in [response_content[i:i+20] for i in range(0, len(response_content), 20)]:
                full_text += chunk
                placeholder.markdown(full_text + "▌")
                time.sleep(0.02)
            placeholder.markdown(full_text)
            
            # Salvar resposta
            assistant_msg = {"role": "assistant", "content": full_text}
            if query:
                assistant_msg["query"] = query
            st.session_state.messages.append(assistant_msg)
            
        except Exception as e:
            st.error(f"❌ Erro ao processar: {e}")

# Função da página de chat
def chat_page():
    """Página principal do chat"""
    # Sidebar com informações do usuário
    with st.sidebar:
        st.markdown(f"### 👤 {get_user_info()['username']}")
        st.caption(f"Logado há {int(get_user_info()['session_duration'] // 60)} minutos")
        
        if st.button("🚪 Sair", use_container_width=True):
            logout()
        
        st.markdown("---")
        
        # Resumo financeiro
        st.markdown("### 💰 Resumo Financeiro")
        
        engine = get_database_engine()
        df = carregar_dados(engine)
        
        if not df.empty:
            receitas = df[df['Tipo'] == 'Ativo']['Valor'].sum()
            gastos = df[df['Tipo'] == 'Passivo']['Valor'].sum()
            saldo = receitas - gastos
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Receitas", f"R$ {receitas:,.0f}")
            with col2:
                st.metric("Gastos", f"R$ {gastos:,.0f}")
            
            st.metric(
                "Saldo", 
                f"R$ {saldo:,.0f}",
                delta=f"{(saldo/gastos*100):.0f}%" if gastos > 0 else "∞"
            )
        else:
            st.info("Nenhuma transação ainda")
    
    # Header principal
    st.title(f'{config["app_icon"]} {config["app_name"]}')
    st.caption('Seu assistente financeiro inteligente com IA')
    
    # Container principal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Container de chat
        chat_container = st.container()
        
        # Renderizar histórico
        with chat_container:
            for msg in st.session_state.messages:
                renderizar_mensagem(msg)
        
        # Área de input
        st.markdown("---")
        
        # Tabs de input
        tab1, tab2 = st.tabs(["💬 Texto", "🎤 Áudio"])
        
        with tab1:
            if prompt := st.chat_input("Digite sua mensagem..."):
                processar_resposta(prompt, "text")
                st.rerun()
        
        with tab2:
            col_audio1, col_audio2 = st.columns([3, 1])
            with col_audio1:
                audio_data = st.audio_input("Gravar mensagem de voz")
            with col_audio2:
                st.write(' ')
                st.write(' ')
                if st.button("📤 Enviar", key="send_audio", disabled=not audio_data, use_container_width=True):
                    if audio_data:
                        transcricao = processar_audio(audio_data)
                        processar_resposta(transcricao, "audio")
                        st.rerun()
    
    with col2:
        # Transações recentes
        st.markdown("### 📋 Transações Recentes")
        
        engine = get_database_engine()
        df = carregar_dados(engine)
        
        if not df.empty:
            # Preparar dados
            df_recent = df.head(5).copy()
            df_recent['Data'] = df_recent['Data'].astype(str).str.replace(r'\s00:00:00$', '', regex=True)
            df_recent['Valor_Display'] = df_recent.apply(
                lambda x: f"+R$ {x['Valor']:.0f}" if x['Tipo'] == 'Ativo' else f"-R$ {x['Valor']:.0f}",
                axis=1
            )
            
            # Exibir transações
            for _, row in df_recent.iterrows():
                tipo_icon = "💰" if row['Tipo'] == 'Ativo' else "💸"
                cor = "green" if row['Tipo'] == 'Ativo' else "red"
                
                st.markdown(f"""
                <div style="padding: 10px; margin: 5px 0; border-left: 3px solid {cor}; background-color: rgba(128,128,128,0.1);">
                    <div style="font-size: 12px; color: gray;">{row['Data']}</div>
                    <div>{tipo_icon} <strong>{row['Descrição']}</strong></div>
                    <div style="color: {cor}; font-weight: bold;">{row['Valor_Display']}</div>
                    <div style="font-size: 11px; color: gray;">{row['Categorias']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhuma transação ainda")
        
        # Botões de ação
        st.markdown("---")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🔄 Atualizar", key="refresh_chat", use_container_width=True):
                invalidate_cache()
                st.rerun()
        
        with col_btn2:
            if st.button("🗑️ Limpar Chat", key="clear_chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

# Configuração da navegação
pages = [
    st.Page(chat_page, title="Chat", icon="💬"),
    st.Page("dashboard.py", title="Dashboard", icon="📊")
]

# Executar navegação
pg = st.navigation(pages)
pg.run()