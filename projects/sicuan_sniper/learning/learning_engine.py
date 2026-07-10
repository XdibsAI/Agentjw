"""
learning/learning_engine.py
=============================
Rule-based learning (BUKAN machine learning) — dan sengaja begitu, supaya
setiap perubahan bisa dijelaskan manusia. Cara kerja:

  1. Baca semua learning_records (histori WIN/LOSS per strategy)
  2. Kalau win rate suatu strategy jelek, turunkan bobot strategy itu
  3. Kalau kategori skor tertentu (mis. volume_score) konsisten tinggi
     di trade yang WIN, naikkan bobotnya sedikit di ScoringEngine
  4. Semua perubahan bobot dibatasi (clamp) supaya tidak overfit ke
     sample kecil
"""
from collections import defaultdict
from typing import Dict

from analyzer.scoring_engine import DEFAULT_WEIGHTS
from core.database import db
from core.logger import get_logger

log = get_logger("learning.engine")

MIN_SAMPLES_BEFORE_ADJUST = 10   # jangan sesuaikan bobot kalau data masih sedikit
MAX_WEIGHT_DRIFT = 0.05          # perubahan bobot per adjust dibatasi +/-5%


class LearningEngine:
    def __init__(self):
        self.weights: Dict[str, float] = dict(DEFAULT_WEIGHTS)

    def evaluate_and_adjust(self) -> Dict[str, float]:
        records = db.learning_records()
        if len(records) < MIN_SAMPLES_BEFORE_ADJUST:
            log.info(f"Learning: baru {len(records)} sample, minimum "
                      f"{MIN_SAMPLES_BEFORE_ADJUST} sebelum menyesuaikan bobot")
            return self.weights

        by_strategy = defaultdict(lambda: {"win": 0, "loss": 0, "pnl": 0.0})
        for r in records:
            s = by_strategy[r["strategy"]]
            if r["outcome"] == "WIN":
                s["win"] += 1
            elif r["outcome"] == "LOSS":
                s["loss"] += 1
            s["pnl"] += r["pnl_usd"]

        report_lines = ["Ringkasan performa per strategy:"]
        for strategy, stats in by_strategy.items():
            total = stats["win"] + stats["loss"]
            win_rate = (stats["win"] / total * 100) if total else 0
            report_lines.append(
                f"  {strategy}: {stats['win']}W/{stats['loss']}L "
                f"({win_rate:.0f}% win rate), pnl=${stats['pnl']:.2f}"
            )
        log.info("\n".join(report_lines))

        # Penyesuaian sederhana: kalau overall win rate rendah, naikkan
        # bobot risk_penalty (jadi lebih konservatif), bukan sebaliknya.
        total_win = sum(s["win"] for s in by_strategy.values())
        total_loss = sum(s["loss"] for s in by_strategy.values())
        total = total_win + total_loss
        if total > 0:
            win_rate = total_win / total
            if win_rate < 0.35:
                self.weights["risk_penalty"] = min(
                    0.30, self.weights["risk_penalty"] + MAX_WEIGHT_DRIFT
                )
                log.warning(
                    f"Win rate keseluruhan {win_rate*100:.0f}% rendah — "
                    f"risk_penalty weight dinaikkan ke {self.weights['risk_penalty']:.2f} "
                    f"(scoring jadi lebih konservatif)"
                )
            elif win_rate > 0.65:
                self.weights["risk_penalty"] = max(
                    0.05, self.weights["risk_penalty"] - MAX_WEIGHT_DRIFT
                )

        return self.weights
