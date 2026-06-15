"""
tools/video/openrouter_client.py - OpenRouter LLM Client
Drop-in supplement for core/llm_client.py using OpenRouter API
"""
import json
import time
from typing import List, Dict, Optional
from core.logger import logger


class OpenRouterClient:
    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: str, model: str = "qwen/qwen3-coder"):
        self.api_key = api_key
        self.model = model
        logger.info(f"OpenRouter client initialized: {model}")

    def chat(
        self,
        messages: List[Dict],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> str:
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)
        return self._call(full_messages, temperature, max_tokens)

    def chat_openrouter(
        self,
        system: str,
        user: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        return self._call(messages, temperature, max_tokens)

    def _call(self, messages: List[Dict], temperature: float, max_tokens: int) -> str:
        import requests
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://agentjw.local",
            "X-Title": "AgentJW Video Studio",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        for attempt in range(3):
            try:
                resp = requests.post(self.BASE_URL, headers=headers, json=payload, timeout=120)
                resp.raise_for_status()
                data = resp.json()
                if "error" in data:
                    raise ValueError(f"OpenRouter error: {data['error']}")
                content = data["choices"][0]["message"]["content"]
                logger.debug(f"OpenRouter response: {len(content)} chars")
                return content
            except Exception as e:
                logger.warning(f"OpenRouter attempt {attempt+1}/3 failed: {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
                else:
                    raise

    def count_tokens(self, text: str) -> int:
        return len(text.split()) * 2

    def generate_image(self, prompt: str, output_path: str, model: str):
        import base64
        import requests

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://agentjw.local",
            "X-Title": "AgentJW Video Studio",
        }

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        resp = requests.post(
            self.BASE_URL,
            headers=headers,
            json=payload,
            timeout=300
        )

        resp.raise_for_status()

        data = resp.json()

        msg = data["choices"][0]["message"]

        image_url = None

        if "images" in msg:
            try:
                image_url = msg["images"][0]["image_url"]["url"]
            except Exception:
                pass

        if image_url is None and "content" in msg:
            content = msg["content"]

            if isinstance(content, list):
                for item in content:
                    if item.get("type") == "image_url":
                        image_url = item["image_url"]["url"]
                        break

        if not image_url:
            raise RuntimeError(
                f"No image found in OpenRouter response keys={list(msg.keys())}"
            )

        if not image_url.startswith("data:image"):
            raise RuntimeError(
                f"Unexpected image url format: {image_url[:80]}"
            )

        b64 = image_url.split(",", 1)[1]

        with open(output_path, "wb") as f:
            f.write(base64.b64decode(b64))

        return output_path

