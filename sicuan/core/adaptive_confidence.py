"""
Adaptive Confidence - V3.2
Menyesuaikan confidence score berdasarkan data historis dan konteks
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ConfidenceFactors:
    """Faktor-faktor yang mempengaruhi confidence"""
    base_confidence: float = 0.5
    historical_success: float = 0.0
    experience_similarity: float = 0.0
    auto_learning_boost: float = 0.0
    drift_penalty: float = 0.0
    recency_bonus: float = 0.0
    
    def calculate(self) -> float:
        """Hitung final confidence"""
        total = (
            self.base_confidence * 0.20 +
            self.historical_success * 0.35 +
            self.experience_similarity * 0.25 +
            self.auto_learning_boost * 0.15 +
            self.recency_bonus * 0.05 -
            self.drift_penalty
        )
        return max(0.0, min(1.0, total))


class AdaptiveConfidence:
    """
    Adaptive Confidence Engine - menyesuaikan confidence berdasarkan data
    """

    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.history_file = self.memory_dir / "confidence_history.json"
        self.history: List[Dict] = []
        self._load_history()
        
        # Threshold
        self.min_confidence = 0.3
        self.max_confidence = 0.98
        self.drift_threshold = 0.10  # 10% penurunan = drift

    def calculate_confidence(
        self,
        action: str,
        user_request: str = "",
        intent: str = "",
        project: str = "",
        similar_experiences: List = None
    ) -> Dict:
        """
        Hitung adaptive confidence untuk sebuah action
        """
        factors = ConfidenceFactors()
        
        # 1. Base confidence (dari auto learning / default)
        factors.base_confidence = self._get_base_confidence(action)
        
        # 2. Historical success rate
        factors.historical_success = self._get_historical_success(action)
        
        # 3. Experience similarity
        if similar_experiences:
            factors.experience_similarity = self._calculate_similarity_score(
                similar_experiences
            )
        
        # 4. Auto learning boost
        factors.auto_learning_boost = self._get_auto_learning_boost(action)
        
        # 5. Drift penalty
        factors.drift_penalty = self._get_drift_penalty(action)
        
        # 6. Recency bonus
        factors.recency_bonus = self._get_recency_bonus(action)
        
        # Hitung final confidence
        final_confidence = factors.calculate()
        
        # Ensure dalam range
        final_confidence = max(self.min_confidence, min(self.max_confidence, final_confidence))
        
        # Simpan history
        self._save_confidence_record(action, final_confidence, factors)
        
        return {
            "confidence": final_confidence,
            "factors": {
                "base": factors.base_confidence,
                "historical_success": factors.historical_success,
                "experience_similarity": factors.experience_similarity,
                "auto_learning_boost": factors.auto_learning_boost,
                "drift_penalty": factors.drift_penalty,
                "recency_bonus": factors.recency_bonus
            },
            "level": self._get_confidence_level(final_confidence)
        }

    def _get_base_confidence(self, action: str) -> float:
        """Dapatkan base confidence dari auto learning"""
        # Default berdasarkan action
        defaults = {
            "scan_project": 0.85,
            "analyze_project": 0.80,
            "build_project": 0.75,
            "repair_project": 0.70,
            "modify_logic": 0.65,
            "run_bot": 0.80,
            "status": 0.90,
            "list_projects": 0.95,
        }
        base = defaults.get(action, 0.50)
        
        # Cek auto learning config
        learning_file = self.memory_dir / "learning_insights.json"
        if learning_file.exists():
            try:
                data = json.loads(learning_file.read_text())
                confidence_config = data.get("confidence_config", {})
                if action in confidence_config:
                    base = confidence_config[action].get("base_confidence", base)
            except:
                pass
        
        return base

    def _get_historical_success(self, action: str) -> float:
        """Dapatkan historical success rate untuk action"""
        # Dari experience engine
        try:
            from sicuan.core.experience_engine import get_experience_engine
            engine = get_experience_engine()
            stats = engine.get_stats()
            
            action_stats = stats.get("action_stats", {})
            total = action_stats.get(action, 0)
            
            if total == 0:
                return 0.5
            
            # Hitung success rate
            successful = stats.get("successful_actions", {}).get(action, 0)
            rate = successful / total if total > 0 else 0.5
            
            # Clip ke range 0.3-0.98
            return max(0.3, min(0.98, rate))
            
        except:
            return 0.5

    def _calculate_similarity_score(self, similar_experiences: List) -> float:
        """Hitung similarity score dari experiences"""
        if not similar_experiences:
            return 0.0
        
        # Ambil confidence dari experiences yang mirip
        confidences = [e.confidence for e in similar_experiences if hasattr(e, 'confidence')]
        if not confidences:
            return 0.0
        
        avg_conf = sum(confidences) / len(confidences)
        return avg_conf / 100  # Normalize ke 0-1

    def _get_auto_learning_boost(self, action: str) -> float:
        """Dapatkan boost dari auto learning"""
        learning_file = self.memory_dir / "learning_insights.json"
        if learning_file.exists():
            try:
                data = json.loads(learning_file.read_text())
                action_boost = data.get("action_boost", {}).get(action, 0)
                return min(0.15, action_boost)  # Max 15% boost
            except:
                pass
        return 0.0

    def _get_drift_penalty(self, action: str) -> float:
        """Dapatkan penalty dari drift detection"""
        drift_file = self.memory_dir / "drift_alerts.json"
        if drift_file.exists():
            try:
                data = json.loads(drift_file.read_text())
                alerts = data.get("alerts", [])
                
                # Cek alert untuk action ini
                for alert in alerts[-10:]:
                    if alert.get("metric") == action:
                        severity = alert.get("severity", "warning")
                        if severity == "critical":
                            return 0.15  # Penalty 15%
                        elif severity == "warning":
                            return 0.08  # Penalty 8%
            except:
                pass
        return 0.0

    def _get_recency_bonus(self, action: str) -> float:
        """Dapatkan bonus untuk action yang baru sukses"""
        # Cek history terakhir untuk action ini
        if not self.history:
            return 0.0
        
        # Filter history untuk action ini
        recent = []
        for h in self.history:
            if isinstance(h, dict) and h.get("action") == action:
                recent.append(h)
        
        if not recent:
            return 0.0
        
        # Cek 5 terakhir
        last_5 = recent[-5:]
        success_count = 0
        for h in last_5:
            if isinstance(h, dict) and h.get("success", False):
                success_count += 1
        
        if success_count >= 4:
            return 0.05  # Bonus 5%
        elif success_count >= 3:
            return 0.03  # Bonus 3%
        
        return 0.0

    def _get_confidence_level(self, confidence: float) -> str:
        """Dapatkan level confidence"""
        if confidence >= 0.85:
            return "HIGH"
        elif confidence >= 0.70:
            return "MEDIUM"
        elif confidence >= 0.50:
            return "LOW"
        else:
            return "VERY_LOW"

    def _save_confidence_record(self, action: str, confidence: float, factors: ConfidenceFactors):
        """Simpan record confidence untuk history"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "confidence": confidence,
            "factors": {
                "base": factors.base_confidence,
                "historical_success": factors.historical_success,
                "experience_similarity": factors.experience_similarity,
                "auto_learning_boost": factors.auto_learning_boost,
                "drift_penalty": factors.drift_penalty,
                "recency_bonus": factors.recency_bonus
            }
        }
        self.history.append(record)
        
        # Simpan 100 record terakhir
        if len(self.history) > 100:
            self.history = self.history[-100:]
        
        self._save_history()

    def _load_history(self):
        """Load history dari disk"""
        if self.history_file.exists():
            try:
                data = json.loads(self.history_file.read_text())
                # Jika data adalah dict, convert ke list
                if isinstance(data, dict):
                    # Ambil history dari dict
                    if "history" in data:
                        self.history = data["history"]
                    else:
                        self.history = []
                elif isinstance(data, list):
                    self.history = data
                else:
                    self.history = []
            except:
                self.history = []
        else:
            self.history = []

    def _save_history(self):
        """Save history ke disk"""
        data = {
            "history": self.history,
            "updated_at": datetime.now().isoformat()
        }
        self.history_file.write_text(json.dumps(data, indent=2))

    def get_summary(self) -> Dict:
        """Dapatkan ringkasan adaptive confidence"""
        if not self.history:
            return {"total_records": 0}
        
        confidences = [h.get("confidence", 0) for h in self.history]
        avg_confidence = sum(confidences) / len(confidences)
        
        # Per action
        action_stats = {}
        for h in self.history:
            action = h.get("action", "unknown")
            if action not in action_stats:
                action_stats[action] = []
            action_stats[action].append(h.get("confidence", 0))
        
        action_avg = {
            action: sum(cs) / len(cs)
            for action, cs in action_stats.items()
        }
        
        return {
            "total_records": len(self.history),
            "avg_confidence": avg_confidence,
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "action_avg_confidence": action_avg,
            "latest": self.history[-1] if self.history else None
        }

    def print_summary(self):
        """Print summary ke console"""
        summary = self.get_summary()
        
        print("\n" + "=" * 60)
        print("📊 ADAPTIVE CONFIDENCE - SUMMARY")
        print("=" * 60)
        print(f"Total Records     : {summary.get('total_records', 0)}")
        print(f"Avg Confidence    : {summary.get('avg_confidence', 0):.2%}")
        print(f"Min Confidence    : {summary.get('min_confidence', 0):.2%}")
        print(f"Max Confidence    : {summary.get('max_confidence', 0):.2%}")
        
        if summary.get('action_avg_confidence'):
            print("\n📊 Per Action:")
            for action, conf in sorted(summary['action_avg_confidence'].items(), 
                                       key=lambda x: x[1], reverse=True)[:5]:
                level = "✅" if conf >= 0.85 else "⚠️" if conf >= 0.70 else "❌"
                print(f"  {level} {action}: {conf:.2%}")
        
        if summary.get('latest'):
            latest = summary['latest']
            print(f"\n📋 Latest Record:")
            print(f"  Action: {latest.get('action')}")
            print(f"  Confidence: {latest.get('confidence'):.2%}")
            print(f"  Factors: {latest.get('factors', {})}")
        
        print("=" * 60)


# Singleton
_confidence = None

def get_adaptive_confidence():
    global _confidence
    if _confidence is None:
        _confidence = AdaptiveConfidence()
    return _confidence
