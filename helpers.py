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