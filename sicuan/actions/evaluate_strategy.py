"""
evaluate_strategy - Evaluasi performa strategi berdasarkan data nyata
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import statistics

from sicuan.core.result_contract import ResultContract
from core.logger import logger


@dataclass
class StrategyMetrics:
    """Metrik performa strategi"""
    winrate: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    total_pnl: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    expectancy: float = 0.0
    sharpe_ratio: float = 0.0
    max_consecutive_losses: int = 0
    avg_holding_time: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def calculate_score(self) -> float:
        """Hitung skor keseluruhan (0-100)"""
        score = 0
        
        # 1. Winrate (max 25 points)
        if self.winrate >= 50:
            score += 20 + (self.winrate - 50) / 5
        else:
            score += self.winrate / 2.5
        score = min(score, 25)
        
        # 2. Profit Factor (max 25 points)
        if self.profit_factor >= 1.0:
            score += 15 + (self.profit_factor - 1.0) * 10
        else:
            score += self.profit_factor * 15
        score = min(score, 25)
        
        # 3. Drawdown (max 20 points)
        if self.max_drawdown <= 10:
            score += 20
        elif self.max_drawdown <= 20:
            score += 15
        elif self.max_drawdown <= 30:
            score += 10
        else:
            score += 5
        
        # 4. Expectancy (max 20 points)
        if self.expectancy > 0:
            score += 10 + min(self.expectancy * 10, 10)
        else:
            score += max(self.expectancy * 5, -5)
        score = max(0, min(score, 20))
        
        # 5. Sharpe Ratio (max 10 points)
        if self.sharpe_ratio > 1.0:
            score += 5 + min((self.sharpe_ratio - 1.0) * 2, 5)
        else:
            score += self.sharpe_ratio * 5
        score = min(score, 10)
        
        return round(score, 2)


class StrategyEvaluator:
    """Evaluator strategi berbasis data"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.db_path = project_dir / "trade_history.db"
        self.trades: List[Dict] = []
        self.metrics: StrategyMetrics = None
        
    def load_trades(self) -> List[Dict]:
        """Load trades dari database"""
        if not self.db_path.exists():
            logger.warning(f"Trade database not found: {self.db_path}")
            return []
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM trades 
                ORDER BY timestamp
            """)
            self.trades = [dict(row) for row in cursor.fetchall()]
            conn.close()
            logger.info(f"Loaded {len(self.trades)} trades")
            return self.trades
        except Exception as e:
            logger.error(f"Failed to load trades: {e}")
            return []
    
    def calculate_metrics(self) -> StrategyMetrics:
        """Hitung metrik dari trades"""
        if not self.trades:
            return StrategyMetrics()
        
        trades = self.trades
        total = len(trades)
        
        # Hitung dasar
        pnl_values = [t.get('pnl', 0) for t in trades]
        winning = [p for p in pnl_values if p > 0]
        losing = [p for p in pnl_values if p < 0]
        
        total_pnl = sum(pnl_values)
        win_count = len(winning)
        lose_count = len(losing)
        winrate = (win_count / total * 100) if total > 0 else 0
        
        # Profit Factor
        gross_profit = sum(winning) if winning else 0
        gross_loss = abs(sum(losing)) if losing else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Drawdown
        cumulative = []
        running = 0
        max_drawdown = 0
        peak = 0
        
        for pnl in pnl_values:
            running += pnl
            cumulative.append(running)
            if running > peak:
                peak = running
            drawdown = (peak - running) / peak * 100 if peak > 0 else 0
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Expectancy
        expectancy = total_pnl / total if total > 0 else 0
        
        # Average win/loss
        avg_win = sum(winning) / len(winning) if winning else 0
        avg_loss = sum(losing) / len(losing) if losing else 0
        
        # Sharpe Ratio (annualized, assuming daily returns)
        if len(pnl_values) > 1:
            std_dev = statistics.stdev(pnl_values) if len(pnl_values) > 1 else 1
            sharpe_ratio = (total_pnl / len(pnl_values)) / (std_dev * (252 ** 0.5)) if std_dev > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Max consecutive losses
        max_consecutive_losses = 0
        current_loss_streak = 0
        for pnl in pnl_values:
            if pnl < 0:
                current_loss_streak += 1
                max_consecutive_losses = max(max_consecutive_losses, current_loss_streak)
            else:
                current_loss_streak = 0
        
        return StrategyMetrics(
            winrate=round(winrate, 2),
            profit_factor=round(profit_factor, 3),
            max_drawdown=round(max_drawdown, 2),
            total_pnl=round(total_pnl, 4),
            total_trades=total,
            winning_trades=win_count,
            losing_trades=lose_count,
            avg_win=round(avg_win, 4),
            avg_loss=round(avg_loss, 4),
            expectancy=round(expectancy, 4),
            sharpe_ratio=round(sharpe_ratio, 3),
            max_consecutive_losses=max_consecutive_losses,
            avg_holding_time=0  # TODO: implement from trade data
        )
    
    def evaluate(self) -> Dict:
        """Evaluasi lengkap strategi"""
        self.load_trades()
        self.metrics = self.calculate_metrics()
        
        score = self.metrics.calculate_score()
        
        # Rekomendasi
        if score >= 80:
            recommendation = "EXCELLENT"
        elif score >= 60:
            recommendation = "GOOD"
        elif score >= 40:
            recommendation = "FAIR"
        else:
            recommendation = "POOR"
        
        return {
            "metrics": self.metrics.to_dict(),
            "score": score,
            "recommendation": recommendation,
            "total_trades": len(self.trades),
            "timestamp": datetime.now().isoformat()
        }


def execute(task: dict) -> dict:
    """Execute evaluate_strategy"""
    target = task.get("target", "")
    context = task.get("context", {})
    
    # Cari project
    project_dir = Path("/home/dibs/agentjw/projects") / target
    if not project_dir.exists():
        # Coba cari di daftar project
        from memory.unified_projects import unified_projects
        projects = unified_projects.list_projects()
        proj = None
        for p in projects:
            if target.lower() in p["name"].lower():
                proj = p
                break
        if proj:
            project_dir = Path(proj["project_dir"])
        else:
            contract = ResultContract(
                success=False,
                action="evaluate_strategy",
                entity=target,
                display=f"❌ Project '{target}' tidak ditemukan",
                errors=[f"Project '{target}' tidak ditemukan"]
            )
            return contract.to_dict()
    
    try:
        evaluator = StrategyEvaluator(project_dir)
        result = evaluator.evaluate()
        
        # Build display
        m = result["metrics"]
        display = f"""
📊 STRATEGY EVALUATION: {target}
{'=' * 50}

📈 Performance:
  Winrate         : {m['winrate']:.1f}%
  Profit Factor   : {m['profit_factor']:.3f}
  Expectancy      : {m['expectancy']:.4f} SOL
  Total PnL       : {m['total_pnl']:.4f} SOL

📉 Risk:
  Max Drawdown    : {m['max_drawdown']:.1f}%
  Sharpe Ratio    : {m['sharpe_ratio']:.3f}
  Max Consecutive Losses: {m['max_consecutive_losses']}

📊 Trades:
  Total           : {m['total_trades']}
  Winning         : {m['winning_trades']} ({m['winrate']:.1f}%)
  Losing          : {m['losing_trades']}
  Avg Win         : {m['avg_win']:.4f} SOL
  Avg Loss        : {m['avg_loss']:.4f} SOL

🎯 Score: {result['score']}/100
🏷️  Recommendation: {result['recommendation']}
"""
        
        contract = ResultContract(
            success=True,
            action="evaluate_strategy",
            entity=target,
            display=display,
            metrics=m,
            confidence=1.0,
            data=result
        )
        return contract.to_dict()
        
    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        contract = ResultContract(
            success=False,
            action="evaluate_strategy",
            entity=target,
            display=f"❌ Gagal mengevaluasi strategi: {str(e)}",
            errors=[str(e)]
        )
        return contract.to_dict()
