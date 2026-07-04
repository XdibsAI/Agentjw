"""
Trade Analytics Engine - Analisis mendalam data trading
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
import statistics


class TradeAnalytics:
    """Analisis mendalam data trading"""

    def __init__(self, db_path: str = "projects/godmeme_bot/trading.db"):
        self.db_path = Path(db_path)
        self.conn = None

    def analyze(self) -> Dict[str, Any]:
        """Analisis lengkap data trading"""
        if not self.db_path.exists():
            return {"error": "Database tidak ditemukan"}

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

        result = {
            "summary": self._get_summary(),
            "loss_distribution": self._get_loss_distribution(),
            "win_distribution": self._get_win_distribution(),
            "by_score": self._get_performance_by_score(),
            "by_token_age": self._get_performance_by_age(),
            "by_liquidity": self._get_performance_by_liquidity(),
            "by_hold_time": self._get_performance_by_hold_time(),
            "by_exit_reason": self._get_performance_by_exit_reason(),
            "recommendations": []
        }

        # Generate rekomendasi
        result["recommendations"] = self._generate_recommendations(result)

        self.conn.close()
        return result

    def _get_summary(self) -> Dict:
        """Summary statistik"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END) as buys,
                SUM(CASE WHEN side='SELL' THEN 1 ELSE 0 END) as sells,
                SUM(realized_pnl) as total_pnl,
                AVG(realized_pnl) as avg_pnl,
                SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN realized_pnl < 0 THEN 1 ELSE 0 END) as losses,
                MIN(realized_pnl) as min_pnl,
                MAX(realized_pnl) as max_pnl
            FROM trades WHERE realized_pnl IS NOT NULL
        """)
        row = cursor.fetchone()
        return dict(row) if row else {}

    def _get_loss_distribution(self) -> Dict:
        """Distribusi loss"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                realized_pnl,
                token_symbol,
                strategy,
                created_at
            FROM trades 
            WHERE realized_pnl < 0
            ORDER BY realized_pnl ASC
        """)
        rows = cursor.fetchall()
        
        losses = [dict(row) for row in rows]
        
        # Group by loss size
        distribution = {
            "tiny": {"count": 0, "total_pnl": 0},   # -0.001 to -0.003
            "small": {"count": 0, "total_pnl": 0},  # -0.003 to -0.006
            "medium": {"count": 0, "total_pnl": 0}, # -0.006 to -0.010
            "large": {"count": 0, "total_pnl": 0},  # -0.010 to -0.020
            "huge": {"count": 0, "total_pnl": 0},   # < -0.020
        }
        
        for loss in losses:
            pnl = float(loss['realized_pnl'])
            if pnl >= -0.003:
                distribution["tiny"]["count"] += 1
                distribution["tiny"]["total_pnl"] += pnl
            elif pnl >= -0.006:
                distribution["small"]["count"] += 1
                distribution["small"]["total_pnl"] += pnl
            elif pnl >= -0.010:
                distribution["medium"]["count"] += 1
                distribution["medium"]["total_pnl"] += pnl
            elif pnl >= -0.020:
                distribution["large"]["count"] += 1
                distribution["large"]["total_pnl"] += pnl
            else:
                distribution["huge"]["count"] += 1
                distribution["huge"]["total_pnl"] += pnl
        
        # Top 5 worst tokens
        token_loss = defaultdict(float)
        for loss in losses:
            token_loss[loss['token_symbol']] += float(loss['realized_pnl'])
        
        worst_tokens = sorted(token_loss.items(), key=lambda x: x[1])[:5]
        distribution["worst_tokens"] = worst_tokens
        
        return distribution

    def _get_win_distribution(self) -> Dict:
        """Distribusi win"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                realized_pnl,
                token_symbol,
                strategy,
                created_at
            FROM trades 
            WHERE realized_pnl > 0
            ORDER BY realized_pnl DESC
        """)
        rows = cursor.fetchall()
        wins = [dict(row) for row in rows]
        
        distribution = {
            "tiny": {"count": 0, "total_pnl": 0},   # 0 to 0.005
            "small": {"count": 0, "total_pnl": 0},  # 0.005 to 0.010
            "medium": {"count": 0, "total_pnl": 0}, # 0.010 to 0.020
            "large": {"count": 0, "total_pnl": 0},  # 0.020 to 0.050
            "huge": {"count": 0, "total_pnl": 0},   # > 0.050
        }
        
        for win in wins:
            pnl = float(win['realized_pnl'])
            if pnl <= 0.005:
                distribution["tiny"]["count"] += 1
                distribution["tiny"]["total_pnl"] += pnl
            elif pnl <= 0.010:
                distribution["small"]["count"] += 1
                distribution["small"]["total_pnl"] += pnl
            elif pnl <= 0.020:
                distribution["medium"]["count"] += 1
                distribution["medium"]["total_pnl"] += pnl
            elif pnl <= 0.050:
                distribution["large"]["count"] += 1
                distribution["large"]["total_pnl"] += pnl
            else:
                distribution["huge"]["count"] += 1
                distribution["huge"]["total_pnl"] += pnl
        
        # Top 5 best tokens
        token_win = defaultdict(float)
        for win in wins:
            token_win[win['token_symbol']] += float(win['realized_pnl'])
        
        best_tokens = sorted(token_win.items(), key=lambda x: x[1], reverse=True)[:5]
        distribution["best_tokens"] = best_tokens
        
        return distribution

    def _get_performance_by_score(self) -> Dict:
        """Performa berdasarkan score"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                strategy,
                realized_pnl,
                token_symbol
            FROM trades 
            WHERE realized_pnl IS NOT NULL
        """)
        rows = cursor.fetchall()
        
        # Parse score dari strategy (contoh: "godmeme_score_12")
        score_perf = defaultdict(lambda: {"count": 0, "total_pnl": 0, "wins": 0, "losses": 0})
        
        for row in rows:
            strategy = row['strategy'] or ""
            score = 0
            if "score_" in strategy:
                try:
                    score = int(strategy.split("score_")[1].split("_")[0])
                except:
                    pass
            
            if score > 0:
                score_perf[score]["count"] += 1
                score_perf[score]["total_pnl"] += row['realized_pnl']
                if row['realized_pnl'] > 0:
                    score_perf[score]["wins"] += 1
                else:
                    score_perf[score]["losses"] += 1
        
        # Hitung win rate
        for score, data in score_perf.items():
            data["win_rate"] = (data["wins"] / data["count"] * 100) if data["count"] > 0 else 0
            data["avg_pnl"] = data["total_pnl"] / data["count"] if data["count"] > 0 else 0
        
        return dict(score_perf)

    def _get_performance_by_age(self) -> Dict:
        """Performa berdasarkan umur token"""
        # Simulasi data (akan diambil dari database jika ada)
        # Untuk sekarang, return empty
        return {"data": "Belum ada data umur token"}

    def _get_performance_by_liquidity(self) -> Dict:
        """Performa berdasarkan likuiditas"""
        return {"data": "Belum ada data likuiditas"}

    def _get_performance_by_hold_time(self) -> Dict:
        """Performa berdasarkan waktu hold"""
        return {"data": "Belum ada data hold time"}

    def _get_performance_by_exit_reason(self) -> Dict:
        """Performa berdasarkan alasan exit"""
        return {"data": "Belum ada data exit reason"}

    def _generate_recommendations(self, data: Dict) -> List[str]:
        """Generate rekomendasi berdasarkan analisis"""
        recommendations = []
        
        summary = data.get("summary", {})
        loss_dist = data.get("loss_distribution", {})
        score_perf = data.get("by_score", {})
        
        # 1. Cek win rate
        total = summary.get("total", 0)
        wins = summary.get("wins", 0)
        winrate = (wins / total * 100) if total > 0 else 0
        
        if winrate < 50:
            recommendations.append(f"⚠️ Win rate {winrate:.1f}% terlalu rendah (target >50%)")
        
        # 2. Cek loss distribution
        tiny_losses = loss_dist.get("tiny", {}).get("count", 0)
        if tiny_losses > 0:
            recommendations.append(f"⚠️ {tiny_losses} loss kecil (-0.003 SOL) → kemungkinan slippage/fee")
        
        # 3. Cek score performance
        if score_perf:
            best_score = max(score_perf.items(), key=lambda x: x[1].get("win_rate", 0))
            worst_score = min(score_perf.items(), key=lambda x: x[1].get("win_rate", 0))
            
            recommendations.append(f"💡 Score terbaik: {best_score[0]} (Win Rate: {best_score[1].get('win_rate', 0):.1f}%)")
            recommendations.append(f"💡 Score terburuk: {worst_score[0]} (Win Rate: {worst_score[1].get('win_rate', 0):.1f}%)")
            
            if worst_score[0] < 10:
                recommendations.append(f"🔧 Saran: Naikkan score threshold ke {worst_score[0] + 1}")
        
        return recommendations

    def print_report(self, data: Dict = None):
        """Print report ke console"""
        if data is None:
            data = self.analyze()
        
        print("\n" + "=" * 60)
        print("📊 TRADE ANALYTICS REPORT")
        print("=" * 60)
        
        summary = data.get("summary", {})
        print(f"\n📈 SUMMARY:")
        print(f"  Total Trades   : {summary.get('total', 0)}")
        print(f"  BUY            : {summary.get('buys', 0)}")
        print(f"  SELL           : {summary.get('sells', 0)}")
        print(f"  Total PnL      : {summary.get('total_pnl', 0):.4f} SOL")
        print(f"  Win Rate       : {summary.get('wins', 0) / summary.get('total', 1) * 100:.1f}%")
        print(f"  Wins           : {summary.get('wins', 0)}")
        print(f"  Losses         : {summary.get('losses', 0)}")
        
        # Loss distribution
        loss_dist = data.get("loss_distribution", {})
        print(f"\n🔴 LOSS DISTRIBUTION:")
        for category in ["tiny", "small", "medium", "large", "huge"]:
            data_cat = loss_dist.get(category, {})
            if data_cat.get("count", 0) > 0:
                avg = data_cat.get("total_pnl", 0) / data_cat.get("count", 1)
                print(f"  {category}: {data_cat.get('count', 0)} (avg: {avg:.4f} SOL)")
        
        # Score performance
        score_perf = data.get("by_score", {})
        if score_perf:
            print(f"\n📊 PERFORMANCE BY SCORE:")
            for score, perf in sorted(score_perf.items()):
                print(f"  Score {score}: {perf.get('count', 0)} trades, Win Rate: {perf.get('win_rate', 0):.1f}%")
        
        # Recommendations
        recs = data.get("recommendations", [])
        if recs:
            print(f"\n💡 REKOMENDASI:")
            for rec in recs:
                print(f"  {rec}")
        
        print("=" * 60)
