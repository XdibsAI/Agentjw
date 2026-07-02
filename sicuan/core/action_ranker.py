"""
Action Ranker - V3.4
Memberikan skor dan prioritas per action berdasarkan data historis
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ActionScore:
    """Skor untuk sebuah action"""
    action: str
    score: float
    success_rate: float
    avg_duration: float
    confidence: float
    priority: str  # HIGH, MEDIUM, LOW
    rank: int
    reason: str


class ActionRanker:
    """
    Action Ranking - memberikan skor dan prioritas per action
    """

    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.ranking_file = self.memory_dir / "action_ranking.json"
        self.action_stats: Dict[str, Dict] = {}
        self._load()

    def update_stats(self, action: str, success: bool, duration: float, confidence: float):
        """Update statistik action"""
        if action not in self.action_stats:
            self.action_stats[action] = {
                "count": 0,
                "success_count": 0,
                "total_duration": 0,
                "total_confidence": 0,
                "last_used": None
            }
        
        stats = self.action_stats[action]
        stats["count"] += 1
        if success:
            stats["success_count"] += 1
        stats["total_duration"] += duration
        stats["total_confidence"] += confidence
        stats["last_used"] = datetime.now().isoformat()
        
        self._save()

    def get_action_rank(self, action: str) -> ActionScore:
        """Dapatkan ranking untuk sebuah action"""
        stats = self.action_stats.get(action, {})
        
        # Hitung metrics
        count = stats.get("count", 0)
        if count == 0:
            # Default untuk action baru
            return ActionScore(
                action=action,
                score=0.5,
                success_rate=0.5,
                avg_duration=10.0,
                confidence=0.5,
                priority="MEDIUM",
                rank=99,
                reason="Belum ada data"
            )
        
        success_rate = stats.get("success_count", 0) / count
        avg_duration = stats.get("total_duration", 0) / count
        avg_confidence = stats.get("total_confidence", 0) / count
        
        # Hitung score: weighted combination
        # 40% success_rate, 30% confidence, 20% recency, 10% duration
        recency_bonus = self._get_recency_bonus(stats.get("last_used"))
        duration_score = max(0, 1 - (avg_duration / 60))  # 0-1, 60 detik = 0
        
        score = (
            success_rate * 0.40 +
            avg_confidence * 0.30 +
            recency_bonus * 0.20 +
            duration_score * 0.10
        )
        
        # Tentukan priority
        if score >= 0.8:
            priority = "HIGH"
        elif score >= 0.6:
            priority = "MEDIUM"
        else:
            priority = "LOW"
        
        # Hitung rank
        rank = self._calculate_rank(action, score)
        
        reason = self._generate_reason(success_rate, avg_confidence, count, priority)
        
        return ActionScore(
            action=action,
            score=score,
            success_rate=success_rate,
            avg_duration=avg_duration,
            confidence=avg_confidence,
            priority=priority,
            rank=rank,
            reason=reason
        )

    def get_all_ranks(self) -> List[ActionScore]:
        """Dapatkan ranking semua actions"""
        ranks = []
        for action in self.action_stats:
            ranks.append(self.get_action_rank(action))
        
        # Sort by score
        ranks.sort(key=lambda x: x.score, reverse=True)
        
        # Update rank numbers
        for i, rank in enumerate(ranks):
            rank.rank = i + 1
        
        return ranks

    def get_top_actions(self, limit: int = 5) -> List[ActionScore]:
        """Dapatkan top N actions"""
        ranks = self.get_all_ranks()
        return ranks[:limit]

    def get_worst_actions(self, limit: int = 5) -> List[ActionScore]:
        """Dapatkan worst N actions"""
        ranks = self.get_all_ranks()
        return ranks[-limit:]

    def _get_recency_bonus(self, last_used: Optional[str]) -> float:
        """Hitung recency bonus (0-1)"""
        if not last_used:
            return 0.0
        
        try:
            last_date = datetime.fromisoformat(last_used)
            days_ago = (datetime.now() - last_date).days
            return max(0, 1 - (days_ago / 30))  # 30 hari = 0
        except:
            return 0.0

    def _calculate_rank(self, action: str, score: float) -> int:
        """Hitung rank berdasarkan score"""
        all_scores = []
        for act, stats in self.action_stats.items():
            count = stats.get("count", 0)
            if count > 0:
                success_rate = stats.get("success_count", 0) / count
                avg_confidence = stats.get("total_confidence", 0) / count
                recency_bonus = self._get_recency_bonus(stats.get("last_used"))
                duration_score = max(0, 1 - (stats.get("total_duration", 0) / count / 60))
                
                s = (
                    success_rate * 0.40 +
                    avg_confidence * 0.30 +
                    recency_bonus * 0.20 +
                    duration_score * 0.10
                )
                all_scores.append((act, s))
        
        all_scores.sort(key=lambda x: x[1], reverse=True)
        
        for i, (act, _) in enumerate(all_scores):
            if act == action:
                return i + 1
        
        return len(all_scores) + 1

    def _generate_reason(self, success_rate: float, confidence: float, count: int, priority: str) -> str:
        """Generate reason untuk ranking"""
        if count == 0:
            return "Belum ada data"
        
        reasons = []
        if success_rate >= 0.9:
            reasons.append("success rate sangat tinggi")
        elif success_rate >= 0.7:
            reasons.append("success rate baik")
        else:
            reasons.append("success rate perlu ditingkatkan")
        
        if confidence >= 0.8:
            reasons.append("confidence tinggi")
        elif confidence >= 0.6:
            reasons.append("confidence cukup")
        else:
            reasons.append("confidence rendah")
        
        if count >= 10:
            reasons.append(f"berdasarkan {count} pengalaman")
        elif count >= 5:
            reasons.append(f"berdasarkan {count} pengalaman")
        else:
            reasons.append(f"hanya {count} pengalaman")
        
        return f"Priority {priority}: " + ", ".join(reasons)

    def get_summary(self) -> Dict:
        """Dapatkan summary action ranking"""
        ranks = self.get_all_ranks()
        
        return {
            "total_actions": len(ranks),
            "high_priority": len([r for r in ranks if r.priority == "HIGH"]),
            "medium_priority": len([r for r in ranks if r.priority == "MEDIUM"]),
            "low_priority": len([r for r in ranks if r.priority == "LOW"]),
            "top_actions": [{"action": r.action, "score": r.score, "priority": r.priority} for r in ranks[:5]],
            "timestamp": datetime.now().isoformat()
        }

    def print_summary(self):
        """Print summary ke console"""
        summary = self.get_summary()
        ranks = self.get_all_ranks()
        
        print("\n" + "=" * 60)
        print("📊 ACTION RANKING - SUMMARY")
        print("=" * 60)
        print(f"Total Actions    : {summary['total_actions']}")
        print(f"High Priority    : {summary['high_priority']}")
        print(f"Medium Priority  : {summary['medium_priority']}")
        print(f"Low Priority     : {summary['low_priority']}")
        
        if ranks:
            print("\n📋 Ranked Actions:")
            for rank in ranks[:10]:
                icon = "🔥" if rank.priority == "HIGH" else "📌" if rank.priority == "MEDIUM" else "💤"
                print(f"  {rank.rank:2}. {icon} {rank.action}")
                print(f"      Score: {rank.score:.2%} | Success: {rank.success_rate:.1%} | Conf: {rank.confidence:.1%}")
                print(f"      Reason: {rank.reason}")
        
        print("=" * 60)

    def _load(self):
        """Load dari disk"""
        if self.ranking_file.exists():
            try:
                data = json.loads(self.ranking_file.read_text())
                self.action_stats = data.get("action_stats", {})
                print(f"[RANKER] Loaded {len(self.action_stats)} actions")
            except:
                self.action_stats = {}

    def _save(self):
        """Save ke disk"""
        data = {
            "action_stats": self.action_stats,
            "updated_at": datetime.now().isoformat()
        }
        self.ranking_file.write_text(json.dumps(data, indent=2))


# Singleton
_ranker = None

def get_action_ranker():
    global _ranker
    if _ranker is None:
        _ranker = ActionRanker()
    return _ranker
