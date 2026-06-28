from sicuan.project_trace import trace_project

CRITICAL_FLOWS = {
    "trading": [
        "_should_buy",
        "_open_position",
        "_monitor_positions",
        "_close_position"
    ],
    "paper_wallet": [
        "load_paper_balance",
        "save_paper_balance"
    ]
}


def analyze_runtime_flow(project_dir):

    trace = trace_project(project_dir)

    calls = trace["calls"]

    result = {}

    for flow_name, flow in CRITICAL_FLOWS.items():

        status = []

        for fn in flow:

            status.append(
                {
                    "function": fn,
                    "exists": fn in trace["functions"]
                }
            )

        result[flow_name] = status

    return result
