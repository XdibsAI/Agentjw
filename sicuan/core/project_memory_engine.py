import json
from pathlib import Path

MEMORY_FILE = Path("memory/project_autonomy.json")


class ProjectMemoryEngine:

    def __init__(self):
        MEMORY_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not MEMORY_FILE.exists():
            MEMORY_FILE.write_text("{}")

    def load(self):
        return json.loads(
            MEMORY_FILE.read_text()
        )

    def save(self, data):
        MEMORY_FILE.write_text(
            json.dumps(
                data,
                indent=2
            )
        )

    def update_project(
        self,
        project_name,
        payload
    ):
        data = self.load()
        data[project_name] = payload
        self.save(data)

    def get_project(
        self,
        project_name
    ):
        return self.load().get(
            project_name,
            {}
        )
