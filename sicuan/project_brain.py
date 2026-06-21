import json
from pathlib import Path

ROOT = Path(__file__).parent.parent

class ProjectBrain:

    def scan(self):

        projects = {}

        pdir = ROOT / "projects"

        if not pdir.exists():
            return {}

        for p in pdir.iterdir():

            if not p.is_dir():
                continue

            projects[p.name] = {
                "path": str(p),
                "status": "active"
            }

        out = ROOT / "memory/project_state.json"

        out.write_text(
            json.dumps(projects, indent=2)
        )

        return projects
