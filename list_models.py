import requests
import os
from dotenv import load_dotenv

load_dotenv()

r = requests.get(
    "https://openrouter.ai/api/v1/models",
    headers={
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"
    },
    timeout=60
)

print(r.status_code)

data = r.json()

for m in data.get("data", []):
    model_id = m.get("id","")

    if any(x in model_id.lower() for x in [
        "image",
        "flux",
        "recraft",
        "ideogram",
        "nano",
        "gemini"
    ]):
        print(model_id)
