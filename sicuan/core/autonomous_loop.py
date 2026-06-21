"""
AutonomousLoop — LLM-driven, bukan keyword parsing.
Scheduler lama tetap jalan untuk morning briefing & trading monitor.
"""

from sicuan.core.auto_scheduler import AutoScheduler
from sicuan.core.self_review_loop import SelfReviewLoop
from sicuan.core.knowledge_engine import KnowledgeEngine
from sicuan.brain import SiCuanBrain


class AutonomousLoop:

    def run(self):

        # ── Step 1: Scheduler ──
        scheduler = AutoScheduler()
        scheduler.run()

        # ── Step 2: Knowledge context ──
        ke = KnowledgeEngine()
        knowledge = ke.load_all()

        # ── Step 3: SiCuan Brain planner + executor ──
        brain = SiCuanBrain()

        result = brain.think_and_respond(
            "Audit project aktif. Jika ada masalah teknis, lakukan perbaikan melalui planner dan executor."
        )

        # ── Step 4: Self review ──
        review = SelfReviewLoop()
        review_data = review.run()

        return {
            "executed": result,
            "review": review_data,
            "knowledge_focus": ke.summary().get("focus"),
        }
