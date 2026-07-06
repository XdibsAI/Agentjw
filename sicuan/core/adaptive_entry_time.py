"""
Adaptive Entry Time - Belajar waktu entry terbaik dari data
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict


class AdaptiveEntryTime:
    """Adaptif entry time berdasarkan data trading"""

    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.data_file = self.memory_dir / "entry_time_data.json"
        self.hour_data = defaultdict(lambda: {"trades": 0, "wins": 0, "pnl": 0.0})
        self._load()

    def update(self, hour: int, win: bool, pnl: float):
        """Update data untuk jam tertentu"""
        self.hour_data[hour]["trades"] += 1
        if win:
            self.hour_data[hour]["wins"] += 1
        self.hour_data[hour]["pnl"] += pnl
        self._save()

    def get_hour_performance(self, hour: int) -> Dict:
        """Dapatkan performa di jam tertentu"""
        data = self.hour_data[hour]
        trades = data["trades"]
        if trades == 0:
            return {
                "hour": hour,
                "trades": 0,
                "win_rate": 0,
                "avg_pnl": 0,
                "total_pnl": 0,
                "confidence": 0
            }
        
        win_rate = (data["wins"] / trades) * 100
        avg_pnl = data["pnl"] / trades
        
        # Confidence based on number of trades
        confidence = min(1.0, trades / 10)  # 10 trades = 100% confidence
        
        return {
            "hour": hour,
            "trades": trades,
            "wins": data["wins"],
            "win_rate": win_rate,
            "total_pnl": data["pnl"],
            "avg_pnl": avg_pnl,
            "confidence": confidence
        }

    def get_best_hours(self, min_trades: int = 3) -> List[Dict]:
        """Dapatkan jam dengan performa terbaik"""
        results = []
        for hour in range(24):
            data = self.get_hour_performance(hour)
            if data["trades"] >= min_trades:
                results.append(data)
        
        # Sort by win rate, then by trades
        results.sort(key=lambda x: (x["win_rate"], x["trades"]), reverse=True)
        return results

    def get_worst_hours(self, min_trades: int = 3) -> List[Dict]:
        """Dapatkan jam dengan performa terburuk"""
        results = []
        for hour in range(24):
            data = self.get_hour_performance(hour)
            if data["trades"] >= min_trades:
                results.append(data)
        
        # Sort by win rate (ascending)
        results.sort(key=lambda x: x["win_rate"])
        return results

    def should_entry(self, hour: int, min_win_rate: float = 50) -> bool:
        """Cek apakah jam ini baik untuk entry"""
        data = self.get_hour_performance(hour)
        
        # Jika belum ada data, boleh entry
        if data["trades"] == 0:
            return True
        
        # Jika win rate di atas threshold, boleh entry
        if data["win_rate"] >= min_win_rate:
            return True
        
        return False

    def get_recommendation(self) -> str:
        """Dapatkan rekomendasi entry time"""
        best = self.get_best_hours(3)
        worst = self.get_worst_hours(3)
        
        lines = []
        lines.append("📊 **Adaptive Entry Time Recommendation**")
        lines.append("")
        lines.append(f"📈 Total data: {sum(h['trades'] for h in self.hour_data.values())} trades")
        lines.append("")
        
        if best:
            lines.append("✅ **Best Entry Hours:**")
            for h in best[:3]:
                lines.append(f"  • {h['hour']:02d}:00 UTC — {h['trades']} trades, Win Rate: {h['win_rate']:.1f}%, Avg PnL: {h['avg_pnl']:.4f} SOL")
        
        if worst:
            lines.append("")
            lines.append("❌ **Worst Entry Hours:**")
            for h in worst[:3]:
                lines.append(f"  • {h['hour']:02d}:00 UTC — {h['trades']} trades, Win Rate: {h['win_rate']:.1f}%, Avg PnL: {h['avg_pnl']:.4f} SOL")
        
        lines.append("")
        lines.append("💡 **Strategy:**")
        lines.append("  • Prioritize entry during best hours")
        lines.append("  • Avoid entry during worst hours")
        lines.append("  • System learns and adapts automatically")
        
        return "\n".join(lines)

    def _load(self):
        """Load data dari disk"""
        if self.data_file.exists():
            try:
                data = json.loads(self.data_file.read_text())
                for hour_str, values in data.items():
                    hour = int(hour_str)
                    self.hour_data[hour] = values
                print(f"[ENTRY] Loaded {len(self.hour_data)} hours data")
            except:
                pass

    def _save(self):
        """Save data ke disk"""
        data = {}
        for hour, values in self.hour_data.items():
            data[str(hour)] = values
        self.data_file.write_text(json.dumps(data, indent=2))


# Singleton
_entry = None

def get_entry_time():
    global _entry
    if _entry is None:
        _entry = AdaptiveEntryTime()
    return _entry
