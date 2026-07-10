"""
strategies/profiles.py
========================
Kumpulan strategy siap pakai. Tiap strategy adalah kombinasi bobot +
threshold yang berbeda, sesuai gaya dari spesifikasi (Ultra Early,
Momentum, Volume Spike, dst). Semua modular — tinggal di-enable/disable.
"""
from strategies.base import StrategyProfile

ULTRA_EARLY = StrategyProfile(
    name="ultra_early",
    weight_overrides={"liquidity": 0.15, "developer": 0.20, "risk_penalty": 0.20},
    buy_score_threshold=80.0,   # lebih ketat karena token sangat baru = risiko tinggi
    min_liquidity_usd=3000.0,
    description="Masuk sangat awal (<10 menit), bobot developer/risk dinaikkan "
                 "karena data historis token masih minim.",
)

MOMENTUM = StrategyProfile(
    name="momentum",
    weight_overrides={"momentum": 0.25, "volume": 0.20},
    buy_score_threshold=72.0,
    min_liquidity_usd=5000.0,
    description="Fokus buy/sell ratio dan volume spike, dipakai untuk token "
                 "yang sudah punya beberapa menit trading history.",
)

VOLUME_SPIKE = StrategyProfile(
    name="volume_spike",
    weight_overrides={"volume": 0.30, "momentum": 0.20},
    buy_score_threshold=70.0,
    min_liquidity_usd=5000.0,
    description="Trigger dari lonjakan volume tiba-tiba dibanding baseline.",
)

CONSERVATIVE = StrategyProfile(
    name="conservative",
    weight_overrides={"risk_penalty": 0.25, "developer": 0.20},
    buy_score_threshold=85.0,
    min_liquidity_usd=10000.0,
    description="Threshold paling ketat, dipakai kalau mau turunkan frekuensi "
                 "trading tapi naikkan kualitas per trade.",
)

ALL_PROFILES = {
    p.name: p for p in [ULTRA_EARLY, MOMENTUM, VOLUME_SPIKE, CONSERVATIVE]
}
