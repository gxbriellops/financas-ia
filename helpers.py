from groq import Groq
import os
import base64
import json

def vision(pic_byte):
    pic_base64 = base64.b64encode(pic_byte).decode('utf-8')
    img_data_url = f"data:image/png;base64,{pic_base64}"

    groq_api = os.getenv('GROQ_API_KEY')

    client = Groq(api_key=groq_api)
    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What's in this image?"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": img_data_url
                        }
                    }
                ]
            }
        ],
        temperature=0.5,
        max_completion_tokens=1024,
        top_p=1,
        stream=False,
        stop=None,
    )

    return completion.choices[0].message

def speetch_to_text(audio):
    groq_api = os.getenv('GROQ_API_KEY')
    client = Groq(api_key=groq_api)

    # audio é um UploadedFile do Streamlit
    file_tuple = (audio.name, audio.getvalue(), audio.type)

    transcription = client.audio.transcriptions.create(
        file=file_tuple,  # Passa como tupla (nome, bytes, tipo)
        model="whisper-large-v3-turbo",
        prompt="Specify context or spelling",
        response_format="verbose_json",
        timestamp_granularities=["word", "segment"],
        language="pt",
        temperature=0.0
    )
    return json.dumps(transcription, indent=2, default=str)