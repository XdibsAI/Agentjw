from pathlib import Path

p = Path("sicuan/brain.py")
src = p.read_text()

old = '''  "action": "null | build_project | repair_project | run_bot | scan_project | show_log | request_api_key | modify_project | video_info | get_file | move_to_gallery | list_media",'''

new = '''  "action": "null | build_project | repair_project | run_bot | scan_project | godmeme_status | show_log | request_api_key | modify_project | video_info | get_file | move_to_gallery | list_media",'''

if old not in src:
    raise SystemExit("ACTION ENUM NOT FOUND")

src = src.replace(old,new,1)

old_rule = '''Kalau user minta "buka/download file", action = "get_file"'''

new_rule = '''Kalau user minta "status godmeme", "cuan godmeme", "ringkasan trading", "profit bot", atau kondisi bot, action = "godmeme_status"

Kalau user minta "buka/download file", action = "get_file"'''

if old_rule not in src:
    raise SystemExit("RULE NOT FOUND")

src = src.replace(old_rule,new_rule,1)

anchor = '''              elif action == "show_log":'''

handler = '''
              elif action == "godmeme_status":
                  import json
                  import sqlite3
                  from pathlib import Path as _Path

                  bot_dir = _Path("/home/dibs/agentjw/projects/godmeme_bot")

                  status_file = bot_dir / "godmeme_status.json"
                  db_file = bot_dir / "trading.db"

                  status = {}
                  if status_file.exists():
                      try:
                          status = json.loads(status_file.read_text())
                      except Exception:
                          status = {}

                  buys = sells = 0
                  pnl = 0.0
                  recent = []

                  if db_file.exists():
                      try:
                          conn = sqlite3.connect(db_file)
                          cur = conn.cursor()

                          cur.execute("""
                              SELECT side, token_symbol, realized_pnl
                              FROM trades
                              ORDER BY id DESC
                              LIMIT 10
                          """)

                          rows = cur.fetchall()

                          for side, symbol, rpnl in rows:
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
                      "🤖 GODMEME STATUS\\n"
                      f"Status: {status.get('status','unknown')}\\n"
                      f"Mode: {status.get('mode','unknown')}\\n"
                      f"PID: {status.get('pid','-')}\\n"
                      f"Balance: {status.get('balance','-')} SOL\\n"
                      f"Daily PnL: {status.get('daily_pnl',pnl):+.4f} SOL\\n"
                      f"Trades: {status.get('trades_today', buys+sells)}\\n"
                      f"Last event: {status.get('last_event','-')}\\n\\n"
                      "Recent:\\n- " + "\\n- ".join(recent[:5])
                  )

'''

if anchor not in src:
    raise SystemExit("SHOW_LOG ANCHOR NOT FOUND")

src = src.replace(anchor, handler + anchor,1)

p.write_text(src)
print("PATCH GODMEME STATUS DONE")
