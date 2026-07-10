"""
decision/decision_engine.py
=============================
Mengubah (token, analysis, score) jadi Signal dengan action yang jelas
DAN alasan yang bisa dijelaskan manusia — bukan cuma angka. Ini penting
supaya kalau ada trade buruk, kamu bisa telusuri kenapa sistem memutuskan
begitu (dipakai juga oleh LearningEngine).
"""
from typing import List

from config import settings
from core.models import Action, AnalysisResult, ScoreBreakdown, Signal, Token

# Flag yang membuat token otomatis SKIP tidak peduli skornya setinggi apa —
# ini adalah hard filter, bukan sekadar pengurang skor.
HARD_SKIP_FLAGS = {"mint_authority_active", "freeze_authority_active"}


class DecisionEngine:
    def __init__(self, strategy_name: str = "default"):
        self.strategy_name = strategy_name

    def decide(
        self,
        token: Token,
        analysis: AnalysisResult,
        score: ScoreBreakdown,
        open_position_count: int,
    ) -> Signal:
        hard_skip = HARD_SKIP_FLAGS.intersection(analysis.risk_flags)
        if hard_skip:
            return Signal(
                token_address=token.address,
                action=Action.SKIP,
                reason=f"Hard filter gagal: {', '.join(sorted(hard_skip))}",
                score=score.total_score,
                strategy=self.strategy_name,
            )

        if analysis.liquidity_usd < settings.min_liquidity_usd:
            return Signal(
                token_address=token.address,
                action=Action.SKIP,
                reason=f"Liquidity ${analysis.liquidity_usd:,.0f} < minimum "
                       f"${settings.min_liquidity_usd:,.0f}",
                score=score.total_score,
                strategy=self.strategy_name,
            )

        if open_position_count >= settings.max_concurrent_positions:
            return Signal(
                token_address=token.address,
                action=Action.WATCH,
                reason=f"Slot posisi penuh ({open_position_count}/"
                       f"{settings.max_concurrent_positions}), token masuk watchlist",
                score=score.total_score,
                strategy=self.strategy_name,
            )

        if score.total_score >= settings.buy_score_threshold:
            size = self._position_size(score.total_score)
            return Signal(
                token_address=token.address,
                action=Action.BUY,
                reason=(
                    f"Score {score.total_score:.1f} >= threshold "
                    f"{settings.buy_score_threshold}. "
                    f"Liquidity=${analysis.liquidity_usd:,.0f}, "
                    f"vol5m=${analysis.volume_5m_usd:,.0f}, "
                    f"buy/sell={analysis.buy_sell_ratio_5m:.2f}"
                ),
                score=score.total_score,
                strategy=self.strategy_name,
                suggested_size_usd=size,
            )

        if score.total_score >= settings.watch_score_threshold:
            return Signal(
                token_address=token.address,
                action=Action.WATCH,
                reason=f"Score {score.total_score:.1f} di zona watch "
                       f"({settings.watch_score_threshold}-{settings.buy_score_threshold})",
                score=score.total_score,
                strategy=self.strategy_name,
            )

        return Signal(
            token_address=token.address,
            action=Action.SKIP,
            reason=f"Score {score.total_score:.1f} di bawah threshold watch "
                   f"({settings.watch_score_threshold})",
            score=score.total_score,
            strategy=self.strategy_name,
        )

    def _position_size(self, score: float) -> float:
        """Semakin tinggi skor, semakin besar porsi max_position_size_usd
        yang dipakai — tapi tidak pernah melebihi batas dari RiskManager."""
        max_size = settings.max_position_size_usd
        if score >= 90:
            return max_size
        if score >= 80:
            return max_size * 0.7
        return max_size * 0.5

    def decide_exit(
        self,
        current_price: float,
        entry_price: float,
        highest_price_seen: float,
        age_minutes: float,
    ) -> Signal | None:
        """Dipanggil oleh PositionManager tiap tick untuk cek exit signal
        selain TP/trailing/hard-stop biasa (mis. emergency exit kalau
        harga crash sangat cepat)."""
        if entry_price <= 0:
            return None
        drop_from_entry = (current_price - entry_price) / entry_price * 100
        drop_from_high = (
            (current_price - highest_price_seen) / highest_price_seen * 100
            if highest_price_seen > 0 else 0
        )

        if drop_from_entry <= -60:
            return Signal(
                token_address="",
                action=Action.EMERGENCY_EXIT,
                reason=f"Crash {drop_from_entry:.1f}% dari entry — kemungkinan rug pull",
                strategy=self.strategy_name,
            )
        return None
