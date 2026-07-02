"""
Planner Optimizer - V3.3
Belajar dari pengalaman untuk memilih urutan action yang optimal
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class ActionPlan:
    """Rencana action dengan skor"""
    actions: List[str]
    score: float
    confidence: float
    success_rate: float
    avg_duration: float
    experience_count: int


class PlannerOptimizer:
    """
    Planner Optimization - memilih urutan action terbaik dari pengalaman
    """

    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.optimization_file = self.memory_dir / "planner_optimization.json"
        self.action_sequences: Dict[str, Dict] = {}  # intent -> {sequence: stats}
        self._load()

    def get_optimal_plan(self, intent: str, user_request: str = "") -> ActionPlan:
        """
        Dapatkan plan optimal untuk intent tertentu
        """
        # 1. Cari sequence terbaik dari pengalaman
        best_sequence = self._find_best_sequence(intent)
        
        if best_sequence:
            return best_sequence
        
        # 2. Fallback: buat plan default
        return self._create_default_plan(intent)

    def _find_best_sequence(self, intent: str) -> Optional[ActionPlan]:
        """Cari sequence terbaik dari experience"""
        if intent not in self.action_sequences:
            return None
        
        sequences = self.action_sequences[intent]
        
        # Cari sequence dengan score tertinggi
        best = None
        best_score = -1
        
        for seq_key, stats in sequences.items():
            # Hitung score: success_rate * confidence * (1 + recency_bonus)
            score = (
                stats.get("success_rate", 0) *
                stats.get("avg_confidence", 0) *
                (1 + stats.get("recency_bonus", 0))
            )
            
            if score > best_score:
                best_score = score
                best = ActionPlan(
                    actions=stats.get("actions", []),
                    score=score,
                    confidence=stats.get("avg_confidence", 0.5),
                    success_rate=stats.get("success_rate", 0),
                    avg_duration=stats.get("avg_duration", 0),
                    experience_count=stats.get("count", 0)
                )
        
        return best

    def _create_default_plan(self, intent: str) -> ActionPlan:
        """Buat plan default berdasarkan intent"""
        default_plans = {
            "build": ["scan_project", "analyze_project", "build_project"],
            "repair": ["analyze_project", "repair_project"],
            "analyze": ["scan_project", "analyze_project"],
            "modify": ["trace_code", "modify_logic"],
            "run": ["status", "run_bot"],
        }
        
        actions = default_plans.get(intent, ["analyze_project"])
        
        return ActionPlan(
            actions=actions,
            score=0.5,
            confidence=0.5,
            success_rate=0.5,
            avg_duration=10.0,
            experience_count=0
        )

    def learn_from_experience(self, experiences: List[Dict]):
        """
        Belajar dari experience untuk mengoptimalkan planner
        """
        for exp in experiences:
            self._learn_single_experience(exp)
        
        self._save()

    def _learn_single_experience(self, experience: Dict):
        """Belajar dari satu experience"""
        intent = experience.get("intent", "unknown")
        actions = experience.get("actions", [])
        success = experience.get("success", False)
        confidence = experience.get("confidence", 0.5)
        duration = experience.get("duration", 0)
        
        if not actions:
            return
        
        # Buat key untuk sequence
        seq_key = " → ".join(actions)
        
        # Init jika belum ada
        if intent not in self.action_sequences:
            self.action_sequences[intent] = {}
        
        if seq_key not in self.action_sequences[intent]:
            self.action_sequences[intent][seq_key] = {
                "actions": actions,
                "count": 0,
                "success_count": 0,
                "total_confidence": 0,
                "total_duration": 0,
                "last_used": None
            }
        
        # Update stats
        stats = self.action_sequences[intent][seq_key]
        stats["count"] += 1
        if success:
            stats["success_count"] += 1
        stats["total_confidence"] += confidence
        stats["total_duration"] += duration
        stats["last_used"] = datetime.now().isoformat()
        
        # Hitung metrics
        stats["success_rate"] = stats["success_count"] / stats["count"]
        stats["avg_confidence"] = (stats["total_confidence"] / stats["count"]) / 100
        stats["avg_duration"] = stats["total_duration"] / stats["count"]
        
        # Recency bonus: jika last_used dalam 7 hari
        if stats["last_used"]:
            last_date = datetime.fromisoformat(stats["last_used"])
            days_ago = (datetime.now() - last_date).days
            stats["recency_bonus"] = max(0, 1 - (days_ago / 30))  # 0-1

    def get_plan_recommendation(self, intent: str, user_request: str = "") -> Dict:
        """
        Dapatkan rekomendasi plan dengan penjelasan
        """
        optimal = self.get_optimal_plan(intent, user_request)
        
        return {
            "intent": intent,
            "recommended_actions": optimal.actions,
            "confidence": optimal.confidence,
            "success_rate": optimal.success_rate,
            "experience_count": optimal.experience_count,
            "reason": self._generate_reason(optimal, intent)
        }

    def _generate_reason(self, plan: ActionPlan, intent: str) -> str:
        """Generate penjelasan kenapa plan ini dipilih"""
        if plan.experience_count == 0:
            return f"Default plan untuk intent '{intent}' (belum ada experience)"
        
        return (
            f"Dipilih dari {plan.experience_count} pengalaman "
            f"(success rate: {plan.success_rate:.1%}, "
            f"confidence: {plan.confidence:.1%})"
        )

    def get_summary(self) -> Dict:
        """Dapatkan summary planner optimization"""
        total_intents = len(self.action_sequences)
        total_sequences = sum(len(seq) for seq in self.action_sequences.values())
        
        # Best sequences per intent
        best_sequences = {}
        for intent in self.action_sequences:
            best = self._find_best_sequence(intent)
            if best:
                best_sequences[intent] = {
                    "actions": best.actions,
                    "success_rate": best.success_rate,
                    "confidence": best.confidence,
                    "count": best.experience_count
                }
        
        return {
            "total_intents": total_intents,
            "total_sequences": total_sequences,
            "best_sequences": best_sequences,
            "timestamp": datetime.now().isoformat()
        }

    def print_summary(self):
        """Print summary ke console"""
        summary = self.get_summary()
        
        print("\n" + "=" * 60)
        print("📋 PLANNER OPTIMIZATION - SUMMARY")
        print("=" * 60)
        print(f"Total Intents    : {summary['total_intents']}")
        print(f"Total Sequences  : {summary['total_sequences']}")
        
        if summary['best_sequences']:
            print("\n📊 Best Sequences per Intent:")
            for intent, data in summary['best_sequences'].items():
                actions = " → ".join(data['actions'])
                rate = data['success_rate']
                conf = data['confidence']
                count = data['count']
                print(f"  {intent}: {actions}")
                print(f"    Success: {rate:.1%} | Confidence: {conf:.1%} | Count: {count}")
        
        print("=" * 60)

    def _load(self):
        """Load dari disk"""
        if self.optimization_file.exists():
            try:
                data = json.loads(self.optimization_file.read_text())
                self.action_sequences = data.get("action_sequences", {})
                print(f"[PLANNER] Loaded {len(self.action_sequences)} intents")
            except:
                self.action_sequences = {}

    def _save(self):
        """Save ke disk"""
        data = {
            "action_sequences": self.action_sequences,
            "updated_at": datetime.now().isoformat()
        }
        self.optimization_file.write_text(json.dumps(data, indent=2))


# Singleton
_optimizer = None

def get_planner_optimizer():
    global _optimizer
    if _optimizer is None:
        _optimizer = PlannerOptimizer()
    return _optimizer
