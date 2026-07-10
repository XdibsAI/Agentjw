"""
strategies/base.py
====================
Strategy = profil parameter (bukan kode terpisah). Tiap strategy override
sebagian weight scoring dan/atau threshold, lalu di-pass ke ScoringEngine
dan DecisionEngine. Ini yang membuat strategy "modular, bisa
diaktifkan/dimatikan" tanpa duplikasi logic.
"""
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class StrategyProfile:
    name: str
    enabled: bool = True
    weight_overrides: Dict[str, float] = field(default_factory=dict)
    buy_score_threshold: float = 75.0
    min_liquidity_usd: float = 3000.0
    description: str = ""
