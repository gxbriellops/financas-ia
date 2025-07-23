from groq import Groq
import os
import base64

# Carrega a imagem local e converte para base64
with open("AVISO.png", "rb") as img_file:
    b64_img = base64.b64encode(img_file.read()).decode("utf-8")
img_data_url = f"data:image/png;base64,{b64_img}"

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
completion = client.chat.completions.create(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "O que está nessa imagem?"
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
    temperature=.5,
    max_completion_tokens=1024,
    top_p=1,
    stream=False,
    stop=None,
)

print(completion.choices[0].message.content)
