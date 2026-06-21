import json
from pathlib import Path

from sicuan.core.task_executor import TaskExecutor
from sicuan.core.reflection_engine import ReflectionEngine
from sicuan.core.project_brain import ProjectBrain
from sicuan.core.capability_engine import CapabilityEngine
from sicuan.core.workspace_scanner import WorkspaceScanner
from sicuan.core.task_generator import TaskGenerator

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "memory"


class AutonomousController:

    def _load(self, file, default):
        try:
            if file.exists():
                return json.loads(file.read_text())
        except Exception:
            pass
        return default

    def _save(self, file, data):
        file.write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False
            )
        )

    def _generate_tasks(self, result):

        tasks = []

        if not isinstance(result, dict):
            return tasks

        for rec in result.get("recommendations", []):

            r = rec.lower()

            if "volume filter" in r:
                tasks.append("Analyze volume filter")

            elif "marketcap filter" in r:
                tasks.append("Analyze marketcap filter")

        return tasks

    def run_once(self):

        queue_file = MEMORY / "task_queue.json"

        queue = self._load(queue_file, [])

        if not queue:

            projects = ProjectBrain().scan()
            caps = CapabilityEngine().scan()
            workspace = WorkspaceScanner().scan()

            reflection = ReflectionEngine().reflect(
                projects,
                caps,
                workspace
            )

            queue = TaskGenerator().generate(
                reflection
            )

            self._save(
                queue_file,
                queue
            )

        executor = TaskExecutor()

        result = executor.execute_next()

        queue = self._load(
            queue_file,
            []
        )

        new_tasks = self._generate_tasks(
            result
        )

        for task in new_tasks:

            if task not in queue:
                queue.append(task)

        self._save(
            queue_file,
            queue
        )

        projects = ProjectBrain().scan()
        caps = CapabilityEngine().scan()
        workspace = WorkspaceScanner().scan()

        reflection = ReflectionEngine().reflect(
            projects,
            caps,
            workspace
        )

        executive = {
            "current_focus":
                reflection.get("current_focus"),

            "priority":
                reflection.get("priority"),

            "next_action":
                reflection.get("next_action"),

            "remaining_tasks":
                len(queue),

            "last_result":
                result
        }

        self._save(
            MEMORY / "executive_state.json",
            executive
        )

        review = {
            "last_execution": result,
            "generated_tasks": new_tasks,
            "queue_size": len(queue)
        }

        self._save(
            MEMORY / "self_review.json",
            review
        )

        return {
            "result": result,
            "new_tasks": new_tasks,
            "executive": executive
        }


if __name__ == "__main__":
    print(
        AutonomousController().run_once()
    )
