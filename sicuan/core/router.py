"""Router - Request routing and orchestration"""

import json
from typing import Dict, Any, Optional, Callable
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Router:
    """Request router with rules-based routing"""
    
    def __init__(self, rules_path: Optional[Path] = None):
        self.rules_path = rules_path or Path("sicuan/config/routing_rules.json")
        self.routes = {}
        self.default_handler = None
        self._load_rules()
    
    def _load_rules(self):
        """Load routing rules from file"""
        if self.rules_path.exists():
            try:
                rules = json.loads(self.rules_path.read_text())
                print(f"[ROUTER] Loaded {len(rules)} rules from {self.rules_path}")
                self.routes = rules
                return
            except Exception as e:
                logger.warning(f"Failed to load routing rules: {e}")
        
        # Default rules
        self.routes = {
            "workflow": {
                "create": "workflow_engine.create_workflow",
                "execute": "workflow_engine.execute",
                "status": "workflow_engine.get_status"
            },
            "ceo": {
                "decision": "ceo_agent.make_decision",
                "health": "ceo_agent.get_health_score",
                "priorities": "ceo_agent.get_priorities"
            },
            "metrics": {
                "get": "production_metrics.get_dashboard",
                "workflow": "production_metrics.record_workflow",
                "recovery": "production_metrics.record_recovery"
            },
            "permission": {
                "check": "permission_engine.check_permission",
                "add_user": "permission_engine.add_user",
                "remove_user": "permission_engine.remove_user"
            }
        }
        print(f"[ROUTER] Using {len(self.routes)} default rules")
    
    def route(self, category: str, action: str) -> Optional[str]:
        """Get handler path for category and action"""
        if category in self.routes:
            if action in self.routes[category]:
                return self.routes[category][action]
        return None
    
    def get_handler(self, category: str, action: str) -> Optional[Callable]:
        """Get handler function for category and action"""
        handler_path = self.route(category, action)
        if not handler_path:
            return None
        
        # Parse handler path
        parts = handler_path.split('.')
        if len(parts) != 2:
            return None
        
        module_name, function_name = parts
        
        try:
            # Import module
            import importlib
            module = importlib.import_module(f"sicuan.core.{module_name}")
            handler = getattr(module, function_name, None)
            if handler:
                logger.debug(f"Handler found: {handler_path}")
                return handler
        except ImportError as e:
            logger.warning(f"Could not import {module_name}: {e}")
        
        return None

# Singleton
_router = None

def get_router() -> Router:
    """Get singleton router instance"""
    global _router
    if _router is None:
        _router = Router()
    return _router
