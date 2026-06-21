import sqlite3
from collections import defaultdict
from pathlib import Path


def audit_godmeme():

    db = Path(
        "/home/dibs/agentjw/projects/godmeme_bot/trading.db"
    )

    if not db.exists():
        return {
            "error": f"Database tidak ditemukan: {db}"
        }


    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row


    trades = conn.execute("""
        SELECT
            token_symbol,
            realized_pnl
        FROM trades
        WHERE side='SELL'
        AND realized_pnl IS NOT NULL
    """).fetchall()


    total = len(trades)

    wins = []
    losses = []

    token_pnl = defaultdict(float)


    for t in trades:

        pnl = float(
            t["realized_pnl"] or 0
        )

        token = t["token_symbol"] or "UNKNOWN"

        token_pnl[token] += pnl


        if pnl > 0:
            wins.append(pnl)
        else:
            losses.append(pnl)



    return {

        "closed_trades": total,

        "wins": len(wins),

        "losses": len(losses),

        "winrate": round(
            (len(wins)/total)*100,2
        ) if total else 0,


        "total_realized_pnl":
            round(sum(token_pnl.values()),6),


        "average_win":
            round(sum(wins)/len(wins),6)
            if wins else 0,


        "average_loss":
            round(sum(losses)/len(losses),6)
            if losses else 0,


        "best_tokens":
            sorted(
                token_pnl.items(),
                key=lambda x:x[1],
                reverse=True
            )[:5],


        "worst_tokens":
            sorted(
                token_pnl.items(),
                key=lambda x:x[1]
            )[:5]

    }
