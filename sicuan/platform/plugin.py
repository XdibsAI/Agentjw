"""
Plugin SDK - Discover dan register plugin
"""

from pathlib import Path
import json
import importlib
import sys
from typing import Dict, List, Optional


class PluginManager:
    """Plugin management system"""

    def __init__(self):
        self.plugin_dir = Path("/home/dibs/agentjw/plugins")
        self.plugin_dir.mkdir(exist_ok=True)
        self.plugins = {}
        self._discover()

    def _discover(self):
        """Discover plugins"""
        for plugin_path in self.plugin_dir.glob("*/plugin.json"):
            try:
                metadata = json.loads(plugin_path.read_text())
                plugin_name = plugin_path.parent.name
                self.plugins[plugin_name] = {
                    "name": plugin_name,
                    "path": str(plugin_path.parent),
                    "metadata": metadata,
                    "loaded": False
                }
            except:
                pass

    def load(self, plugin_name: str) -> bool:
        """Load plugin"""
        if plugin_name not in self.plugins:
            return False
        
        plugin = self.plugins[plugin_name]
        if plugin["loaded"]:
            return True
        
        # Add to path
        plugin_path = Path(plugin["path"])
        sys.path.insert(0, str(plugin_path))
        
        # Import main module
        try:
            module = importlib.import_module(plugin_name)
            if hasattr(module, "register"):
                module.register()
            plugin["loaded"] = True
            return True
        except Exception as e:
            print(f"[PLUGIN] Error loading {plugin_name}: {e}")
            return False

    def list_plugins(self) -> List[Dict]:
        """List all plugins"""
        return [
            {
                "name": name,
                "metadata": p["metadata"],
                "loaded": p["loaded"]
            }
            for name, p in self.plugins.items()
        ]


def get_plugin_manager():
    _manager = None
    if _manager is None:
        _manager = PluginManager()
    return _manager
