"""
analyzer/scoring_engine.py
=============================
Weighted scoring dari AnalysisResult -> ScoreBreakdown. Bobot bisa
disesuaikan oleh LearningEngine berdasarkan histori trade (lihat
learning/learning_engine.py) — engine ini menerima weights dari luar,
tidak hardcode, supaya bisa "belajar".
"""
from dataclasses import asdict
from typing import Dict

from core.models import AnalysisResult, ScoreBreakdown

DEFAULT_WEIGHTS: Dict[str, float] = {
    "liquidity": 0.20,
    "holder": 0.15,
    "volume": 0.15,
    "momentum": 0.15,
    "wallet": 0.10,
    "developer": 0.10,
    "social": 0.05,
    # risk_score dikurangi dari total, bukan dijumlah — bobotnya di bawah
    "risk_penalty": 0.10,
}


class ScoringEngine:
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or dict(DEFAULT_WEIGHTS)

    def score(self, analysis: AnalysisResult) -> ScoreBreakdown:
        b = ScoreBreakdown()

        b.liquidity_score = self._liquidity_score(analysis)
        b.holder_score = self._holder_score(analysis)
        b.volume_score = self._volume_score(analysis)
        b.momentum_score = self._momentum_score(analysis)
        b.wallet_score = self._wallet_score(analysis)
        b.developer_score = self._developer_score(analysis)
        b.social_score = self._social_score(analysis)
        b.risk_score = self._risk_penalty(analysis)

        w = self.weights
        positive = (
            b.liquidity_score * w["liquidity"]
            + b.holder_score * w["holder"]
            + b.volume_score * w["volume"]
            + b.momentum_score * w["momentum"]
            + b.wallet_score * w["wallet"]
            + b.developer_score * w["developer"]
            + b.social_score * w["social"]
        )
        penalty = b.risk_score * w["risk_penalty"]
        b.total_score = max(0.0, min(100.0, positive - penalty))
        return b

    # ── sub-scores, semua 0-100 ────────────────────────────────────

    def _liquidity_score(self, a: AnalysisResult) -> float:
        if a.liquidity_usd <= 0:
            return 0.0
        # skala log-ish sederhana: 3k=50, 10k=75, 30k+=100
        if a.liquidity_usd >= 30000:
            return 100.0
        if a.liquidity_usd >= 10000:
            return 75.0
        if a.liquidity_usd >= 3000:
            return 50.0
        return 20.0

    def _holder_score(self, a: AnalysisResult) -> float:
        score = 0.0
        if a.holder_count >= 200:
            score = 100.0
        elif a.holder_count >= 100:
            score = 80.0
        elif a.holder_count >= 30:
            score = 50.0
        else:
            score = 15.0
        if a.top_holder_percent > 0:
            if a.top_holder_percent > 50:
                score *= 0.2
            elif a.top_holder_percent > 25:
                score *= 0.6
        return score

    def _volume_score(self, a: AnalysisResult) -> float:
        if a.volume_5m_usd >= 5000:
            return 100.0
        if a.volume_5m_usd >= 1000:
            return 70.0
        if a.volume_5m_usd >= 500:
            return 45.0
        return 10.0

    def _momentum_score(self, a: AnalysisResult) -> float:
        ratio = a.buy_sell_ratio_5m
        if ratio >= 3:
            return 100.0
        if ratio >= 2:
            return 80.0
        if ratio >= 1.2:
            return 55.0
        if ratio >= 0.8:
            return 30.0
        return 5.0  # sell pressure dominan — sinyal buruk

    def _wallet_score(self, a: AnalysisResult) -> float:
        score = 60.0  # netral karena kita tidak punya wallet-labeling akurat
        if a.smart_money_detected:
            score += 25
        if a.whale_activity_detected:
            score += 10
        if a.fresh_wallet_ratio > 0.7:
            score -= 30  # mayoritas wallet baru = indikasi bot/sybil
        return max(0.0, min(100.0, score))

    def _developer_score(self, a: AnalysisResult) -> float:
        score = 70.0
        if not a.mint_authority_revoked:
            score -= 40
        if not a.freeze_authority_revoked:
            score -= 30
        if a.lp_burned or a.liquidity_locked:
            score += 20
        if a.creator_history_flags:
            score -= 15 * len(a.creator_history_flags)
        return max(0.0, min(100.0, score))

    def _social_score(self, a: AnalysisResult) -> float:
        present = sum(1 for v in a.social_signals.values() if v)
        total = max(1, len(a.social_signals))
        return 100.0 * present / total

    def _risk_penalty(self, a: AnalysisResult) -> float:
        # skala 0-100, makin banyak & makin parah flag makin tinggi penaltinya
        severe_flags = {"mint_authority_active", "freeze_authority_active", "extremely_new_high_risk"}
        penalty = 0.0
        for flag in a.risk_flags:
            penalty += 30.0 if flag in severe_flags else 10.0
        return min(100.0, penalty)
