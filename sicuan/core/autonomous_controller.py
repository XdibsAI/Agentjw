from pathlib import Path
import json
import time

from sicuan.core.autonomous_executor import AutonomousExecutor
from sicuan.core.autonomous_action_bridge import AutonomousActionBridge
from sicuan.core.autonomous_logic_runner import AutonomousLogicRunner
from sicuan.core.autonomous_agent_executor import AutonomousAgentExecutor

from sicuan.core.project_autonomy_manager import (
    ProjectAutonomyManager
)


class AutonomousController:

    def __init__(self):
        self.manager = ProjectAutonomyManager()
        self.executor = AutonomousExecutor()
        self.bridge = AutonomousActionBridge()
        self.logic_runner = AutonomousLogicRunner()
        self.agent_executor = AutonomousAgentExecutor()


    def audit(self, project_dir):

        project_dir = Path(project_dir)

        return self.manager.audit_project(
            project_dir
        )


    def decide(self, project_dir):

        project_dir = Path(project_dir)

        return self.manager.next_action(
            project_dir
        )


    def save_cycle_report(self, data):

        memory = Path(
            "memory/autonomy_reports.json"
        )

        memory.parent.mkdir(
            exist_ok=True
        )

        reports = []

        if memory.exists():
            try:
                reports = json.loads(
                    memory.read_text()
                )
            except:
                reports = []

        reports.append(data)

        memory.write_text(
            json.dumps(
                reports[-100:],
                indent=2,
                default=str
            )
        )


    def run_cycle(self, project_dir):

        project_dir = Path(project_dir)

        audit = self.audit(
            project_dir
        )

        decision = self.decide(
            project_dir
        )

        result = {
            "timestamp": time.time(),
            "project": project_dir.name,
            "audit": {
                "confidence":
                audit["trace"]["confidence"],

                "features":
                audit["trace"]["features"],

                "functions":
                list(
                    audit["trace"]["functions"].keys()
                )
            },
            "decision": decision
        }


        execution = self.executor.execute(
            project_dir,
            decision
        )

        result["execution"] = execution

        result["next_step"] = self.bridge.dispatch(
            project_dir,
            execution
        )

        result["logic_task"] = self.logic_runner.run(
            project_dir,
            result["next_step"]
        )

        if result["logic_task"]["status"] == "QUEUED":

            result["agent_result"] = self.agent_executor.execute(
                result["logic_task"]["agent_task"]
            )

        self.save_cycle_report(
            result
        )


        return result
