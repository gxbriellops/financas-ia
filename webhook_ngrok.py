from flask import Flask, request, jsonify
from helpers import obter_data

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
@app.route('/webhook/<evento>', methods=['POST'])
def webhook(evento=None):
    data = request.get_json()
    print(f"Evento recebido: {evento}")
    msg, remetente, bool_remetente, nome, instancia, tipo_msg, url_imagem, url_audio = obter_data(data=data)

    # Trate o evento se precisar
    if evento == "messages-upsert":
        # Exemplo: responder, salvar no banco etc
        pass

    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    app.run(port=5000, debug=True)