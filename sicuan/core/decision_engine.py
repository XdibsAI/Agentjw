"""
Decision Engine - Voting, Confidence, Fallback, Memory Feedback
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class ModelPerformance:
    """Track performa model"""
    model_name: str
    total_calls: int = 0
    success_count: int = 0
    avg_time: float = 0.0
    avg_cost: float = 0.0
    success_rate: float = 0.0
    last_used: str = ""
    tasks: List[str] = field(default_factory=list)


class DecisionEngine:
    """
    Decision Engine dengan:
    - Confidence scoring
    - Multi-model voting
    - Fallback mechanism
    - Memory feedback
    """

    def __init__(self):
        self.perf_file = Path("/home/dibs/agentjw/memory/model_performance.json")
        self.voting_threshold = 0.6
        self._load_performance()

    def _load_performance(self):
        """Load performance data"""
        self.performances = {}
        if self.perf_file.exists():
            try:
                data = json.loads(self.perf_file.read_text())
                for name, perf in data.items():
                    self.performances[name] = ModelPerformance(**perf)
            except:
                pass

    def _save_performance(self):
        """Save performance data"""
        data = {}
        for name, perf in self.performances.items():
            data[name] = {
                "model_name": perf.model_name,
                "total_calls": perf.total_calls,
                "success_count": perf.success_count,
                "avg_time": perf.avg_time,
                "avg_cost": perf.avg_cost,
                "success_rate": perf.success_rate,
                "last_used": perf.last_used,
                "tasks": perf.tasks[-10:]
            }
        self.perf_file.write_text(json.dumps(data, indent=2))

    def record_performance(self, model_name: str, success: bool, time_taken: float, cost: float, task: str):
        """Record model performance"""
        if model_name not in self.performances:
            self.performances[model_name] = ModelPerformance(model_name=model_name)

        perf = self.performances[model_name]
        perf.total_calls += 1
        if success:
            perf.success_count += 1
        perf.avg_time = (perf.avg_time * (perf.total_calls - 1) + time_taken) / perf.total_calls
        perf.avg_cost = (perf.avg_cost * (perf.total_calls - 1) + cost) / perf.total_calls
        perf.success_rate = perf.success_count / perf.total_calls * 100
        perf.last_used = datetime.now().isoformat()
        if task not in perf.tasks[-10:]:
            perf.tasks.append(task)

        self._save_performance()

    def get_model_score(self, model_name: str) -> float:
        """Dapatkan skor model berdasarkan performa"""
        if model_name in self.performances:
            perf = self.performances[model_name]
            # Weighted: success_rate 70%, speed 20%, cost 10%
            speed_score = max(0, 100 - (perf.avg_time / 10))  # 10 detik = 0
            cost_score = max(0, 100 - (perf.avg_cost * 1000))  # $0.01 = 0
            return (perf.success_rate * 0.7) + (speed_score * 0.2) + (cost_score * 0.1)
        return 50.0

    def get_confidence(self, task: str, candidates: List[Dict]) -> Dict:
        """Hitung confidence untuk setiap candidate model"""
        results = {}
        for candidate in candidates:
            model_name = candidate.get("name", "")
            score = self.get_model_score(model_name)

            # Adjust based on task relevance
            task_score = self._get_task_relevance(task, candidate)
            confidence = (score * 0.6) + (task_score * 0.4)

            results[model_name] = {
                "confidence": confidence / 100,
                "score": score,
                "task_score": task_score,
                "history": self.performances.get(model_name)
            }

        return results

    def _get_task_relevance(self, task: str, candidate: Dict) -> float:
        """Hitung relevansi model dengan task"""
        task_lower = task.lower()
        strengths = candidate.get("strengths", [])

        if any(s in task_lower for s in strengths):
            return 85.0
        return 50.0

    def vote(self, results: List[Dict], threshold: float = 0.6) -> Dict:
        """Voting dari multiple model results"""
        if not results:
            return {"consensus": False, "result": None}

        # Count votes
        votes = {}
        for r in results:
            key = r.get("decision", r.get("result", "unknown"))
            if key not in votes:
                votes[key] = {"count": 0, "details": []}
            votes[key]["count"] += 1
            votes[key]["details"].append(r)

        # Find winner
        winner = max(votes.items(), key=lambda x: x[1]["count"])
        consensus = winner[1]["count"] / len(results) >= threshold

        return {
            "consensus": consensus,
            "winner": winner[0],
            "votes": votes,
            "total": len(results),
            "threshold": threshold
        }

    def fallback_chain(self, primary_model: str, fallbacks: List[str]) -> str:
        """Fallback chain jika primary model gagal"""
        chain = [primary_model] + fallbacks
        return " → ".join(chain)

    def get_performance_summary(self) -> str:
        """Dapatkan summary performa model"""
        if not self.performances:
            return "Belum ada data performa."

        lines = ["📊 **Model Performance**"]
        lines.append("")
        lines.append("| Model | Calls | Success Rate | Avg Time | Avg Cost |")
        lines.append("|-------|-------|--------------|----------|----------|")
        for name, perf in sorted(self.performances.items(), key=lambda x: x[1].success_rate, reverse=True):
            lines.append(f"| {name[:20]} | {perf.total_calls} | {perf.success_rate:.1f}% | {perf.avg_time:.2f}s | ${perf.avg_cost:.4f} |")
        return "\n".join(lines)


# Singleton
_engine = None

def get_decision_engine():
    global _engine
    if _engine is None:
        _engine = DecisionEngine()
    return _engine
