"""
API Gateway - Single entry point untuk semua client
"""

import json
import time
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass
from functools import wraps


@dataclass
class APIKey:
    """API Key untuk workspace"""
    key: str
    workspace_id: str
    name: str
    created_at: str
    last_used: Optional[str] = None
    expires_at: Optional[str] = None
    is_active: bool = True
    rate_limit: int = 100  # requests per minute


class APIGateway:
    """API Gateway dengan authentication & rate limiting"""

    def __init__(self):
        self.keys_dir = Path("/home/dibs/agentjw/memory/api_keys")
        self.keys_dir.mkdir(exist_ok=True)
        self.rate_limits = {}
        self._load_keys()

    def _load_keys(self):
        """Load semua API keys"""
        self.keys = {}
        for f in self.keys_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                key = data.get("key")
                if key:
                    self.keys[key] = APIKey(**data)
            except:
                pass

    def _save_key(self, api_key: APIKey):
        """Save API key"""
        key_file = self.keys_dir / f"{api_key.key[:8]}.json"
        key_file.write_text(json.dumps({
            "key": api_key.key,
            "workspace_id": api_key.workspace_id,
            "name": api_key.name,
            "created_at": api_key.created_at,
            "last_used": api_key.last_used,
            "expires_at": api_key.expires_at,
            "is_active": api_key.is_active,
            "rate_limit": api_key.rate_limit
        }, indent=2))
        self.keys[api_key.key] = api_key

    def create_key(self, workspace_id: str, name: str, rate_limit: int = 100) -> str:
        """Buat API key baru"""
        key = f"sk_sicuan_{secrets.token_hex(24)}"
        api_key = APIKey(
            key=key,
            workspace_id=workspace_id,
            name=name,
            created_at=datetime.now().isoformat(),
            rate_limit=rate_limit
        )
        self._save_key(api_key)
        return key

    def validate_key(self, key: str) -> Optional[APIKey]:
        """Validasi API key"""
        if key not in self.keys:
            return None
        
        api_key = self.keys[key]
        if not api_key.is_active:
            return None
        
        # Check expiration
        if api_key.expires_at:
            expires = datetime.fromisoformat(api_key.expires_at)
            if datetime.now() > expires:
                return None
        
        # Update last_used
        api_key.last_used = datetime.now().isoformat()
        self._save_key(api_key)
        
        return api_key

    def check_rate_limit(self, key: str) -> bool:
        """Check rate limit"""
        now = time.time()
        minute = int(now / 60)
        
        if key not in self.rate_limits:
            self.rate_limits[key] = {}
        
        if minute not in self.rate_limits[key]:
            self.rate_limits[key][minute] = 0
        
        self.rate_limits[key][minute] += 1
        limit = self.keys.get(key, APIKey(key="", workspace_id="", name="")).rate_limit
        
        return self.rate_limits[key][minute] <= limit

    def authenticate(self, headers: Dict) -> Dict:
        """Authenticate request"""
        api_key = headers.get("X-API-Key") or headers.get("Authorization", "").replace("Bearer ", "")
        
        if not api_key:
            return {"success": False, "error": "API key required", "status": 401}
        
        key_data = self.validate_key(api_key)
        if not key_data:
            return {"success": False, "error": "Invalid API key", "status": 401}
        
        if not self.check_rate_limit(api_key):
            return {"success": False, "error": "Rate limit exceeded", "status": 429}
        
        return {
            "success": True,
            "workspace_id": key_data.workspace_id,
            "api_key": key_data
        }


def get_api_gateway():
    _gateway = None
    if _gateway is None:
        _gateway = APIGateway()
    return _gateway
