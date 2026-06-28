import sqlite3
import json
import os
import time
from pathlib import Path


BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "trading.db"
STATUS_PATH = BASE_DIR / "godmeme_status.json"


def check_pid(pid):
    if not pid:
        return False

    try:
        os.kill(int(pid), 0)
        return True
    except Exception:
        return False


def load_status_file():
    if not STATUS_PATH.exists():
        return {}

    try:
        return json.loads(STATUS_PATH.read_text())
    except Exception:
        return {}


def read_trades():
    """
    PENTING: total/buy/sell/realized_pnl WAJIB dihitung dari SELURUH
    histori trades (agregat SQL), TIDAK BOLEH dari subset yang dibatasi
    LIMIT — itu bug lama yang membuat status selalu lapor "20 trades"
    walau total sebenarnya ratusan. "recent" (daftar 20 transaksi
    terakhir untuk ditampilkan) tetap dibatasi, tapi terpisah dari
    angka agregat.
    """
    result = {
        "total": 0,
        "buy": 0,
        "sell": 0,
        "realized_pnl": 0.0,
        "recent": []
    }

    if not DB_PATH.exists():
        return result

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Agregat dari SELURUH tabel — sumber kebenaran untuk total/buy/sell/pnl
        cur.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN side = 'BUY' THEN 1 ELSE 0 END) AS buy_count,
                SUM(CASE WHEN side = 'SELL' THEN 1 ELSE 0 END) AS sell_count,
                COALESCE(SUM(CASE WHEN realized_pnl IS NOT NULL THEN CAST(realized_pnl AS REAL) ELSE 0 END), 0) AS total_pnl
            FROM trades
        """)
        agg = cur.fetchone()
        result["total"] = agg[0] or 0
        result["buy"] = agg[1] or 0
        result["sell"] = agg[2] or 0
        result["realized_pnl"] = agg[3] or 0.0

        # Daftar 20 transaksi TERBARU — cuma untuk ditampilkan sebagai preview,
        # bukan dasar hitung agregat di atas.
        cur.execute("""
            SELECT
                id,
                token_symbol,
                side,
                amount,
                price,
                realized_pnl
            FROM trades
            ORDER BY id DESC
            LIMIT 20
        """)

        for row in cur.fetchall():
            tid, symbol, side, amount, price, pnl = row
            result["recent"].append({
                "id": tid,
                "symbol": symbol,
                "side": side,
                "amount": amount,
                "price": price,
                "pnl": pnl
            })

        conn.close()

    except Exception as e:
        result["error"] = str(e)

    return result


def read_positions():
    positions = []

    if not DB_PATH.exists():
        return positions

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("""
            SELECT
                token_symbol,
                amount,
                entry_price,
                stop_loss,
                take_profit,
                status
            FROM positions
            WHERE status != 'closed'
            ORDER BY id DESC
        """)

        for row in cur.fetchall():
            symbol, amount, entry, sl, tp, status = row

            positions.append({
                "symbol": symbol,
                "amount": amount,
                "entry": entry,
                "stop_loss": sl,
                "take_profit": tp,
                "status": status
            })

        conn.close()

    except Exception:
        pass

    return positions


def get_godmeme_status():

    file_status = load_status_file()

    pid = file_status.get("pid")

    trades = read_trades()

    positions = read_positions()


    return {
        "process": {
            "pid": pid,
            "alive": check_pid(pid)
        },

        "mode": file_status.get("mode"),

        "balance": file_status.get("balance"),

        "database": {
            "trades": trades["total"],
            "buy": trades["buy"],
            "sell": trades["sell"],
            "realized_pnl": round(
                trades["realized_pnl"],
                6
            )
        },

        # total_positions = jumlah SEBENARNYA posisi terbuka (sebelum
        # dipotong di pemanggil). Pemanggil (brain.py) boleh tampilkan
        # cuma sebagian untuk ringkas, TAPI harus tahu dan bilang ke user
        # kalau ada sisanya — jangan diam-diam memotong tanpa keterangan.
        "total_open_positions": len(positions),
        "positions": positions,

        "last_event": file_status.get(
            "last_event",
            "-"
        ),

        "source": "trading.db"

    }


if __name__ == "__main__":
    print(
        json.dumps(
            get_godmeme_status(),
            indent=2
        )
    )