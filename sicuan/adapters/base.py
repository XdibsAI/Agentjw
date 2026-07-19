"""
Base Adapter — Interface untuk semua adapter
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseAdapter(ABC):
    """Base class untuk semua adapter"""
    
    @abstractmethod
    def execute(self, action: str, params: Dict = None) -> Dict:
        """Execute action via adapter"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> list:
        """Daftar capabilities yang didukung"""
        pass

# Registry
_adapters = {}

def register_adapter(name: str, adapter: BaseAdapter):
    _adapters[name] = adapter
    print(f"✅ Registered adapter: {name}")

def get_adapter(name: str) -> Optional[BaseAdapter]:
    return _adapters.get(name)

def get_all_adapters() -> dict:
    return _adapters

# Lazy init — avoids circular import
_initialized = False

def init_adapters():
    """Auto-register all available adapters (lazy)"""
    global _initialized
    if _initialized:
        return
    
    # Lazy imports
    from .openclaw_adapter import OpenClawAdapter
    from .hermes_adapter import HermesAdapter
    
    register_adapter("openclaw", OpenClawAdapter())
    register_adapter("hermes", HermesAdapter())
    
    _initialized = True
    print(f"📋 Registered {len(_adapters)} adapters: {list(_adapters.keys())}")

# Auto-init on first use, not on import
# init_adapters() will be called when needed
