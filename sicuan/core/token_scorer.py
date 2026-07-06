"""
Token Scorer - Multi-feature scoring system
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class TokenFeatures:
    """Feature token untuk scoring"""
    liquidity: float = 0
    volume: float = 0
    momentum: float = 0  # price change %
    age_min: float = 0
    entry_hour: int = 0
    historical_win_rate: float = 50  # default 50%


class TokenScorer:
    """Multi-feature scoring untuk token"""

    def __init__(self):
        self.weights = {
            "liquidity": 0.20,
            "volume": 0.20,
            "momentum": 0.20,
            "age": 0.15,
            "entry_hour": 0.10,
            "historical_wr": 0.15,
        }
        self.min_samples = 30  # minimum samples untuk percaya
        self.min_hour_samples = 10

    def score(self, features: TokenFeatures, hour_data: Dict = None) -> Dict:
        """Hitung score token dengan multi-feature"""
        
        scores = {}
        
        # 1. Liquidity Score (0-100)
        if features.liquidity >= 50000:
            scores["liquidity"] = 100
        elif features.liquidity >= 35000:
            scores["liquidity"] = 75
        elif features.liquidity >= 20000:
            scores["liquidity"] = 50
        else:
            scores["liquidity"] = 25
        
        # 2. Volume Score (0-100)
        if features.volume >= 100000:
            scores["volume"] = 100
        elif features.volume >= 50000:
            scores["volume"] = 75
        elif features.volume >= 20000:
            scores["volume"] = 50
        else:
            scores["volume"] = 25
        
        # 3. Momentum Score (0-100)
        if 15 <= features.momentum <= 30:
            scores["momentum"] = 100
        elif 12 <= features.momentum < 15:
            scores["momentum"] = 75
        elif 30 < features.momentum <= 45:
            scores["momentum"] = 50
        else:
            scores["momentum"] = 25
        
        # 4. Age Score (0-100)
        if 10 <= features.age_min <= 30:
            scores["age"] = 100
        elif 5 <= features.age_min < 10:
            scores["age"] = 75
        elif 30 < features.age_min <= 60:
            scores["age"] = 50
        else:
            scores["age"] = 25
        
        # 5. Entry Hour Score (0-100) - dengan confidence
        hour = features.entry_hour
        if hour_data and hour in hour_data:
            data = hour_data[hour]
            trades = data.get("trades", 0)
            win_rate = data.get("win_rate", 50)
            avg_pnl = data.get("avg_pnl", 0)
            
            # Confidence based on sample size
            confidence = min(1.0, trades / self.min_hour_samples)
            
            # Expectancy-based score
            if avg_pnl > 0.005:
                expectancy_score = 100
            elif avg_pnl > 0:
                expectancy_score = 75
            elif avg_pnl > -0.005:
                expectancy_score = 50
            else:
                expectancy_score = 25
            
            # Combine win rate & expectancy with confidence
            if confidence < 0.3:
                # Not enough data → use default (neutral)
                scores["entry_hour"] = 50
            else:
                # Weighted: 60% win_rate, 40% expectancy
                scores["entry_hour"] = (win_rate * 0.6 + expectancy_score * 0.4) * confidence + 50 * (1 - confidence)
        else:
            # No data → neutral
            scores["entry_hour"] = 50
        
        # 6. Historical Win Rate Score (0-100)
        wr = features.historical_win_rate
        if wr >= 60:
            scores["historical_wr"] = 100
        elif wr >= 50:
            scores["historical_wr"] = 75
        elif wr >= 40:
            scores["historical_wr"] = 50
        else:
            scores["historical_wr"] = 25
        
        # Calculate final score
        final_score = 0
        for key, weight in self.weights.items():
            if key in scores:
                final_score += scores[key] * weight
        
        # Determine action based on score
        if final_score >= 70:
            action = "BUY"
            confidence = min(1.0, (final_score - 50) / 50)
        elif final_score >= 50:
            action = "SKIP"
            confidence = 0.5
        else:
            action = "BLOCK"
            confidence = max(0, (50 - final_score) / 50)
        
        return {
            "total_score": final_score,
            "scores": scores,
            "action": action,
            "confidence": confidence,
            "reason": f"Score: {final_score:.1f} → {action}"
        }
