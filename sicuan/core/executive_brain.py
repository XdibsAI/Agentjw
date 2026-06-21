import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class ExecutiveBrain:

    def __init__(
        self,
        capability_engine,
        workspace_scanner,
        project_brain,
        reflection_engine
    ):
        self.capability_engine = capability_engine
        self.workspace_scanner = workspace_scanner
        self.project_brain = project_brain
        self.reflection_engine = reflection_engine

    def think(self):

        caps = self.capability_engine.scan()
        workspace = self.workspace_scanner.scan()
        reflection = self.reflection_engine.reflect()

        projects = workspace.get("projects", {})

        active_projects = []

        for name, data in projects.items():

            active_projects.append({
                "name": name,
                "files": data.get("python_files", 0)
            })

        active_projects.sort(
            key=lambda x: x["files"],
            reverse=True
        )

        focus = None

        if active_projects:
            focus = active_projects[0]["name"]

        next_actions = []

        if focus:

            next_actions.extend([
                f"review project {focus}",
                f"analyze {focus}",
                "codebase health check"
            ])

        state = {
            "focus": focus,
            "capabilities": caps,
            "project_count": len(projects),
            "next_actions": next_actions,
            "reflection": reflection
        }

        out = ROOT / "memory" / "executive_state.json"

        out.write_text(
            json.dumps(
                state,
                indent=2,
                ensure_ascii=False
            )
        )

        return state
