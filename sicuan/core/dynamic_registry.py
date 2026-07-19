"""
Dynamic Tool Registry — Registry berbasis metadata dengan discovery otomatis
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

@dataclass
class ToolDefinition:
    name: str
    provider: str
    priority: int = 100
    timeout: int = 60
    retry: int = 2
    fallback: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

class DynamicToolRegistry:
    """
    Registry dinamis dengan metadata dan discovery otomatis
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("sicuan/config/tools.json")
        self._tools: Dict[str, ToolDefinition] = {}
        self._load_defaults()
    
    def _load_defaults(self):
        """Load default tools"""
        defaults = {
            "send_message": ToolDefinition(
                name="send_message",
                provider="openclaw",
                priority=100,
                timeout=30,
                retry=2,
                fallback=[],
                capabilities=["telegram", "whatsapp", "discord", "slack"],
                description="Send message to any platform"
            ),
            "broadcast": ToolDefinition(
                name="broadcast",
                provider="openclaw",
                priority=100,
                timeout=60,
                retry=2,
                fallback=[],
                capabilities=["telegram", "whatsapp", "discord", "slack"],
                description="Broadcast message to all channels"
            ),
            "browser": ToolDefinition(
                name="browser",
                provider="hermes",
                priority=100,
                timeout=120,
                retry=3,
                fallback=["openclaw"],
                capabilities=["navigate", "click", "screenshot"],
                description="Browser automation"
            ),
            "search": ToolDefinition(
                name="search",
                provider="hermes",
                priority=100,
                timeout=60,
                retry=2,
                fallback=["openclaw"],
                capabilities=["web", "news"],
                description="Search the web"
            ),
            "vision": ToolDefinition(
                name="vision",
                provider="hermes",
                priority=100,
                timeout=120,
                retry=2,
                fallback=[],
                capabilities=["analyze", "ocr"],
                description="Vision/Image analysis"
            ),
            "computer_use": ToolDefinition(
                name="computer_use",
                provider="hermes",
                priority=100,
                timeout=180,
                retry=3,
                fallback=[],
                capabilities=["click", "type", "screenshot"],
                description="Computer use automation"
            ),
            "file": ToolDefinition(
                name="file",
                provider="native",
                priority=100,
                timeout=30,
                retry=1,
                fallback=["hermes"],
                capabilities=["read", "write", "list"],
                description="File operations"
            ),
            "code": ToolDefinition(
                name="code",
                provider="native",
                priority=100,
                timeout=60,
                retry=2,
                fallback=["hermes"],
                capabilities=["execute", "analyze"],
                description="Code execution"
            ),
            "get_channels": ToolDefinition(
                name="get_channels",
                provider="openclaw",
                priority=100,
                timeout=30,
                retry=2,
                fallback=[],
                capabilities=[],
                description="Get list of available channels"
            ),
        }
        
        for name, tool in defaults.items():
            self.register(tool)
    
    def register(self, tool: ToolDefinition):
        """Register a tool"""
        self._tools[tool.name] = tool
        print(f"✅ Registered tool: {tool.name} (provider: {tool.provider})")
    
    def discover(self, provider: str, tools: List[Dict]):
        """Auto-discover and register tools from provider"""
        for tool_data in tools:
            tool = ToolDefinition(
                name=tool_data.get("name"),
                provider=provider,
                priority=tool_data.get("priority", 100),
                timeout=tool_data.get("timeout", 60),
                retry=tool_data.get("retry", 2),
                fallback=tool_data.get("fallback", []),
                capabilities=tool_data.get("capabilities", []),
                description=tool_data.get("description", ""),
                metadata=tool_data.get("metadata", {})
            )
            self.register(tool)
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get tool by name"""
        return self._tools.get(name)
    
    def get_best_tool(self, capability: str, platform: str = None) -> Optional[ToolDefinition]:
        """Get best tool for a capability and platform"""
        candidates = []
        
        for tool in self._tools.values():
            # Check capability
            if capability not in tool.capabilities and tool.name != capability:
                continue
            
            # Check platform support
            if platform and platform not in tool.capabilities and tool.name != capability:
                continue
            
            candidates.append(tool)
        
        if not candidates:
            return None
        
        # Sort by priority (higher = better)
        candidates.sort(key=lambda x: x.priority, reverse=True)
        return candidates[0]
    
    def list_all(self) -> Dict:
        """List all tools with metadata"""
        return {
            name: {
                "provider": tool.provider,
                "priority": tool.priority,
                "timeout": tool.timeout,
                "retry": tool.retry,
                "fallback": tool.fallback,
                "capabilities": tool.capabilities,
                "description": tool.description
            }
            for name, tool in self._tools.items()
        }
    
    def save(self):
        """Save registry to file"""
        data = {
            name: {
                "provider": tool.provider,
                "priority": tool.priority,
                "timeout": tool.timeout,
                "retry": tool.retry,
                "fallback": tool.fallback,
                "capabilities": tool.capabilities,
                "description": tool.description
            }
            for name, tool in self._tools.items()
        }
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(data, indent=2))

# Singleton
_registry = None

def get_dynamic_registry() -> DynamicToolRegistry:
    global _registry
    if _registry is None:
        _registry = DynamicToolRegistry()
    return _registry
