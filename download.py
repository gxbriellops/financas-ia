import base64
import requests
import os
from pathlib import Path

def download_media(url, filename):
    """Baixa mídia da URL e retorna o caminho do arquivo"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Criar diretório temporário se não existir
        temp_dir = Path("temp_media")
        temp_dir.mkdir(exist_ok=True)
        
        # Salvar arquivo
        filepath = temp_dir / filename
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return filepath
    except Exception as e:
        raise Exception(f"Erro ao baixar mídia: {e}")

def process_image(url_imagem):
    """Baixa imagem, converte para base64 e exclui o arquivo"""
    try:
        # Baixar imagem
        filepath = download_media(url_imagem, "temp_image.jpg")
        
        # Converter para base64
        with open(filepath, 'rb') as f:
            base64_data = base64.b64encode(f.read()).decode()
        
        # Excluir arquivo
        # os.remove(filepath)
        
        return {
            "success": True,
            "base64": base64_data,
            "message": "Imagem processada com sucesso",
            "filepath": filepath
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro ao processar imagem: {e}"
        }

def process_audio(url_audio):
    """Baixa áudio e exclui após o processamento"""
    try:
        # Baixar áudio
        filepath = download_media(url_audio, "temp_audio.ogg")
        
        # Aqui você pode processar o áudio conforme necessário
        # Por exemplo, enviar para STT, etc.
        
        # Excluir arquivo
        # os.remove(filepath)
        
        return {
            "success": True,
            "message": "Áudio processado com sucesso",
            "filepath": filepath
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro ao processar áudio: {e}"
        }