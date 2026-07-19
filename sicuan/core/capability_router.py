"""
Capability Router — Routing berdasarkan capability dengan priority & fallback
"""

from typing import Dict, Any, Optional, List
from sicuan.adapters.base import get_all_adapters
from sicuan.core.tool_registry import get_tool_registry, ProviderStatus

class CapabilityRouter:
    
    # Map platform names to tool names
    CAPABILITY_MAP = {
        "telegram": "send_message",
        "whatsapp": "send_message", 
        "discord": "send_message",
        "slack": "send_message",
        "browser": "browser",
        "search": "search",
        "vision": "vision",
        "computer_use": "computer_use",
        "file": "file",
        "code": "code",
    }
    """
    Router yang memilih adapter berdasarkan capability menggunakan Tool Registry
    """
    
    def __init__(self):
        from sicuan.adapters.base import init_adapters
        init_adapters()  # Lazy init
        self.adapters = get_all_adapters()
        self.registry = get_tool_registry()
        self._init_status()
    
    def _init_status(self):
        """Initialize adapter status"""
        # Check each adapter
        for name in self.adapters:
            self.registry.set_status(name, ProviderStatus.HEALTHY)
    
    def route(self, capability: str, params: Dict = None) -> Dict:
        """
        Route capability ke adapter terbaik
        """
        params = params or {}
        platform = params.get("platform")
        
        # Map capability to tool name
        tool_name = self.CAPABILITY_MAP.get(capability, capability)
        
        # If capability is platform name, add platform to params
        if capability in ["telegram", "whatsapp", "discord", "slack"]:
            params["platform"] = capability
        
        """
        Route capability ke adapter terbaik
        """
        params = params or {}
        platform = params.get("platform")  # Platform specifier (telegram, whatsapp, etc.)
        
        # 1. Get best tool from registry
        tool = self.registry.get_best_tool(capability, platform)
        
        if tool:
            # Try primary provider
            if tool.provider in self.adapters:
                result = self.adapters[tool.provider].execute(tool.name, params)
                if result.get("status") != "error":
                    return result
            
            # Try fallbacks
            for fallback in tool.fallback:
                if fallback in self.adapters:
                    result = self.adapters[fallback].execute(tool.name, params)
                    if result.get("status") != "error":
                        return result
        
        # 2. Try all adapters that support this capability
        for name, adapter in self.adapters.items():
            if capability in adapter.get_capabilities():
                result = adapter.execute(capability, params)
                if result.get("status") != "error":
                    return result
        
        return {"status": "error", "message": f"No adapter available for capability: {capability} (platform: {platform})"}
    
    def get_available_capabilities(self) -> Dict:
        """Get all available capabilities with their adapters"""
        result = {}
        for name, adapter in self.adapters.items():
            for cap in adapter.get_capabilities():
                if cap not in result:
                    result[cap] = []
                result[cap].append(name)
        return result
    
    def health_check(self) -> Dict:
        """Check health of all adapters"""
        result = {}
        for name, adapter in self.adapters.items():
            # TODO: Implement actual health check
            result[name] = {"status": "healthy"}
        return result

# Singleton
_router = None

def get_capability_router() -> CapabilityRouter:
    global _router
    if _router is None:
        _router = CapabilityRouter()
    return _router
