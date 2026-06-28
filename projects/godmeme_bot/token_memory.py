"""
token_memory.py - Blacklist token yang sudah terbukti loss berulang.
Data persisted ke token_memory.json, di-update tiap kali posisi closed.
"""
import json
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

MEMORY_FILE = Path(__file__).parent / "token_memory.json"
LOSS_THRESHOLD_FOR_BLACKLIST = 2  # blacklist setelah loss >= N kali


def _load() -> Dict:
    if not MEMORY_FILE.exists():
        return {}
    try:
        return json.loads(MEMORY_FILE.read_text())
    except Exception as e:
        logger.warning(f"token_memory load failed: {e}")
        return {}


def _save(data: Dict) -> None:
    try:
        MEMORY_FILE.write_text(json.dumps(data, indent=2))
    except Exception as e:
        logger.error(f"token_memory save failed: {e}")


def is_blacklisted(symbol: str) -> bool:
    """Cek apakah token sudah di-blacklist karena loss berulang."""
    data = _load()
    entry = data.get(symbol)
    return bool(entry and entry.get("blocked"))


def record_trade_result(symbol: str, pnl_sol: float) -> None:
    """Dipanggil tiap kali posisi closed (di _close_position)."""
    data = _load()
    entry = data.get(symbol, {"trades": 0, "loss": 0, "win": 0, "blocked": False})

    entry["trades"] += 1
    if pnl_sol < 0:
        entry["loss"] += 1
    else:
        entry["win"] += 1

    if entry["loss"] >= LOSS_THRESHOLD_FOR_BLACKLIST:
        entry["blocked"] = True

    data[symbol] = entry
    _save(data)

    if entry["blocked"]:
        logger.info(f"Token {symbol} masuk blacklist (loss={entry['loss']}x)")


def get_blacklist_summary() -> Dict:
    """Untuk reporting/audit - lihat semua token yang di-block."""
    data = _load()
    return {sym: e for sym, e in data.items() if e.get("blocked")}


def seed_from_trading_db(db_path: str = None) -> int:
    """
    Inisialisasi blacklist dari data trading.db yang sudah ada,
    supaya token yang historically loss berulang langsung ke-block
    tanpa harus nunggu terjadi lagi.
    """
    import sqlite3

    db_path = db_path or str(Path(__file__).parent / "trading.db")
    db = Path(db_path)
    if not db.exists():
        logger.warning(f"trading.db tidak ditemukan di {db_path}")
        return 0

    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT token_symbol, realized_pnl
        FROM trades
        WHERE side='SELL' AND realized_pnl IS NOT NULL
    """).fetchall()
    conn.close()

    data = _load()
    for r in rows:
        symbol = r["token_symbol"] or "UNKNOWN"
        pnl = float(r["realized_pnl"] or 0)
        entry = data.get(symbol, {"trades": 0, "loss": 0, "win": 0, "blocked": False})
        entry["trades"] += 1
        if pnl < 0:
            entry["loss"] += 1
        else:
            entry["win"] += 1
        if entry["loss"] >= LOSS_THRESHOLD_FOR_BLACKLIST:
            entry["blocked"] = True
        data[symbol] = entry

    _save(data)
    blocked_count = sum(1 for e in data.values() if e.get("blocked"))
    logger.info(f"Seeded token_memory dari {len(rows)} historical trades, {blocked_count} token blacklisted")
    return blocked_count