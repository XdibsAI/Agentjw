import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "memory"

class TaskGenerator:

    def generate(self, reflection):

        tasks = []

        focus = reflection.get("current_focus")

        if focus:

            tasks.extend([
                f"Analyze {focus}",
                f"Review project {focus}",
                "Codebase health check"
            ])

        for p in reflection.get(
            "problems",
            []
        ):
            tasks.append(
                f"Fix: {p}"
            )

        return list(
            dict.fromkeys(tasks)
        )
