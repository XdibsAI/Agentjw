"""
Compatibility TaskExecutor
"""

import json
from pathlib import Path

ROOT = Path("/home/dibs/agentjw")
QUEUE = ROOT / "memory/task_queue.json"


class TaskExecutor:

    def execute_next(self):

        if not QUEUE.exists():
            return {
                "status": "no_queue"
            }

        try:

            tasks = json.loads(
                QUEUE.read_text()
            )

            if not tasks:
                return {
                    "status": "empty"
                }

            current = tasks.pop(0)

            QUEUE.write_text(
                json.dumps(
                    tasks,
                    indent=2,
                    ensure_ascii=False
                )
            )

            return {
                "status": "executed",
                "task": current
            }

        except Exception as e:

            return {
                "status": "error",
                "error": str(e)
            }
