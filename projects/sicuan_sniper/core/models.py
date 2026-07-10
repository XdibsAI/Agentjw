"""
core/models.py
==============
Struktur data inti dipakai di seluruh modul. Semua dataclass, bukan dict
mentah, supaya field yang salah ketik ketahuan saat development bukan
saat runtime di production.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Action(str, Enum):
    BUY = "BUY"
    WATCH = "WATCH"
    SKIP = "SKIP"
    SELL = "SELL"
    EMERGENCY_EXIT = "EMERGENCY_EXIT"


class PositionStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


@dataclass
class Token:
    address: str
    symbol: str
    name: str
    source: str                       # "dexscreener" | "birdeye" | "pumpfun" | "raydium"
    pair_address: Optional[str] = None
    created_at: Optional[str] = None
    discovered_at: str = field(default_factory=now)
    raw: Dict[str, Any] = field(default_factory=dict)   # payload asli dari sumber


@dataclass
class AnalysisResult:
    token_address: str
    liquidity_usd: float = 0.0
    liquidity_locked: bool = False
    market_cap_usd: float = 0.0
    fdv_usd: float = 0.0
    holder_count: int = 0
    top_holder_percent: float = 0.0
    creator_wallet: Optional[str] = None
    creator_history_flags: List[str] = field(default_factory=list)
    mint_authority_revoked: bool = False
    freeze_authority_revoked: bool = False
    lp_burned: bool = False
    volume_5m_usd: float = 0.0
    volume_1h_usd: float = 0.0
    buy_sell_ratio_5m: float = 1.0
    age_minutes: float = 0.0
    smart_money_detected: bool = False
    whale_activity_detected: bool = False
    fresh_wallet_ratio: float = 0.0
    social_signals: Dict[str, bool] = field(default_factory=dict)  # {"twitter": True, ...}
    risk_flags: List[str] = field(default_factory=list)   # ["no_lp_lock", "mint_active", ...]
    analyzed_at: str = field(default_factory=now)


@dataclass
class ScoreBreakdown:
    liquidity_score: float = 0.0
    holder_score: float = 0.0
    volume_score: float = 0.0
    momentum_score: float = 0.0
    wallet_score: float = 0.0
    developer_score: float = 0.0
    risk_score: float = 0.0            # makin tinggi = makin berisiko (dikurangi dari total)
    social_score: float = 0.0
    total_score: float = 0.0


@dataclass
class Signal:
    token_address: str
    action: Action
    reason: str
    score: float = 0.0
    strategy: str = "default"
    suggested_size_usd: float = 0.0
    created_at: str = field(default_factory=now)


@dataclass
class Trade:
    id: Optional[int]
    token_address: str
    side: str                  # "BUY" | "SELL"
    price_usd: float
    amount_token: float
    amount_usd: float
    fee_usd: float
    tx_signature: Optional[str]
    is_paper: bool
    strategy: str
    executed_at: str = field(default_factory=now)


@dataclass
class Position:
    id: Optional[int]
    token_address: str
    symbol: str
    status: PositionStatus
    entry_price_usd: float
    entry_amount_token: float
    entry_amount_usd: float
    remaining_amount_token: float
    realized_pnl_usd: float = 0.0
    unrealized_pnl_usd: float = 0.0
    highest_price_seen: float = 0.0
    strategy: str = "default"
    opened_at: str = field(default_factory=now)
    closed_at: Optional[str] = None
    exit_reason: Optional[str] = None
