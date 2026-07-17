"""
LLM Client — Unified LLM client (OpenAI + Anthropic + Groq + OpenRouter + Ollama + NVIDIA NIM)
"""
import os
import json
import requests
from typing import List, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import config
from core.logger import logger
from core.router import ModelRouter
from core.cost_tracker import CostTracker


class LLMClient:
    """Unified LLM client dengan multi-provider support"""

    def __init__(self):
        self.provider = config.LLM_PROVIDER
        self.model = config.get_model()
        self._client = None
        
        # NVIDIA NIM fallback
        self.nvidia_nim_api_key = os.getenv("NVIDIA_NIM_API_KEY", "")
        self.nvidia_nim_base_url = os.getenv("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
        self.nvidia_nim_model = os.getenv("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct")
        
        self.router = ModelRouter()
        self.cost_tracker = CostTracker()
        self._init_client()

    def _init_client(self):
        if self.provider == "openai":
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=config.OPENAI_API_KEY)
            except:
                pass

    def _get_api_key(self):
        import os
        if self.provider == "openai":
            return os.getenv("OPENAI_API_KEY")
        elif self.provider == "anthropic":
            return os.getenv("ANTHROPIC_API_KEY")
        elif self.provider == "groq":
            return os.getenv("GROQ_API_KEY")
        elif self.provider == "openrouter":
            return os.getenv("OPENROUTER_API_KEY")
        else:
            return os.getenv("OPENROUTER_API_KEY")

    def chat(self, messages: List[Dict], system: Optional[str] = None,
             temperature: float = 0.7, max_tokens: int = 16000,
             json_mode: bool = False) -> str:
        """Main chat method"""
        if json_mode:
            temperature = 0.0
        return self._openai_chat(messages, system, temperature, max_tokens, json_mode)

    def chat_with_fallback(self, messages: List[Dict], system: Optional[str] = None,
                           temperature: float = 0.7, max_tokens: int = 16000,
                           json_mode: bool = False) -> str:
        """Chat dengan fallback chain"""
        # 1. Coba OpenAI
        try:
            return self._openai_chat(messages, system, temperature, max_tokens, json_mode)
        except Exception as e:
            logger.warning(f"OpenAI failed: {e}")
        
        # 2. Coba OpenRouter
        try:
            return self._openrouter_chat(messages, system, temperature, max_tokens, json_mode)
        except Exception as e:
            logger.warning(f"OpenRouter failed: {e}")
        
        # 3. Coba NVIDIA NIM
        try:
            return self._nvidia_nim_chat(messages, system, temperature, max_tokens, json_mode)
        except Exception as e:
            logger.warning(f"NVIDIA NIM failed: {e}")
        
        # 4. Coba Ollama
        try:
            return self._ollama_chat(messages, system, temperature, max_tokens, json_mode)
        except Exception as e:
            logger.warning(f"Ollama failed: {e}")
        
        return "❌ All LLM providers failed"

    def _openai_chat(self, messages: List[Dict], system: Optional[str] = None,
                     temperature: float = 0.7, max_tokens: int = 16000,
                     json_mode: bool = False) -> str:
        """Chat via OpenAI"""
        # Coba OpenRouter dulu via OpenAI client
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        if not api_key:
            raise Exception("No API key available")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        messages_list = []
        if system:
            messages_list.append({"role": "system", "content": system})
        messages_list.extend(messages)
        
        payload = {
            "model": "gpt-4o",
            "messages": messages_list,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            try:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                raise Exception(f"JSON parse error: {e} - Status: {response.status_code} - Body: {response.text[:200]}")
        raise Exception(f"HTTP {response.status_code}")

    def _openrouter_chat(self, messages: List[Dict], system: Optional[str] = None,
                         temperature: float = 0.7, max_tokens: int = 16000,
                         json_mode: bool = False) -> str:
        """Chat via OpenRouter"""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise Exception("OPENROUTER_API_KEY not set")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://agentjw.ai",
            "X-Title": "AgentJW"
        }
        
        messages_list = []
        if system:
            messages_list.append({"role": "system", "content": system})
        messages_list.extend(messages)
        
        payload = {
            "model": "qwen/qwen3-coder",
            "messages": messages_list,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                 headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        raise Exception(f"HTTP {response.status_code}")

    def _nvidia_nim_chat(self, messages: List[Dict], system: Optional[str] = None,
                         temperature: float = 0.7, max_tokens: int = 16000,
                         json_mode: bool = False) -> str:
        """Chat via NVIDIA NIM"""
        if not self.nvidia_nim_api_key:
            raise Exception("NVIDIA_NIM_API_KEY not set")
        
        # Gunakan model yang valid
        model = self.nvidia_nim_model or "meta/llama-3.1-70b-instruct"
        
        messages_list = []
        if system:
            messages_list.append({"role": "system", "content": system})
        messages_list.extend(messages)
        
        payload = {
            "model": model,
            "messages": messages_list,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        headers = {
            "Authorization": f"Bearer {self.nvidia_nim_api_key}",
            "Content-Type": "application/json"
        }
        
        base_url = self.nvidia_nim_base_url or "https://integrate.api.nvidia.com/v1"
        
        try:
            response = requests.post(f"{base_url}/chat/completions", 
                                     headers=headers, json=payload, timeout=120)
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            elif response.status_code == 403:
                raise Exception("NVIDIA NIM 403 - API key tidak valid atau model tidak diizinkan")
            else:
                raise Exception(f"HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            raise Exception("NVIDIA NIM connection failed")
        except Exception as e:
            raise Exception(f"NVIDIA NIM error: {e}")

    def _ollama_chat(self, messages: List[Dict], system: Optional[str] = None,
                     temperature: float = 0.7, max_tokens: int = 16000,
                     json_mode: bool = False) -> str:
        """Chat via Ollama"""
        messages_list = []
        if system:
            messages_list.append({"role": "system", "content": system})
        messages_list.extend(messages)
        
        payload = {
            "model": "llama3.2",
            "messages": messages_list,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            response = requests.post("http://localhost:11434/api/chat", json=payload, timeout=120)
            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "")
            raise Exception(f"HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            raise Exception("Ollama not running")

    def count_tokens(self, text: str) -> int:
        """Estimate token count"""
        return len(text) // 4


_client = None


def get_llm_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client


# Global instance untuk backward compatibility
llm = None

def get_llm():
    global llm
    if llm is None:
        llm = LLMClient()
    return llm
