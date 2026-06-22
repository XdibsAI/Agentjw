from pathlib import Path


class AutonomousPlanner:

    def plan(self, audit_result):

        features = audit_result["trace"]["features"]

        missing = []

        for name, files in features.items():
            if not files:
                missing.append(name)


        if missing:
            return {
                "action": "modify_logic",
                "reason": "missing_features",
                "targets": missing
            }


        confidence = audit_result["trace"]["confidence"]

        if confidence < 90:
            return {
                "action": "analyze_project",
                "reason": "low_trace_confidence"
            }


        return {
            "action": "optimize_logic",
            "reason": "all_core_features_exist",
            "targets": [
                "performance",
                "profitability",
                "risk_management"
            ]
        }
