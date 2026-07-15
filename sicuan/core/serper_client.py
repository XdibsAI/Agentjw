"""
SerperDev Client - Google Search API
"""
import os
import requests
from typing import Dict, List, Optional


class SerperClient:
    """Client untuk SerperDev Google Search API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SERPER_API_KEY")
        self.base_url = "https://google.serper.dev"

    def search(self, query: str, num_results: int = 5) -> Dict:
        """Search Google dan return hasil"""
        if not self.api_key:
            return {"error": "SERPER_API_KEY not configured"}

        url = f"{self.base_url}/search"
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "q": query,
            "num": num_results
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text[:100]}"}
        except Exception as e:
            return {"error": str(e)}

    def search_news(self, query: str, num_results: int = 5) -> Dict:
        """Search Google News"""
        if not self.api_key:
            return {"error": "SERPER_API_KEY not configured"}

        url = f"{self.base_url}/news"
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "q": query,
            "num": num_results
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text[:100]}"}
        except Exception as e:
            return {"error": str(e)}

    def format_search_result(self, result: Dict) -> str:
        """Format search result untuk ditampilkan"""
        if "error" in result:
            return f"❌ {result['error']}"

        if not result.get("organic"):
            return "Tidak ada hasil ditemukan."

        lines = []
        for i, item in enumerate(result["organic"][:5], 1):
            title = item.get("title", "No title")
            snippet = item.get("snippet", "")
            link = item.get("link", "")
            lines.append(f"{i}. **{title}**")
            if snippet:
                lines.append(f"   {snippet[:200]}")
            lines.append(f"   🔗 {link}")
            lines.append("")

        return "\n".join(lines)


_client = None


def get_serper_client() -> SerperClient:
    global _client
    if _client is None:
        _client = SerperClient()
    return _client
