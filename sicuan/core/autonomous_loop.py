"""
AutonomousLoop — LLM-driven, bukan keyword parsing.
Scheduler lama tetap jalan untuk morning briefing & trading monitor.
"""
from sicuan.core.auto_scheduler import AutoScheduler
from sicuan.core.self_review_loop import SelfReviewLoop
from sicuan.core.knowledge_engine import KnowledgeEngine
from sicuan.core.llm_task_executor import LLMTaskExecutor


class AutonomousLoop:

    def run(self):

        # ── Step 1: Scheduler (morning briefing, trading monitor) ──
        scheduler = AutoScheduler()
        scheduler.run()

        # ── Step 2: Load knowledge context ──
        ke = KnowledgeEngine()
        knowledge = ke.load_all()

        # ── Step 3: LLM decide + execute (1 siklus) ──
        executor = LLMTaskExecutor()
        result = executor.run_cycle()

        # ── Step 4: Self review ──
        review = SelfReviewLoop()
        review_data = review.run()

        return {
            "executed": result,
            "review": review_data,
            "knowledge_focus": ke.summary().get("focus"),
        }
