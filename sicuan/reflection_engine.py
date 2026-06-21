import json
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent

class ReflectionEngine:

    def save(self, task, result, lesson):

        path = ROOT / "memory/reflections.json"

        if path.exists():
            data = json.loads(path.read_text())
        else:
            data = []

        data.append({
            "time": time.time(),
            "task": task,
            "result": result,
            "lesson": lesson
        })

        path.write_text(
            json.dumps(data[-500:], indent=2)
        )
