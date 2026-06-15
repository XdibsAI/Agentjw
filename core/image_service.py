"""
core/image_service.py - Global Image Service
Pakai google/gemini-2.5-flash-image via OpenRouter
"""
import os
import time
import base64
import requests
from pathlib import Path
from typing import Optional
from core.logger import logger

UPLOAD_DIR = Path("/home/dibs/agentjw/uploads")
IMAGE_MODEL = "google/gemini-2.5-flash-image"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class ImageService:

    @staticmethod
    def _get_key() -> str:
        from dotenv import load_dotenv
        load_dotenv("/home/dibs/agentjw/.env")
        return os.getenv("OPENROUTER_API_KEY", "")

    @staticmethod
    def generate(prompt: str, output_path: str = None,
                 model: str = IMAGE_MODEL) -> dict:
        if not output_path:
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            output_path = str(UPLOAD_DIR / f"generated_{int(time.time())}.png")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        api_key = ImageService._get_key()
        if not api_key:
            return {"success": False, "error": "OPENROUTER_API_KEY kosong"}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://agentjw.local",
            "X-Title": "SiCuan Image Studio",
        }

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            logger.info(f"Generating image: {model} | {prompt[:60]}")
            r = requests.post(OPENROUTER_URL, headers=headers,
                              json=payload, timeout=120)
            r.raise_for_status()
            data = r.json()

            msg = data["choices"][0]["message"]
            content = msg.get("content", "")

            # Cari image di response — bisa list atau string
            image_data = None

            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "image_url":
                            image_data = item["image_url"]["url"]
                            break
                        elif item.get("type") == "image":
                            image_data = item.get("source", {}).get("data")
                            break

            elif isinstance(content, str) and content.startswith("data:"):
                image_data = content

            # Cek juga di msg langsung
            if not image_data and "images" in msg:
                try:
                    image_data = msg["images"][0]["image_url"]["url"]
                except Exception:
                    pass

            if image_data:
                if "base64," in str(image_data):
                    b64 = image_data.split("base64,", 1)[1]
                    Path(output_path).write_bytes(base64.b64decode(b64))
                elif str(image_data).startswith("http"):
                    img_r = requests.get(image_data, timeout=30)
                    Path(output_path).write_bytes(img_r.content)
                else:
                    # Pure base64
                    Path(output_path).write_bytes(base64.b64decode(image_data))

                size = Path(output_path).stat().st_size
                logger.info(f"Image saved: {output_path} ({size//1024}KB)")
                return {"success": True, "path": output_path, "size_kb": size//1024}

            # Debug — print raw response
            logger.error(f"No image in response. Keys: {list(msg.keys())}")
            logger.error(f"Content type: {type(content)} | Content: {str(content)[:300]}")
            return {"success": False, "error": f"No image in response: {str(msg)[:200]}",
                    "raw": data}

        except Exception as e:
            logger.error(f"ImageService error: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def is_image_request(text: str) -> bool:
        keywords = [
            "logo", "gambar", "image", "poster", "thumbnail",
            "banner", "stiker", "avatar", "foto", "ilustrasi",
            "generate image", "buat gambar", "bikin logo", "bikin gambar",
            "design", "visual", "artwork", "icon", "generate foto"
        ]
        return any(k in text.lower() for k in keywords)

    @staticmethod
    def send_to_telegram(image_path: str, caption: str = "",
                         chat_id: str = "5090639343") -> bool:
        from dotenv import load_dotenv
        load_dotenv("/home/dibs/agentjw/.env")
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if not token or not Path(image_path).exists():
            return False
        try:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            with open(image_path, "rb") as f:
                r = requests.post(url, data={"chat_id": chat_id, "caption": caption[:1000]},
                                  files={"photo": f}, timeout=30)
            return r.status_code == 200
        except Exception as e:
            logger.error(f"send_to_telegram: {e}")
            return False


image_service = ImageService()
