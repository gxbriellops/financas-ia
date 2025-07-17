def obter_data(data):
    msg = data['data']['message'].get('conversation', '')
    remetente = data['data']['key']['remoteJid']
    bool_remetente = data['data']['key']['fromMe']
    nome = data['data']['pushName']
    instancia = data.get('instance', '')
    tipo_msg = data['data'].get('messageType', '')
    url_imagem = data['data']['message'].get('imageMessage', None)
    url_audio = data['data']['message'].get('audioMessage', None)
    return msg, remetente, bool_remetente, nome, instancia, tipo_msg, url_imagem, url_audio