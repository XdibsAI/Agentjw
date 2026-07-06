"""
Strategy Department - Kelola strategi trading & optimasi
"""

from typing import Dict, Any, List
from pathlib import Path
import json

from sicuan.departments.base import Department


class StrategyDepartment(Department):
    """Strategy Department — Trading strategies & optimization"""

    def __init__(self, config: Dict = None):
        super().__init__("strategy", config)
        self.strategy_file = Path("projects/godmeme_bot/strategy.py")
        self.config_file = Path("projects/godmeme_bot/config.py")

    def get_status(self) -> Dict:
        """Dapatkan status strategi"""
        return {
            "name": "Strategy",
            "strategy_file": self.strategy_file.exists(),
            "config_file": self.config_file.exists(),
            "score_threshold": self._get_score_threshold(),
            "daily_loss_limit": self._get_daily_loss_limit(),
            "stop_loss_percent": self._get_stop_loss_percent(),
            "features": self._get_features()
        }

    def get_summary(self) -> str:
        """Dapatkan ringkasan strategi"""
        status = self.get_status()
        return f"""
📊 **Strategy Summary**
  Score Threshold  : {status['score_threshold']}
  Daily Loss Limit : {status['daily_loss_limit']} SOL
  Stop Loss        : {status['stop_loss_percent']}%
  Features         : {', '.join(status['features'][:5])}
"""

    def execute(self, action: str, params: Dict) -> Dict:
        """Eksekusi action strategy"""
        if action == "get_config":
            return {"status": "ok", "data": self._get_config()}
        elif action == "update_threshold":
            return self._update_score_threshold(params.get("value", 8))
        elif action == "features":
            return {"status": "ok", "data": self._get_features()}
        else:
            return {"error": f"Unknown action: {action}"}

    def _get_score_threshold(self) -> int:
        """Dapatkan score threshold"""
        try:
            content = self.strategy_file.read_text()
            for line in content.split('\n'):
                if "should = score >=" in line:
                    return int(line.split(">=")[1].strip())
            return 10
        except:
            return 10

    def _get_daily_loss_limit(self) -> float:
        """Dapatkan daily loss limit"""
        try:
            content = self.config_file.read_text()
            for line in content.split('\n'):
                if "MAX_DAILY_LOSS_SOL" in line:
                    return float(line.split("=")[1].strip())
            return 1.0
        except:
            return 1.0

    def _get_stop_loss_percent(self) -> float:
        """Dapatkan stop loss percent"""
        try:
            content = self.config_file.read_text()
            for line in content.split('\n'):
                if "STOP_LOSS_PERCENT" in line:
                    return float(line.split("=")[1].strip())
            return 5.0
        except:
            return 5.0

    def _get_features(self) -> List[str]:
        """Dapatkan daftar features"""
        features = []
        try:
            content = self.strategy_file.read_text()
            keywords = ["stop_loss", "take_profit", "trailing_stop", "wallet_restore", 
                       "position_restore", "open_position", "close_position", 
                       "liquidity_filter", "volume_filter", "marketcap_filter"]
            for kw in keywords:
                if kw in content:
                    features.append(kw)
            return features
        except:
            return []

    def _get_config(self) -> Dict:
        """Dapatkan konfigurasi lengkap"""
        return {
            "score_threshold": self._get_score_threshold(),
            "daily_loss_limit": self._get_daily_loss_limit(),
            "stop_loss_percent": self._get_stop_loss_percent(),
            "features": self._get_features()
        }

    def _update_score_threshold(self, new_threshold: int) -> Dict:
        """Update score threshold"""
        try:
            content = self.strategy_file.read_text()
            lines = content.split('\n')
            new_lines = []
            updated = False
            
            for line in lines:
                if "should = score >=" in line:
                    new_lines.append(f"        should = score >= {new_threshold}")
                    updated = True
                else:
                    new_lines.append(line)
            
            if updated:
                self.strategy_file.write_text('\n'.join(new_lines))
                return {"status": "ok", "message": f"Score threshold updated to {new_threshold}"}
            else:
                return {"error": "Score threshold not found"}
        except Exception as e:
            return {"error": str(e)}
