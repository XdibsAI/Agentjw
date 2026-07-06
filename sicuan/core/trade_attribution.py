"""
Trade Attribution Engine - Analisis alasan menang/kalah setiap trade
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class Attribution:
    """Hasil atribusi untuk satu trade"""
    trade_id: str
    token: str
    entry_price: float
    exit_price: float
    pnl: float
    win: bool
    reasons: List[str]
    patterns: List[str]
    market_condition: str
    confidence: float


class TradeAttributionEngine:
    """Engine untuk menganalisis kenapa trade menang/kalah"""

    def __init__(self, db_path: str = "projects/godmeme_bot/trading.db"):
        self.db_path = Path(db_path)
        self.attributions: List[Attribution] = []

    def analyze_trade(self, trade: Dict) -> Attribution:
        """Analisis satu trade"""
        reasons = []
        patterns = []
        
        # 1. Cek liquidity change
        liquidity_change = trade.get("liquidity_change", 0)
        if liquidity_change < -30:
            reasons.append("liquidity_collapse")
            patterns.append("rug_risk")
        
        # 2. Cek volume change
        volume_change = trade.get("volume_change", 0)
        if volume_change < -50:
            reasons.append("volume_drop")
        
        # 3. Cek entry timing
        entry_delay = trade.get("entry_delay", 0)
        if entry_delay > 60:
            reasons.append("late_entry")
            patterns.append("fomo")
        
        # 4. Cek holder activity
        holder_change = trade.get("holder_change", 0)
        if holder_change < -10:
            reasons.append("holder_dump")
            patterns.append("whale_exit")
        
        # 5. Cek whale movement
        whale_activity = trade.get("whale_activity", 0)
        if whale_activity > 20:
            reasons.append("whale_buy" if trade.get("pnl", 0) > 0 else "whale_sell")
        
        # 6. Cek market condition
        market = trade.get("market_condition", "neutral")
        
        # 7. Cek momentum
        momentum = trade.get("momentum", 0)
        if momentum < -10:
            reasons.append("momentum_reversal")
            patterns.append("top_catch")
        
        # 8. Cek slippage
        slippage = trade.get("slippage", 0)
        if slippage > 5:
            reasons.append("high_slippage")
        
        # 9. Cek if it was a win
        pnl = trade.get("pnl", 0)
        win = pnl > 0
        
        # If win, look for positive patterns
        if win:
            if "whale_buy" in reasons:
                patterns.append("smart_money")
            if entry_delay < 30:
                patterns.append("good_entry")
            if market in ["bullish", "high_volume"]:
                patterns.append("good_market")
        else:
            # If loss, look for negative patterns
            if "late_entry" in reasons:
                patterns.append("chasing")
            if "liquidity_collapse" in reasons:
                patterns.append("rug")
            if "holder_dump" in reasons:
                patterns.append("dumped")
        
        # Determine confidence based on number of reasons
        confidence = min(0.9, 0.3 + len(reasons) * 0.1)
        
        return Attribution(
            trade_id=trade.get("id", ""),
            token=trade.get("token", "unknown"),
            entry_price=trade.get("entry_price", 0),
            exit_price=trade.get("exit_price", 0),
            pnl=pnl,
            win=win,
            reasons=reasons,
            patterns=patterns,
            market_condition=market,
            confidence=confidence
        )

    def analyze_trades(self, trades: List[Dict]) -> List[Attribution]:
        """Analisis banyak trades"""
        results = []
        for trade in trades:
            result = self.analyze_trade(trade)
            results.append(result)
            self.attributions.append(result)
        return results

    def get_stats(self) -> Dict:
        """Dapatkan statistik atribusi"""
        if not self.attributions:
            return {"total": 0}
        
        total = len(self.attributions)
        wins = sum(1 for a in self.attributions if a.win)
        losses = total - wins
        
        # Top reasons
        reason_counts = {}
        for attr in self.attributions:
            for reason in attr.reasons:
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        # Top patterns
        pattern_counts = {}
        for attr in self.attributions:
            for pattern in attr.patterns:
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        # Win rate by reason
        reason_win_rate = {}
        for reason in reason_counts.keys():
            win_with_reason = sum(1 for a in self.attributions if a.win and reason in a.reasons)
            total_with_reason = sum(1 for a in self.attributions if reason in a.reasons)
            reason_win_rate[reason] = (win_with_reason / total_with_reason * 100) if total_with_reason > 0 else 0
        
        return {
            "total": total,
            "wins": wins,
            "losses": losses,
            "win_rate": (wins / total * 100) if total > 0 else 0,
            "reason_counts": reason_counts,
            "pattern_counts": pattern_counts,
            "reason_win_rate": reason_win_rate,
            "top_reasons": sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "top_patterns": sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }

    def get_learning_insights(self) -> List[str]:
        """Dapatkan insight untuk auto learning"""
        stats = self.get_stats()
        insights = []
        
        # 1. Reason to avoid
        for reason, win_rate in stats.get("reason_win_rate", {}).items():
            if win_rate < 30 and stats.get("reason_counts", {}).get(reason, 0) > 3:
                insights.append(f"⚠️ Hindari: {reason} (win_rate: {win_rate:.1f}%)")
        
        # 2. Pattern to avoid
        for pattern, count in stats.get("pattern_counts", {}).items():
            if count > 5:
                insights.append(f"📊 Pattern terdeteksi: {pattern} ({count} trades)")
        
        # 3. Improvement suggestions
        if stats.get("win_rate", 0) < 40:
            insights.append("💡 Fokus perbaiki entry quality, bukan exit")
        
        return insights

    def print_summary(self):
        """Print summary attribusi"""
        stats = self.get_stats()
        insights = self.get_learning_insights()
        
        print("\n" + "=" * 60)
        print("📊 TRADE ATTRIBUTION SUMMARY")
        print("=" * 60)
        print(f"Total Trades  : {stats.get('total', 0)}")
        print(f"Wins          : {stats.get('wins', 0)}")
        print(f"Losses        : {stats.get('losses', 0)}")
        print(f"Win Rate      : {stats.get('win_rate', 0):.1f}%")
        
        if stats.get('top_reasons'):
            print("\n🔍 Top Reasons:")
            for reason, count in stats['top_reasons'][:5]:
                wr = stats.get('reason_win_rate', {}).get(reason, 0)
                print(f"  {reason}: {count} trades (win_rate: {wr:.1f}%)")
        
        if stats.get('top_patterns'):
            print("\n📈 Top Patterns:")
            for pattern, count in stats['top_patterns'][:5]:
                print(f"  {pattern}: {count} trades")
        
        if insights:
            print("\n💡 Insights:")
            for insight in insights:
                print(f"  {insight}")
        
        print("=" * 60)
