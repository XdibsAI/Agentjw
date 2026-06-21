from pathlib import Path
import time


class AutonomousExecutor:

    def execute(
        self,
        project_dir,
        decision
    ):

        action = decision.get(
            "action"
        )

        mode = decision.get(
            "mode"
        )


        if mode == "optimization":

            return {
                "status": "READY",
                "mode": "optimization",
                "project": Path(project_dir).name,
                "tasks": decision.get(
                    "targets",
                    []
                ),
                "timestamp": time.time()
            }


        if mode == "repair":

            return {
                "status": "READY",
                "mode": "repair",
                "project": Path(project_dir).name,
                "targets": decision.get(
                    "targets",
                    []
                ),
                "timestamp": time.time()
            }


        if action == "analyze_project":

            return {
                "status": "ANALYZED",
                "mode": "analysis",
                "project": Path(project_dir).name,
                "timestamp": time.time()
            }


        return {
            "status": "NO_ACTION",
            "reason": decision
        }
