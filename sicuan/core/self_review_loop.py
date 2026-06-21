import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "memory"

class SelfReviewLoop:

    def run(self):

        history_file = (
            MEMORY /
            "execution_history.json"
        )

        if not history_file.exists():

            return {
                "completed": 0
            }

        history = json.loads(
            history_file.read_text()
        )

        completed = len(history)

        review = {
            "completed_tasks": completed,
            "last_task":
                history[-1]["task"]
                if history else None,
            "status": "learning"
        }

        (
            MEMORY /
            "self_review.json"
        ).write_text(
            json.dumps(
                review,
                indent=2
            )
        )

        return review
