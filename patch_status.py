from pathlib import Path

p = Path("sicuan/brain.py")
s = p.read_text()

anchor = '            elif action == "show_log":'

if 'elif action == "godmeme_status"' in s:
    print("STATUS ALREADY EXISTS")
    exit()

if anchor not in s:
    print("ANCHOR NOT FOUND")
    exit()

block = r'''            elif action == "godmeme_status":
                import json
                import sqlite3
                from pathlib import Path as _Path

                bot_dir = _Path("/home/dibs/agentjw/projects/godmeme_bot")

                status = {}
                sf = bot_dir / "godmeme_status.json"

                if sf.exists():
                    try:
                        status = json.loads(sf.read_text())
                    except Exception:
                        pass

                total = 0
                buys = 0
                sells = 0
                pnl = 0.0
                recent = []

                db = bot_dir / "trading.db"

                if db.exists():
                    try:
                        conn = sqlite3.connect(db)
                        cur = conn.cursor()

                        cur.execute("""
                            SELECT token_symbol, side, realized_pnl
                            FROM trades
                            ORDER BY id DESC
                            LIMIT 10
                        """)

                        for symbol, side, rpnl in cur.fetchall():
                            total += 1

                            if side == "BUY":
                                buys += 1
                            elif side == "SELL":
                                sells += 1

                            if rpnl:
                                pnl += float(rpnl)

                            recent.append(
                                f"{side} {symbol}" +
                                (f" {float(rpnl):+.4f} SOL" if rpnl else "")
                            )

                        conn.close()

                    except Exception:
                        pass

                return (
                    "🤖 GODMEME STATUS\n"
                    f"Status: {status.get('status','unknown')}\n"
                    f"Mode: {status.get('mode','unknown')}\n"
                    f"PID: {status.get('pid','-')}\n"
                    f"Balance: {status.get('balance','-')} SOL\n"
                    f"Daily PnL: {status.get('daily_pnl', pnl):+.4f} SOL\n"
                    f"Trades DB: {total} (BUY {buys} / SELL {sells})\n"
                    f"Last event: {status.get('last_event','-')}\n\n"
                    "Recent:\n- " + "\n- ".join(recent[:5])
                )

'''

s = s.replace(anchor, block + anchor, 1)

p.write_text(s)
print("STATUS PATCH DONE")
