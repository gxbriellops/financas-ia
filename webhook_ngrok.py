from flask import Flask, request, jsonify
from helpers import obter_data, audio_texto, imagem_texto
from agno.agent import Agent
from agno.models.groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
@app.route('/webhook/<evento>', methods=['POST'])
def webhook(evento=None):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error"}), 400
        
        msg, remetente, bool_remetente, nome, instancia, tipo_msg, url_imagem, url_audio = obter_data(data)
        
        print(f"Tipo: {tipo_msg}, De: {nome}")
        
        # Ignorar mensagens próprias
        if bool_remetente:
            return jsonify({"status": "ok"}), 200
        
        if tipo_msg == 'imageMessage' and url_imagem:
            resultado = imagem_texto(url_imagem, instancia)
            print(f"Imagem: {resultado}")
            
        elif tipo_msg == 'audioMessage' and url_audio:
            resultado = audio_texto(url_audio, instancia)
            print(f"Áudio: {resultado}")
            
        elif tipo_msg == 'conversation' and msg:
            agent = Agent(model=Groq(id="llama3-70b-8192"), markdown=True, stream=True)
            agent.print_response(msg)
            
        else:
            print(f'Tipo "{tipo_msg}" não suportado')

        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        print(f"Erro no webhook: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)