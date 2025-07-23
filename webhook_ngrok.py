from flask import Flask, request, jsonify
from helpers import obter_data
from agno.agent import Agent
from agno.models.groq import Groq
import os
import logging
from dotenv import load_dotenv

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
        
        dados = obter_data(data)

        print(dados)

        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logging.error(f"Erro no webhook: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

