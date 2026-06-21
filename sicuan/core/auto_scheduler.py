import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "memory"

class AutoScheduler:

    def run(self):

        queue_file = MEMORY / "task_queue.json"

        if not queue_file.exists():

            return {
                "status": "no_queue"
            }

        queue = json.loads(
            queue_file.read_text()
        )

        if not queue:

            return {
                "status": "empty"
            }

        state = {
            "current_focus": queue[0],
            "remaining": len(queue),
            "next_action": queue[0]
        }

        (
            MEMORY /
            "executive_state.json"
        ).write_text(
            json.dumps(
                state,
                indent=2
            )
        )

        return state
