from pathlib import Path

from sicuan.core.autonomous_project_operator import (
    AutonomousProjectOperator
)

from sicuan.core.autonomous_planner import AutonomousPlanner

from sicuan.core.project_memory_engine import (
    ProjectMemoryEngine
)


class ProjectAutonomyManager:

    def __init__(self):

        self.operator = AutonomousProjectOperator()
        self.memory = ProjectMemoryEngine()
        self.planner = AutonomousPlanner()

    def audit_project(
        self,
        project_dir
    ):

        project_dir = Path(project_dir)

        result = self.operator.inspect(
            project_dir
        )

        self.memory.update_project(
            project_dir.name,
            {
                "confidence":
                result["trace"]["confidence"],

                "features":
                result["trace"]["features"],

                "functions":
                list(
                    result["trace"]["functions"].keys()
                )
            }
        )

        return result

    def next_action(
        self,
        project_dir
    ):

        audit = self.audit_project(
            project_dir
        )

        missing = []

        for feature, files in audit["trace"]["features"].items():

            if not files:
                missing.append(feature)


        if missing:

            return {
                "mode": "repair",
                "action": "modify_logic",
                "reason": "missing_features",
                "targets": missing
            }


        return {
            "mode": "optimization",
            "action": "modify_logic",
            "reason": "all_core_features_exist",
            "targets": [
                "performance",
                "profitability",
                "risk_management"
            ]
        }
