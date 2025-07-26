from agno.agent import Agent, RunResponse
from agno.models.google import Gemini
from agno.tools.sql import SQLTools
from sqlalchemy import create_engine
from dotenv import load_dotenv
from datetime import datetime
import streamlit as st
import time
import os
from helpers import speetch_to_text
import json
import re
from dashboard import carregar_dados

# Configuração inicial
load_dotenv()
data_atual = datetime.now().date()

# Constantes
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
DB_PATH = 'sqlite:///./gastos_receita.db'

# Instruções do sistema
SYSTEM_INSTRUCTIONS = f'''
# System Message - Assistente Financeiro SQLite

Voce tem que adicionar os gastos no formato de data YYYY/MM/DD

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

O objetivo é proporcionar uma experiência de gestão financeira intuitiva, automatizada e inteligente através de linguagem natural e escrevendo em markdown para ficar mais legível.
'''

# Inicialização do agente
engine = create_engine(DB_PATH)
agente = Agent(
    model=Gemini(id='gemini-2.0-flash-001', api_key=GEMINI_API_KEY),
    add_history_to_messages=True,
    markdown=False,
    show_tool_calls=True,
    retries=3,
    system_message=SYSTEM_INSTRUCTIONS,
    tools=[SQLTools(db_engine=engine)],
    store_events=True
)

# Configuração do Streamlit
st.set_page_config(page_icon='🤖', page_title='economiza.ai', layout="wide")

# Inicializar estado da sessão
if "messages" not in st.session_state:
    st.session_state.messages = []

# Função para processar áudio
def processar_audio(audio_file):
    """Processa áudio e retorna transcrição"""
    try:
        audio_transcrito = speetch_to_text(audio=audio_file)
        transcricao_dict = json.loads(audio_transcrito)
        
        # Extrair texto usando regex
        match = re.search(r'text=[\'"]([^\'"]+)[\'"]', str(transcricao_dict))
        texto_extraido = match.group(1) if match else None
        
        if texto_extraido:
            return texto_extraido
        else:
            # Tentar extrair diretamente do dict
            if isinstance(transcricao_dict, dict) and 'text' in transcricao_dict:
                return transcricao_dict['text']
            return 'Não foi possível transcrever o áudio'
    
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
            # Obter resposta do agente
            response = agente.run(content)
            
            # Extrair query SQL se houver
            query = ""
            if hasattr(response, 'tools') and response.tools:
                query = response.tools[0].tool_args.get('query', '')
                with st.expander("🔍 Ver SQL executado"):
                    st.code(query, language='sql')
            
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
    # Header
    st.title('🤖 economiza.ai')
    st.caption('Seu assistente financeiro inteligente')
    
    # Container principal com duas colunas
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Container de chat
        chat_container = st.container()
        
        # Renderizar histórico de mensagens
        with chat_container:
            for msg in st.session_state.messages:
                renderizar_mensagem(msg)
        
        # Área de input
        st.markdown("---")
        
        # Tabs de input
        tab1, tab2 = st.tabs(["💬 Texto", "🎤 Áudio"])
        
        # Tab de texto
        with tab1:
            if prompt := st.chat_input("Digite sua mensagem..."):
                processar_resposta(prompt, "text")
                st.rerun()
        
        # Tab de áudio
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
        # Resumo de transações recentes
        st.markdown("### 📋 Transações Recentes")
        
        df = carregar_dados()
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
        if st.button("🔄 Atualizar", key="refresh_chat", use_container_width=True):
            st.rerun()
        
        if st.button("🗑️ Limpar Conversa", key="clear_chat", use_container_width=True):
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