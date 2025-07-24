from agno.agent import Agent, RunResponse
from agno.models.google import Gemini
from agno.tools.sql import SQLTools
from sqlalchemy import create_engine
from dotenv import load_dotenv
from datetime import datetime
import streamlit as st
import time
from typing import Optional, List
import base64
import os

data_atual = datetime.now().date()

load_dotenv()

instructions = '''
# System Message - Assistente Financeiro SQLite

**Identificação**: Sempre se apresente como "🤖 economiza.ai: [seu conteúdo]"

Você é um assistente financeiro especializado em SQLite que gerencia automaticamente a tabela `receita_gastos` através de linguagem natural, executando operações de forma inteligente e proativa.

## Estrutura da Tabela: `receita_gastos`

|Campo|Tipo|Descrição|
|---|---|---|
|Data|DATE|Data da transação (padrão: data atual)|
|Descrição|TEXT|Descrição clara da transação|
|Valor|REAL|Valor monetário (sempre positivo)|
|Categorias|TEXT|Categoria predefinida|
|Tipo|TEXT|"Ativo" (receita) ou "Passivo" (gasto)|

## Categorias Predefinidas

- **Alimentação**: Restaurantes, supermercado, delivery, lanches, mercado
- **Transporte**: Gasolina, Uber, ônibus, estacionamento, manutenção
- **Saúde**: Consultas, remédios, farmácia, psicólogo, autocuidado
- **Casa**: Internet, contas, ração pet, limpeza, móveis, utilidades
- **Compras**: Roupas, eletrônicos, barbeador, celular, acessórios
- **Entretenimento**: Streaming, cinema, jogos, Netflix, Spotify
- **Educação**: Livros, cursos, mensalidades, materiais
- **Receita**: Salários, diárias, vendas, rendimentos

## Inteligência Preditiva

### Processamento Automático

Execute operações imediatamente sem solicitar confirmações desnecessárias. Inferir informações baseado no contexto:

**Padrões de Entrada → Classificação Automática:**

```
"Gastei 20 reais com ração" → Data: {data_atual}, Descrição: "Ração", Valor: 20, Categoria: "Casa", Tipo: "Passivo"

"Comprei barbeador por 84" → Data: {data_atual}, Descrição: "Barbeador", Valor: 84, Categoria: "Compras", Tipo: "Passivo"

"Recebi 1500 de diárias" → Data: {data_atual}, Descrição: "Diárias", Valor: 1500, Categoria: "Receita", Tipo: "Ativo"

"Paguei 120 na consulta" → Data: {data_atual}, Descrição: "Consulta médica", Valor: 120, Categoria: "Saúde", Tipo: "Passivo"
```

### Detecção de Contexto

**Indicadores de Tipo:**

- **Passivo**: "gastei", "comprei", "paguei", "despesa"
- **Ativo**: "recebi", "salário", "diárias", "venda", "ganho"

**Classificação por Palavra-chave:**

- Identifique automaticamente a categoria através de termos relacionados
- Use sempre a data atual para novos registros
- Converta valores textuais para numérico (ex: "84 reais" → 84.0)

## Operações Automáticas

### Execução Imediata Para:

1. **Inserção**: Detectar menções de gastos/receitas e adicionar automaticamente
2. **Consulta**: Responder perguntas sobre gastos, totais, períodos
3. **Análise**: Calcular somas, médias, comparações por categoria/período
4. **Edição**: Corrigir registros quando solicitado
5. **Exclusão**: Remover transações específicas

### Filtros Inteligentes:

- **Temporal**: "este mês", "semana passada", "últimos 30 dias"
- **Categoria**: "gastos com alimentação", "receitas do trabalho"
- **Valor**: "gastos acima de 100", "menores despesas"

## Comunicação e Resposta

### Formato de Resposta:

- **Confirmação**: "Gasto registrado: [descrição] - R$ [valor] ([categoria])"
- **Análise**: Apresente dados em formato claro com totais e percentuais
- **Sugestões**: Ofereça insights sobre padrões de gastos quando relevante

### Exemplos de Interação:

**Usuário**: "Comprei um livro por 50 reais" **SQL Executado**:

```sql
INSERT INTO receita_gastos (Data, Descrição, Valor, Categorias, Tipo) 
VALUES (DATE('now'), 'Livro', 50.0, 'Educação', 'Passivo');
```

**Resposta**: "🤖 economiza.ai: Gasto registrado com sucesso! Livro - R$ 50,00 (Educação)"

**Usuário**: "Quanto gastei este mês?" **SQL Executado**:

```sql
SELECT SUM(Valor) as Total FROM receita_gastos 
WHERE Tipo = 'Passivo' AND strftime('%Y-%m', Data) = strftime('%Y-%m', 'now');
```

## Diretrizes Operacionais

### Seja Proativo:

- Execute ações imediatamente quando o contexto for claro
- Não peça confirmações para operações básicas de inserção
- Sugira análises relevantes após inserções
- Ofereça insights sobre padrões financeiros

### Mantenha Precisão:

- Valide valores numéricos
- Garanta classificação correta de categorias
- Use sempre data atual para novos registros
- Mantenha consistência na nomenclatura

### Comunicação Natural:

- Use linguagem conversacional e amigável
- Formate números monetários adequadamente (R$ X,XX)
- Apresente resumos claros e organizados
- Seja conciso mas informativo

O objetivo é proporcionar uma experiência de gestão financeira intuitiva, automatizada e inteligente através de linguagem natural.
"""
'''

gemini_api = os.getenv('GEMINI_API_KEY')

engine = create_engine('sqlite:///./gastos_receita.db')

agente = Agent(
    model=Gemini(id='gemini-2.0-flash-001', api_key=gemini_api),
    add_history_to_messages=True,
    markdown=False,
    show_tool_calls=True,
    retries=3,
    system_message=instructions,
    tools=[SQLTools(db_engine=engine)],
    store_events=True
)


# Config
st.set_page_config(page_icon='🤖', page_title=' economiza.ai', layout="wide")

# Inicializar estados
def init_session_state():
    """Inicializa os estados da sessão com cache management"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "uploaded_images" not in st.session_state:
        st.session_state.uploaded_images = []
    if "audio_processed" not in st.session_state:
        st.session_state.audio_processed = set()

@st.cache_data
def process_image(file_bytes: bytes, filename: str) -> dict:
    """Processa e cacheia imagens PNG"""
    return {
        "name": filename,
        "data": base64.b64encode(file_bytes).decode(),
        "size": len(file_bytes)
    }

def render_message(message: dict):
    """Renderiza uma mensagem no chat"""
    with st.chat_message(message["role"]):
        if message["role"] == "assistant" and "query" in message:
            st.caption(f"🔍 {message['query']}")
        
        st.write(message["content"])
        
        # Mostrar imagens anexadas se houver
        if "images" in message:
            cols = st.columns(min(len(message["images"]), 3))
            for idx, img in enumerate(message["images"]):
                with cols[idx % 3]:
                    st.image(f"data:image/png;base64,{img['data']}", 
                            caption=img['name'], 
                            use_container_width=True)

def simulate_streaming(content: str, placeholder):
    """Simula streaming de texto para melhor UX"""
    full_response = ""
    chunk_size = 15
    
    for i in range(0, len(content), chunk_size):
        chunk = content[i:i+chunk_size]
        full_response += chunk
        placeholder.write(full_response + "▌")
        time.sleep(0.03)
    
    placeholder.write(full_response)
    return full_response

# Estados iniciais
if "messages" not in st.session_state:
    st.session_state.messages = []
if "media_cache" not in st.session_state:
    st.session_state.media_cache = []

# Funções auxiliares
@st.cache_data
def process_media(data: bytes, filename: str, media_type: str) -> dict:
    """Processa e cacheia mídia"""
    return {
        "type": media_type,
        "name": filename,
        "data": base64.b64encode(data).decode(),
        "timestamp": datetime.now().strftime("%H:%M")
    }

def render_message(msg: dict):
    """Renderiza mensagem adaptada ao tipo de conteúdo"""
    with st.chat_message(msg["role"]):
        # Indicador de tipo de input
        if msg.get("input_type") and msg["role"] == "user":
            icon = {"text": "💬", "audio": "🎤", "camera": "📸", "file": "📎"}
            st.caption(f"{icon.get(msg['input_type'], '💬')} via {msg['input_type']}")
        
        # Query do assistente
        if msg["role"] == "assistant" and msg.get("query"):
            st.caption(f"🔍 {msg['query']}")
        
        # Conteúdo principal
        st.write(msg["content"])
        
        # Mídia anexada
        if media := msg.get("media"):
            cols = st.columns(min(len(media), 3))
            for i, m in enumerate(media):
                with cols[i % 3]:
                    if m["type"] in ["camera", "file"]:
                        st.image(f"data:image/png;base64,{m['data']}", 
                                caption=f"{m['name']} - {m['timestamp']}")
                    elif m["type"] == "audio":
                        st.info(f"🎵 Áudio: {m['timestamp']}")

def process_input(content: str, input_type: str, media: list = None):
    """Processa input e gera resposta adaptada"""
    # Mensagem do usuário
    user_msg = {
        "role": "user",
        "content": content,
        "input_type": input_type,
        "media": media or []
    }
    st.session_state.messages.append(user_msg)
    
    # Resposta do assistente
    with st.chat_message("assistant"):
        try:
            # Simular processamento baseado no tipo
            response = agente.run(content)
            
            # Adaptar resposta ao tipo de input
            prefix = {
                "audio": "🎤 Transcrição processada: ",
                "camera": "📸 Análise da imagem: ",
                "file": "📎 Arquivo analisado: ",
                "text": ""
            }
            
            # Query e conteúdo
            query = response.tools[0].tool_args.get('query', '') if hasattr(response, 'tools') and response.tools else ""
            if query:
                st.caption(f"🔍 {query}")
            
            # Streaming
            content = prefix.get(input_type, "") + (response.content if hasattr(response, 'content') else str(response))
            placeholder = st.empty()
            full_text = ""
            
            for chunk in [content[i:i+20] for i in range(0, len(content), 20)]:
                full_text += chunk
                placeholder.write(full_text + "▌")
                time.sleep(0.02)
            
            placeholder.write(full_text)
            
            # Salvar resposta
            assistant_msg = {"role": "assistant", "content": full_text}
            if query:
                assistant_msg["query"] = query
            st.session_state.messages.append(assistant_msg)
            
        except Exception as e:
            st.error(f"❌ Erro: {e}")

# Interface principal
st.header('🤖 economiza.ai')
st.subheader('Chat')

# Tabs de input
tab1, tab2, tab3, tab4 = st.tabs(["💬 Texto", "🎤 Áudio", "📸 Câmera", "📎 Arquivo"])

with tab1:
    if prompt := st.chat_input("Digite sua mensagem..."):
        process_input(prompt, "text", st.session_state.media_cache)
        st.session_state.media_cache = []
        st.rerun()

with tab2:
    col1, col2 = st.columns([3, 1])
    with col1:
        audio = st.audio_input("Gravar mensagem")
    with col2:
        st.write(' ')
        st.write(' ')
        if st.button("📤 Enviar", key="send_audio", disabled=not audio):
            if audio:
                # Simular transcrição
                transcription = "Transcrição do áudio capturado"
                media = [process_media(audio.read(), f"audio_{datetime.now().strftime('%H%M%S')}.wav", "audio")]
                process_input(transcription, "audio", media)
                st.rerun()

with tab3:
    col1, col2 = st.columns([3, 1])
    with col1:
        enable = st.checkbox('Ative a câmera')
        photo = st.camera_input("Tirar foto", disabled=not enable)
    with col2:
        st.write(' ')
        st.write(' ')
        if st.button("📤 Enviar", key="send_photo", disabled=not photo):
            if photo:
                media = [process_media(photo.read(), f"foto_{datetime.now().strftime('%H%M%S')}.png", "camera")]
                process_input("Analisar esta imagem", "camera", media)
                st.rerun()

with tab4:
    col1, col2 = st.columns([3, 1])
    with col1:
        files = st.file_uploader("Anexar PNG", type=['png'], accept_multiple_files=True)
        if files:
            st.session_state.media_cache = [
                process_media(f.read(), f.name, "file") for f in files
            ]
            st.info(f"📎 {len(files)} arquivo(s) anexado(s)")
    with col2:
        st.write(' ')
        st.write(' ')
        if st.button("📤 Enviar", key="send_files", disabled=not files):
            if st.session_state.media_cache:
                process_input(f"Analisar {len(st.session_state.media_cache)} arquivo(s)", "file")
                st.rerun()

# Chat container
for msg in st.session_state.messages:
    render_message(msg)

# Preview de mídia anexada
if st.session_state.media_cache:
    with st.expander(f"📎 Mídia anexada ({len(st.session_state.media_cache)})"):
        cols = st.columns(4)
        for i, m in enumerate(st.session_state.media_cache):
            with cols[i % 4]:
                st.image(f"data:image/png;base64,{m['data']}", caption=m['name'])

# Sidebar
with st.sidebar:
    st.metric("💬 Mensagens", len(st.session_state.messages))
    st.metric("📎 Mídias", sum(len(m.get("media", [])) for m in st.session_state.messages))
    
    if st.button("🗑️ Limpar"):
        st.session_state.clear()
        st.rerun()