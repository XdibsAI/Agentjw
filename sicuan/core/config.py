"""Configuration Management for AgentJW"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    """Centralized configuration management"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("sicuan/config/settings.json")
        self._config = self._load()
        
    def _load(self) -> Dict:
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                return json.loads(self.config_path.read_text())
            except:
                pass
        return self._default_config()
    
    def _default_config(self) -> Dict:
        """Default configuration"""
        return {
            "app": {
                "name": "AgentJW",
                "version": "0.8.0",
                "environment": "development"
            },
            "api": {
                "host": "0.0.0.0",
                "port": 18791,
                "debug": True
            },
            "llm": {
                "default_model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000,
                "timeout": 30,
                "retry_count": 3
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "security": {
                "permission_file": "memory/permissions.json",
                "session_timeout": 3600
            },
            "workflow": {
                "max_steps": 20,
                "timeout": 300,
                "retry_on_failure": True
            },
            "metrics": {
                "enabled": True,
                "file": "memory/production_metrics.json"
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot notation key"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save()
    
    def _save(self) -> None:
        """Save configuration to file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(self._config, indent=2))
    
    def reload(self) -> None:
        """Reload configuration from file"""
        self._config = self._load()

# Singleton
_config = None

def get_config() -> Config:
    """Get singleton config instance"""
    global _config
    if _config is None:
        _config = Config()
    return _config
