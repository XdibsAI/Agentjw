"""
Action Registry - Metadata action, alias resolver, lazy loader.
TIDAK mengandung logic eksekusi.
"""

from typing import Dict, Optional, List, Callable
import importlib
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))


class ActionRegistry:

    def _discover_actions(self):
        """Auto-discover actions from sicuan/actions/ folder"""
        from pathlib import Path
        actions_dir = Path(__file__).parent / "actions"
        if not actions_dir.exists():
            return
        for file in actions_dir.glob("*.py"):
            if file.stem in ["__init__", "base"]:
                continue
            if file.stem not in self._actions:
                self._actions[file.stem] = {
                    "module": f"sicuan.actions.{file.stem}",
                    "entry": "execute",
                    "category": "auto_discovered",
                    "description": f"Auto-discovered action: {file.stem}",
                }
                print(f"[ACTION] Auto-discovered: {file.stem}")

    """Registry metadata action - resolve, has, get_metadata, list_actions"""
    
    def __init__(self):
        self._actions: Dict[str, Dict] = {}
        self._aliases: Dict[str, str] = {}
        self._init_actions()
    
    def _init_actions(self):
        """Daftar semua action - mulai dari tier-1"""
        
        # Tier 1 - Paling sering dipakai
        self._actions["scan_project"] = {
            "module": "sicuan.actions.scan_project",
            "entry": "execute",
            "category": "project",
            "description": "Scan struktur project",
            "requires_target": True,
        }
        self._actions["analyze_project"] = {
            "module": "sicuan.actions.analyze_project",
            "entry": "execute",
            "category": "project",
            "description": "Analisa health & struktur project",
            "requires_target": True,
        }
        self._actions["trace_code"] = {
            "module": "sicuan.actions.trace_code",
            "entry": "execute",
            "category": "code",
            "description": "Trace dependency/symbol",
            "requires_target": True,
        }
        self._actions["modify_logic"] = {
            "module": "sicuan.actions.modify_logic",
            "entry": "execute",
            "category": "code",
            "description": "Modifikasi logic dengan trace guard",
            "requires_target": True,
        }
        self._actions["repair_project"] = {
            "module": "sicuan.actions.repair_project",
            "entry": "execute",
            "category": "code",
            "description": "Perbaiki project bermasalah",
            "requires_target": True,
        }
        
        self._actions["build_task_queue"] = {
            "module": "sicuan.actions.build_task_queue",
            "entry": "execute",
            "category": "planning",
            "description": "Generate task queue dari goals, projects, reflection state",
            "requires_target": False,
        }
        # Aliases
        self._aliases = {
            "system_audit": "analyze_project",
            "diagnose_issue": "analyze_project",
            "health_check": "show_log",
            "inspect_runtime": "show_log",
            "inspect_codebase": "scan_project",
            "review_architecture": "analyze_project",
            "compare_results": "analyze_project",
            "buat task queue": "build_task_queue",
            "update prioritas": "build_task_queue",
            "apa prioritas": "build_task_queue",
            "update fokus": "build_task_queue",
            "fokus sekarang": "build_task_queue",
        }
    
    def resolve(self, name: str) -> Optional[str]:
        """Resolve alias ke action sebenarnya"""
        real_name = self._aliases.get(name, name)
        if real_name in self._actions:
            return real_name
        return None
    
    def has(self, name: str) -> bool:
        """Cek apakah action terdaftar (termasuk alias)"""
        return self.resolve(name) is not None
    
    def get_metadata(self, name: str) -> Optional[Dict]:
        """Dapatkan metadata action"""
        real_name = self.resolve(name)
        if not real_name:
            return None
        return self._actions.get(real_name)
    
    def list_actions(self) -> List[str]:
        """List semua action"""
        return list(self._actions.keys())
    
    def list_by_category(self, category: str) -> List[str]:
        """List action berdasarkan kategori"""
        return [
            name for name, meta in self._actions.items()
            if meta.get("category") == category
        ]
    
    def load_handler(self, name: str) -> Optional[Callable]:
        """
        Lazy load handler untuk action.
        Executor yang memanggil ini, registry hanya menyediakan metadata.
        """
        meta = self.get_metadata(name)
        if not meta:
            return None
        
        module_path = meta.get("module")
        entry_point = meta.get("entry", "execute")
        
        if not module_path:
            return None
        
        try:
            module = importlib.import_module(module_path)
            handler = getattr(module, entry_point)
            return handler
        except (ImportError, AttributeError) as e:
            return None
