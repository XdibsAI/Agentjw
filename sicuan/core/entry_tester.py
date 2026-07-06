"""
Entry Tester - Test entry di jam 07 UTC
"""

import asyncio
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List


class EntryTester:
    """Test entry quality berdasarkan waktu"""

    def __init__(self):
        self.db_path = Path("projects/godmeme_bot/trading.db")
        self.results = {}

    def analyze_hour_performance(self, hour: int) -> Dict:
        """Analisis performa di jam tertentu"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN realized_pnl < 0 THEN 1 ELSE 0 END) as losses,
                    SUM(realized_pnl) as total_pnl,
                    AVG(realized_pnl) as avg_pnl
                FROM trades 
                WHERE realized_pnl IS NOT NULL 
                AND strftime('%H', created_at) = ?
            """, (f"{hour:02d}",))
            
            row = cursor.fetchone()
            conn.close()
            
            total = row[0] or 0
            wins = row[1] or 0
            losses = row[2] or 0
            win_rate = (wins / total * 100) if total > 0 else 0
            
            return {
                "hour": hour,
                "total": total,
                "wins": wins,
                "losses": losses,
                "win_rate": win_rate,
                "total_pnl": row[3] or 0.0,
                "avg_pnl": row[4] or 0.0
            }
        except Exception as e:
            return {"error": str(e)}

    def get_best_hours(self, limit: int = 3) -> List:
        """Dapatkan jam dengan performa terbaik"""
        results = []
        for hour in range(24):
            result = self.analyze_hour_performance(hour)
            if result.get("total", 0) > 0:
                results.append(result)
        
        # Sort by win rate
        results.sort(key=lambda x: x.get("win_rate", 0), reverse=True)
        return results[:limit]

    def get_worst_hours(self, limit: int = 3) -> List:
        """Dapatkan jam dengan performa terburuk"""
        results = []
        for hour in range(24):
            result = self.analyze_hour_performance(hour)
            if result.get("total", 0) > 0:
                results.append(result)
        
        # Sort by win rate (ascending)
        results.sort(key=lambda x: x.get("win_rate", 0))
        return results[:limit]

    def get_recommendation(self) -> str:
        """Dapatkan rekomendasi entry time"""
        best = self.get_best_hours(1)
        worst = self.get_worst_hours(1)
        
        if not best:
            return "Belum ada data entry time yang cukup."
        
        best_hour = best[0]
        worst_hour = worst[0] if worst else None
        
        lines = []
        lines.append("📊 **Entry Time Recommendation**")
        lines.append("")
        lines.append(f"✅ **Best Entry Time: {best_hour['hour']:02d}:00 UTC**")
        lines.append(f"   - Trades: {best_hour['total']}")
        lines.append(f"   - Win Rate: {best_hour['win_rate']:.1f}%")
        lines.append(f"   - PnL: {best_hour['total_pnl']:.4f} SOL")
        lines.append("")
        
        if worst_hour and worst_hour['hour'] != best_hour['hour']:
            lines.append(f"❌ **Worst Entry Time: {worst_hour['hour']:02d}:00 UTC**")
            lines.append(f"   - Trades: {worst_hour['total']}")
            lines.append(f"   - Win Rate: {worst_hour['win_rate']:.1f}%")
            lines.append(f"   - PnL: {worst_hour['total_pnl']:.4f} SOL")
        
        lines.append("")
        lines.append("💡 **Rekomendasi:**")
        lines.append(f"   - Prioritaskan entry di jam {best_hour['hour']:02d}:00 UTC")
        if worst_hour:
            lines.append(f"   - Hindari entry di jam {worst_hour['hour']:02d}:00 UTC")
        
        return "\n".join(lines)
