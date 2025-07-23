import base64
import requests
from pathlib import Path
import mimetypes

# Node 1: Evolution API - get-media-base64
def evolution_api_node(tipo_msg, url_imagem, url_audio, instancia, nome, remetente):
    """
    Extrai base64 da mídia usando sua função obter_data
    """
    
    # Determinar qual URL usar baseado no tipo de mensagem
    if tipo_msg == 'imageMessage' and url_imagem:
        media_url = url_imagem
        media_type = "image"
        filename = f"imagem_evolution"
    elif tipo_msg == 'audioMessage' and url_audio:
        media_url = url_audio
        media_type = "audio"
        filename = f"audio_evolution"
    else:
        raise ValueError(f"Tipo de mensagem não suportado: {tipo_msg}")
    
    # Download da URL e converte para base64
    try:
        response = requests.get(media_url, timeout=30)
        response.raise_for_status()
        b64 = base64.b64encode(response.content).decode()
        
        # Detectar mimetype baseado no content-type
        content_type = response.headers.get('content-type', 'application/octet-stream')
        
        # Se não conseguir detectar, usar tipo da mensagem
        if content_type == 'application/octet-stream':
            if media_type == "audio":
                content_type = "audio/ogg"  # WhatsApp geralmente usa OGG para áudio
            elif media_type == "image":
                content_type = "image/jpeg"  # WhatsApp geralmente usa JPEG para imagem
        
        return {
            "base64": b64,
            "mimetype": content_type,
            "filename": filename,
            "remetente": remetente,
            "nome": nome,
            "instancia": instancia,
            "tipo_msg": tipo_msg
        }
        
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Erro ao baixar mídia: {e}")
    except Exception as e:
        raise ValueError(f"Erro inesperado: {e}")

# Node 2: Convert to File - Move Base64 String to File
def convert_to_file_node(media_data, output_dir="files"):
    """
    Converte base64 para arquivo físico
    """
    Path(output_dir).mkdir(exist_ok=True)
    
    # Decodificar base64
    file_content = base64.b64decode(media_data["base64"])
    
    # Determinar extensão
    mimetype = media_data["mimetype"]
    ext = mimetypes.guess_extension(mimetype) or ".bin"
    
    # Gerar caminho do arquivo
    filename = f"{media_data['filename']}{ext}"
    filepath = Path(output_dir) / filename
    
    # Salvar arquivo
    with open(filepath, 'wb') as f:
        f.write(file_content)
    
    return {
        "filepath": str(filepath),
        "filename": filename,
        "size": len(file_content),
        "type": "audio" if mimetype.startswith("audio") else "image" if mimetype.startswith("image") else "other"
    }

# Node 3: caminho base64 - Processa caminho para uso
def processo_caminho_node(file_data):
    """
    Finaliza processamento do arquivo para STT/Vision
    """
    filepath = Path(file_data["filepath"])
    
    return {
        **file_data,
        "absolute_path": str(filepath.absolute()),
        "ready": True,
        "for_stt": file_data["type"] == "audio",
        "for_vision": file_data["type"] == "image"
    }

# Pipeline completo adaptado para sua função
def whatsapp_media_pipeline(tipo_msg, url_imagem, url_audio):
    """
    Executa o pipeline completo usando sua função obter_data
    """
    
    if tipo_msg not in ['imageMessage', 'audioMessage']:
        raise ValueError(f"Mensagem não contém mídia processável. Tipo: {tipo_msg}")
    
    if not url_imagem and not url_audio:
        raise ValueError("URLs de mídia não encontradas")
    
    try:
        # Node 1: Evolution API
        print(f"📱 Processando {tipo_msg}...")
        media_b64 = evolution_api_node(tipo_msg=None, url_imagem=None, url_audio=None, instancia=None, nome=None, remetente=None)
        
        # Node 2: Convert to File  
        print("💾 Convertendo para arquivo...")
        file_data = convert_to_file_node()
        
        # Node 3: Processo caminho
        print("🗂️ Finalizando processamento...")
        result = processo_caminho_node()
        
        print("✅ Pipeline concluído!")
        return result
        
    except Exception as e:
        print(f"❌ Erro no pipeline: {e}")
        return {"error": str(e)}