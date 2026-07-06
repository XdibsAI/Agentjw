"""
Finance Department - Kelola keuangan & PnL
"""

from typing import Dict, Any
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path

from sicuan.departments.base import Department


class FinanceDepartment(Department):
    """Finance Department — PnL, budgeting, reporting"""

    def __init__(self, config: Dict = None):
        super().__init__("finance", config)
        self.db_path = Path("projects/godmeme_bot/trading.db")

    def get_status(self) -> Dict:
        """Dapatkan status keuangan"""
        return {
            "name": "Finance",
            "total_pnl": self._get_total_pnl(),
            "total_trades": self._get_total_trades(),
            "win_rate": self._get_win_rate(),
            "balance": self._get_balance(),
            "daily_pnl": self._get_daily_pnl(),
            "weekly_pnl": self._get_weekly_pnl(),
            "monthly_pnl": self._get_monthly_pnl()
        }

    def get_summary(self) -> str:
        """Dapatkan ringkasan keuangan"""
        status = self.get_status()
        return f"""
📊 **Finance Summary**
  Total PnL    : {status['total_pnl']:.4f} SOL
  Total Trades : {status['total_trades']}
  Win Rate     : {status['win_rate']:.1f}%
  Balance      : {status['balance']:.4f} SOL
  Daily PnL    : {status['daily_pnl']:.4f} SOL
  Weekly PnL   : {status['weekly_pnl']:.4f} SOL
  Monthly PnL  : {status['monthly_pnl']:.4f} SOL
"""

    def execute(self, action: str, params: Dict) -> Dict:
        """Eksekusi action finance"""
        if action == "report":
            return {"status": "ok", "data": self.get_status()}
        elif action == "summary":
            return {"status": "ok", "data": self.get_summary()}
        elif action == "daily":
            return {"status": "ok", "data": self._get_daily_pnl()}
        elif action == "weekly":
            return {"status": "ok", "data": self._get_weekly_pnl()}
        elif action == "monthly":
            return {"status": "ok", "data": self._get_monthly_pnl()}
        else:
            return {"error": f"Unknown action: {action}"}

    def _get_total_pnl(self) -> float:
        """Total PnL"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(realized_pnl) FROM trades WHERE realized_pnl IS NOT NULL")
            result = cursor.fetchone()[0] or 0.0
            conn.close()
            return float(result)
        except:
            return 0.0

    def _get_total_trades(self) -> int:
        """Total trades"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM trades WHERE realized_pnl IS NOT NULL")
            result = cursor.fetchone()[0] or 0
            conn.close()
            return result
        except:
            return 0

    def _get_win_rate(self) -> float:
        """Win rate"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
                    COUNT(*) as total
                FROM trades WHERE realized_pnl IS NOT NULL
            """)
            row = cursor.fetchone()
            conn.close()
            wins = row[0] or 0
            total = row[1] or 1
            return (wins / total * 100) if total > 0 else 0
        except:
            return 0

    def _get_balance(self) -> float:
        """Current balance"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT balance FROM config ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            conn.close()
            return float(result[0]) if result else 6.181848
        except:
            return 6.181848

    def _get_daily_pnl(self) -> float:
        """Daily PnL"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(realized_pnl) FROM trades 
                WHERE DATE(created_at) = ? AND realized_pnl IS NOT NULL
            """, (today,))
            result = cursor.fetchone()[0] or 0.0
            conn.close()
            return float(result)
        except:
            return 0.0

    def _get_weekly_pnl(self) -> float:
        """Weekly PnL"""
        try:
            week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(realized_pnl) FROM trades 
                WHERE DATE(created_at) >= ? AND realized_pnl IS NOT NULL
            """, (week_ago,))
            result = cursor.fetchone()[0] or 0.0
            conn.close()
            return float(result)
        except:
            return 0.0

    def _get_monthly_pnl(self) -> float:
        """Monthly PnL"""
        try:
            month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(realized_pnl) FROM trades 
                WHERE DATE(created_at) >= ? AND realized_pnl IS NOT NULL
            """, (month_ago,))
            result = cursor.fetchone()[0] or 0.0
            conn.close()
            return float(result)
        except:
            return 0.0
