"""
sicuan/actions/analyze_trading_data.py
========================================
Analisis data trading langsung dari trading.db
"""
import sqlite3
from pathlib import Path


def _to_float(value, default=0.0):
    """Safe convert to float"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def execute(brain=None, **kwargs) -> str:
    db_path = Path("/home/dibs/agentjw/projects/godmeme_bot/trading.db")
    if not db_path.exists():
        return "❌ trading.db tidak ditemukan"

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        # Total summary
        summary = conn.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END) as buys,
                   SUM(CASE WHEN side='SELL' THEN 1 ELSE 0 END) as sells,
                   SUM(realized_pnl) as total_pnl,
                   AVG(realized_pnl) as avg_pnl,
                   SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
                   SUM(CASE WHEN realized_pnl < 0 THEN 1 ELSE 0 END) as losses
            FROM trades WHERE realized_pnl IS NOT NULL
        """).fetchone()

        total = summary['total'] or 0
        wins = summary['wins'] or 0
        losses = summary['losses'] or 0
        total_pnl = _to_float(summary['total_pnl'])
        avg_pnl = _to_float(summary['avg_pnl'])
        winrate = (wins / total * 100) if total > 0 else 0

        # Top 3 biggest losses
        worst = conn.execute("""
            SELECT token_symbol, realized_pnl, created_at, strategy
            FROM trades
            WHERE realized_pnl < 0
            ORDER BY realized_pnl ASC LIMIT 3
        """).fetchall()

        # Top 3 biggest wins
        best = conn.execute("""
            SELECT token_symbol, realized_pnl, created_at, strategy
            FROM trades
            WHERE realized_pnl > 0
            ORDER BY realized_pnl DESC LIMIT 3
        """).fetchall()

        # Recent 3 trades
        recent = conn.execute("""
            SELECT token_symbol, side, realized_pnl, created_at
            FROM trades
            ORDER BY created_at DESC LIMIT 3
        """).fetchall()

        conn.close()

        # Build output
        lines = []
        lines.append("📊 ANALISIS TRADING GODMEME")
        lines.append("=" * 40)
        lines.append("")
        lines.append(f"📈 Total Trades    : {total}")
        lines.append(f"   BUY              : {summary['buys']}")
        lines.append(f"   SELL             : {summary['sells']}")
        lines.append(f"   Total PnL        : {total_pnl:.4f} SOL")
        lines.append(f"   Avg PnL          : {avg_pnl:.4f} SOL")
        lines.append(f"   Win Rate         : {winrate:.1f}%")
        lines.append(f"   Winning Trades   : {wins}")
        lines.append(f"   Losing Trades    : {losses}")
        lines.append("")

        if worst:
            lines.append("🔴 TOP 3 LOSSES:")
            for i, row in enumerate(worst, 1):
                pnl = _to_float(row['realized_pnl'])
                lines.append(f"  {i}. {row['token_symbol']}: {pnl:.4f} SOL ({row['strategy']})")
            lines.append("")

        if best:
            lines.append("🟢 TOP 3 WINS:")
            for i, row in enumerate(best, 1):
                pnl = _to_float(row['realized_pnl'])
                lines.append(f"  {i}. {row['token_symbol']}: {pnl:.4f} SOL ({row['strategy']})")
            lines.append("")

        if recent:
            lines.append("📋 RECENT 3 TRADES:")
            for row in recent:
                pnl = _to_float(row['realized_pnl'])
                side_icon = "🟢" if row['side'] == "BUY" else "🔴"
                lines.append(f"  {side_icon} {row['token_symbol']} ({row['side']}) PnL: {pnl:.4f} SOL")
            lines.append("")

        # Rekomendasi
        lines.append("💡 REKOMENDASI:")
        if total_pnl < 0:
            lines.append("  ⚠️ Total PnL negatif. Perbaiki strategi!")
            if winrate < 50:
                lines.append(f"     - Win rate {winrate:.1f}% terlalu rendah (target >50%)")
            if worst:
                pnl = _to_float(worst[0]['realized_pnl'])
                lines.append(f"     - Loss terbesar: {worst[0]['token_symbol']} ({pnl:.4f} SOL)")
        else:
            lines.append("  ✅ Total PnL positif. Pertahankan strategi!")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Error analisis: {e}"
