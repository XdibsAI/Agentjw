"""
Trading Agent — Kelola bot trading
"""

from typing import Dict, Any, List
from pathlib import Path

from sicuan.agents.base import Agent


class TradingAgent(Agent):
    """Trading Agent — Kelola bot trading"""

    def __init__(self):
        super().__init__("TradingAgent", "Trading Bot Manager")
        self.db_path = Path("projects/godmeme_bot/trading.db")

    def get_capabilities(self) -> list:
        return ["trading", "bot", "pnl", "status", "position"]

    def execute(self, task: Dict) -> Dict:
        """Eksekusi task trading"""
        action = task.get("action", "status")
        
        if action == "status":
            return self._get_status()
        elif action == "pnl":
            return self._get_pnl()
        elif action == "positions":
            return self._get_positions()
        elif action == "trades":
            return self._get_recent_trades(task.get("limit", 10))
        else:
            return {"error": f"Unknown action: {action}"}

    def _get_status(self) -> Dict:
        """Dapatkan status bot"""
        try:
            import sqlite3
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END) as buys,
                    SUM(CASE WHEN side='SELL' THEN 1 ELSE 0 END) as sells,
                    SUM(realized_pnl) as total_pnl
                FROM trades WHERE realized_pnl IS NOT NULL
            """)
            row = cursor.fetchone()
            conn.close()
            
            return {
                "status": "ok",
                "data": {
                    "total_trades": row[0] or 0,
                    "buys": row[1] or 0,
                    "sells": row[2] or 0,
                    "total_pnl": row[3] or 0.0
                }
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _get_pnl(self) -> Dict:
        """Dapatkan PnL"""
        try:
            import sqlite3
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    SUM(realized_pnl) as total_pnl,
                    AVG(realized_pnl) as avg_pnl,
                    MIN(realized_pnl) as min_pnl,
                    MAX(realized_pnl) as max_pnl
                FROM trades WHERE realized_pnl IS NOT NULL
            """)
            row = cursor.fetchone()
            conn.close()
            
            return {
                "status": "ok",
                "data": {
                    "total_pnl": row[0] or 0.0,
                    "avg_pnl": row[1] or 0.0,
                    "min_pnl": row[2] or 0.0,
                    "max_pnl": row[3] or 0.0
                }
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _get_positions(self) -> Dict:
        """Dapatkan posisi"""
        return {"status": "ok", "data": {"message": "Positions feature coming soon"}}

    def _get_recent_trades(self, limit: int = 10) -> Dict:
        """Dapatkan recent trades"""
        try:
            import sqlite3
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT token_symbol, side, realized_pnl, created_at
                FROM trades 
                WHERE realized_pnl IS NOT NULL
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            conn.close()
            
            trades = []
            for row in rows:
                trades.append({
                    "token": row[0] or "unknown",
                    "side": row[1] or "unknown",
                    "pnl": row[2] or 0.0,
                    "time": row[3] or ""
                })
            
            return {"status": "ok", "data": trades}
        except Exception as e:
            return {"status": "error", "message": str(e)}
