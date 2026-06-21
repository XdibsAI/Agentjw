from pathlib import Path


class AutonomousActionBridge:

    def __init__(self):
        self.history = []


    def dispatch(
        self,
        project_dir,
        execution
    ):

        mode = execution.get("mode")


        if mode == "optimization":

            return {
                "next_agent": "logic_modifier",
                "instruction": (
                    f"Optimize {Path(project_dir).name} "
                    "for performance, profitability, risk management"
                ),
                "targets": execution.get(
                    "tasks",
                    []
                )
            }


        if mode == "repair":

            return {
                "next_agent": "logic_modifier",
                "instruction": (
                    f"Repair missing features "
                    f"in {Path(project_dir).name}"
                ),
                "targets": execution.get(
                    "targets",
                    []
                )
            }


        return {
            "next_agent": None,
            "instruction": "no action"
        }
