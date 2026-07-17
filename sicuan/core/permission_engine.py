"""Permission Engine - Centralized access control for AgentJW"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PermissionEngine:
    """Centralized permission management"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("memory/permissions.json")
        self.permissions = self._load()
        
    def _load(self) -> Dict:
        """Load permissions from file"""
        if self.config_path.exists():
            try:
                return json.loads(self.config_path.read_text())
            except:
                pass
        return self._default_permissions()
    
    def _default_permissions(self) -> Dict:
        """Default permission structure"""
        return {
            "roles": {
                "admin": ["*"],
                "developer": [
                    "read:*",
                    "write:code",
                    "write:config",
                    "execute:workflow",
                    "deploy:staging"
                ],
                "operator": [
                    "read:metrics",
                    "read:logs",
                    "execute:workflow",
                    "read:customer"
                ],
                "viewer": [
                    "read:dashboard",
                    "read:metrics"
                ]
            },
            "users": {},
            "actions": {
                "deploy": {
                    "staging": ["developer", "admin"],
                    "production": ["admin"]
                },
                "git": {
                    "push": ["developer", "admin"],
                    "force_push": ["admin"]
                },
                "project": {
                    "delete": ["admin"],
                    "create": ["developer", "admin"],
                    "update": ["developer", "admin"]
                },
                "customer": {
                    "delete": ["admin"],
                    "create": ["developer", "operator", "admin"],
                    "update": ["developer", "operator", "admin"]
                }
            }
        }
    
    def check_permission(self, user: str, action: str, resource: str = None) -> bool:
        """
        Check if user has permission for action
        
        Args:
            user: User identifier
            action: Action to perform (e.g., 'deploy', 'git:push')
            resource: Optional resource identifier
        
        Returns:
            True if permitted, False otherwise
        """
        # Get user role
        user_data = self.permissions["users"].get(user, {})
        role = user_data.get("role", "viewer")
        
        # Admin has all permissions
        if role == "admin":
            return True
        
        # Get role permissions
        role_permissions = self.permissions["roles"].get(role, [])
        
        # Check wildcard
        if "*" in role_permissions:
            return True
        
        # Check specific action
        if action in role_permissions:
            return True
        
        # Check action with wildcard (e.g., "read:*")
        action_parts = action.split(":")
        for perm in role_permissions:
            if perm.endswith(":*"):
                prefix = perm[:-2]
                if action.startswith(prefix):
                    return True
        
        # Check resource-specific permissions
        if resource and action in self.permissions["actions"]:
            resource_config = self.permissions["actions"][action]
            if resource in resource_config:
                if role in resource_config[resource]:
                    return True
        
        logger.warning(f"Permission denied: {user} -> {action} (role: {role})")
        return False
    
    def require_permission(self, user: str, action: str, resource: str = None):
        """Check permission and raise exception if denied"""
        if not self.check_permission(user, action, resource):
            raise PermissionError(f"User {user} not authorized for {action}")
        return True
    
    def add_user(self, username: str, role: str = "viewer"):
        """Add user with role"""
        if role not in self.permissions["roles"]:
            raise ValueError(f"Invalid role: {role}")
        
        self.permissions["users"][username] = {
            "role": role,
            "added": datetime.now().isoformat()
        }
        self._save()
        logger.info(f"User {username} added with role {role}")
    
    def remove_user(self, username: str):
        """Remove user"""
        if username in self.permissions["users"]:
            del self.permissions["users"][username]
            self._save()
            logger.info(f"User {username} removed")
    
    def _save(self):
        """Save permissions to file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(self.permissions, indent=2))
    
    def get_user_role(self, username: str) -> Optional[str]:
        """Get role for user"""
        user_data = self.permissions["users"].get(username, {})
        return user_data.get("role")

# Singleton
_permission_engine = None

def get_permission_engine() -> PermissionEngine:
    """Get singleton instance"""
    global _permission_engine
    if _permission_engine is None:
        _permission_engine = PermissionEngine()
    return _permission_engine
