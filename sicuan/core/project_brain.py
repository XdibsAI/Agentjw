import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class ProjectBrain:

    def scan(self):

        result = {}

        pdir = ROOT / "projects"

        if not pdir.exists():
            return {}

        for p in pdir.iterdir():

            if not p.is_dir():
                continue

            py_count = len(list(p.rglob("*.py")))

            result[p.name] = {
                "path": str(p),
                "python_files": py_count,
                "status": "active"
            }

        out = ROOT / "memory/project_state.json"

        out.write_text(
            json.dumps(result, indent=2)
        )

        return result
