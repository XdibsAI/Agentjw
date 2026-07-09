"""
Authentication - JWT, OAuth, Workspace login
"""

import json
import jwt
import time
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional


class Auth:
    """Authentication dengan JWT + OAuth"""

    def __init__(self):
        self.auth_dir = Path("/home/dibs/agentjw/memory/auth")
        self.auth_dir.mkdir(exist_ok=True)
        self.secret_key = secrets.token_hex(32)
        self.token_expiry = 7 * 24 * 60 * 60  # 7 days

    def generate_token(self, workspace_id: str, user_id: int, email: str = "") -> str:
        """Generate JWT token"""
        payload = {
            "workspace_id": workspace_id,
            "user_id": user_id,
            "email": email,
            "exp": int(time.time()) + self.token_expiry,
            "iat": int(time.time())
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def verify_token(self, token: str) -> Dict:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return {
                "success": True,
                "workspace_id": payload.get("workspace_id"),
                "user_id": payload.get("user_id"),
                "email": payload.get("email")
            }
        except jwt.ExpiredSignatureError:
            return {"success": False, "error": "Token expired"}
        except jwt.InvalidTokenError:
            return {"success": False, "error": "Invalid token"}

    def generate_workspace_token(self, workspace_id: str) -> str:
        """Generate workspace-specific token"""
        return self.generate_token(workspace_id, 0, "")


def get_auth():
    _auth = None
    if _auth is None:
        _auth = Auth()
    return _auth
