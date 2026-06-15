import os
import requests
from dotenv import load_dotenv

load_dotenv()

headers = {
    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
    "Content-Type": "application/json",
}

payload = {
    "model": os.getenv("OPENROUTER_IMAGE_MODEL"),
    "messages": [
        {
            "role": "user",
            "content": "Ultra realistic futuristic data center documentary scene, cinematic lighting, 4k"
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
print(r.text[:4000])
