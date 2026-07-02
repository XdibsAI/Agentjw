"""
Executive Brain Evolusi - V3
Belajar dari pengalaman, bukan hanya LLM
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Decision:
    """Record keputusan yang diambil"""
    timestamp: str
    user_request: str
    intent: str
    action: str
    target: str
    confidence: float
    reasoning: List[str]
    success: bool
    duration: float
    experience_id: Optional[str] = None
    similar_experience_id: Optional[str] = None


class ExecutiveBrainEvolved:
    """
    Executive Brain yang berevolusi - belajar dari pengalaman
    """

    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.decisions_file = self.memory_dir / "executive_decisions.json"
        self.decisions: List[Decision] = []
        self._load_decisions()
        
        # Referensi ke komponen lain
        self._init_components()

    def _init_components(self):
        """Init komponen yang dibutuhkan"""
        try:
            from sicuan.core.experience_engine import get_experience_engine
            self.experience_engine = get_experience_engine()
        except:
            self.experience_engine = None
        
        try:
            from sicuan.core.continuous_learning import ContinuousLearning
            self.learner = ContinuousLearning()
        except:
            self.learner = None
        
        try:
            from sicuan.core.self_review_data import get_self_review
            self.self_review = get_self_review()
        except:
            self.self_review = None

    def decide(self, user_request: str, context: Dict = None) -> Dict:
        """
        Ambil keputusan dengan mempertimbangkan:
        1. Pengalaman sebelumnya (Experience Engine)
        2. Learnings (Auto Learning)
        3. Konteks saat ini
        4. Confidence scoring
        """
        context = context or {}
        
        # 1. Cari pengalaman serupa
        similar_experiences = []
        if self.experience_engine:
            similar_experiences = self.experience_engine.get_similar_experiences(
                user_request, 
                intent=context.get("intent"),
                limit=3
            )
        
        # 2. Cari learning yang relevan
        learnings = self._get_relevant_learnings(user_request)
        
        # 3. Build decision dengan LLM + experience
        decision = self._build_decision(
            user_request=user_request,
            context=context,
            similar_experiences=similar_experiences,
            learnings=learnings
        )
        
        # 4. Simpan decision untuk learning
        self._save_decision(decision)
        
        return decision

    def _get_relevant_learnings(self, user_request: str) -> List:
        """Dapatkan learning yang relevan"""
        learnings = []
        
        # Dari auto learning
        insights_file = self.memory_dir / "learning_insights.json"
        if insights_file.exists():
            try:
                data = json.loads(insights_file.read_text())
                learnings.extend(data.get("insights", []))
            except:
                pass
        
        return learnings[:5]

    def _build_decision(self, user_request: str, context: Dict,
                        similar_experiences: List, learnings: List) -> Dict:
        """Build decision dengan kombinasi experience + LLM"""
        
        # Build prompt dengan experience
        experience_context = ""
        if similar_experiences:
            experience_context = "\nPengalaman serupa sebelumnya:\n"
            for exp in similar_experiences[:2]:
                experience_context += f"- {exp.user_request} → {exp.actions} (conf: {exp.confidence}%)\n"
        
        learning_context = ""
        if learnings:
            learning_context = "\nPembelajaran yang relevan:\n"
            for l in learnings[:3]:
                learning_context += f"- {l}\n"
        
        # Combine dengan context
        full_context = context.get("context", "") + experience_context + learning_context
        
        # Panggil LLM dengan context yang kaya
        from sicuan.brain import SiCuanBrain
        brain = SiCuanBrain()
        result = brain.think_and_respond(user_request, [{"role": "user", "content": full_context}])
        
        # Enhance dengan experience
        action = result.get("action")
        confidence = result.get("confidence", 0.5)
        
        # Boost confidence jika ada experience yang mirip
        if similar_experiences:
            avg_exp_conf = sum(e.confidence for e in similar_experiences[:2]) / min(2, len(similar_experiences))
            confidence = (confidence + avg_exp_conf / 100) / 2
        
        # Boost jika ada learning yang relevan
        if learnings:
            confidence = min(1.0, confidence + 0.05)
        
        return {
            "action": action,
            "target": context.get("project", "unknown"),
            "confidence": confidence,
            "reasoning": result.get("reasoning", ["LLM decision"]),
            "similar_experiences": [e.id for e in similar_experiences[:2]],
            "learnings_used": [l[:50] for l in learnings[:2]]
        }

    def _save_decision(self, decision: Dict):
        """Simpan decision untuk learning"""
        dec = Decision(
            timestamp=datetime.now().isoformat(),
            user_request=decision.get("user_request", ""),
            intent=decision.get("intent", "unknown"),
            action=decision.get("action", "unknown"),
            target=decision.get("target", "unknown"),
            confidence=decision.get("confidence", 0.5),
            reasoning=decision.get("reasoning", []),
            success=decision.get("success", False),
            duration=decision.get("duration", 0),
            experience_id=decision.get("experience_id"),
            similar_experience_id=decision.get("similar_experience_id")
        )
        self.decisions.append(dec)
        self._save_decisions()

    def _load_decisions(self):
        """Load decisions dari disk"""
        if self.decisions_file.exists():
            try:
                data = json.loads(self.decisions_file.read_text())
                self.decisions = [Decision(**d) for d in data.get("decisions", [])]
            except:
                self.decisions = []

    def _save_decisions(self):
        """Save decisions ke disk"""
        data = {
            "decisions": [d.__dict__ for d in self.decisions],
            "updated_at": datetime.now().isoformat()
        }
        self.decisions_file.write_text(json.dumps(data, indent=2))

    def get_stats(self) -> Dict:
        """Dapatkan statistik decision"""
        total = len(self.decisions)
        if total == 0:
            return {"total": 0}
        
        successful = len([d for d in self.decisions if d.success])
        avg_confidence = sum(d.confidence for d in self.decisions) / total
        
        # Per action
        action_stats = {}
        for d in self.decisions:
            if d.success:
                action_stats[d.action] = action_stats.get(d.action, 0) + 1
        
        return {
            "total": total,
            "successful": successful,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "avg_confidence": avg_confidence,
            "action_stats": action_stats
        }

    def print_summary(self):
        """Print summary ke console"""
        stats = self.get_stats()
        
        print("\n" + "=" * 60)
        print("🧠 EXECUTIVE BRAIN EVOLVED - SUMMARY")
        print("=" * 60)
        print(f"Total Decisions   : {stats.get('total', 0)}")
        print(f"Successful        : {stats.get('successful', 0)}")
        print(f"Success Rate      : {stats.get('success_rate', 0):.1f}%")
        print(f"Avg Confidence    : {stats.get('avg_confidence', 0):.2f}")
        
        if stats.get('action_stats'):
            print("\n📊 Per Action:")
            for action, count in sorted(stats['action_stats'].items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {action}: {count}")
        
        print("=" * 60)


# Singleton
_brain = None

def get_executive_brain_evolved():
    global _brain
    if _brain is None:
        _brain = ExecutiveBrainEvolved()
    return _brain

    def _calculate_adaptive_confidence(self, action: str, user_request: str, 
                                       similar_experiences: List) -> Dict:
        """Hitung adaptive confidence untuk action"""
        from sicuan.core.adaptive_confidence import get_adaptive_confidence
        conf_engine = get_adaptive_confidence()
        
        return conf_engine.calculate_confidence(
            action=action,
            user_request=user_request,
            similar_experiences=similar_experiences
        )
