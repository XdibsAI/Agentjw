"""
Continuous Learning v1 - Belajar dari data nyata
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any
import statistics

from core.logger import logger


class ContinuousLearning:
    """
    Continuous Learning Engine - belajar dari data pilot production.
    """
    
    def __init__(self, dataset_dir: Path = Path("datasets")):
        self.dataset_dir = dataset_dir
        self.workflows = []
        self.reflections = []
        self.shadow_comparisons = []
        self.metrics = {}
        self.learnings = {}
        
    def load_datasets(self):
        """Load semua dataset"""
        logger.info("Loading datasets...")
        
        # Load workflows
        wf_file = self.dataset_dir / "workflow_history.jsonl"
        if wf_file.exists():
            with open(wf_file) as f:
                self.workflows = [json.loads(line) for line in f]
            logger.info(f"Loaded {len(self.workflows)} workflows")
        
        # Load reflections
        ref_file = self.dataset_dir / "reflections.jsonl"
        if ref_file.exists():
            with open(ref_file) as f:
                self.reflections = [json.loads(line) for line in f]
            logger.info(f"Loaded {len(self.reflections)} reflections")
        
        # Load shadow comparisons
        shadow_file = self.dataset_dir / "shadow_comparisons.jsonl"
        if shadow_file.exists():
            with open(shadow_file) as f:
                self.shadow_comparisons = [json.loads(line) for line in f]
            logger.info(f"Loaded {len(self.shadow_comparisons)} shadow comparisons")
        
        # Load metrics
        metrics_file = self.dataset_dir / "runtime_metrics.json"
        if metrics_file.exists():
            with open(metrics_file) as f:
                self.metrics = json.load(f)
            logger.info("Loaded runtime metrics")
    
    def analyze(self):
        """Analisis dataset untuk mendapatkan insight"""
        logger.info("Analyzing dataset...")
        
        learnings = {}
        
        # 1. Action Performance
        action_stats = defaultdict(lambda: {"total": 0, "success": 0, "duration": []})
        for wf in self.workflows:
            action = wf.get("action", "unknown")
            action_stats[action]["total"] += 1
            if wf.get("success", False):
                action_stats[action]["success"] += 1
            if wf.get("duration", 0) > 0:
                action_stats[action]["duration"].append(wf.get("duration", 0))
        
        # 2. Best and Worst Actions
        best_actions = []
        worst_actions = []
        for action, stats in action_stats.items():
            total = stats["total"]
            if total > 0:
                rate = stats["success"] / total * 100
                avg_dur = statistics.mean(stats["duration"]) if stats["duration"] else 0
                if rate >= 95:
                    best_actions.append((action, rate, avg_dur))
                elif rate < 80:
                    worst_actions.append((action, rate, avg_dur))
        
        learnings["best_actions"] = sorted(best_actions, key=lambda x: -x[1])[:5]
        learnings["worst_actions"] = sorted(worst_actions, key=lambda x: x[1])[:5]
        
        # 3. Reflection Confidence Analysis
        confidence_scores = [r.get("confidence", 0) for r in self.reflections if r.get("confidence", 0) > 0]
        if confidence_scores:
            learnings["avg_confidence"] = statistics.mean(confidence_scores)
            learnings["confidence_std"] = statistics.stdev(confidence_scores) if len(confidence_scores) > 1 else 0
        
        # 4. Retry Analysis
        retries = [r.get("retry_count", 0) for r in self.reflections]
        total_retries = sum(retries)
        learnings["total_retries"] = total_retries
        learnings["avg_retries"] = total_retries / len(retries) if retries else 0
        
        # 5. Duration Analysis
        durations = [wf.get("duration", 0) for wf in self.workflows if wf.get("duration", 0) > 0]
        if durations:
            learnings["avg_duration"] = statistics.mean(durations)
            learnings["max_duration"] = max(durations)
            learnings["slowest_action"] = max(
                [(a, statistics.mean(s["duration"]) if s["duration"] else 0) 
                 for a, s in action_stats.items() if s["duration"]],
                key=lambda x: x[1]
            ) if action_stats else ("none", 0)
        
        # 6. Planner Accuracy
        # Dari shadow comparisons, hitung match rate per action
        if self.shadow_comparisons:
            shadow_stats = defaultdict(lambda: {"total": 0, "matches": 0})
            for sc in self.shadow_comparisons:
                action = sc.get("action", "unknown")
                shadow_stats[action]["total"] += 1
                if sc.get("match", False):
                    shadow_stats[action]["matches"] += 1
            
            learnings["shadow_match_rate"] = {}
            for action, stats in shadow_stats.items():
                if stats["total"] > 0:
                    learnings["shadow_match_rate"][action] = stats["matches"] / stats["total"] * 100
        
        # 7. Recommendations
        recommendations = []
        
        # If any action has low success rate
        if learnings.get("worst_actions"):
            for action, rate, _ in learnings["worst_actions"]:
                recommendations.append(f"⚠️ Improve {action}: success rate {rate:.1f}%")
        
        # If retry rate is high
        if learnings.get("avg_retries", 0) > 1:
            recommendations.append(f"🔄 Reduce retries: avg {learnings['avg_retries']:.2f} retries per workflow")
        
        # If duration is high
        if learnings.get("avg_duration", 0) > 5:
            slowest = learnings.get("slowest_action", ("unknown", 0))
            recommendations.append(f"🐢 Optimize {slowest[0]}: {slowest[1]:.2f}s avg duration")
        
        # If shadow match is low
        for action, rate in learnings.get("shadow_match_rate", {}).items():
            if rate < 90 and action not in ["gallery", "video_info", "business_analysis"]:
                recommendations.append(f"📊 Improve {action} shadow match: {rate:.1f}%")
        
        learnings["recommendations"] = recommendations
        
        self.learnings = learnings
        return learnings
    
    def apply_learnings(self):
        """Terapkan pembelajaran ke sistem — implementasi nyata."""
        import json
        from pathlib import Path
        from datetime import datetime

        logger.info("Applying learnings...")

        if not self.learnings:
            self.analyze()

        learnings = self.learnings
        mem = Path(__file__).resolve().parents[2] / "memory"
        applied = []

        # 1. Update ReflectionEngine confidence threshold
        try:
            avg_conf = learnings.get("avg_confidence", 0)
            if avg_conf > 0:
                new_threshold = 0.6 if avg_conf > 85 else 0.8 if avg_conf < 70 else 0.7
                config = {"confidence_threshold": new_threshold,
                          "updated_at": datetime.now().isoformat(),
                          "based_on_avg_confidence": avg_conf}
                (mem / "reflection_config.json").write_text(
                    json.dumps(config, indent=2), encoding="utf-8")
                applied.append(f"ReflectionEngine threshold={new_threshold} (conf={avg_conf:.1f}%)")
        except Exception as e:
            logger.warning(f"reflection config failed: {e}")

        # 2. Update retry limit
        try:
            avg_retries = learnings.get("avg_retries", 0)
            retry_limit = 2 if avg_retries < 0.5 else 3 if avg_retries < 1.5 else 4
            (mem / "retry_config.json").write_text(
                json.dumps({"retry_limit": retry_limit,
                            "updated_at": datetime.now().isoformat(),
                            "based_on_avg_retries": avg_retries}, indent=2),
                encoding="utf-8")
            applied.append(f"RetryLimit={retry_limit} (avg_retries={avg_retries:.2f})")
        except Exception as e:
            logger.warning(f"retry config failed: {e}")

        # 3. Simpan learning insights
        try:
            insights = {
                "generated_at": datetime.now().isoformat(),
                "best_actions": learnings.get("best_actions", []),
                "worst_actions": learnings.get("worst_actions", []),
                "recommendations": learnings.get("recommendations", []),
                "avg_confidence": learnings.get("avg_confidence", 0),
                "avg_retries": learnings.get("avg_retries", 0),
                "shadow_match_rate": learnings.get("shadow_match_rate", {}),
                "applied_changes": applied,
            }
            (mem / "learning_insights.json").write_text(
                json.dumps(insights, indent=2, ensure_ascii=False, default=str),
                encoding="utf-8")
            applied.append("Saved learning_insights.json")
        except Exception as e:
            logger.warning(f"insights save failed: {e}")

        # 4. Inject ke memory store
        try:
            from memory.memory_store import memory_store
            recs = learnings.get("recommendations", [])
            worst = learnings.get("worst_actions", [])
            if recs or worst:
                text = f"Auto-learning {datetime.now().strftime('%Y-%m-%d')}: "
                if worst:
                    text += f"Perlu perbaikan: {', '.join([a[0] for a in worst[:3]])}. "
                if recs:
                    text += recs[0]
                memory_store.store(type="sicuan_insight", content=text, importance=7.0)
                applied.append("Insight injected to memory store")
        except Exception as e:
            logger.warning(f"memory store inject failed: {e}")

        logger.info(f"Applied {len(applied)} learnings")
        return {"applied": applied, "learnings": learnings}

    def report(self):
        """Generate laporan Continuous Learning"""
        if not self.learnings:
            self.analyze()
        
        learnings = self.learnings
        
        print("\n" + "=" * 60)
        print("🧠 CONTINUOUS LEARNING REPORT")
        print("=" * 60)
        
        print("\n📊 Performance Summary:")
        print(f"  Total workflows    : {len(self.workflows)}")
        print(f"  Success rate       : {sum(1 for w in self.workflows if w.get('success', False)) / len(self.workflows) * 100:.1f}%")
        print(f"  Avg confidence     : {learnings.get('avg_confidence', 0):.1f}%")
        print(f"  Avg retries        : {learnings.get('avg_retries', 0):.2f}")
        print(f"  Avg duration       : {learnings.get('avg_duration', 0):.2f}s")
        
        print("\n🏆 Best Actions:")
        for action, rate, dur in learnings.get('best_actions', []):
            print(f"  ✅ {action}: {rate:.1f}% ({dur:.2f}s avg)")
        
        print("\n⚠️ Actions to Improve:")
        for action, rate, dur in learnings.get('worst_actions', []):
            print(f"  ❌ {action}: {rate:.1f}% ({dur:.2f}s avg)")
        
        print("\n📊 Shadow Match Rate:")
        for action, rate in learnings.get('shadow_match_rate', {}).items():
            status = "✅" if rate >= 95 else "⚠️" if rate >= 80 else "❌"
            print(f"  {status} {action}: {rate:.1f}%")
        
        print("\n💡 Recommendations:")
        for rec in learnings.get('recommendations', []):
            print(f"  {rec}")
        
        print("\n" + "=" * 60)


def get_continuous_learning() -> ContinuousLearning:
    """Singleton instance"""
    global _continuous_learning
    if '_continuous_learning' not in globals():
        _continuous_learning = ContinuousLearning()
    return _continuous_learning
