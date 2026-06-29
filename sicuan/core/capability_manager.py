"""
Capability Manager - Register, discover, execute capabilities
"""

from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
import importlib


@dataclass
class Capability:
    """Sebuah capability/plugin"""
    name: str
    description: str
    handler: Callable
    version: str = "1.0.0"
    permissions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


class CapabilityManager:
    """Manage all capabilities/plugins"""
    
    _instance = None
    _capabilities: Dict[str, Capability] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, capability: Capability):
        """Register a capability"""
        self._capabilities[capability.name] = capability
        print(f"[CAPABILITY] Registered: {capability.name}")
    
    def unregister(self, name: str):
        """Unregister a capability"""
        if name in self._capabilities:
            del self._capabilities[name]
            print(f"[CAPABILITY] Unregistered: {name}")
    
    def get(self, name: str) -> Optional[Capability]:
        """Get capability by name"""
        return self._capabilities.get(name)
    
    def execute(self, name: str, params: Dict) -> Any:
        """Execute a capability"""
        capability = self.get(name)
        if not capability:
            raise ValueError(f"Capability '{name}' not found")
        return capability.handler(params)
    
    def list_all(self) -> List[str]:
        """List all capabilities"""
        return list(self._capabilities.keys())
    
    def discover(self, path: str):
        """Discover capabilities from a module"""
        # TODO: Auto-discover from plugins directory
        pass
