"""
Analysis Agent — Analisis data & trading
"""

from typing import Dict, Any, List
from pathlib import Path

from sicuan.agents.base import Agent


class AnalysisAgent(Agent):
    """Analysis Agent — Analisis data & trading"""

    def __init__(self):
        super().__init__("AnalysisAgent", "Data Analyst")
        self.db_path = Path("projects/godmeme_bot/trading.db")

    def get_capabilities(self) -> list:
        return ["analysis", "analytics", "stats", "trend", "pattern"]

    def execute(self, task: Dict) -> Dict:
        """Eksekusi task analysis"""
        action = task.get("action", "summary")
        
        if action == "summary":
            return self._get_summary()
        elif action == "win_rate":
            return self._get_win_rate()
        elif action == "distribution":
            return self._get_distribution()
        else:
            return {"error": f"Unknown action: {action}"}

    def _get_summary(self) -> Dict:
        """Dapatkan summary"""
        try:
            import sqlite3
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN realized_pnl < 0 THEN 1 ELSE 0 END) as losses,
                    SUM(realized_pnl) as total_pnl,
                    AVG(realized_pnl) as avg_pnl
                FROM trades WHERE realized_pnl IS NOT NULL
            """)
            row = cursor.fetchone()
            conn.close()
            
            total = row[0] or 1
            wins = row[1] or 0
            losses = row[2] or 0
            win_rate = (wins / total * 100) if total > 0 else 0
            
            return {
                "status": "ok",
                "data": {
                    "total_trades": total,
                    "wins": wins,
                    "losses": losses,
                    "win_rate": win_rate,
                    "total_pnl": row[3] or 0.0,
                    "avg_pnl": row[4] or 0.0
                }
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _get_win_rate(self) -> Dict:
        """Dapatkan win rate"""
        summary = self._get_summary()
        if summary["status"] == "ok":
            return {
                "status": "ok",
                "data": {
                    "win_rate": summary["data"]["win_rate"],
                    "wins": summary["data"]["wins"],
                    "losses": summary["data"]["losses"]
                }
            }
        return summary

    def _get_distribution(self) -> Dict:
        """Dapatkan distribusi PnL"""
        try:
            import sqlite3
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT realized_pnl
                FROM trades WHERE realized_pnl IS NOT NULL
            """)
            rows = cursor.fetchall()
            conn.close()
            
            pnls = [r[0] for r in rows]
            
            return {
                "status": "ok",
                "data": {
                    "total": len(pnls),
                    "positive": len([p for p in pnls if p > 0]),
                    "negative": len([p for p in pnls if p < 0]),
                    "zero": len([p for p in pnls if p == 0]),
                    "min": min(pnls) if pnls else 0,
                    "max": max(pnls) if pnls else 0
                }
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
