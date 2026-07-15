"""
Fetcher - Abstraction layer untuk fetching URL
"""
import requests
import os
import json
from typing import Dict, Optional
from urllib.parse import urlparse


class BaseHandler:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
        }

    def can_handle(self, url: str) -> bool:
        return False

    def fetch(self, url: str) -> Dict:
        return {"error": "Not implemented"}

    def _get(self, url: str, **kwargs) -> requests.Response:
        headers = self.headers.copy()
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
        return requests.get(url, headers=headers, timeout=10, **kwargs)


class GMGNHandler(BaseHandler):
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("GMGN_API_KEY", "")
    def can_handle(self, url: str) -> bool:
        return "gmgn.ai" in url

    def fetch(self, url: str) -> Dict:
        try:
            response = self._get(url)
            if response.status_code == 200:
                data = response.json()
                return {"success": True, "data": data, "type": "json"}
            return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}


class GitHubHandler(BaseHandler):
    def can_handle(self, url: str) -> bool:
        return "github.com" in url

    def fetch(self, url: str) -> Dict:
        try:
            response = self._get(url)
            if response.status_code == 200:
                return {"success": True, "data": response.text, "type": "html"}
            return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}


class YouTubeHandler(BaseHandler):
    def can_handle(self, url: str) -> bool:
        return "youtube.com" in url or "youtu.be" in url

    def fetch(self, url: str) -> Dict:
        return {"error": "YouTube needs API key", "type": "api_required"}


class DefaultHandler(BaseHandler):
    def can_handle(self, url: str) -> bool:
        return True

    def fetch(self, url: str) -> Dict:
        try:
            response = self._get(url)
            if response.status_code == 200:
                return {"success": True, "data": response.text, "type": "html"}
            return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}


class Fetcher:
    def __init__(self):
        self.handlers = [
            GMGNHandler(),
            GitHubHandler(),
            YouTubeHandler(),
            DefaultHandler(),
        ]

    def fetch(self, url: str) -> Dict:
        for handler in self.handlers:
            if handler.can_handle(url):
                return handler.fetch(url)
        return {"error": "No handler found"}


_fetcher = None


def get_fetcher() -> Fetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = Fetcher()
    return _fetcher
