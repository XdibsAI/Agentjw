import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "qwen/qwen-image",
    "messages": [
        {
            "role": "user",
            "content": "Cinematic documentary shot of a futuristic data center, dramatic lighting, ultra realistic, 4k"
        }
    ]
}

r = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers=headers,
    json=payload,
    timeout=180
)

print("STATUS:", r.status_code)
print(r.text[:5000])
