"""
Godmeme Status Action - Get status of godmeme_bot
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict

from sicuan.adapters.project_adapter import get_project_adapter


def execute(task: dict) -> dict:
    """
    Execute godmeme status check
    """
    try:
        # Get project data from adapter
        adapter = get_project_adapter()
        projects = adapter.get_projects()
        
        # Find godmeme_bot project
        godmeme_project = None
        for p in projects:
            if p.get("name") == "godmeme_bot":
                godmeme_project = p
                break
        
        if not godmeme_project:
            return {
                "success": False,
                "display": "❌ Project godmeme_bot tidak ditemukan",
                "data": {}
            }
        
        # Import status_sync_provider
        import sys
        sys.path.insert(0, '/home/dibs/agentjw')
        from projects.godmeme_bot.status_sync_provider import get_godmeme_status
        
        # Get status
        data = get_godmeme_status()
        
        # Build response
        process = data.get("process", {})
        mode = data.get("mode", "unknown")
        balance = data.get("balance", 0)
        database = data.get("database", {})
        
        response = f"""
🤖 GODMEME STATUS
Process: {'RUNNING' if process.get('alive', False) else 'STOPPED'}
PID: {process.get('pid', 'N/A')}
Mode: {mode}
Balance: {balance:.6f} SOL

Trades: {database.get('trades', 0)}
BUY: {database.get('buy', 0)}
SELL: {database.get('sell', 0)}
Realized PnL: {database.get('realized_pnl', 0):.6f} SOL

Last Event: {data.get('last_event', 'N/A')}
"""
        
        return {
            "success": True,
            "display": response.strip(),
            "data": data
        }
        
    except Exception as e:
        return {
            "success": False,
            "display": f"❌ Error getting godmeme status: {str(e)}",
            "data": {"error": str(e)}
        }
