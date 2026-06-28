"""
Data Awareness - Mengetahui data apa yang tersedia dan apa yang tidak
"""

from pathlib import Path
from typing import Dict, List, Set, Optional
import sqlite3
import json
from dataclasses import dataclass, field


@dataclass
class DataAvailability:
    """Status ketersediaan data"""
    has_trade_history: bool = False
    trade_count: int = 0
    has_pnl_per_trade: bool = False
    has_timestamps: bool = False
    has_entry_exit: bool = False
    has_exit_reason: bool = False
    has_equity_curve: bool = False
    available_fields: Set[str] = field(default_factory=set)
    missing_fields: Set[str] = field(default_factory=set)


class DataAwarenessEngine:
    """Engine untuk mengetahui data apa yang tersedia"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.db_path = project_dir / "trade_history.db"
        self.status = DataAvailability()
        self._scan()
    
    def _scan(self):
        """Scan data yang tersedia"""
        # Cek database
        if self.db_path.exists():
            self.status.has_trade_history = True
            self._scan_database()
        
        # Cek log
        log_files = list(self.project_dir.glob("*.log"))
        if log_files:
            self.status.available_fields.add("logs")
            for log in log_files:
                if "trading" in log.name:
                    self.status.available_fields.add("trading_log")
    
    def _scan_database(self):
        """Scan database trade_history.db"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Cek tabel
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            if "trades" in tables:
                # Hitung jumlah trade
                cursor.execute("SELECT COUNT(*) FROM trades")
                self.status.trade_count = cursor.fetchone()[0]
                
                # Cek kolom
                cursor.execute("PRAGMA table_info(trades)")
                columns = [row[1] for row in cursor.fetchall()]
                self.status.available_fields.update(columns)
                
                # Cek data penting
                if "pnl" in columns:
                    self.status.has_pnl_per_trade = True
                if "timestamp" in columns:
                    self.status.has_timestamps = True
                if "entry_price" in columns and "exit_price" in columns:
                    self.status.has_entry_exit = True
                if "exit_reason" in columns:
                    self.status.has_exit_reason = True
                
                # Cek equity curve (dari cumulative PnL)
                if self.status.has_pnl_per_trade:
                    self.status.has_equity_curve = True
            
            conn.close()
            
        except Exception as e:
            pass
    
    def get_status_report(self) -> str:
        """Dapatkan laporan ketersediaan data"""
        lines = ["📊 DATA AVAILABILITY REPORT", "=" * 40]
        
        if self.status.has_trade_history:
            lines.append(f"✅ Trade History: {self.status.trade_count} trades")
        else:
            lines.append("❌ Trade History: NOT AVAILABLE")
        
        if self.status.has_pnl_per_trade:
            lines.append("✅ PnL per trade: AVAILABLE")
        else:
            lines.append("❌ PnL per trade: NOT AVAILABLE")
        
        if self.status.has_entry_exit:
            lines.append("✅ Entry/Exit prices: AVAILABLE")
        else:
            lines.append("❌ Entry/Exit prices: NOT AVAILABLE")
        
        if self.status.has_exit_reason:
            lines.append("✅ Exit reasons: AVAILABLE")
        else:
            lines.append("❌ Exit reasons: NOT AVAILABLE")
        
        if self.status.has_equity_curve:
            lines.append("✅ Equity curve: AVAILABLE")
        else:
            lines.append("❌ Equity curve: NOT AVAILABLE")
        
        if self.status.available_fields:
            lines.append(f"\n📋 Available fields: {', '.join(list(self.status.available_fields)[:10])}")
        
        return "\n".join(lines)
    
    def can_calculate(self, metric: str) -> bool:
        """Cek apakah metrik bisa dihitung"""
        required_fields = {
            "winrate": {"pnl"},
            "profit_factor": {"pnl"},
            "avg_win": {"pnl"},
            "avg_loss": {"pnl"},
            "expectancy": {"pnl"},
            "sharpe_ratio": {"pnl", "timestamp"},
            "max_drawdown": {"pnl"},
            "equity_curve": {"pnl"},
            "exit_reason_distribution": {"exit_reason"},
        }
        
        if metric not in required_fields:
            return False
        
        required = required_fields[metric]
        return required.issubset(self.status.available_fields)
