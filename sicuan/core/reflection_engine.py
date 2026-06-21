import json
from pathlib import Path
from memory.project_registry import ProjectRegistry

ROOT = Path(__file__).resolve().parents[2]

class ReflectionEngine:

    def reflect(
        self,
        projects,
        capabilities,
        workspace
    ):

        state = {
            "current_focus": None,
            "priority": [],
            "problems": [],
            "waiting_user": [],
            "next_action": None
        }

        registry = ProjectRegistry()

        items = registry.list_projects()

        if items:

            state["current_focus"] = items[0][0]

        missing = []

        for name, status in capabilities.items():

            if not status:
                missing.append(name)

        if missing:

            state["problems"].append(
                f"Missing capabilities: {', '.join(missing)}"
            )

        if workspace.get("python_files", 0) == 0:

            state["problems"].append(
                "No python files detected"
            )

        focus = state.get("current_focus")

        if focus:

            project_log = (
                ROOT /
                "projects" /
                focus /
                "trading_bot.log"
            )

            if project_log.exists():

                try:

                    txt = project_log.read_text(
                        errors="ignore"
                    )

                    if (
                        "TOTAL TOKENS: 0" in txt
                        or
                        "scanner returning zero tokens" in txt.lower()
                    ):
                        state["problems"].append(
                            "Scanner returning zero tokens"
                        )

                except Exception:
                    pass

        out = ROOT / "memory/reflection_state.json"

        out.write_text(
            json.dumps(
                state,
                indent=2
            )
        )

        return state
