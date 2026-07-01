import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class TaskQueue:

    def __init__(self):

        self.file = ROOT / "memory" / "task_queue.json"

        if not self.file.exists():

            self.file.write_text("[]")

    def load(self):

        return json.loads(
            self.file.read_text()
        )

    def push(self, task):

        q = self.load()

        q.append(task)

        self.file.write_text(
            json.dumps(
                q,
                indent=2,
                ensure_ascii=False
            )
        )

    def pop(self):

        q = self.load()

        if not q:
            return None

        task = q.pop(0)

        self.file.write_text(
            json.dumps(
                q,
                indent=2,
                ensure_ascii=False
            )
        )

        return task
