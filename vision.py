from groq import Groq
import os
import base64

def vision(img_data_url):
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

    return completion.choices[0].message.content
