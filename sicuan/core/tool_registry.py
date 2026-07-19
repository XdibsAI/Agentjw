"""
Tool Registry — Registry dengan metadata, priority, fallback, health
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

class ProviderStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    UNKNOWN = "unknown"

@dataclass
class ToolEntry:
    """Metadata untuk satu tool"""
    name: str
    provider: str
    priority: int = 100
    fallback: List[str] = field(default_factory=list)
    status: ProviderStatus = ProviderStatus.UNKNOWN
    capabilities: List[str] = field(default_factory=list)
    description: str = ""
    
    def is_available(self) -> bool:
        return self.status in [ProviderStatus.HEALTHY, ProviderStatus.DEGRADED]

class ToolRegistry:
    """
    Registry untuk semua tool dengan metadata
    """
    
    def __init__(self):
        self._tools: Dict[str, ToolEntry] = {}
        self._adapter_status = {}
        self._init_default_tools()
    
    def _init_default_tools(self):
        """Initialize default tools"""
        # OpenClaw tools
        self.register(ToolEntry(
            name="send_message",
            provider="openclaw",
            priority=100,
            fallback=[],
            capabilities=["telegram", "whatsapp", "discord", "slack"],
            description="Send message to any platform"
        ))
        self.register(ToolEntry(
            name="broadcast",
            provider="openclaw",
            priority=100,
            fallback=[],
            capabilities=["telegram", "whatsapp", "discord", "slack"],
            description="Broadcast message to all channels"
        ))
        self.register(ToolEntry(
            name="get_channels",
            provider="openclaw",
            priority=100,
            fallback=[],
            capabilities=[],
            description="Get list of available channels"
        ))
        
        # Hermes tools
        self.register(ToolEntry(
            name="browser",
            provider="hermes",
            priority=100,
            fallback=["openclaw"],
            capabilities=["navigate", "click", "screenshot"],
            description="Browser automation"
        ))
        self.register(ToolEntry(
            name="search",
            provider="hermes",
            priority=100,
            fallback=["openclaw"],
            capabilities=["web", "news"],
            description="Search the web"
        ))
        self.register(ToolEntry(
            name="vision",
            provider="hermes",
            priority=100,
            fallback=[],
            capabilities=["analyze", "ocr"],
            description="Vision/Image analysis"
        ))
        self.register(ToolEntry(
            name="computer_use",
            provider="hermes",
            priority=100,
            fallback=[],
            capabilities=["click", "type", "screenshot"],
            description="Computer use automation"
        ))
        self.register(ToolEntry(
            name="file",
            provider="native",
            priority=100,
            fallback=["hermes"],
            capabilities=["read", "write", "list"],
            description="File operations"
        ))
        self.register(ToolEntry(
            name="code",
            provider="native",
            priority=100,
            fallback=["hermes"],
            capabilities=["execute", "analyze"],
            description="Code execution"
        ))
    
    def register(self, entry: ToolEntry):
        """Register a tool"""
        self._tools[entry.name] = entry
        print(f"✅ Registered tool: {entry.name} (provider: {entry.provider})")
    
    def get_tool(self, name: str) -> Optional[ToolEntry]:
        """Get tool by name"""
        return self._tools.get(name)
    
    def get_tools_by_provider(self, provider: str) -> List[ToolEntry]:
        """Get all tools by provider"""
        return [t for t in self._tools.values() if t.provider == provider]
    
    def get_tools_by_capability(self, capability: str) -> List[ToolEntry]:
        """Get all tools that support a capability"""
        return [t for t in self._tools.values() if capability in t.capabilities]
    
    def set_status(self, provider: str, status: ProviderStatus):
        """Set status for all tools of a provider"""
        self._adapter_status[provider] = status
        for tool in self._tools.values():
            if tool.provider == provider:
                tool.status = status
    
    def get_best_tool(self, capability: str, platform: str = None) -> Optional[ToolEntry]:
        """
        Get best tool for a capability and platform
        """
        candidates = []
        
        for tool in self._tools.values():
            # Check if tool supports this capability
            if capability not in tool.capabilities and tool.name != capability:
                continue
            
            # Check if tool supports platform
            if platform and platform not in tool.capabilities and tool.name != capability:
                continue
            
            # Check availability
            if not tool.is_available():
                continue
            
            candidates.append(tool)
        
        if not candidates:
            return None
        
        # Sort by priority (higher = better)
        candidates.sort(key=lambda x: x.priority, reverse=True)
        return candidates[0]
    
    def list_all(self) -> Dict:
        """List all tools with metadata"""
        result = {}
        for name, tool in self._tools.items():
            result[name] = {
                "provider": tool.provider,
                "priority": tool.priority,
                "status": tool.status.value,
                "capabilities": tool.capabilities,
                "description": tool.description,
                "fallback": tool.fallback
            }
        return result

# Singleton
_registry = None

def get_tool_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
