"""
Evaluator Engine - Membandingkan performa sebelum dan sesudah perubahan
"""

from typing import Dict, List, Any
from dataclasses import dataclass
import json
from pathlib import Path
from core.logger import logger


@dataclass
class PerformanceMetrics:
    """Metrik performa untuk evaluasi"""
    winrate: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    total_pnl: float = 0.0
    total_trades: int = 0
    sharpe_ratio: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    risk_reward: float = 0.0
    
    def is_better_than(self, other: 'PerformanceMetrics', thresholds: Dict = None) -> Dict:
        """Bandingkan dua metrik"""
        thresholds = thresholds or {
            "winrate": 5,  # minimal 5% improvement
            "profit_factor": 0.1,
            "max_drawdown": -5,  # drawdown harus turun
        }
        
        improvements = {}
        overall = True
        
        # Winrate
        wr_improvement = self.winrate - other.winrate
        improvements["winrate"] = wr_improvement
        if wr_improvement < thresholds["winrate"]:
            overall = False
        
        # Profit Factor
        pf_improvement = self.profit_factor - other.profit_factor
        improvements["profit_factor"] = pf_improvement
        if pf_improvement < thresholds["profit_factor"]:
            overall = False
        
        # Drawdown (harus turun)
        dd_improvement = other.max_drawdown - self.max_drawdown
        improvements["max_drawdown"] = dd_improvement
        if dd_improvement < thresholds["max_drawdown"]:
            overall = False
        
        return {
            "overall": overall,
            "improvements": improvements,
            "recommendation": "merge" if overall else "reject"
        }


class EvaluatorEngine:
    """Engine untuk mengevaluasi perubahan kode"""
    
    def __init__(self):
        self.baseline: Dict[str, PerformanceMetrics] = {}
        self.results: List[Dict] = []
        
    def run_backtest(self, project_dir: Path, strategy_name: str) -> PerformanceMetrics:
        """Jalankan backtest dan return metrik"""
        logger.info(f"Running backtest for {strategy_name} in {project_dir}")
        
        # TODO: Integrasi dengan backtest engine
        # Untuk sementara, return dummy data
        return PerformanceMetrics(
            winrate=45.0,
            profit_factor=0.85,
            max_drawdown=32.0,
            total_pnl=-3.8,
            total_trades=120,
            sharpe_ratio=0.4,
            avg_win=0.15,
            avg_loss=0.12,
            risk_reward=1.25
        )
    
    def evaluate_change(self, project_dir: Path, strategy_name: str, 
                        before: PerformanceMetrics, after: PerformanceMetrics,
                        thresholds: Dict = None) -> Dict:
        """Evaluasi perubahan kode"""
        
        result = before.is_better_than(after, thresholds)
        
        # Simpan hasil
        evaluation = {
            "strategy": strategy_name,
            "before": before.__dict__,
            "after": after.__dict__,
            "decision": result["recommendation"],
            "improvements": result["improvements"],
            "timestamp": str(Path(".").resolve())
        }
        self.results.append(evaluation)
        
        # Log hasil
        if result["recommendation"] == "merge":
            logger.info(f"✅ Change approved: {strategy_name}")
        else:
            logger.warning(f"❌ Change rejected: {strategy_name}")
            for metric, improvement in result["improvements"].items():
                logger.info(f"  {metric}: {improvement:+.2f}")
        
        return evaluation
    
    def get_report(self) -> Dict:
        """Dapatkan laporan evaluasi"""
        if not self.results:
            return {"total": 0, "approved": 0, "rejected": 0}
        
        approved = sum(1 for r in self.results if r["decision"] == "merge")
        return {
            "total": len(self.results),
            "approved": approved,
            "rejected": len(self.results) - approved,
            "approval_rate": approved / len(self.results) * 100
        }
