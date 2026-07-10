"""
reporting/reporting_engine.py
================================
Statistik dari data trade nyata (paper atau live) yang tersimpan di DB.
Semua angka dihitung dari histori sungguhan — tidak ada yang di-hardcode
atau diasumsikan.
"""
import math
import statistics
from collections import defaultdict
from datetime import datetime
from typing import Dict, List

from core.database import db
from core.logger import get_logger

log = get_logger("reporting.engine")


class ReportingEngine:
    def generate_summary(self) -> Dict:
        closed = db.closed_positions()
        if not closed:
            return {"message": "Belum ada posisi yang closed — belum ada data untuk dilaporkan."}

        pnls = [p["realized_pnl_usd"] for p in closed]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]

        total_trades = len(closed)
        win_rate = len(wins) / total_trades * 100 if total_trades else 0
        avg_win = statistics.mean(wins) if wins else 0
        avg_loss = statistics.mean(losses) if losses else 0
        total_pnl = sum(pnls)
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf")
        risk_reward = (abs(avg_win / avg_loss)) if avg_loss != 0 else float("inf")

        max_drawdown = self._max_drawdown(pnls)
        sharpe = self._sharpe_ratio(pnls)

        per_strategy = self._group_by(closed, "strategy")
        per_token = self._group_by(closed, "symbol")

        return {
            "total_trades": total_trades,
            "win_rate_percent": round(win_rate, 1),
            "total_realized_pnl_usd": round(total_pnl, 4),
            "avg_win_usd": round(avg_win, 4),
            "avg_loss_usd": round(avg_loss, 4),
            "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else "inf",
            "risk_reward_ratio": round(risk_reward, 2) if risk_reward != float("inf") else "inf",
            "max_drawdown_usd": round(max_drawdown, 4),
            "sharpe_ratio": round(sharpe, 3),
            "per_strategy": per_strategy,
            "per_token": per_token,
        }

    def _group_by(self, closed: List[dict], key: str) -> Dict[str, Dict]:
        groups = defaultdict(list)
        for p in closed:
            groups[p[key]].append(p["realized_pnl_usd"])
        out = {}
        for name, pnls in groups.items():
            wins = [p for p in pnls if p > 0]
            out[name] = {
                "trades": len(pnls),
                "win_rate_percent": round(len(wins) / len(pnls) * 100, 1) if pnls else 0,
                "total_pnl_usd": round(sum(pnls), 4),
            }
        return out

    def _max_drawdown(self, pnls: List[float]) -> float:
        cumulative = 0.0
        peak = 0.0
        max_dd = 0.0
        for pnl in pnls:
            cumulative += pnl
            peak = max(peak, cumulative)
            drawdown = peak - cumulative
            max_dd = max(max_dd, drawdown)
        return max_dd

    def _sharpe_ratio(self, pnls: List[float]) -> float:
        if len(pnls) < 2:
            return 0.0
        mean = statistics.mean(pnls)
        stdev = statistics.stdev(pnls)
        if stdev == 0:
            return 0.0
        return mean / stdev * math.sqrt(len(pnls))

    def print_report(self) -> None:
        summary = self.generate_summary()
        if "message" in summary:
            log.info(summary["message"])
            return

        log.info("=" * 60)
        log.info("LAPORAN PERFORMA SICUAN SNIPER")
        log.info("=" * 60)
        log.info(f"Total trades       : {summary['total_trades']}")
        log.info(f"Win rate           : {summary['win_rate_percent']}%")
        log.info(f"Total realized PnL : ${summary['total_realized_pnl_usd']}")
        log.info(f"Avg win / avg loss : ${summary['avg_win_usd']} / ${summary['avg_loss_usd']}")
        log.info(f"Profit factor      : {summary['profit_factor']}")
        log.info(f"Risk/reward        : {summary['risk_reward_ratio']}")
        log.info(f"Max drawdown       : ${summary['max_drawdown_usd']}")
        log.info(f"Sharpe ratio       : {summary['sharpe_ratio']}")
        log.info("-- Per strategy --")
        for name, s in summary["per_strategy"].items():
            log.info(f"  {name}: {s['trades']} trades, {s['win_rate_percent']}% win, "
                      f"pnl=${s['total_pnl_usd']}")
