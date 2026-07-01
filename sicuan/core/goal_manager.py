import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class GoalManager:

    def __init__(self):

        self.file = ROOT / "memory" / "goals.json"

        if not self.file.exists():

            self.file.write_text(
                json.dumps({
                    "primary_goal": "",
                    "secondary_goals": [],
                    "completed_tasks": [],
                    "blocked_tasks": []
                }, indent=2)
            )

    def load(self):

        return json.loads(
            self.file.read_text()
        )

    def save(self, data):

        self.file.write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False
            )
        )
