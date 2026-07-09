"""
Billing - Quota based, bukan credit fixed
"""

from pathlib import Path
from datetime import datetime
from typing import Dict


class Billing:
    """Billing dengan quota per workspace"""

    def __init__(self):
        self.billing_dir = Path("/home/dibs/agentjw/memory/billing")
        self.billing_dir.mkdir(exist_ok=True)

    def get_plan(self, plan_name: str) -> Dict:
        """Dapatkan detail plan"""
        plans = {
            "free": {
                "name": "Free",
                "monthly_tokens": 10000,
                "price": 0,
                "features": ["Chat", "Basic Memory", "1 Agent"]
            },
            "pro": {
                "name": "Pro",
                "monthly_tokens": 500000,
                "price": 29.99,
                "features": ["Chat", "Memory", "5 Agents", "Plugins"]
            },
            "business": {
                "name": "Business",
                "monthly_tokens": 5000000,
                "price": 99.99,
                "features": ["All Pro", "Custom Models", "Team", "Priority"]
            }
        }
        return plans.get(plan_name, plans["free"])

    def use_tokens(self, workspace_id: str, tokens: int) -> Dict:
        """Gunakan tokens, cek quota"""
        from .workspace import get_workspace
        workspace = get_workspace()
        ws = workspace.get(workspace_id)
        
        if not ws:
            return {"success": False, "error": "Workspace not found"}
        
        quota = ws["billing"]["quota"]
        remaining = quota["monthly_tokens"] - quota["used_tokens"]
        
        if remaining < tokens:
            return {
                "success": False,
                "error": "Quota exceeded",
                "remaining": remaining,
                "needed": tokens
            }
        
        quota["used_tokens"] += tokens
        workspace.update(workspace_id, ws)
        
        return {
            "success": True,
            "remaining": quota["monthly_tokens"] - quota["used_tokens"],
            "used": quota["used_tokens"],
            "total": quota["monthly_tokens"]
        }

    def get_usage(self, workspace_id: str) -> Dict:
        """Dapatkan usage"""
        from .workspace import get_workspace
        workspace = get_workspace()
        ws = workspace.get(workspace_id)
        
        if not ws:
            return {"error": "Workspace not found"}
        
        quota = ws["billing"]["quota"]
        return {
            "total": quota["monthly_tokens"],
            "used": quota["used_tokens"],
            "remaining": quota["monthly_tokens"] - quota["used_tokens"],
            "plan": ws["billing"]["plan"],
            "reset_date": quota["reset_date"]
        }


def get_billing():
    _billing = None
    if _billing is None:
        _billing = Billing()
    return _billing
