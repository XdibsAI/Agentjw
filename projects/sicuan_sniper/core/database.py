"""
core/database.py
=================
Storage abstraction — SQLite untuk development. Semua akses lewat class ini,
jadi kalau nanti pindah ke Postgres, cukup ganti implementasi di sini,
modul lain (position manager, reporting, dst) tidak perlu berubah.
"""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from config import settings
from core.models import Position, PositionStatus, Trade


SCHEMA = """
CREATE TABLE IF NOT EXISTS tokens (
    address TEXT PRIMARY KEY,
    symbol TEXT,
    name TEXT,
    source TEXT,
    pair_address TEXT,
    discovered_at TEXT,
    raw_json TEXT
);

CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_address TEXT,
    payload_json TEXT,
    analyzed_at TEXT
);

CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_address TEXT,
    total_score REAL,
    breakdown_json TEXT,
    scored_at TEXT
);

CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_address TEXT,
    action TEXT,
    reason TEXT,
    score REAL,
    strategy TEXT,
    suggested_size_usd REAL,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_address TEXT,
    side TEXT,
    price_usd REAL,
    amount_token REAL,
    amount_usd REAL,
    fee_usd REAL,
    tx_signature TEXT,
    is_paper INTEGER,
    strategy TEXT,
    executed_at TEXT
);

CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_address TEXT,
    symbol TEXT,
    status TEXT,
    entry_price_usd REAL,
    entry_amount_token REAL,
    entry_amount_usd REAL,
    remaining_amount_token REAL,
    realized_pnl_usd REAL DEFAULT 0,
    unrealized_pnl_usd REAL DEFAULT 0,
    highest_price_seen REAL DEFAULT 0,
    strategy TEXT,
    opened_at TEXT,
    closed_at TEXT,
    exit_reason TEXT
);

CREATE TABLE IF NOT EXISTS learning_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_address TEXT,
    strategy TEXT,
    outcome TEXT,          -- "WIN" | "LOSS" | "BREAKEVEN"
    pnl_usd REAL,
    hold_minutes REAL,
    score_at_entry REAL,
    notes TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS daily_stats (
    date TEXT PRIMARY KEY,
    realized_pnl_usd REAL DEFAULT 0,
    trade_count INTEGER DEFAULT 0,
    win_count INTEGER DEFAULT 0,
    loss_count INTEGER DEFAULT 0,
    consecutive_losses INTEGER DEFAULT 0,
    circuit_breaker_tripped INTEGER DEFAULT 0
);
"""


class Database:
    def __init__(self, path: Optional[Path] = None):
        self.path = path or settings.database_full_path
        with self._conn() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # ── tokens ──────────────────────────────────────────────────────
    def upsert_token(self, token) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO tokens (address, symbol, name, source, pair_address, discovered_at, raw_json)
                   VALUES (?,?,?,?,?,?,?)
                   ON CONFLICT(address) DO UPDATE SET symbol=excluded.symbol""",
                (token.address, token.symbol, token.name, token.source,
                 token.pair_address, token.discovered_at, json.dumps(token.raw)),
            )

    def token_exists(self, address: str) -> bool:
        with self._conn() as conn:
            row = conn.execute("SELECT 1 FROM tokens WHERE address=?", (address,)).fetchone()
            return row is not None

    # ── trades ──────────────────────────────────────────────────────
    def insert_trade(self, trade: Trade) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO trades
                   (token_address, side, price_usd, amount_token, amount_usd,
                    fee_usd, tx_signature, is_paper, strategy, executed_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (trade.token_address, trade.side, trade.price_usd, trade.amount_token,
                 trade.amount_usd, trade.fee_usd, trade.tx_signature,
                 int(trade.is_paper), trade.strategy, trade.executed_at),
            )
            return cur.lastrowid

    def all_trades(self) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM trades ORDER BY executed_at").fetchall()
            return [dict(r) for r in rows]

    # ── positions ───────────────────────────────────────────────────
    def insert_position(self, pos: Position) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO positions
                   (token_address, symbol, status, entry_price_usd, entry_amount_token,
                    entry_amount_usd, remaining_amount_token, realized_pnl_usd,
                    unrealized_pnl_usd, highest_price_seen, strategy, opened_at, closed_at, exit_reason)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (pos.token_address, pos.symbol, pos.status.value, pos.entry_price_usd,
                 pos.entry_amount_token, pos.entry_amount_usd, pos.remaining_amount_token,
                 pos.realized_pnl_usd, pos.unrealized_pnl_usd, pos.highest_price_seen,
                 pos.strategy, pos.opened_at, pos.closed_at, pos.exit_reason),
            )
            return cur.lastrowid

    def update_position(self, pos: Position) -> None:
        with self._conn() as conn:
            conn.execute(
                """UPDATE positions SET status=?, remaining_amount_token=?, realized_pnl_usd=?,
                   unrealized_pnl_usd=?, highest_price_seen=?, closed_at=?, exit_reason=?
                   WHERE id=?""",
                (pos.status.value, pos.remaining_amount_token, pos.realized_pnl_usd,
                 pos.unrealized_pnl_usd, pos.highest_price_seen, pos.closed_at,
                 pos.exit_reason, pos.id),
            )

    def open_positions(self) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM positions WHERE status='OPEN' ORDER BY opened_at"
            ).fetchall()
            return [dict(r) for r in rows]

    def closed_positions(self) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM positions WHERE status='CLOSED' ORDER BY closed_at"
            ).fetchall()
            return [dict(r) for r in rows]

    # ── learning ────────────────────────────────────────────────────
    def insert_learning_record(self, **kwargs) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO learning_records
                   (token_address, strategy, outcome, pnl_usd, hold_minutes,
                    score_at_entry, notes, created_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (kwargs.get("token_address"), kwargs.get("strategy"), kwargs.get("outcome"),
                 kwargs.get("pnl_usd"), kwargs.get("hold_minutes"), kwargs.get("score_at_entry"),
                 kwargs.get("notes", ""), kwargs.get("created_at")),
            )

    def learning_records(self) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM learning_records").fetchall()
            return [dict(r) for r in rows]

    # ── daily stats / risk state ───────────────────────────────────
    def get_daily_stats(self, date: str) -> Dict[str, Any]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM daily_stats WHERE date=?", (date,)).fetchone()
            if row:
                return dict(row)
            conn.execute("INSERT INTO daily_stats (date) VALUES (?)", (date,))
            return {
                "date": date, "realized_pnl_usd": 0, "trade_count": 0,
                "win_count": 0, "loss_count": 0, "consecutive_losses": 0,
                "circuit_breaker_tripped": 0,
            }

    def update_daily_stats(self, date: str, **fields) -> None:
        if not fields:
            return
        set_clause = ", ".join(f"{k}=?" for k in fields)
        with self._conn() as conn:
            conn.execute(f"UPDATE daily_stats SET {set_clause} WHERE date=?",
                         (*fields.values(), date))


db = Database()
