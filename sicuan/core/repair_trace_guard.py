from sicuan.project_trace import trace_project


KEYWORDS = {
    "buy": [
        "_should_buy",
        "_open_position",
        "execute_buy",
        "process_new_token"
    ],
    "sell": [
        "_close_position",
        "execute_take_profit",
        "execute_stop_loss"
    ],
    "stoploss": [
        "check_stop_loss",
        "execute_stop_loss"
    ],
    "takeprofit": [
        "check_take_profit",
        "execute_take_profit"
    ],
    "position": [
        "_open_position",
        "_close_position",
        "add_position",
        "remove_position"
    ]
}


def build_repair_context(project_dir: str):

    trace = trace_project(project_dir)

    return {
        "confidence": trace["confidence"],
        "feature_count": len(trace["features"]),
        "function_count": len(trace["functions"]),
        "functions": list(trace["functions"].keys()),
        "calls": trace["calls"],
        "features": trace["features"],

        "features_found": [
            k for k, v in trace["features"].items()
            if v
        ],

        "features_missing": [
            k for k, v in trace["features"].items()
            if not v
        ]
    }


def rank_functions_for_request(ctx, request):

    request = request.lower()

    ranked = []

    for keyword, funcs in KEYWORDS.items():

        if keyword in request:

            for fn in funcs:

                if fn in ctx["functions"]:
                    ranked.append(fn)

    return sorted(set(ranked))


def must_trace_before_repair(project_dir: str):

    ctx = build_repair_context(project_dir)

    if ctx["confidence"] < 70:
        raise RuntimeError(
            f"TRACE CONFIDENCE TOO LOW: {ctx['confidence']}"
        )

    return ctx
