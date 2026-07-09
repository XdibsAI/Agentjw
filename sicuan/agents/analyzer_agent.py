"""
AnalyzerAgent - Advanced Trading Analysis with Risk Metrics
"""

from pathlib import Path
import sqlite3
import math


class AnalyzerAgent:
    """Agent khusus untuk data analysis - advanced metrics"""

    def __init__(self):
        self.project_dir = Path("/home/dibs/agentjw/projects/godmeme_bot")

    def execute(self, instruction: str) -> dict:
        """Execute analysis task with advanced metrics"""
        
        if "trading.db" in instruction or "trade" in instruction.lower():
            return self._analyze_trading(instruction)
        
        if "config" in instruction.lower():
            return self._analyze_config(instruction)
        
        if any(kw in instruction.lower() for kw in ["jalankan bot", "run bot", "start bot"]):
            return self._run_bot()
        
        return {
            "success": False,
            "display": "❌ Tidak ada data yang bisa dianalisis"
        }

    def _analyze_trading(self, instruction: str) -> dict:
        """Advanced trading analysis with risk metrics"""
        db_path = self.project_dir / "trading.db"
        
        if not db_path.exists():
            return {
                "success": False,
                "display": "❌ Database trading.db tidak ditemukan"
            }
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Basic stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN realized_pnl < 0 THEN 1 ELSE 0 END) as losses,
                    SUM(realized_pnl) as total_pnl,
                    AVG(realized_pnl) as avg_pnl,
                    SUM(CASE WHEN realized_pnl > 0 THEN realized_pnl ELSE 0 END) as total_win,
                    SUM(CASE WHEN realized_pnl < 0 THEN realized_pnl ELSE 0 END) as total_loss,
                    MIN(realized_pnl) as max_loss,
                    MAX(realized_pnl) as max_win
                FROM trades
                WHERE realized_pnl IS NOT NULL
            """)
            row = cursor.fetchone()
            
            if not row or row[0] == 0:
                return {
                    "success": False,
                    "display": "❌ Tidak ada data trading"
                }
            
            total, wins, losses, total_pnl, avg_pnl, total_win, total_loss, max_loss, max_win = row
            
            # Risk metrics
            win_rate = wins / total * 100 if total > 0 else 0
            loss_rate = losses / total * 100 if total > 0 else 0
            profit_factor = abs(total_win / total_loss) if total_loss != 0 else 0
            expectancy = (win_rate * avg_pnl) / 100 if win_rate > 0 else 0
            
            # Drawdown (simple)
            cursor.execute("""
                SELECT realized_pnl FROM trades WHERE realized_pnl IS NOT NULL ORDER BY id
            """)
            pnl_series = [row[0] for row in cursor.fetchall()]
            
            max_drawdown = 0
            peak = 0
            running = 0
            for pnl in pnl_series:
                running += pnl if isinstance(pnl, (int, float)) else 0
                if running > peak:
                    peak = running
                drawdown = peak - running
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            conn.close()
            
            # Build report
            report = []
            report.append("📊 **ADVANCED TRADING ANALYSIS**")
            report.append("")
            report.append("**Basic Statistics:**")
            report.append(f"  Total Trades: {total}")
            report.append(f"  Wins: {wins} ({win_rate:.1f}%)")
            report.append(f"  Losses: {losses} ({loss_rate:.1f}%)")
            report.append(f"  Total PnL: {total_pnl:.4f} SOL")
            report.append(f"  Avg PnL: {avg_pnl:.4f} SOL")
            report.append("")
            report.append("**Risk Metrics:**")
            report.append(f"  Profit Factor: {profit_factor:.2f}")
            report.append(f"  Expectancy: {expectancy:.4f} SOL/trade")
            report.append(f"  Max Win: {float(max_win):.4f} SOL")
            report.append(f"  Max Loss: {float(max_loss):.4f} SOL")
            report.append(f"  Max Drawdown: {max_drawdown:.4f} SOL")
            report.append("")
            
            if total_pnl < 0:
                report.append("⚠️ **Rekomendasi:**")
                report.append(f"  - Total PnL negatif: {total_pnl:.4f} SOL")
                report.append("  - Turunkan stop loss dari 15% ke 5%")
                report.append("  - Filter entry dengan volume > $10k")
                report.append("  - Gunakan trailing stop setelah +4%")
            
            return {
                "success": True,
                "action": "analyze",
                "display": "\n".join(report),
                "data": {
                    "total": total,
                    "wins": wins,
                    "losses": losses,
                    "win_rate": win_rate,
                    "total_pnl": total_pnl,
                    "avg_pnl": avg_pnl,
                    "profit_factor": profit_factor,
                    "expectancy": expectancy,
                    "max_drawdown": max_drawdown
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "display": f"❌ Error: {e}"
            }

    def _analyze_config(self, instruction: str) -> dict:
        """Analyze config"""
        config_path = self.project_dir / "config.py"
        if not config_path.exists():
            return {
                "success": False,
                "display": "❌ config.py tidak ditemukan"
            }
        
        content = config_path.read_text()
        lines = content.splitlines()
        
        params = []
        for line in lines:
            if "=" in line and not line.strip().startswith("#"):
                key = line.split("=")[0].strip()
                value = line.split("=")[1].strip()
                params.append(f"  {key} = {value}")
        
        report = ["📋 **CONFIG PARAMETERS**", ""] + params[:20]
        
        return {
            "success": True,
            "action": "analyze",
            "display": "\n".join(report),
            "data": {"params": params}
        }

    def _run_bot(self) -> dict:
        """Run the trading bot"""
        import subprocess
        
        bot_dir = self.project_dir
        if not bot_dir.exists():
            return {
                "success": False,
                "display": "❌ Bot directory not found"
            }
        
        try:
            subprocess.Popen(
                ["python3", "main.py"],
                cwd=str(bot_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return {
                "success": True,
                "display": "✅ Bot berhasil dijalankan!",
                "data": {"status": "running", "dir": str(bot_dir)}
            }
        except Exception as e:
            return {
                "success": False,
                "display": f"❌ Gagal menjalankan bot: {e}"
            }


def get_analyzer_agent():
    return AnalyzerAgent()
