from pathlib import Path
import time


class AutonomousLogicRunner:

    def __init__(self):
        self.results = []


    def run(
        self,
        project_dir,
        next_step
    ):

        agent = next_step.get(
            "next_agent"
        )

        if agent != "logic_modifier":
            return {
                "status": "SKIP",
                "reason": "no_logic_agent"
            }


        project = Path(project_dir).name

        task = {
            "project": project,
            "agent": agent,
            "instruction": next_step.get(
                "instruction"
            ),
            "targets": next_step.get(
                "targets",
                []
            ),
            "timestamp": time.time()
        }


        self.results.append(task)


        return {
            "status": "QUEUED",
            "agent_task": task
        }
