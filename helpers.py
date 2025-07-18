import os
import json
import requests
import base64
import tempfile
from groq import Groq

def obter_data(data):
    """Extrai dados da mensagem do webhook"""
    try:
        message_data = data.get('data', {})
        message_content = message_data.get('message', {})
        key_data = message_data.get('key', {})
        
        msg = message_content.get('conversation', '')
        remetente = key_data.get('remoteJid', '')
        bool_remetente = key_data.get('fromMe', False)
        nome = message_data.get('pushName', '')
        instancia = data.get('instance', '')
        tipo_msg = message_data.get('messageType', '')
        
        # Para imagem e áudio, pegar a URL diretamente
        url_imagem = message_content.get('imageMessage', {}).get('url') if 'imageMessage' in message_content else None
        url_audio = message_content.get('audioMessage', {}).get('url') if 'audioMessage' in message_content else None
        
        return msg, remetente, bool_remetente, nome, instancia, tipo_msg, url_imagem, url_audio
    except Exception as e:
        print(f"Erro ao extrair dados: {e}")
        return '', '', False, '', '', '', None, None

def get_media_base64(instance, media_url):
    """Faz download da mídia e retorna em base64"""
    try:
        # URL da API Evolution para pegar mídia em base64
        # Ajuste conforme sua configuração da Evolution API
        api_url = f"https://your-evolution-api.com/instance/{instance}/media/base64"
        
        payload = {"mediaUrl": media_url}
        headers = {
            "Content-Type": "application/json",
            "apikey": os.environ.get("EVOLUTION_API_KEY", "")  # Configure sua chave
        }
        
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            return response.json().get('base64', '')
        else:
            print(f"Erro ao baixar mídia: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Erro ao baixar mídia: {e}")
        return None

def audio_texto(media_url, instance):
    """Converte áudio em texto"""
    try:
        # Pegar áudio em base64
        base64_audio = get_media_base64(instance, media_url)
        if not base64_audio:
            return "Erro ao baixar áudio"
        
        # Salvar temporariamente para o Groq
        audio_data = base64.b64decode(base64_audio)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name
        
        try:
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            
            with open(temp_path, "rb") as file:
                transcription = client.audio.transcriptions.create(
                    file=file,
                    model="whisper-large-v3-turbo",
                    language="pt",
                    temperature=0.0
                )
                return transcription.text
        finally:
            # Limpar arquivo temporário
            os.unlink(temp_path)
            
    except Exception as e:
        print(f"Erro ao transcrever áudio: {e}")
        return "Erro na transcrição"

def imagem_texto(media_url, instance):
    """Analisa imagem usando Groq Vision"""
    try:
        # Pegar imagem em base64
        base64_image = get_media_base64(instance, media_url)
        if not base64_image:
            return "Erro ao baixar imagem"
        
        # Montar data URL
        image_data_url = f"data:image/jpeg;base64,{base64_image}"
        
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        
        completion = client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Descreva esta imagem em português."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_data_url}
                        }
                    ]
                }
            ],
            temperature=0.7,
            max_completion_tokens=1024
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        print(f"Erro ao analisar imagem: {e}")
        return "Erro na análise da imagem"