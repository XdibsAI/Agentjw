from sicuan.project_trace import trace_project
from sicuan.core.repair_trace_guard import (
    build_repair_context,
    rank_functions_for_request,
)


class AutonomousProjectOperator:

    def inspect(self, project_dir):

        trace = trace_project(project_dir)
        ctx = build_repair_context(project_dir)

        return {
            "trace": trace,
            "repair_context": ctx,
        }

    def determine_missing_features(self, trace):

        missing = []

        for feature, files in trace["features"].items():
            if not files:
                missing.append(feature)

        return missing

    def determine_targets(
        self,
        project_dir,
        instruction
    ):
        ctx = build_repair_context(project_dir)

        return rank_functions_for_request(
            ctx,
            instruction
        )
