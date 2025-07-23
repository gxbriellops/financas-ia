from flask import Flask, request, jsonify
from helpers import obter_data
from download import process_image, process_audio
from agno.agent import Agent
from agno.models.groq import Groq
import os
import logging
from dotenv import load_dotenv
from stt import stt
from vision import vision

load_dotenv()

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

@app.route('/webhook', methods=['POST'])
@app.route('/webhook/<evento>', methods=['POST'])
def webhook(evento=None):
    try:
        data = request.get_json()
        if not data:
            logging.error("Request sem dados")
            return jsonify({"status": "error"}), 400
        
        # Extrair dados da mensagem
        msg, remetente, bool_remetente, nome, instancia, tipo_msg, url_imagem, url_audio = obter_data(data)
        
        # Processar mídia baseado no tipo
        if tipo_msg == 'imageMessage' and url_imagem:
            resultado = process_image(url_imagem)
            if resultado['success']:
                transcricao_imagem = vision(img_data_url=resultado['base64'])
                print(transcricao_imagem)
                os.remove(resultado['filepath'])
            else:
                logging.error(f"❌ {resultado['message']}")
                
        elif tipo_msg == 'audioMessage' and url_audio:
            resultado = process_audio(url_audio)
            if resultado['success']:
                transcricao_audio = stt(filepath=resultado['filepath'])
                print(transcricao_audio)
                os.remove(resultado['filepath'])
            else:
                logging.error(f"❌ {resultado['message']}")
        else:
            logging.info(f"Mensagem tipo: {tipo_msg} - Sem mídia para processar")

        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logging.error(f"Erro no webhook: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)