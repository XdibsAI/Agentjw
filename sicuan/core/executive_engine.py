import json
from sicuan.adapters.project_adapter import get_project_adapter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MEMORY = ROOT / "memory"

class ExecutiveEngine:

    def _load_json(self, path, default):
        try:
            if path.exists():
                return json.loads(path.read_text())
        except Exception:
            pass
        return default

    def run(self):

        goals = self._load_json(
            MEMORY / "goals.json",
            {}
        )

        projects = self._load_json(
            MEMORY / "project_state.json",
            {}
        )

        workspace = self._load_json(
            MEMORY / "workspace_state.json",
            {}
        )

        capabilities = self._load_json(
            MEMORY / "capabilities.json",
            {}
        )

        reflection = self._load_json(
            MEMORY / "reflection_state.json",
            {}
        )

        queue = []

        problems = reflection.get(
            "problems",
            []
        )

        # =========================
        # PROBLEM DRIVEN TASKS
        # =========================

        for problem in problems:

            p = problem.lower()

            if "scanner" in p:
                queue.append(
                    "Analyze strategy.py"
                )

                queue.append(
                    "Find token source issue"
                )

                queue.append(
                    "Validate DexScreener filters"
                )

            elif "capabilities" in p:

                queue.append(
                    "Repair capability detection"
                )

            else:

                queue.append(
                    f"Investigate: {problem}"
                )

        # =========================
        # PROJECT DRIVEN TASKS
        # =========================

        
        items = adapter.get_projects()

        if items:

            project_name = items[0][0]

            queue.extend([
                f"Review project {project_name}",
                f"Analyze {project_name}",
                f"Validate logic {project_name}",
                f"Improve project {project_name}"
            ])

        # =========================
        # WORKSPACE DRIVEN TASKS
        # =========================

        if workspace.get("python_files", 0) > 50:

            queue.append(
                "Maintain codebase health"
            )

        # =========================
        # REMOVE DUPLICATES
        # =========================

        seen = set()

        final_queue = []

        for task in queue:

            if task not in seen:

                final_queue.append(task)

                seen.add(task)

        state = {

            "current_focus":
                final_queue[0]
                if final_queue else None,

            "priority":
                final_queue,

            "next_action":
                final_queue[0]
                if final_queue else "idle"
        }

        (MEMORY / "task_queue.json").write_text(
            json.dumps(
                final_queue,
                indent=2
            )
        )

        (MEMORY / "executive_state.json").write_text(
            json.dumps(
                state,
                indent=2
            )
        )

        return state
