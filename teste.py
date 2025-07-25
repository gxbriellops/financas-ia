import streamlit as st
import base64
from helpers import vision, speetch_to_text
import json
import re

tab1, tab2, tab3 = st.tabs(['Câmera', 'Arquivo', 'Audio'])

with tab1:
    enable = st.checkbox('Ativar câmera')
    picture = st.camera_input("Tire uma foto", disabled=not enable)
    if st.button("Processar Imagem"):
        if picture:
            imagem_capturada = picture
            pic_byte = picture.getvalue()
            vision_trancription = vision(pic_byte=pic_byte)
            st.write("Imagem capturada e guardada na variável 'imagem_capturada'.")
            st.image(imagem_capturada)
            st.write(vision_trancription.content)
        else:
            st.warning("Nenhuma foto tirada.")

with tab2:
    uploaded_files = st.file_uploader("Escolha um ou mais arquivos", accept_multiple_files=True)
    if st.button("Processar Arquivos"):
        if uploaded_files:
            arquivos_enviados = uploaded_files
            st.write(f"{len(arquivos_enviados)} arquivo(s) capturado(s) e guardado(s) na variável 'arquivos_enviados'.")
            transcricoes = []
            for arquivo in arquivos_enviados:
                file_bytes = arquivo.getvalue()
                vision_trancription = vision(pic_byte=file_bytes)
                st.image(arquivo)
                transcricoes.append(vision_trancription.content)
            todas_transcricoes = "\n".join(transcricoes)
            st.write(todas_transcricoes)
        else:
            st.warning("Nenhum arquivo enviado.")

with tab3:
    audio_data = st.audio_input("Grave uma mensagem de voz")
    
    if st.button("Processar Áudio"):
        if audio_data:
            try:
                audio_transcrito = speetch_to_text(audio=audio_data)
                transcricao_dict = json.loads(audio_transcrito)
                
                # Extrai texto usando regex
                match = re.search(r'text=[\'"]([^\'"]+)[\'"]', transcricao_dict)
                texto_extraido = match.group(1) if match else None
                
                if texto_extraido:
                    st.write(texto_extraido)
                else:
                    st.write("Nenhum texto encontrado entre text=\"\".")
                    
            except (json.JSONDecodeError, Exception) as e:
                st.error(f"Erro ao processar áudio: {e}")
