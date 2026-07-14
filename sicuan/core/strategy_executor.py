"""
StrategyExecutor — thin queue-management layer used by
AutonomousRefactorLoop to add and retrieve refactor/analysis tasks.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
QUEUE_FILE = ROOT / "memory" / "refactor_task_queue.json"


class StrategyExecutor:
    def __init__(self, queue_file: Path = QUEUE_FILE):
        self.queue_file = queue_file
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_queue(self) -> List[Dict]:
        if not self.queue_file.exists():
            return []
        try:
            return json.loads(self.queue_file.read_text())
        except Exception:
            return []

    def _save_queue(self, queue: List[Dict]) -> None:
        self.queue_file.write_text(json.dumps(queue, indent=2))

    def push_to_queue(self, tasks: Optional[List[Dict]] = None) -> Dict:
        queue = self._load_queue()
        added = []
        for t in (tasks or []):
            if t not in queue:
                queue.append(t)
                added.append(t)
        self._save_queue(queue)
        return {"added": added, "queue_size": len(queue)}

    def inject_tasks(self, recommendations: List[str]) -> Dict:
        tasks = [
            {"action": "strategy_recommendation", "recommendations": [r]}
            for r in recommendations
        ]
        return self.push_to_queue(tasks)
