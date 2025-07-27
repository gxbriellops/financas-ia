from groq import Groq
import os
import base64
import json
import streamlit as st
import hashlib
from config import get_api_keys

@st.cache_data(show_spinner="Analisando imagem...", ttl=3600)
def vision(pic_byte):
    """
    Analisa imagem usando Groq Vision com cache.
    Cache baseado no hash da imagem para evitar reprocessamento.
    """
    # Criar hash único da imagem para cache
    img_hash = hashlib.md5(pic_byte).hexdigest()
    
    pic_base64 = base64.b64encode(pic_byte).decode('utf-8')
    img_data_url = f"data:image/png;base64,{pic_base64}"

    api_keys = get_api_keys()
    groq_api = api_keys['GROQ_API_KEY']

    client = Groq(api_key=groq_api)
    completion = client.chat.completions.create(
        model="llama-3.2-11b-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Você é um assistente especializado em análise de documentos financeiros. Analise esta imagem procurando por:

1. VALORES MONETÁRIOS (preços, totais, subtotais)
2. DESCRIÇÃO do produto/serviço
3. DATA da transação (se visível)
4. ESTABELECIMENTO/EMPRESA
5. TIPO DE DOCUMENTO (nota fiscal, recibo, comprovante, etc)

EXTRAIA e ORGANIZE essas informações de forma clara e estruturada. Se encontrar múltiplas transações, liste cada uma separadamente. Seja preciso com os valores e detalhes."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": img_data_url
                        }
                    }
                ]
            }
        ],
        temperature=0.5,
        max_completion_tokens=1024,
        top_p=1,
        stream=False,
        stop=None,
    )

    return completion.choices[0].message.content

@st.cache_data(show_spinner="Transcrevendo áudio...", ttl=3600)
def speech_to_text_cached(audio_bytes, audio_name, audio_type):
    """
    Converte áudio em texto com cache.
    Cache baseado no hash do áudio.
    """
    # Criar hash único do áudio para cache
    audio_hash = hashlib.md5(audio_bytes).hexdigest()
    
    api_keys = get_api_keys()
    groq_api = api_keys['GROQ_API_KEY']
    client = Groq(api_key=groq_api)

    file_tuple = (audio_name, audio_bytes, audio_type)

    transcription = client.audio.transcriptions.create(
        file=file_tuple,
        model="whisper-large-v3-turbo",
        prompt="Transcreva o áudio em português brasileiro, focando em informações sobre gastos, receitas ou transações financeiras.",
        response_format="verbose_json",
        language="pt",
        temperature=0.0
    )
    
    return transcription

def speetch_to_text(audio):
    """
    Wrapper para compatibilidade que usa a versão com cache.
    audio é um UploadedFile do Streamlit.
    """
    # Extrair dados do UploadedFile
    audio_bytes = audio.getvalue()
    audio_name = audio.name
    audio_type = audio.type
    
    # Chamar versão com cache
    transcription = speech_to_text_cached(audio_bytes, audio_name, audio_type)
    
    return json.dumps(transcription, indent=2, default=str)

# Alias para compatibilidade
speech_to_text = speetch_to_text

@st.cache_data(ttl=300)
def extract_text_from_transcription(transcription_json):
    """Extrai texto limpo da transcrição com cache"""
    try:
        transcricao_dict = json.loads(transcription_json)
        
        # Tentar extrair diretamente
        if isinstance(transcricao_dict, dict) and 'text' in transcricao_dict:
            return transcricao_dict['text']
        
        # Tentar com regex
        import re
        match = re.search(r'text=[\'"]([^\'"]+)[\'"]', str(transcricao_dict))
        if match:
            return match.group(1)
        
        return "Não foi possível transcrever o áudio"
    except Exception as e:
        return f"Erro na transcrição: {str(e)}"

@st.cache_resource
def get_groq_client():
    """Retorna cliente Groq com cache de recurso"""
    api_keys = get_api_keys()
    return Groq(api_key=api_keys['GROQ_API_KEY'])