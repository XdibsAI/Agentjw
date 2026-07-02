"""
Experience Engine - Simpan dan gunakan kembali workflow sukses
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class Experience:
    """Record pengalaman dari satu workflow"""
    id: str
    timestamp: str
    user_request: str
    intent: str
    plan: List[Dict]  # List of actions
    actions: List[str]  # Action names
    result: str
    success: bool
    confidence: float
    duration: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Tags untuk pencarian
    tags: List[str] = field(default_factory=list)
    project: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Experience':
        return cls(**data)


class ExperienceEngine:
    """Engine untuk menyimpan dan mencari pengalaman"""

    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.experiences_file = self.memory_dir / "experiences.json"
        self.experiences: List[Experience] = []
        self._load()
    
    def save_experience(
        self,
        user_request: str,
        intent: str,
        plan: List[Dict],
        actions: List[str],
        result: str,
        success: bool,
        confidence: float,
        duration: float,
        project: str = "",
        tags: List[str] = None,
        metadata: Dict = None
    ) -> Experience:
        """Simpan pengalaman dari workflow"""
        
        # Generate tags otomatis
        auto_tags = self._generate_tags(user_request, intent, actions, project)
        if tags:
            auto_tags.extend(tags)
        auto_tags = list(set(auto_tags))  # Remove duplicates
        
        experience = Experience(
            id=f"exp_{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now().isoformat(),
            user_request=user_request,
            intent=intent,
            plan=plan,
            actions=actions,
            result=result[:500],
            success=success,
            confidence=confidence,
            duration=duration,
            project=project,
            tags=auto_tags,
            metadata=metadata or {}
        )
        
        self.experiences.append(experience)
        self._save()
        print(f"[EXPERIENCE] Saved: {experience.id} ({user_request[:50]}...)")
        return experience
    
    def find_experiences(
        self,
        query: str = None,
        intent: str = None,
        project: str = None,
        tags: List[str] = None,
        min_confidence: float = 0.0,
        limit: int = 10
    ) -> List[Experience]:
        """Cari pengalaman berdasarkan query/tags"""
        results = self.experiences
        
        # Filter by success
        results = [e for e in results if e.success]
        
        # Filter by intent
        if intent:
            results = [e for e in results if e.intent == intent]
        
        # Filter by project
        if project:
            results = [e for e in results if e.project == project]
        
        # Filter by tags
        if tags:
            results = [e for e in results if any(t in e.tags for t in tags)]
        
        # Filter by min confidence
        if min_confidence > 0:
            results = [e for e in results if e.confidence >= min_confidence]
        
        # Sort by confidence dan timestamp
        results.sort(key=lambda e: (e.confidence, e.timestamp), reverse=True)
        
        return results[:limit]
    
    def get_similar_experiences(self, user_request: str, intent: str = None, limit: int = 3) -> List[Experience]:
        """Dapatkan pengalaman yang mirip dengan request"""
        # Simple matching: cari kata kunci dari request
        keywords = set(user_request.lower().split())
        
        scored = []
        for exp in self.experiences:
            if not exp.success:
                continue
            
            if intent and exp.intent != intent:
                continue
            
            # Hitung skor berdasarkan kata kunci
            exp_keywords = set(exp.user_request.lower().split())
            common = keywords & exp_keywords
            score = len(common) / max(len(keywords), 1)
            
            # Bonus untuk tags yang match
            tag_score = sum(1 for t in exp.tags if t in user_request.lower())
            score += tag_score * 0.1
            
            # Bonus untuk confidence
            score += exp.confidence / 100
            
            scored.append((exp, score))
        
        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)
        return [exp for exp, _ in scored[:limit]]
    
    def get_by_action(self, action: str, limit: int = 5) -> List[Experience]:
        """Dapatkan pengalaman berdasarkan action"""
        return [e for e in self.experiences if action in e.actions and e.success][:limit]
    
    def get_stats(self) -> Dict:
        """Dapatkan statistik experience"""
        total = len(self.experiences)
        successful = len([e for e in self.experiences if e.success])
        
        # Per action
        action_stats = {}
        for exp in self.experiences:
            if not exp.success:
                continue
            for action in exp.actions:
                action_stats[action] = action_stats.get(action, 0) + 1
        
        # Per intent
        intent_stats = {}
        for exp in self.experiences:
            if exp.success:
                intent_stats[exp.intent] = intent_stats.get(exp.intent, 0) + 1
        
        # Per project
        project_stats = {}
        for exp in self.experiences:
            if exp.success and exp.project:
                project_stats[exp.project] = project_stats.get(exp.project, 0) + 1
        
        return {
            "total": total,
            "successful": successful,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "action_stats": action_stats,
            "intent_stats": intent_stats,
            "project_stats": project_stats,
            "latest": self.experiences[-1].to_dict() if self.experiences else None
        }
    
    def _generate_tags(self, user_request: str, intent: str, actions: List[str], project: str) -> List[str]:
        """Generate tags otomatis"""
        tags = []
        
        # Dari intent
        tags.append(intent)
        
        # Dari actions
        tags.extend(actions[:3])
        
        # Dari kata kunci
        keywords = ["build", "fix", "repair", "analyze", "scan", "status", "log", "deploy", "test"]
        for kw in keywords:
            if kw in user_request.lower():
                tags.append(kw)
        
        # Dari project
        if project:
            tags.append(project)
        
        return tags
    
    def _save(self):
        """Save experiences ke disk"""
        data = {
            "experiences": [e.to_dict() for e in self.experiences],
            "updated_at": datetime.now().isoformat()
        }
        self.experiences_file.write_text(json.dumps(data, indent=2))
    
    def _load(self):
        """Load experiences dari disk"""
        if not self.experiences_file.exists():
            self.experiences = []
            return
        
        try:
            data = json.loads(self.experiences_file.read_text())
            self.experiences = [Experience.from_dict(e) for e in data.get("experiences", [])]
            print(f"[EXPERIENCE] Loaded {len(self.experiences)} experiences")
        except Exception as e:
            print(f"[EXPERIENCE] Failed to load: {e}")
            self.experiences = []
    
    def print_summary(self):
        """Print summary ke console"""
        stats = self.get_stats()
        
        print("\n" + "=" * 60)
        print("📚 EXPERIENCE ENGINE SUMMARY")
        print("=" * 60)
        print(f"Total Experiences : {stats['total']}")
        print(f"Successful        : {stats['successful']}")
        print(f"Success Rate      : {stats['success_rate']:.1f}%")
        
        if stats['action_stats']:
            print("\n📊 Per Action:")
            for action, count in sorted(stats['action_stats'].items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {action}: {count}")
        
        if stats['intent_stats']:
            print("\n📊 Per Intent:")
            for intent, count in sorted(stats['intent_stats'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {intent}: {count}")
        
        if stats['project_stats']:
            print("\n📊 Per Project:")
            for project, count in sorted(stats['project_stats'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {project}: {count}")
        
        print("=" * 60)


# Singleton
_engine = None

def get_experience_engine():
    global _engine
    if _engine is None:
        _engine = ExperienceEngine()
    return _engine
