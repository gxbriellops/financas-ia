from agno.agent import Agent, RunResponse
from agno.models.google import Gemini
from agno.tools.sql import SQLTools
from sqlalchemy import create_engine
from dotenv import load_dotenv
from datetime import datetime
import streamlit as st
import time
from typing import Optional, List, Dict, Any
import base64
import os
from helpers import vision, speech_to_text
import json
import tempfile

# Configuração inicial
load_dotenv()
data_atual = datetime.now().date()

# Constantes
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
DB_PATH = 'sqlite:///./gastos_receita.db'
CHUNK_SIZE = 20
SLEEP_TIME = 0.02

# Instruções do sistema
SYSTEM_INSTRUCTIONS = f'''
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

# Classes de dados para melhor organização
class MediaData:
    """Encapsula dados de mídia processada"""
    def __init__(self, data: bytes, filename: str, media_type: str):
        self.type = media_type
        self.name = filename
        self.data = base64.b64encode(data).decode()
        self.timestamp = datetime.now().strftime("%H:%M")
        self.raw_data = data
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "name": self.name,
            "data": self.data,
            "timestamp": self.timestamp
        }

class AudioProcessor:
    """Processa áudio usando a função auxiliar speech_to_text"""
    @staticmethod
    def process(audio_data: bytes) -> str:
        """Processa áudio e retorna transcrição"""
        try:
            # Salvar temporariamente o áudio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_file.write(audio_data)
                tmp_file_path = tmp_file.name
            
            # Transcrever usando a função auxiliar
            transcription_json = speech_to_text(tmp_file_path)
            transcription_data = json.loads(transcription_json)
            
            # Limpar arquivo temporário
            os.unlink(tmp_file_path)
            
            # Extrair texto da transcrição
            return transcription_data.get('text', 'Não foi possível transcrever o áudio')
        
        except Exception as e:
            st.error(f"Erro ao processar áudio: {e}")
            return "Erro na transcrição do áudio"

class ImageProcessor:
    """Processa imagens usando a função auxiliar vision"""
    @staticmethod
    def process(image_data: str) -> str:
        """Processa imagem e retorna análise financeira"""
        try:
            # Adicionar prefixo data URL se necessário
            if not image_data.startswith('data:'):
                image_data = f"data:image/png;base64,{image_data}"
            
            # Analisar usando a função auxiliar
            vision_response = vision(image_data)
            return vision_response.content
        
        except Exception as e:
            st.error(f"Erro ao processar imagem: {e}")
            return "Erro na análise da imagem"

class SessionStateManager:
    """Gerencia o estado da sessão"""
    @staticmethod
    def initialize():
        """Inicializa todos os estados necessários"""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "media_cache" not in st.session_state:
            st.session_state.media_cache = []
        if "processed_audio" not in st.session_state:
            st.session_state.processed_audio = set()

class MessageRenderer:
    """Renderiza mensagens no chat"""
    @staticmethod
    def render(msg: Dict[str, Any]):
        """Renderiza uma mensagem com suporte a mídia"""
        with st.chat_message(msg["role"]):
            # Indicador de tipo de input
            if msg.get("input_type") and msg["role"] == "user":
                icons = {"text": "💬", "audio": "🎤", "camera": "📸", "file": "📎"}
                st.caption(f"{icons.get(msg['input_type'], '💬')} via {msg['input_type']}")
            
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
                            st.info(f"🎵 Áudio processado: {m['timestamp']}")

class StreamingWriter:
    """Gerencia escrita com efeito de streaming"""
    @staticmethod
    def write(content: str, placeholder) -> str:
        """Escreve conteúdo com efeito de streaming"""
        full_text = ""
        for chunk in [content[i:i+CHUNK_SIZE] for i in range(0, len(content), CHUNK_SIZE)]:
            full_text += chunk
            placeholder.write(full_text + "▌")
            time.sleep(SLEEP_TIME)
        placeholder.write(full_text)
        return full_text

class InputProcessor:
    """Processa diferentes tipos de input"""
    def __init__(self, agent: Agent):
        self.agent = agent
        self.audio_processor = AudioProcessor()
        self.image_processor = ImageProcessor()
    
    def process(self, content: str, input_type: str, media: List[Dict[str, Any]] = None):
        """Processa input e gera resposta"""
        # Processar conteúdo baseado no tipo
        processed_content = self._preprocess_content(content, input_type, media)
        
        # Adicionar mensagem do usuário
        user_msg = {
            "role": "user",
            "content": processed_content,
            "input_type": input_type,
            "media": media or []
        }
        st.session_state.messages.append(user_msg)
        
        # Gerar e renderizar resposta
        self._generate_response(processed_content, input_type)
    
    def _preprocess_content(self, content: str, input_type: str, media: List[Dict[str, Any]]) -> str:
        """Preprocessa conteúdo baseado no tipo de input"""
        if input_type == "audio":
            return content  # Já processado
        elif input_type == "camera" and media:
            # Processar imagem e adicionar análise ao conteúdo
            image_analysis = self.image_processor.process(media[0]["data"])
            return f"{content}\n\nAnálise da imagem: {image_analysis}"
        elif input_type == "file" and media:
            # Processar múltiplas imagens se necessário
            analyses = []
            for m in media:
                analysis = self.image_processor.process(m["data"])
                analyses.append(f"- {m['name']}: {analysis}")
            return f"{content}\n\nAnálises:\n" + "\n".join(analyses)
        return content
    
    def _generate_response(self, content: str, input_type: str):
        """Gera resposta do assistente"""
        with st.chat_message("assistant"):
            try:
                # Obter resposta do agente
                response = self.agent.run(content)
                
                # Preparar conteúdo da resposta
                prefix = self._get_response_prefix(input_type)
                query = self._extract_query(response)
                
                if query:
                    st.caption(f"🔍 {query}")
                
                # Streaming da resposta
                response_content = self._extract_content(response)
                full_content = prefix + response_content
                
                placeholder = st.empty()
                final_text = StreamingWriter.write(full_content, placeholder)
                
                # Salvar resposta
                assistant_msg = {"role": "assistant", "content": final_text}
                if query:
                    assistant_msg["query"] = query
                st.session_state.messages.append(assistant_msg)
                
            except Exception as e:
                st.error(f"❌ Erro ao processar: {e}")
    
    def _get_response_prefix(self, input_type: str) -> str:
        """Retorna prefixo baseado no tipo de input"""
        prefixes = {
            "audio": "🎤 Áudio processado: ",
            "camera": "📸 Análise visual: ",
            "file": "📎 Arquivos analisados: ",
            "text": ""
        }
        return prefixes.get(input_type, "")
    
    def _extract_query(self, response) -> str:
        """Extrai query SQL da resposta"""
        if hasattr(response, 'tools') and response.tools:
            return response.tools[0].tool_args.get('query', '')
        return ""
    
    def _extract_content(self, response) -> str:
        """Extrai conteúdo da resposta"""
        if hasattr(response, 'content'):
            return response.content
        return str(response)

# Função principal
def main():
    """Função principal da aplicação"""
    # Inicializar estado
    SessionStateManager.initialize()
    
    # Inicializar processador
    processor = InputProcessor(agente)
    
    # Header
    st.header('🤖 economiza.ai')
    st.subheader('Assistente Financeiro Inteligente')
    
    # Tabs de input
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Texto", "🎤 Áudio", "📸 Câmera", "📎 Arquivo"])
    
    with tab1:
        handle_text_input(processor)
    
    with tab2:
        handle_audio_input(processor)
    
    with tab3:
        handle_camera_input(processor)
    
    with tab4:
        handle_file_input(processor)
    
    # Renderizar histórico de mensagens
    for msg in st.session_state.messages:
        MessageRenderer.render(msg)
    
    # Preview de mídia anexada
    show_media_preview()
    
    # Sidebar com métricas
    show_sidebar_metrics()

def handle_text_input(processor: InputProcessor):
    """Gerencia input de texto"""
    if prompt := st.chat_input("Digite sua mensagem..."):
        processor.process(prompt, "text", st.session_state.media_cache)
        st.session_state.media_cache = []
        st.rerun()

def handle_audio_input(processor: InputProcessor):
    """Gerencia input de áudio"""
    col1, col2 = st.columns([3, 1])
    with col1:
        audio = st.audio_input("Gravar mensagem de voz")
    with col2:
        st.write(' ')
        st.write(' ')
        if st.button("📤 Enviar Áudio", key="send_audio", disabled=not audio):
            if audio:
                # Processar áudio
                audio_data = audio.read()
                transcription = AudioProcessor.process(audio_data)
                
                # Criar objeto de mídia
                media_data = MediaData(audio_data, f"audio_{datetime.now().strftime('%H%M%S')}.wav", "audio")
                
                # Processar com transcrição
                processor.process(transcription, "audio", [media_data.to_dict()])
                st.rerun()

def handle_camera_input(processor: InputProcessor):
    """Gerencia input de câmera"""
    col1, col2 = st.columns([3, 1])
    with col1:
        enable = st.checkbox('Ativar câmera')
        photo = st.camera_input("Capturar imagem", disabled=not enable)
    with col2:
        st.write(' ')
        st.write(' ')
        if st.button("📤 Enviar Foto", key="send_photo", disabled=not photo):
            if photo:
                # Criar objeto de mídia
                photo_data = photo.read()
                media_data = MediaData(photo_data, f"foto_{datetime.now().strftime('%H%M%S')}.png", "camera")
                
                # Processar
                processor.process("Analisar informações financeiras desta imagem", "camera", [media_data.to_dict()])
                st.rerun()

def handle_file_input(processor: InputProcessor):
    """Gerencia input de arquivos"""
    col1, col2 = st.columns([3, 1])
    with col1:
        files = st.file_uploader("Anexar imagens PNG", type=['png'], accept_multiple_files=True)
        if files:
            # Processar arquivos
            media_list = []
            for file in files:
                file_data = file.read()
                media_data = MediaData(file_data, file.name, "file")
                media_list.append(media_data.to_dict())
            
            st.session_state.media_cache = media_list
            st.info(f"📎 {len(files)} arquivo(s) anexado(s)")
    
    with col2:
        st.write(' ')
        st.write(' ')
        if st.button("📤 Enviar Arquivos", key="send_files", disabled=not files):
            if st.session_state.media_cache:
                processor.process(
                    f"Analisar informações financeiras em {len(st.session_state.media_cache)} arquivo(s)", 
                    "file"
                )
                st.rerun()

def show_media_preview():
    """Mostra preview de mídia anexada"""
    if st.session_state.media_cache:
        with st.expander(f"📎 Mídia anexada ({len(st.session_state.media_cache)})"):
            cols = st.columns(4)
            for i, m in enumerate(st.session_state.media_cache):
                with cols[i % 4]:
                    st.image(f"data:image/png;base64,{m['data']}", caption=m['name'])

def show_sidebar_metrics():
    """Mostra métricas na sidebar"""
    with st.sidebar:
        st.header("📊 Estatísticas")
        st.metric("💬 Mensagens", len(st.session_state.messages))
        st.metric("📎 Mídias", sum(len(m.get("media", [])) for m in st.session_state.messages))
        
        if st.button("🗑️ Limpar Conversa"):
            st.session_state.clear()
            st.rerun()

# Executar aplicação
if __name__ == "__main__":
    main()